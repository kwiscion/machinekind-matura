"""Small, portable runner for OpenAI-compatible chat-completions endpoints."""

from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


MAX_CALLS = 100
MAX_OUTPUT_TOKENS = 4096
MAX_IMAGE_BYTES = 20 * 1024 * 1024
IMAGE_TYPES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError(f"HTTP redirect refused ({code}); configure the final endpoint URL")


def is_loopback_host(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host.lower() == "localhost"


class LoopbackDirectProxyHandler(urllib.request.ProxyHandler):
    def proxy_open(self, request, proxy, type):
        # Never send an explicitly local model request through inherited proxies.
        host = urllib.parse.urlsplit(request.full_url).hostname or ""
        if is_loopback_host(host):
            return None
        return super().proxy_open(request, proxy, type)


OPENER = urllib.request.build_opener(LoopbackDirectProxyHandler, NoRedirect)


def endpoint_url(base_url: str, allow_remote: bool) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("base_url must be an http(s) URL with a host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base_url cannot contain credentials, query, or fragment")
    loopback = is_loopback_host(parsed.hostname)
    if not loopback and not allow_remote:
        raise ValueError("Remote endpoint refused; pass --allow-remote explicitly")
    if not loopback and parsed.scheme != "https":
        raise ValueError("Remote endpoints must use HTTPS")
    return base_url.rstrip("/") + "/chat/completions"


def load_config(path: Path, allow_remote: bool) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object")
    for field in ("name", "base_url", "model"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f"Config requires nonempty string: {field}")
    config["endpoint"] = endpoint_url(config["base_url"], allow_remote)
    tokens = config.get("max_output_tokens", 512)
    timeout = config.get("timeout_seconds", 120)
    if type(tokens) is not int or not 1 <= tokens <= MAX_OUTPUT_TOKENS:
        raise ValueError(f"max_output_tokens must be an integer from 1 to {MAX_OUTPUT_TOKENS}")
    if type(timeout) not in (int, float) or not 1 <= timeout <= 600:
        raise ValueError("timeout_seconds must be a number from 1 to 600")
    config["max_output_tokens"] = tokens
    config["timeout_seconds"] = timeout
    effort = config.get("reasoning_effort")
    if effort is not None and effort not in ("none", "low", "medium", "high"):
        raise ValueError("reasoning_effort must be none, low, medium, or high")
    if "model_revision" in config and not isinstance(config["model_revision"], str):
        raise ValueError("model_revision must be a string when provided")
    key_name = config.get("api_key_env")
    if key_name is not None:
        if not isinstance(key_name, str) or not key_name:
            raise ValueError("api_key_env must name an environment variable")
        if not os.environ.get(key_name):
            raise ValueError(f"Environment variable {key_name} is not set")
    return config


def image_data_url(path: Path) -> str:
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds {MAX_IMAGE_BYTES} bytes: {path}")
    data = path.read_bytes()
    mime = next((value for magic, value in IMAGE_TYPES.items() if data.startswith(magic)), None)
    if mime is None and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    if mime is None:
        raise ValueError(f"Unsupported image format: {path}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def load_cases(path: Path, max_calls: int) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if len(cases) >= max_calls:
            raise ValueError(f"Input exceeds --max-calls ({max_calls}); no requests sent")
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise ValueError(f"Line {line_number} requires a nonempty string id")
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise ValueError(f"Line {line_number} requires a nonempty string prompt")
        images = case.get("images", [])
        if not isinstance(images, list) or any(not isinstance(item, str) for item in images):
            raise ValueError(f"Line {line_number}: images must be a list of local paths")
        content = [{"type": "text", "text": case["prompt"]}]
        for item in images:
            image_path = Path(item)
            if not image_path.is_absolute():
                image_path = path.parent / image_path
            content.append({"type": "image_url", "image_url": {"url": image_data_url(image_path)}})
        cases.append({"id": case["id"], "content": content if images else case["prompt"]})
    if not cases:
        raise ValueError("Input has no cases")
    return cases


def response_error(answer: object) -> dict | None:
    if not isinstance(answer, dict):
        return {"type": "invalid_response", "message": "Response is not a JSON object"}
    if "error" in answer and answer["error"] is not None:
        detail = answer["error"]
        message = detail.get("message") if isinstance(detail, dict) else detail
        return {"type": "provider", "message": str(message or "Provider returned an error object")}
    choices = answer.get("choices")
    if not isinstance(choices, list) or not choices:
        return {"type": "invalid_response", "message": "Response has no choices"}
    for choice in choices:
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            continue
        content = choice["message"].get("content")
        if isinstance(content, str):
            usable = bool(content.strip())
        elif isinstance(content, list):
            usable = any(isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip() for part in content)
        else:
            usable = False
        if usable and choice.get("finish_reason") != "length":
            return None
    return {"type": "incomplete", "message": "No complete choice contains a nonempty final answer"}


def run_case(case: dict, config: dict) -> dict:
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": case["content"]}],
        "max_tokens": config["max_output_tokens"],
    }
    if config.get("reasoning_effort") is not None:
        payload["reasoning_effort"] = config["reasoning_effort"]
    headers = {"Content-Type": "application/json"}
    if config.get("api_key_env"):
        headers["Authorization"] = "Bearer " + os.environ[config["api_key_env"]]
    request = urllib.request.Request(
        config["endpoint"],
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    result = {
        "id": case["id"],
        "backend": {
            "name": config["name"],
            "base_url": config["base_url"],
            "model": config["model"],
            "model_revision": config.get("model_revision"),
            "response_model": None,
            "response_id": None,
            "system_fingerprint": None,
        },
        "raw_response": None,
        "usage": None,
        "latency_seconds": None,
        "error": None,
    }
    start = time.monotonic()
    try:
        with OPENER.open(request, timeout=config["timeout_seconds"]) as response:
            raw = response.read()
        result["raw_response"] = raw.decode("utf-8", errors="replace")
        answer = json.loads(result["raw_response"])
        result["raw_response"] = answer
        if isinstance(answer, dict):
            result["usage"] = answer.get("usage")
            result["backend"]["response_model"] = answer.get("model")
            result["backend"]["response_id"] = answer.get("id")
            result["backend"]["system_fingerprint"] = answer.get("system_fingerprint")
        result["error"] = response_error(answer)
    except urllib.error.HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        try:
            result["raw_response"] = json.loads(detail)
        except json.JSONDecodeError:
            result["raw_response"] = detail
        result["error"] = {"type": "http", "status": exc.code, "message": detail}
    except (urllib.error.URLError, ValueError, json.JSONDecodeError, TimeoutError, OSError) as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        result["latency_seconds"] = round(time.monotonic() - start, 3)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-calls", type=int, default=20, help=f"1-{MAX_CALLS}; default 20")
    parser.add_argument("--allow-remote", action="store_true", help="Allow HTTPS non-loopback endpoint")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs; send no requests and write no output")
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.max_calls <= MAX_CALLS:
            raise ValueError(f"--max-calls must be 1-{MAX_CALLS}")
        config = load_config(args.config, args.allow_remote)
        cases = load_cases(args.input, args.max_calls)
        if args.dry_run:
            print(json.dumps({"cases": len(cases), "backend": config["name"], "model": config["model"], "endpoint": config["endpoint"], "max_output_tokens": config["max_output_tokens"]}))
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        failures = 0
        with args.output.open("x", encoding="utf-8") as output:
            for case in cases:
                result = run_case(case, config)
                output.write(json.dumps(result, ensure_ascii=False) + "\n")
                output.flush()
                failures += result["error"] is not None
        print(f"Wrote {len(cases)} results to {args.output} ({failures} errors)")
        return 1 if failures else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
