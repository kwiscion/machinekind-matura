"""Bounded native Ollama lab. Default/check mode validates locally without HTTP.

Panel rows retain infer.py's id/prompt/images and declare families explicitly:
  families: [{"name":"baseline"}, {"name":"thinking"}, {"name":"critic"},
             {"name":"pf_statementwise", "statements":[{"id":"1","text":"..."}]}]
Optional readiness:true rows require baseline and readiness_expected_answer;
they count toward all budgets and must match the original synthetic expected answer.
Private envelopes contain source text, images and thinking; never publish them.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import infer

MODEL = "gemma4:12b-it-q4_K_M"
DIGEST = "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"
ASSETS = {
    "1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606": 7381382048,
    "675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842": 175115584,
}
PRIVATE_ROOT = ROOT / "agentsLog" / "ljaniec" / "private"
FAMILIES = {"baseline", "thinking", "critic", "pf_statementwise"}
DISPATCH_ORDER = ["baseline", "pf_statementwise", "critic", "thinking"]
MAX_CALLS, MAX_TOKENS, MAX_SECONDS = 120, 240000, 5400


class StopWave(RuntimeError):
    """No further generation is permitted in this wave."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def nonempty(value, field):
    if not isinstance(value, str) or not value.strip() or "PLACEHOLDER" in value.upper():
        raise ValueError(f"Missing actual {field}")
    return value


