"""Bounded launcher for the essay pilot (issue #80). The only sanctioned way to run it.

  python scripts/Pewciu6/essay_pilot_run.py --manifest <private run dir>/manifest.json --source <input JSONL>

It enforces the whole envelope in one process instead of trusting separate infer.py runs:
  - one global deadline: max_wall_minutes=30 from the moment the run starts
  - per-call timeout = min(420 s, seconds left before the deadline); each call runs in a
    worker thread and is abandoned (run stops) if it overruns that timeout
  - at most 6 calls and 7168 requested output tokens, reserved in a ledger before each call
  - no retries; a failed or missing plan falls back to the single-pass prompt in its write slot
  - deterministic order (single, plan, write; items in manifest order) and a deterministic
    stop: the first bound that would be crossed stops the run, nothing further is sent
  - a run manifest (run_manifest.json) is written on every exit, complete or stopped, with
    calls sent, tokens reserved, per-call timeouts/latencies/errors and all unsent ids

Requests (the orchestrator's own HTTP backend; infer.py is not modified):
  --api ollama (default): POST <root>/api/chat with stream=false, think=false and
      options {num_predict: stage cap, num_ctx: --num-ctx (32768), temperature: --temperature}
  --api openai: POST <base_url>/chat/completions with max_tokens, reasoning_effort from the
      config, plus think=false and options {num_ctx, temperature} for Ollama's compat layer
  --base-url overrides the configs' base_url (e.g. http://127.0.0.1:11434 via an SSH tunnel);
  it goes through infer.endpoint_url, so non-loopback hosts still need --allow-remote + HTTPS.
Without think=false, Gemma on Ollama 0.34.4 spends the budget on hidden thinking and returns
an empty answer with done_reason=length (host smoke on matura-pawel, #80).

The run directory must be the fresh, git-ignored private dir built by `essay_route.py build`.
Raw provider output and the plan-bearing write input stay there. The answer-only handoffs
(answers.single.jsonl / answers.write.jsonl: id, stage, answer, error type; no plans, no raw
responses) are the only candidates for publication, after a manual check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # scripts/: normalize_outputs
sys.path.insert(0, str(HERE.parents[1]))  # repo root: infer
import essay_route  # noqa: E402
from normalize_outputs import final_text  # noqa: E402

RUNNER_REVISION = "essay-pilot-run-v1"
MAX_CALLS = 6
MAX_REQUESTED_TOKENS = 7168
MAX_WALL_SECONDS = 30 * 60
PER_CALL_TIMEOUT = 420
DEFAULT_NUM_CTX = 32768
MIN_CALL_SECONDS = 10  # do not start a call with less time than this left
OVERRUN_GRACE = 5  # extra seconds before an overrunning call thread is abandoned
STAGE_ORDER = ("single", "plan", "write")
STAGE_CONFIG = {"single": "config.final.json", "plan": "config.plan.json", "write": "config.final.json"}
ANSWER_STAGES = ("single", "write")


class Stop(Exception):
    """A bound would be crossed: stop deterministically, send nothing further."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_text_and_images(case: dict) -> tuple[str, list[str]]:
    """infer.load_cases content -> (text, base64 images) for the native Ollama API."""
    content = case["content"]
    if isinstance(content, str):
        return content, []
    text = "".join(part["text"] for part in content if part.get("type") == "text")
    images = [part["image_url"]["url"].split(",", 1)[1] for part in content if part.get("type") == "image_url"]
    return text, images


def build_request(case: dict, config: dict, options: dict) -> tuple[str, dict]:
    """Return (url, JSON body) for one call. Pure: tested without any network."""
    sampling = {"num_ctx": options["num_ctx"]}
    if options.get("temperature") is not None:
        sampling["temperature"] = options["temperature"]
    if options["api"] == "ollama":
        root = config["base_url"].rstrip("/")
        if root.endswith("/v1"):
            root = root[:-3]
        text, images = case_text_and_images(case)
        message = {"role": "user", "content": text}
        if images:
            message["images"] = images
        body = {"model": config["model"], "messages": [message], "stream": False, "think": False,
                "options": dict(sampling, num_predict=config["max_output_tokens"])}
        return root + "/api/chat", body
    body = {"model": config["model"], "messages": [{"role": "user", "content": case["content"]}],
            "max_tokens": config["max_output_tokens"], "think": False, "options": sampling}
    if config.get("reasoning_effort") is not None:
        body["reasoning_effort"] = config["reasoning_effort"]
    if options.get("temperature") is not None:
        body["temperature"] = options["temperature"]
    return config["endpoint"], body


