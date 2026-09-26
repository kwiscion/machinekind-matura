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
MIN_CALL_SECONDS = 10  # do not start a call with less time than this left
OVERRUN_GRACE = 5  # extra seconds before an overrunning call thread is abandoned
STAGE_ORDER = ("single", "plan", "write")
STAGE_CONFIG = {"single": "config.final.json", "plan": "config.plan.json", "write": "config.final.json"}
ANSWER_STAGES = ("single", "write")


class Stop(Exception):
    """A bound would be crossed: stop deterministically, send nothing further."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_backend(case: dict, config: dict) -> dict:
    import infer  # imported lazily so tests never touch the network code path

    return infer.run_case(case, config)


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
    def __init__(self, manifest_path: Path, source: Path, backend=default_backend, clock=time.monotonic,
                 allow_remote: bool = False, config_loader=None, case_loader=None):
        self.manifest_path = manifest_path
        self.run_dir = manifest_path.parent
        self.source = source
        self.backend = backend
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


def main(argv: list[str] | None = None, backend=default_backend, clock=time.monotonic, **loaders) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", required=True, type=Path, help="manifest.json in the private run dir")
    parser.add_argument("--source", required=True, type=Path, help="the input JSONL given to build")
    parser.add_argument("--allow-remote", action="store_true", help="passed to infer.load_config (HTTPS only)")
    parser.add_argument("--check", action="store_true", help="validate the run dir and bounds only; send nothing")
    args = parser.parse_args(argv)
    run = Run(args.manifest, args.source, backend=backend, clock=clock, allow_remote=args.allow_remote, **loaders)
    try:
        run.validate()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        print(json.dumps({"ok": True, "stages": list(run.manifest["stages"]), "max_calls": MAX_CALLS,
                          "max_requested_tokens": MAX_REQUESTED_TOKENS, "max_wall_seconds": MAX_WALL_SECONDS}))
        return 0
    return run.execute()


if __name__ == "__main__":
    raise SystemExit(main())