def load_manifest(path):
    m = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(m, dict):
        raise ValueError("Manifest must be an object")
    for key in ("run_id", "owner", "host", "runtime", "base_url", "input_sha256", "deadline_utc"):
        nonempty(m.get(key), key)
    if m["owner"] != "ljaniec" or m["runtime"] != "ollama-0.34.4":
        raise ValueError("Require ljaniec's actual Ollama 0.34.4 runtime")
    if m.get("model") != MODEL or m.get("model_digest") != DIGEST:
        raise ValueError("Pinned native model/digest required")
    if m.get("context_length") != 32768 or m.get("assets") != ASSETS:
        raise ValueError("Pinned context32768 and model/projector hashes+bytes required")
    if not re.fullmatch(r"[0-9a-f]{64}", m["input_sha256"]):
        raise ValueError("input_sha256 must be SHA256")
    parsed = urllib.parse.urlsplit(m["base_url"])
    if (parsed.scheme != "http" or not parsed.hostname or not infer.is_loopback_host(parsed.hostname)
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("Native endpoint must be a plain loopback HTTP origin")
    # Numeric literals prevent DNS from resolving localhost elsewhere; inherited proxies are disabled.
    if parsed.hostname.lower() == "localhost":
        raise ValueError("Use literal loopback IP, not a DNS name")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Invalid endpoint port") from exc
    rate = m.get("hourly_rate_usd")
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
        raise ValueError("Actual positive hourly_rate_usd required")
    for field, upper in (("max_calls", MAX_CALLS), ("max_requested_tokens", MAX_TOKENS),
                         ("max_wall_seconds", MAX_SECONDS), ("timeout_seconds", 600)):
        if type(m.get(field)) is not int or not 1 <= m[field] <= upper:
            raise ValueError(f"{field} must be an integer in 1..{upper}")
    if m.get("dispatch_order") != DISPATCH_ORDER:
        raise ValueError("dispatch_order must freeze baseline, PF, critic, thinking in that order")
    if type(m.get("num_predict")) is not int or m["num_predict"] not in (1024, 2048):
        raise ValueError("num_predict must be 1024 or 2048, including thinking")
    if type(m.get("readiness_calls")) is not int or not 0 <= m["readiness_calls"] <= 2:
        raise ValueError("readiness_calls must be 0..2, included in wave caps")
    if not m["deadline_utc"].endswith("Z"):
        raise ValueError("deadline_utc must be explicit UTC ending Z")
    deadline = datetime.fromisoformat(m["deadline_utc"].replace("Z", "+00:00"))
    if deadline.tzinfo != timezone.utc:
        raise ValueError("deadline_utc must be UTC")
    m["deadline_epoch"] = deadline.timestamp()
    m["manifest_file_sha256"] = sha256(path)
    m["controller_sha256"] = sha256(__file__)
    return m


def native_source(case):
    content = case["content"]
    if isinstance(content, str):
        return content, []
    text = content[0]["text"]
    images = []
    for part in content[1:]:
        uri = part["image_url"]["url"]
        prefix, encoded = uri.split(",", 1)
        if not prefix.startswith("data:image/") or not prefix.endswith(";base64"):
            raise ValueError("Only infer.py local encoded images accepted")
        base64.b64decode(encoded, validate=True)
        images.append(encoded)
    return text, images


def load_panel(path, manifest):
    # Hash and parse the same bytes. infer.py may read separately, so validate
    # its cached ID/text/ordered decoded image bytes against this frozen snapshot.
    panel_bytes = Path(path).read_bytes()
    if hashlib.sha256(panel_bytes).hexdigest() != manifest["input_sha256"]:
        raise ValueError("Panel SHA256 differs from declared input")
    raw = [json.loads(line) for line in panel_bytes.decode("utf-8").splitlines() if line.strip()]
    cases = infer.load_cases(Path(path), MAX_CALLS)
    if len(raw) != len(cases):
        raise ValueError("Panel changed while loading cases")
    image_hashes = manifest.get("image_hashes")
    if not isinstance(image_hashes, dict):
        raise ValueError("Manifest requires ordered input asset image_hashes mapping (empty for no images)")
    referenced = set()
    for case, row in zip(cases, raw):
        text, encoded_images = native_source(case)
        images = row.get("images", [])
        if case["id"] != row.get("id") or text != row.get("prompt") or len(images) != len(encoded_images):
            raise ValueError("Panel changed while loading ID/prompt/images")
        for image, encoded in zip(images, encoded_images):
            referenced.add(image)
            cached_digest = hashlib.sha256(base64.b64decode(encoded, validate=True)).hexdigest()
            if cached_digest != image_hashes.get(image):
                raise ValueError("Cached image bytes differ from declared image_hashes")
    if set(image_hashes) != referenced:
        raise ValueError("image_hashes must exactly cover panel image paths")
    seen, family_names, readiness = set(), set(), 0
    tasks, calls = [], 0
    for case, row in zip(cases, raw):
        if case["id"] in seen:
            raise ValueError("Duplicate input ID")
        seen.add(case["id"])
        if type(row.get("readiness", False)) is not bool:
            raise ValueError("readiness must be boolean")
        is_ready = row.get("readiness", False)
        if is_ready:
            nonempty(row.get("readiness_expected_answer"), "synthetic readiness expected answer")
        elif "readiness_expected_answer" in row:
            raise ValueError("readiness_expected_answer is only allowed for original synthetic readiness rows")
        families = row.get("families")
        if not isinstance(families, list) or not families:
            raise ValueError("Every panel row must explicitly declare families")
        names = set()
        for family in families:
            if not isinstance(family, dict) or family.get("name") not in FAMILIES:
                raise ValueError("Unknown structured family")
            name = family["name"]
            if name in names or set(family) - {"name", "statements"}:
                raise ValueError("Duplicate family or unknown family fields")
            names.add(name)
            family_names.add(name)
            if name == "pf_statementwise":
                statements = family.get("statements")
                if not isinstance(statements, list) or not 1 <= len(statements) <= 8:
                    raise ValueError("PF family requires explicit 1..8 statements; no parser")
                ids = set()
                for s in statements:
                    if not isinstance(s, dict) or set(s) != {"id", "text"}:
                        raise ValueError("PF statements require id/text")
                    nonempty(s["id"], "statement ID")
                    nonempty(s["text"], "statement text")
                    if s["id"] in ids:
                        raise ValueError("Duplicate statement ID")
                    ids.add(s["id"])
                count = len(statements)
            else:
                if "statements" in family:
                    raise ValueError("statements are only for PF")
                count = 2 if name == "critic" else 1
            if is_ready and (name != "baseline" or len(families) != 1):
                raise ValueError("Readiness rows require baseline only")
            tasks.append({"case": case, "family": family, "readiness": is_ready, "readiness_expected_answer": row.get("readiness_expected_answer"), "calls": count})
            calls += count
        readiness += int(is_ready)
    if readiness != manifest["readiness_calls"]:
        raise ValueError("Panel readiness count differs from manifest")
    if len(family_names) > 4 or calls > manifest["max_calls"] or calls * manifest["num_predict"] > manifest["max_requested_tokens"]:
        raise ValueError("Planned panel exceeds declared wave caps")
    if manifest.get("dispatch_order") != DISPATCH_ORDER:
        raise ValueError("Declared dispatch_order differs from frozen family order")
    # Stable sort retains original panel ID order inside every family; readiness is first.
    tasks.sort(key=lambda t: (not t["readiness"], DISPATCH_ORDER.index(t["family"]["name"])))
    return tasks


class Budget:
    def __init__(self, manifest, ledger, clock=time.monotonic, utc=time.time, runtime_guard=None, monotonic_end=None):
        self.m, self.ledger, self.clock, self.utc = manifest, ledger, clock, utc
        self.end = clock() + manifest["max_wall_seconds"]
        if monotonic_end is not None:
            self.end = min(self.end, monotonic_end)
        self.runtime_guard = runtime_guard
        self.calls = self.tokens = 0

    def remaining(self):
        if self.runtime_guard is not None:
            self.runtime_guard()
        left = min(self.end - self.clock(), self.m["deadline_epoch"] - self.utc())
        if left <= 0:
            raise StopWave("deadline")
        return left

    def reserve(self, identity):
        self.remaining()
        if self.calls >= self.m["max_calls"] or self.tokens + self.m["num_predict"] > self.m["max_requested_tokens"]:
            raise StopWave("budget")
        self.calls += 1
        self.tokens += self.m["num_predict"]
        write_record(self.ledger, {"event": "reserved", **identity, "call": self.calls,
                     "requested_tokens_including_thinking": self.m["num_predict"],
                     "cumulative_requested_tokens": self.tokens, "utc": datetime.fromtimestamp(self.utc(), timezone.utc).isoformat()})


def write_record(handle, record):
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def http_worker():
    """Single bounded HTTP exchange in a killable process. No retries or redirects."""
    spec = json.loads(sys.stdin.read())
    try:
        data = None if spec["payload"] is None else json.dumps(spec["payload"], ensure_ascii=False).encode()
        req = urllib.request.Request(spec["url"], data=data, headers={"Content-Type": "application/json"}, method=spec["method"])
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), infer.NoRedirect())
        with opener.open(req, timeout=spec["timeout"]) as response:
            body = response.read(16 * 1024 * 1024 + 1)
        if len(body) > 16 * 1024 * 1024:
            raise ValueError("Response exceeds bounded size")
        result = {"ok": True, "body": json.loads(body)}
    except Exception as exc:
        result = {"ok": False, "detail": str(exc), "type": type(exc).__name__}
    sys.stdout.write(json.dumps(result))