def as_openai_shape(answer: dict) -> dict:
    """Wrap a native Ollama /api/chat reply so final_text and infer.response_error apply unchanged."""
    message = answer.get("message") if isinstance(answer.get("message"), dict) else {}
    return {
        "id": None,
        "model": answer.get("model"),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": message.get("content") or ""},
                     "finish_reason": answer.get("done_reason")}],
        "usage": {"prompt_tokens": answer.get("prompt_eval_count"), "completion_tokens": answer.get("eval_count")},
        "ollama_native": {k: v for k, v in answer.items() if k != "message"},
        "ollama_thinking_chars": len(message.get("thinking") or ""),
    }


def make_http_backend(options: dict):
    import infer

    def backend(case: dict, config: dict) -> dict:
        url, body = build_request(case, config, options)
        result = {"id": case["id"],
                  "backend": {"name": config["name"], "base_url": config["base_url"], "model": config["model"],
                              "model_revision": config.get("model_revision"), "response_model": None,
                              "response_id": None, "system_fingerprint": None, "api": options["api"]},
                  "raw_response": None, "usage": None, "latency_seconds": None, "error": None}
        request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        start = time.monotonic()
        try:
            with infer.OPENER.open(request, timeout=config["timeout_seconds"]) as response:
                answer = json.loads(response.read().decode("utf-8", errors="replace"))
            if options["api"] == "ollama" and isinstance(answer, dict) and "message" in answer:
                answer = as_openai_shape(answer)
            result["raw_response"] = answer
            if isinstance(answer, dict):
                result["usage"] = answer.get("usage")
                result["backend"]["response_model"] = answer.get("model")
                result["backend"]["response_id"] = answer.get("id")
            result["error"] = infer.response_error(answer)
        except urllib.error.HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", errors="replace")
            result["raw_response"] = detail
            result["error"] = {"type": "http", "status": exc.code, "message": detail}
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
            result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        finally:
            result["latency_seconds"] = round(time.monotonic() - start, 3)
        return result

    return backend


def load_stage_config(path: Path, allow_remote: bool) -> dict:
    import infer

    return infer.load_config(path, allow_remote)


def load_stage_cases(path: Path) -> list[dict]:
    import infer

    return infer.load_cases(path, MAX_CALLS)


def call_with_timeout(backend, case: dict, config: dict, timeout: float) -> dict | None:
    """Run one call in a daemon thread; None means it overran and was abandoned."""
    box = {}

    def target():
        try:
            box["result"] = backend(case, config)
        except BaseException as exc:  # noqa: BLE001 - recorded, never retried
            box["exc"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout + OVERRUN_GRACE)
    if worker.is_alive():
        return None
    if "exc" in box:
        return {"id": case["id"], "raw_response": None, "usage": None, "latency_seconds": None,
                "error": {"type": type(box["exc"]).__name__, "message": str(box["exc"])}}
    return box["result"]


