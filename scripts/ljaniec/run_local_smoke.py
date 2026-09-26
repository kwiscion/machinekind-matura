#!/usr/bin/env python3
"""Measure an already running, offline OpenAI-compatible model server.

Only localhost is accepted. Pass a JSONL with id/prompt and optional local
image paths. Model weights are verified on disk before any request. No exam
answer keys are read by this script.
"""

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import pathlib
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_records(paths):
    records = []
    for name in paths:
        path = pathlib.Path(name).resolve()
        if not path.is_file():
            raise ValueError(f"Missing file: {path}")
        records.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return records


def verify_pinned_candidate(catalog_path, name, repo, revision, weights):
    catalog = json.loads(pathlib.Path(catalog_path).read_text(encoding="utf-8"))
    candidate = next((c for c in catalog["candidates"] if c["name"] == name), None)
    if candidate is None:
        raise ValueError(f"Candidate {name!r} not found in {catalog_path}")
    if candidate["repository"] != repo or candidate["revision"] != revision:
        raise ValueError("Model repository/revision differs from pinned candidate")
    expected = {item["name"]: item for item in candidate["files"]}
    actual = {pathlib.Path(item["path"]).name: item for item in weights}
    if set(expected) != set(actual) or len(actual) != len(weights):
        raise ValueError("Served weight/projector filenames differ from pinned candidate")
    for filename, item in actual.items():
        if item["bytes"] != expected[filename]["bytes"] or item["sha256"].lower() != expected[filename]["sha256_reported"].lower():
            raise ValueError(f"Downloaded file differs from pinned metadata: {filename}")
    return sha256(catalog_path)


def load_prompts(path):
    rows = []
    seen = set()
    with open(path, encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("prompt"), str):
                raise ValueError(f"{path}:{line_no}: expected string id and prompt")
            if row["id"] in seen:
                raise ValueError(f"{path}:{line_no}: duplicate id {row['id']}")
            images = row.get("images", [])
            if not isinstance(images, list) or any(not isinstance(image, str) for image in images):
                raise ValueError(f"{path}:{line_no}: images must be a list of local paths")
            seen.add(row["id"])
            rows.append(row)
    if not rows:
        raise ValueError("Input JSONL is empty")
    return rows


def cpu_rss_bytes(pid):
    if not pid:
        return None
    try:
        status = pathlib.Path(f"/proc/{pid}/status").read_text()
        match = re.search(r"^VmRSS:\s+(\d+) kB$", status, re.MULTILINE)
        return int(match.group(1)) * 1024 if match else None
    except OSError:
        return None


def gpu_used_bytes():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, capture_output=True, timeout=2, check=True,
        )
        return sum(int(v.strip()) for v in result.stdout.splitlines()) * 1024 * 1024
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def sample_memory(stop, samples, pid):
    while not stop.wait(0.1):
        samples.append({"cpu_rss_bytes": cpu_rss_bytes(pid), "gpu_total_used_bytes": gpu_used_bytes()})


def message_content(row, input_dir, image_mode):
    if not row.get("images"):
        return row["prompt"]
    if image_mode == "text-only":
        raise ValueError("image input omitted from text-only run")
    content = [{"type": "text", "text": row["prompt"]}]
    for name in row["images"]:
        path = (input_dir / name).resolve()
        if not path.is_relative_to(input_dir):
            raise ValueError(f"image path leaves input directory: {name}")
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError(f"unsupported image type: {name}")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}})
    return content