def request_json(base_url, route, payload, budget):
    limit = min(budget.m["timeout_seconds"], budget.remaining())
    spec = {"url": base_url.rstrip("/") + route, "method": "GET" if payload is None else "POST",
            "payload": payload, "timeout": limit}
    try:
        # subprocess.run kills and waits for its child on timeout: no background sending thread survives.
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--http-worker"],
                                input=json.dumps(spec), capture_output=True, text=True, timeout=limit, check=True)
        envelope = json.loads(result.stdout)
        budget.remaining()
        if not envelope["ok"]:
            raise StopWave("transport: " + envelope.get("type", "unknown"))
        if not isinstance(envelope["body"], dict):
            raise StopWave("invalid native response")
        return envelope["body"]
    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, OSError) as exc:
        raise StopWave("transport: " + type(exc).__name__) from exc


def health(manifest, budget, transport=request_json, require_loaded=False):
    base = manifest["base_url"]
    version = transport(base, "/api/version", None, budget)
    tags = transport(base, "/api/tags", None, budget)
    show = transport(base, "/api/show", {"model": manifest["model"]}, budget)
    ps = transport(base, "/api/ps", None, budget)
    if version.get("version") != "0.34.4":
        raise StopWave("runtime identity changed: version")
    matches = [m for m in tags.get("models", []) if m.get("name") == manifest["model"]]
    if len(matches) != 1 or matches[0].get("digest") != manifest["model_digest"]:
        raise StopWave("runtime identity changed: tags digest")
    # Native /show binds the served model/projector through generated FROM blob paths.
    from_hashes = set(re.findall(r"(?m)^FROM\s+\S*sha256-([0-9a-f]{64})\s*$", show.get("modelfile", "")))
    if "thinking" not in show.get("capabilities", []):
        raise StopWave("native thinking capability unavailable")
    if from_hashes != set(ASSETS):
        raise StopWave("runtime identity changed: model/projector references")
    if any(m.get("name") != manifest["model"] for m in ps.get("models", [])):
        raise StopWave("unexpected model on owned runtime")
    loaded = [m for m in ps.get("models", []) if m.get("name") == manifest["model"]]
    if (require_loaded and len(loaded) != 1) or len(loaded) > 1:
        raise StopWave("loaded model missing or ambiguous")
    for m in loaded:
        if m.get("digest") != manifest["model_digest"] or m.get("context_length") != manifest["context_length"]:
            raise StopWave("runtime identity changed: loaded digest/context")
    return {"version": version, "tags": tags, "show": show, "ps": ps,
            "asset_identity_method": "native show FROM references; file rehash is separate launch evidence"}