class Run:
    def __init__(self, manifest_path: Path, source: Path, backend=None, clock=time.monotonic,
                 allow_remote: bool = False, config_loader=None, case_loader=None, options=None, base_url=None):
        self.manifest_path = manifest_path
        self.run_dir = manifest_path.parent
        self.source = source
        self.options = options or {"api": "ollama", "num_ctx": DEFAULT_NUM_CTX, "temperature": None}
        self.base_url = base_url
        self.backend = backend or make_http_backend(self.options)
        self.clock = clock
        self.allow_remote = allow_remote
        self.config_loader = config_loader or load_stage_config
        self.case_loader = case_loader or load_stage_cases
        self.calls = []
        self.tokens_reserved = 0
        self.unsent = {}
        self.fallbacks = {}
        self.status = "starting"
        self.stop_reason = None

    # -- validation -------------------------------------------------------------------
    def validate(self) -> None:
        essay_route.require_private_dir(self.run_dir)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("prompt_revision") != essay_route.PROMPT_REVISION:
            raise ValueError("Manifest prompt revision does not match essay_route.py")
        if manifest.get("prompt_template_sha256") != essay_route.template_sha256():
            raise ValueError("Manifest prompt template hash does not match essay_route.py")
        if sha256_file(self.source) != manifest.get("input_sha256"):
            raise ValueError("Source input does not match manifest input_sha256")
        env = manifest.get("envelope", {})
        if env.get("retries") != 0 or env.get("max_wall_minutes", 0) * 60 > MAX_WALL_SECONDS:
            raise ValueError("Manifest envelope must declare 0 retries and at most 30 wall minutes")
        stages = manifest["stages"]
        planned_calls = sum(stages[s]["calls"] for s in stages)
        planned_tokens = sum(stages[s]["calls"] * stages[s]["max_output_tokens"] for s in stages)
        if planned_calls > MAX_CALLS or planned_tokens > MAX_REQUESTED_TOKENS:
            raise ValueError(f"Planned {planned_calls} calls / {planned_tokens} tokens exceed "
                             f"{MAX_CALLS} / {MAX_REQUESTED_TOKENS}")
        existing = [p.name for p in self.run_dir.iterdir()
                    if p.name.endswith(".output.jsonl") or p.name in ("write.input.jsonl", "run_manifest.json", "run.lock")]
        if existing:
            raise ValueError(f"Run dir is not fresh (found {sorted(existing)}); use a new run id")
        self.configs = {}
        for stage in stages:
            config = self.config_loader(self.run_dir / STAGE_CONFIG[stage], self.allow_remote)
            if self.base_url:
                import infer

                config["base_url"] = self.base_url
                config["endpoint"] = infer.endpoint_url(self.base_url, self.allow_remote)
            if config["max_output_tokens"] != stages[stage]["max_output_tokens"]:
                raise ValueError(f"{stage}: config cap {config['max_output_tokens']} != manifest cap")
            self.configs[stage] = config
        self.manifest = manifest

    # -- execution --------------------------------------------------------------------
    def remaining(self) -> float:
        return self.deadline - self.clock()

    def send(self, stage: str, case: dict, out) -> dict:
        cap = self.configs[stage]["max_output_tokens"]
        if len(self.calls) + 1 > MAX_CALLS:
            raise Stop("call_limit")
        if self.tokens_reserved + cap > MAX_REQUESTED_TOKENS:
            raise Stop("token_limit")
        left = self.remaining()
        if left < MIN_CALL_SECONDS:
            raise Stop("deadline")
        timeout = min(PER_CALL_TIMEOUT, left)
        config = dict(self.configs[stage], timeout_seconds=timeout)
        self.tokens_reserved += cap
        record = {"stage": stage, "id": case["id"], "reserved_tokens": cap, "timeout_seconds": round(timeout, 3)}
        self.calls.append(record)
        self.unsent[stage].remove(case["id"])  # sent from here on, whatever happens next
        started = self.clock()
        result = call_with_timeout(self.backend, case, config, timeout)
        record["elapsed_seconds"] = round(self.clock() - started, 3)
        if result is None:
            record["error_type"] = "orchestrator_timeout"
            result = {"id": case["id"], "raw_response": None, "usage": None, "latency_seconds": None,
                      "error": {"type": "orchestrator_timeout", "message": f"call exceeded {timeout:.0f} s"}}
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()
            raise Stop("call_overran")
        error = result.get("error")
        record["error_type"] = error.get("type") if isinstance(error, dict) else (None if error is None else "error")
        out.write(json.dumps(result, ensure_ascii=False) + "\n")
        out.flush()
        if self.remaining() <= 0:
            raise Stop("deadline")
        return result

    def run_stage(self, stage: str, cases: list[dict]) -> list[dict]:
        results = []
        self.unsent[stage] = [case["id"] for case in cases]
        with (self.run_dir / f"{stage}.output.jsonl").open("x", encoding="utf-8") as out:
            for case in cases:
                results.append(self.send(stage, case, out))
        return results

    def execute(self) -> int:
        self.started_wall = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.start = self.clock()
        self.deadline = self.start + MAX_WALL_SECONDS
        lock = os.open(self.run_dir / "run.lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(lock, f"{os.getpid()} {self.started_wall}\n".encode())
        os.close(lock)
        stages = self.manifest["stages"]
        # Every planned id starts as unsent; stages remove ids as calls are sent.
        for stage in STAGE_ORDER:
            if stage in stages:
                self.unsent[stage] = [item["id"] + (essay_route.PLAN_SUFFIX if stage == "plan" else "")
                                      for item in self.manifest["items"]]
        self.status = "running"
        try:
            for stage in STAGE_ORDER:
                if stage not in stages:
                    continue
                if stage == "write":
                    plan_rows = essay_route.read_jsonl_any(self.run_dir / "plan.output.jsonl")
                    rows, self.fallbacks = essay_route.build_write_rows(self.manifest, self.source, plan_rows, self.run_dir)
                    essay_route.write_jsonl(self.run_dir / stages["write"]["file"], rows)
                cases = self.case_loader(self.run_dir / stages[stage]["file"])
                self.run_stage(stage, cases)
            self.status = "complete"
        except Stop as stop:
            self.status, self.stop_reason = "stopped", str(stop)
        except BaseException as exc:  # noqa: BLE001 - always leave a manifest behind
            self.status, self.stop_reason = "stopped", f"exception:{type(exc).__name__}:{exc}"
            if not isinstance(exc, Exception):
                self.finish()
                raise
        return self.finish()

    # -- outputs ----------------------------------------------------------------------
    def write_answers(self) -> dict:
        written = {}
        for stage in ANSWER_STAGES:
            path = self.run_dir / f"{stage}.output.jsonl"
            if not path.exists():
                continue
            rows = essay_route.read_jsonl_any(path)
            answers = []
            for row in rows:
                raw = row.get("raw_response")
                error = row.get("error")
                answers.append({"id": row["id"], "stage": stage,
                                "answer": final_text(raw) if isinstance(raw, dict) and error is None else "",
                                "error_type": error.get("type") if isinstance(error, dict) else None})
            text = "".join(json.dumps(a, ensure_ascii=False) + "\n" for a in answers)
            name = f"answers.{stage}.jsonl"
            with (self.run_dir / name).open("x", encoding="utf-8") as handle:
                handle.write(text)
            written[name] = essay_route.sha256_text(text)
        return written

    def finish(self) -> int:
        answers = {}
        try:
            answers = self.write_answers()
        except (OSError, ValueError) as exc:
            self.stop_reason = (self.stop_reason or "") + f"; answer handoff failed: {exc}"
        record = {
            "runner_revision": RUNNER_REVISION,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "started_utc": self.started_wall,
            "elapsed_seconds": round(self.clock() - self.start, 3),
            "bounds": {"max_calls": MAX_CALLS, "max_requested_tokens": MAX_REQUESTED_TOKENS,
                       "max_wall_seconds": MAX_WALL_SECONDS, "per_call_timeout": PER_CALL_TIMEOUT,
                       "min_call_seconds": MIN_CALL_SECONDS, "retries": 0},
            "request_options": dict(self.options, think=False, base_url=self.configs["single" if "single" in self.configs else "plan"]["base_url"]),
            "manifest_sha256": sha256_file(self.manifest_path),
            "source_sha256": sha256_file(self.source),
            "calls_sent": len(self.calls),
            "tokens_reserved": self.tokens_reserved,
            "calls": self.calls,
            "failed_calls": [f"{c['stage']}:{c['id']}" for c in self.calls if c.get("error_type")],
            "unsent": {stage: ids for stage, ids in self.unsent.items() if ids},
            "plan_fallback_reasons": self.fallbacks,
            "answer_handoffs": answers,
            "notes": "Raw outputs and write.input.jsonl (plans) stay in this private dir. Publish only checked answers.*.jsonl or aggregates.",
        }
        with (self.run_dir / "run_manifest.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(f"{self.status}: {len(self.calls)} call(s), {self.tokens_reserved} reserved tokens"
              + (f", stop_reason={self.stop_reason}" if self.stop_reason else ""))
        return 0 if self.status == "complete" else 1


def main(argv: list[str] | None = None, backend=None, clock=time.monotonic, **loaders) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", required=True, type=Path, help="manifest.json in the private run dir")
    parser.add_argument("--source", required=True, type=Path, help="the input JSONL given to build")
    parser.add_argument("--allow-remote", action="store_true", help="passed to infer.load_config (HTTPS only)")
    parser.add_argument("--base-url", help="override the configs' base_url, e.g. http://127.0.0.1:11434")
    parser.add_argument("--api", choices=["ollama", "openai"], default="ollama",
                        help="ollama: native /api/chat (default); openai: /chat/completions")
    parser.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX, help="Ollama num_ctx (default 32768)")
    parser.add_argument("--temperature", type=float, help="declared sampling temperature (omit = server default)")
    parser.add_argument("--check", action="store_true", help="validate the run dir and bounds only; send nothing")
    args = parser.parse_args(argv)
    if not 2048 <= args.num_ctx <= 131072:
        parser.error("--num-ctx must be 2048-131072")
    if args.temperature is not None and not 0.0 <= args.temperature <= 2.0:
        parser.error("--temperature must be 0-2")
    options = {"api": args.api, "num_ctx": args.num_ctx, "temperature": args.temperature}
    run = Run(args.manifest, args.source, backend=backend, clock=clock, allow_remote=args.allow_remote,
              options=options, base_url=args.base_url, **loaders)
    try:
        run.validate()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        print(json.dumps({"ok": True, "stages": list(run.manifest["stages"]), "max_calls": MAX_CALLS,
                          "request_options": dict(options, think=False),
                          "endpoints": {s: build_request({"id": "x", "content": "x"}, c, options)[0]
                                        for s, c in run.configs.items()},
                          "max_requested_tokens": MAX_REQUESTED_TOKENS, "max_wall_seconds": MAX_WALL_SECONDS}))
        return 0
    return run.execute()


if __name__ == "__main__":
    raise SystemExit(main())