def request(url, model, content, timeout, max_tokens, seed):
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    start = time.monotonic()
    try:
        with LOCAL_OPENER.open(req, timeout=timeout) as response:
            body = json.load(response)
        error = None
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        body, error = None, str(exc)
    latency = time.monotonic() - start
    choice, content, usage = {}, None, {}
    if error is None:
        if not isinstance(body, dict):
            error = "response must be a JSON object"
        else:
            choices = body.get("choices")
            usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                error = "response contained no valid assistant choice"
            else:
                choice = choices[0]
                message = choice.get("message")
                if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                    error = "response contained no string assistant content"
                else:
                    content = message["content"]
                    if not content.strip():
                        error = "response contained empty assistant content"
                    elif choice.get("finish_reason") == "length":
                        error = "response was cut off by the token limit"
    result = {"usage": usage,
              "finish_reason": choice.get("finish_reason"), "latency_s": round(latency, 3),
              "error": error, "raw_api_response": body}
    if content is not None:
        result["raw_response"] = content
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL with id/prompt; never include keys")
    parser.add_argument("--output", required=True, help="new append-only raw JSONL output")
    parser.add_argument("--manifest", required=True, help="new run manifest JSON")
    parser.add_argument("--model-file", action="append", required=True, help="repeat for every served weight shard")
    parser.add_argument("--vision-file", action="append", default=[], help="repeat for projector/vision weights")
    parser.add_argument("--adapter-file", action="append", default=[], help="LoRA bytes reported separately")
    parser.add_argument("--model-repo", required=True)
    parser.add_argument("--revision", required=True, help="immutable model repository commit SHA")
    parser.add_argument("--license", required=True)
    parser.add_argument("--quantization", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--model-id", required=True, help="model name served by the local API")
    parser.add_argument("--candidate-name", help="enforce exact files, bytes, hashes, repository and revision from pinned catalog")
    parser.add_argument("--candidate-catalog", default=str(pathlib.Path(__file__).with_name("model_candidates.json")))
    parser.add_argument("--split", required=True, choices=["DEV", "TRAIN", "VALIDATION"])
    parser.add_argument("--image-mode", choices=["text-only", "send"], default="text-only",
                        help="skip image items with an error, or send local images to localhost server")
    parser.add_argument("--server-url", default="http://127.0.0.1:8080/v1/chat/completions")
    parser.add_argument("--server-pid", type=int, help="sample RSS for this existing server process")
    parser.add_argument("--server-command", required=True, help="exact offline command used to start the server")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--manifest-only", action="store_true", help="validate files/input without querying server")
    args = parser.parse_args()
    parsed = urlparse(args.server_url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("--server-url must be local HTTP")
    if args.max_tokens <= 0 or args.timeout <= 0:
        parser.error("token and timeout limits must be positive")
    if pathlib.Path(args.output).exists() or pathlib.Path(args.manifest).exists():
        parser.error("output/manifest already exists; runs are append-only")

    weights = source_records(args.model_file + args.vision_file)
    adapters = source_records(args.adapter_file)
    catalog_sha = verify_pinned_candidate(args.candidate_catalog, args.candidate_name, args.model_repo, args.revision, weights) if args.candidate_name else None
    weight_bytes = sum(item["bytes"] for item in weights)
    if weight_bytes > 8_000_000_000:
        parser.error(f"saved served weights total {weight_bytes} bytes, above 8,000,000,000")
    prompts = load_prompts(args.input)
    manifest = {
        "run_id": args.run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_repo": args.model_repo, "revision": args.revision, "license": args.license,
        "quantization": args.quantization, "template": args.template, "model_id": args.model_id,
        "weights": weights, "saved_served_weight_bytes": weight_bytes,
        "candidate_name": args.candidate_name, "candidate_catalog_sha256": catalog_sha,
        "adapters": adapters, "adapter_bytes_separate": sum(x["bytes"] for x in adapters),
        "input_sha256": sha256(args.input), "input_count": len(prompts), "split": args.split,
        "image_mode": args.image_mode,
        "server_command": args.server_command, "server_url": args.server_url,
        "server_pid": args.server_pid, "machine": os.uname().nodename,
        "max_tokens": args.max_tokens, "seed": args.seed, "timeout_seconds": args.timeout,
        "status": "manifest-only" if args.manifest_only else "running",
    }
    if args.manifest_only:
        pathlib.Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print(f"Verified {len(prompts)} prompts and {weight_bytes} served weight bytes")
        return

    with open(args.manifest, "x", encoding="utf-8") as initial_manifest:
        initial_manifest.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    baseline_gpu = gpu_used_bytes()
    samples, stop = [], threading.Event()
    sampler = threading.Thread(target=sample_memory, args=(stop, samples, args.server_pid), daemon=True)
    sampler.start()
    errors = 0
    image_skips = 0
    latencies = []
    written = 0
    run_failure = None
    input_dir = pathlib.Path(args.input).resolve().parent
    try:
        with open(args.output, "x", encoding="utf-8") as output:
            for row in prompts:
                try:
                    content = message_content(row, input_dir, args.image_mode)
                    result = request(args.server_url, args.model_id, content, args.timeout, args.max_tokens, args.seed)
                except (OSError, ValueError) as exc:
                    result = {"usage": {}, "latency_s": 0.0, "error": str(exc)}
                    image_skips += bool(row.get("images") and args.image_mode == "text-only")
                result.update({"id": row["id"], "run_id": args.run_id, "backend": "llama.cpp-local",
                               "model": args.model_repo, "model_revision": args.revision})
                errors += bool(result["error"])
                if "raw_api_response" in result:
                    latencies.append(result["latency_s"])
                output.write(json.dumps(result, ensure_ascii=False) + "\n")
                output.flush()
                written += 1
    except BaseException as exc:
        run_failure = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        stop.set()
        sampler.join(timeout=3)
        manifest.update({
            "status": "failed" if run_failure else ("completed" if errors == 0 else "completed-with-errors"),
            "run_failure": run_failure,
            "output_sha256": sha256(args.output) if pathlib.Path(args.output).is_file() else None,
            "output_count": written, "errors": errors,
            "image_items_skipped": image_skips,
            "latency_median_seconds": statistics.median(latencies) if latencies else None,
            "latency_max_seconds": max(latencies) if latencies else None,
            "baseline_gpu_total_used_bytes": baseline_gpu,
            "peak_gpu_total_used_bytes": max((x["gpu_total_used_bytes"] for x in samples if x["gpu_total_used_bytes"] is not None), default=None),
            "peak_server_cpu_rss_bytes": max((x["cpu_rss_bytes"] for x in samples if x["cpu_rss_bytes"] is not None), default=None),
            "memory_note": "GPU metric is total device use during requests and may include other processes; 100 ms sampling can miss peaks. Server load peak is not captured.",
        })
        pathlib.Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"{written} outputs, {errors} errors; manifest: {args.manifest}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