def payload_for(task, manifest, stage, previous=None):
    text, images = native_source(task["case"])
    name = task["family"]["name"]
    if name == "critic" and stage == 1:
        text += "\n\nNiezależna proponowana odpowiedź:\n" + previous + "\n\nSprawdź odpowiedź na podstawie oryginalnego zadania i źródeł. Zwróć wyłącznie poprawioną ostateczną odpowiedź."
    if name == "pf_statementwise":
        s = task["family"]["statements"][stage]
        text += "\n\nRozpatrz osobno stwierdzenie " + s["id"] + ":\n" + s["text"] + "\nZwróć decyzję P/F i krótkie uzasadnienie na podstawie źródeł zadania."
    message = {"role": "user", "content": text}
    if images:
        message["images"] = images
    return {"model": manifest["model"], "stream": False, "think": name == "thinking",
            "truncate": False, "shift": False, "messages": [message],
            "options": {"num_ctx": manifest["context_length"], "num_predict": manifest["num_predict"]}}


def native_usage(response):
    # Preserve observed counts even for failed/empty/truncated answers.
    counts = {k: response.get(k) if type(response.get(k)) is int and response[k] >= 0 else None
              for k in ("prompt_eval_count", "eval_count")}
    counts.update({"final_answer_tokens": None, "thinking_tokens": None,
                   "eval_count_scope": "native generated tokens including thinking; separate counts unavailable"})
    return counts


def answer_and_usage(response, manifest, think=False):
    if (response.get("error") is not None or response.get("truncated") is True
            or response.get("model") != manifest["model"]):
        raise StopWave("native error or response model changed")
    if response.get("done") is not True or response.get("done_reason") != "stop":
        raise StopWave("incomplete native answer")
    message = response.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str) or not message["content"].strip():
        raise StopWave("empty final answer")
    reasoning = message.get("thinking", "")
    if not isinstance(reasoning, str):
        raise StopWave("invalid native thinking field")
    if think and not reasoning.strip():
        raise StopWave("requested native thinking did not produce thinking evidence")
    if not think and reasoning.strip():
        raise StopWave("thinking appeared despite explicit think:false")
    usage = native_usage(response)
    for value in (usage["prompt_eval_count"], usage["eval_count"]):
        if type(value) is not int or value < 0:
            raise StopWave("missing or invalid native usage")
    if usage["prompt_eval_count"] + manifest["num_predict"] > manifest["context_length"]:
        raise StopWave("reported prompt plus generation reserve exceeds context")
    if usage["eval_count"] > manifest["num_predict"]:
        raise StopWave("native generation exceeds requested cap")
    return message["content"], usage


def verify_server_deadline(manifest):
    """Require protected pipe proof from the live owner-side server supervisor.

    A manifest or JSON active:true declaration cannot substitute for a verified
    inherited pipe and live parent/server process identities.
    """
    try:
        import reasoning_lab_supervisor as supervisor
    except ImportError as exc:
        raise ValueError("Native execution blocked: independently reviewed owned-server deadline supervisor required") from exc
    proof = supervisor.verify_parent_proof(manifest)
    if not isinstance(proof, dict) or proof.get("owner_lock_held") is not True:
        raise ValueError("Supervisor must retain the shared owner lock")
    end = proof.get("monotonic_end")
    if type(end) not in (int, float) or not math.isfinite(end) or end <= time.monotonic():
        raise ValueError("Supervisor deadline has elapsed or is invalid")
    proof["runtime_guard"] = lambda: supervisor.guard_parent_proof(proof, manifest)
    return proof


def execute(manifest, tasks, run_dir, transport=request_json, clock=time.monotonic, utc=time.time):
    # One owner lock covers all waves, not just one unique output directory.
    run_dir = Path(run_dir).resolve()
    owner_root = PRIVATE_ROOT.resolve()
    if not run_dir.is_relative_to(owner_root) or run_dir == owner_root:
        raise ValueError("Run directory must resolve under agentsLog/ljaniec/private")
    supervisor_proof = verify_server_deadline(manifest)
    owner_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    lease = (contextlib.nullcontext(None) if supervisor_proof.get("owner_lock_held") is True
             else (owner_root / "reasoning-lab-owner.lock").open("a"))
    with lease as lock:
        if lock is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        os.chmod(run_dir, 0o700)
        with (run_dir / "ledger.jsonl").open("x") as ledger, (run_dir / "private-envelopes.jsonl").open("x") as raw, (run_dir / "answers.jsonl").open("x") as answers:
            budget = Budget(manifest, ledger, clock, utc,
                            runtime_guard=supervisor_proof.get("runtime_guard"),
                            monotonic_end=supervisor_proof.get("monotonic_end"))
            write_record(raw, {"manifest": manifest})
            stopped = None
            try:
                write_record(raw, {"event": "preflight", "health": health(manifest, budget, transport)})
            except Exception as exc:
                stopped = "preflight: " + str(exc)
                write_record(raw, {"event": "failure", "detail": str(exc)})
            completed = failed = unsent = 0
            for task in tasks:
                case_id, family = task["case"]["id"], task["family"]["name"]
                safe = {"id": case_id, "family": family, "readiness": task["readiness"],
                        "backend": {"name": "ollama-native", "model": manifest["model"], "model_revision": manifest["model_digest"]},
                        "answer": None, "usage": [], "latency_seconds": None, "error": None, "status": "unsent",
                        "stages": [{"stage": n, "status": "unsent"} for n in range(task["calls"])]}
                if stopped:
                    safe["error"] = {"type": "unsent", "message": "wave stopped before this family"}
                    unsent += 1
                else:
                    start, finals = clock(), []
                    stage = 0
                    try:
                        for stage in range(task["calls"]):
                            identity = {"id": case_id, "family": family, "stage": stage, "readiness": task["readiness"]}
                            payload = payload_for(task, manifest, stage, finals[-1] if finals else None)
                            budget.reserve(identity)
                            safe["stages"][stage]["status"] = "reserved"
                            payload_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
                            write_record(raw, {"event": "request", **identity, "payload": payload, "request_sha256": payload_hash})
                            response = transport(manifest["base_url"], "/api/chat", payload, budget)
                            safe["stages"][stage]["status"] = "received"
                            write_record(raw, {"event": "response", **identity, "response": response})
                            safe["usage"].append(native_usage(response))
                            # Check identity after every call, including a response that will fail completeness checks.
                            write_record(raw, {"event": "postflight", **identity, "health": health(manifest, budget, transport, True)})
                            final, usage = answer_and_usage(response, manifest, payload["think"])
                            if task["readiness"] and final.strip() != task["readiness_expected_answer"]:
                                raise StopWave("synthetic readiness answer mismatch")
                            safe["stages"][stage]["status"] = "completed"
                            finals.append(final)
                            write_record(ledger, {"event": "completed", **identity})
                        if family == "pf_statementwise":
                            safe["answer"] = "\n".join(s["id"] + ". " + a for s, a in zip(task["family"]["statements"], finals))
                        else:
                            safe["answer"] = finals[-1]
                        safe["status"] = "completed"
                        completed += 1
                    except Exception as exc:
                        stopped = str(exc)
                        attempted = any(s["status"] != "unsent" for s in safe["stages"])
                        safe["status"] = "failed" if attempted else "unsent"
                        if safe["stages"][stage]["status"] != "unsent":
                            safe["stages"][stage]["status"] = "failed"
                            safe["stages"][stage]["server_cancellation"] = "unknown"
                        safe["error"] = {"type": "wave_guard", "message": "request or runtime guard failed; see private evidence"}
                        write_record(raw, {"event": "failure", "id": case_id, "family": family, "stage": stage, "detail": str(exc), "server_cancellation": "unknown" if attempted else "not_dispatched"})
                        write_record(ledger, {"event": "failed", "id": case_id, "family": family, "stage": stage, "attempted": attempted})
                        failed += int(attempted)
                        unsent += int(not attempted)
                    safe["latency_seconds"] = round(clock() - start, 3)
                write_record(answers, safe)
            summary = {"run_id": manifest["run_id"], "completed_families": completed, "failed_families": failed,
                       "unsent_families": unsent, "planned_families": len(tasks), "reserved_calls": budget.calls,
                       "requested_tokens_including_thinking": budget.tokens, "stop_reason": stopped,
                       "estimated_cost_ceiling_usd": manifest["hourly_rate_usd"] * manifest["max_wall_seconds"] / 3600,
                       "actual_cost_usd": None}
            with (run_dir / "summary.json").open("x") as handle:
                json.dump(summary, handle, ensure_ascii=False, indent=2)
            return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true", help="Supervisor-only HTTP generation; requires protected live parent proof and complete actual declaration")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        tasks = load_panel(args.panel, manifest)
        if not args.execute:
            print(json.dumps({"mode": "check", "families": len(tasks), "planned_calls": sum(t["calls"] for t in tasks),
                              "requested_tokens_including_thinking": sum(t["calls"] for t in tasks) * manifest["num_predict"], "http_requests": 0,
                              "dispatch": [{"id": t["case"]["id"], "family": t["family"]["name"], "readiness": t["readiness"]} for t in tasks]}))
            return 0
        if args.run_dir is None:
            raise ValueError("--execute requires new private --run-dir")
        if manifest["deadline_epoch"] <= time.time():
            raise ValueError("Declared UTC deadline has elapsed")
        summary = execute(manifest, tasks, args.run_dir)
        print(json.dumps(summary))
        return 1 if summary["stop_reason"] else 0
    except (ValueError, OSError, StopWave) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--http-worker"]:
        http_worker()
    else:
        raise SystemExit(main())
