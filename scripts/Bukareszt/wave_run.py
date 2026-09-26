#!/usr/bin/env python3
"""Bounded, offline experiment-wave runner for issue #96 (Greg's dedicated H100 factual-evidence lab).

    python3 -B scripts/Bukareszt/wave_run.py --plan <plan.json> --runtime-profile <profile.json> \
        --config agentsLog/kwiscion/gemma4-12b-val40-1024.config.json(CRLF pin) --output <fresh dir under agentsLog/Bukareszt/private/wave/>

A plan names arms; each arm is either
  {"name": ..., "type": "direct", "input": <runner JSONL {id, prompt, images?}>}   one call per case, or
  {"name": ..., "type": "module", "input": ..., "module": <path.py>, "max_calls_per_case": n}
     where module.build(case, call) may make up to n-1 auxiliary calls through `call(prompt_text)` and returns the
     final prompt string (images of the case are always attached to the final call unchanged).
Wave-wide hard caps are kept in `<private>/wave/wave_state.json` across runs: <= 120 calls, <= 240,000 requested
output/reasoning tokens (max_output_tokens per call; reasoning is off), <= 90 minutes from the first launch, and
<= 4 mechanism families. No retries: any infrastructure failure stops the run; every attempt is ledgered.

Reuses the reviewed launcher helpers (agentsLog/kwiscion/offline_rehearsal.py via run_gemma_package.py): frozen
runtime profile validation, binary hash, every manifest blob hash, competing-worker/GPU guard, `unshare -rn`
namespace shared by server and runner, loopback-only network proof, resident digest/context check after each call.
The original config is only re-pointed at the isolated endpoint; generation settings are unchanged.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OWN_PRIVATE = ROOT / "agentsLog" / "Bukareszt" / "private"
WAVE_DIR = OWN_PRIVATE / "wave"
STATE = WAVE_DIR / "wave_state.json"
LEDGER = WAVE_DIR / "ledger.jsonl"
CAPS = {"calls": 120, "requested_tokens": 240_000, "wall_seconds": 90 * 60, "families": 4}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(ROOT / "agentsLog/kwiscion"))
launcher = load("run_gemma_package", ROOT / "agentsLog/kwiscion/run_gemma_package.py")
r = launcher.r  # offline_rehearsal helpers
SELF = Path(__file__).resolve()


def sha(p: Path) -> str:
    return r.sha(Path(p))


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def write_state(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(STATE)


def used(state: dict) -> dict:
    calls = tokens = 0
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            row = json.loads(line)
            calls += 1
            tokens += row["requested_tokens"]
    return {"calls": calls, "requested_tokens": tokens}


def check_caps(state: dict, plan: dict, config: dict) -> dict:
    u = used(state)
    families = set(state.get("families", [])) | {arm.get("family", plan["family"]) for arm in plan["arms"]}
    families.discard("comparator")  # the unchanged bare arm is a comparator, not a mechanism family
    r.require(len(families) <= CAPS["families"], f"Wave family cap exceeded: {sorted(families)}")
    planned_calls = sum(a["planned_calls"] for a in plan["arms"])
    r.require(u["calls"] + planned_calls <= CAPS["calls"], f"Wave call cap: used {u['calls']} + planned {planned_calls} > 120")
    r.require(u["requested_tokens"] + planned_calls * config["max_output_tokens"] <= CAPS["requested_tokens"],
              "Wave requested-token cap exceeded")
    if "started_at_epoch" in state:
        r.require(time.time() - state["started_at_epoch"] < CAPS["wall_seconds"], "Wave 90-minute window elapsed")
    return {"used_before": u, "planned_calls": planned_calls, "families": sorted(families)}


def planned(arm: dict, input_path: Path, inf) -> int:
    n = len(inf.load_cases(input_path, 100))
    return n * (arm.get("max_calls_per_case", 1) if arm["type"] == "module" else 1)


# ------------------------------------------------------------------------------------------------ outer

def execute(a) -> int:
    r.require(sys.platform == "linux", "Execute only on Linux")
    import fcntl
    profile, profile_digest, profile_file_digest = r.load_profile(a.runtime_profile)
    r.check_platform(profile)
    inf, _ = r.modules()
    cfg_path = Path(a.config).resolve()
    r.require(sha(cfg_path) == launcher.CONFIG_SHA, "Original bare Gemma config hash mismatch")
    config = inf.load_config(cfg_path, False)
    plan_path = Path(a.plan).resolve()
    plan = json.loads(plan_path.read_text())
    r.require(set(plan) >= {"wave_id", "family", "arms"} and plan["arms"], "Plan needs wave_id, family, arms")
    for arm in plan["arms"]:
        arm["input"] = str((plan_path.parent / arm["input"]).resolve()) if not Path(arm["input"]).is_absolute() else arm["input"]
        r.require(arm["type"] in ("direct", "module"), "Arm type must be direct or module")
        if arm["type"] == "module":
            arm["module"] = str((plan_path.parent / arm["module"]).resolve())
            r.require(1 <= arm.get("max_calls_per_case", 0) <= 4, "module arms declare max_calls_per_case 1..4")
        arm["planned_calls"] = planned(arm, Path(arm["input"]), inf)
    out = Path(a.output).resolve()
    r.require(out.is_relative_to(WAVE_DIR.resolve()) and not out.exists(), "Fresh output dir under private/wave required")
    WAVE_DIR.mkdir(parents=True, exist_ok=True)
    with (WAVE_DIR / "wave.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = read_state()
        caps = check_caps(state, plan, config)
        r.host_idle(profile)
        launcher.worker_guard(profile=profile)
        r.verify_binary(profile)
        r.verify_assets(profile)
        probe = r.isolation_probe()
        out.mkdir(parents=True)
        cfg = dict(json.loads(cfg_path.read_bytes()))
        cfg["base_url"] = r.ENDPOINT + "/v1"  # isolated endpoint only; generation settings unchanged
        r.write(out / "config.json", cfg)
        frozen = {str(cfg_path): launcher.CONFIG_SHA, str(out / "config.json"): sha(out / "config.json"), str(plan_path): sha(plan_path),
                  str(SELF): sha(SELF), str(ROOT / "infer.py"): sha(ROOT / "infer.py"),
                  str(Path(r.__file__)): sha(Path(r.__file__)), str(Path(launcher.__file__)): sha(Path(launcher.__file__)),
                  profile["ollama_binary"]: profile["ollama_binary_sha256"]}
        for arm in plan["arms"]:
            frozen[arm["input"]] = sha(Path(arm["input"]))
            for img in {i for c in (json.loads(l) for l in Path(arm["input"]).read_text().splitlines() if l.strip())
                        for i in c.get("images", [])}:
                p = (Path(arm["input"]).parent / img).resolve()
                frozen[str(p)] = sha(p)
            if arm["type"] == "module":
                frozen[arm["module"]] = sha(Path(arm["module"]))
        if "started_at_epoch" not in state:
            state.update(started_at_epoch=time.time(), started_at=now(), rate_unverified=True,
                         rate_proxy_usd_per_hour=3.28, rate_note="central-instance proxy; not a bill")
        state["families"] = caps["families"]
        write_state(state)
        record = {"wave_id": plan["wave_id"], "family": plan["family"], "run": out.name, "created_at": now(),
                  "plan": plan, "caps": CAPS, "cap_check": caps, "runtime_profile": profile,
                  "runtime_profile_sha256": profile_digest, "runtime_profile_file_sha256": profile_file_digest,
                  "config_sha256": launcher.CONFIG_SHA, "model_digest": r.DIGEST, "frozen_files": frozen,
                  "isolation_probe": probe, "parent_pid": os.getpid(), "retries": 0,
                  "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "wave_deadline_epoch": state["started_at_epoch"] + CAPS["wall_seconds"]}
        r.write(out / "launch.json", record)
        wall = int(min(a.wall_seconds, record["wave_deadline_epoch"] - time.time()))
        r.require(wall > 60, "Less than a minute left in the wave window")
        cmd = ["unshare", "-rn", "--", sys.executable, "-B", str(SELF), "--inside", "--host-net",
               os.readlink("/proc/self/ns/net"), "--output", str(out)]
        child, status = None, 2
        try:
            child = subprocess.Popen(cmd, start_new_session=True)
            status = child.wait(timeout=wall)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if child is not None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                    child.wait(timeout=15)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
        finally:
            launcher.cleanup_owned(out)
            summary = {"child_status": status, "finished_at": now(), "ledger_after": used(read_state())}
            r.write(out / "outcome.json", summary)
            print(json.dumps(summary))
        return 0 if status == 0 else 1


# ------------------------------------------------------------------------------------------------ inside

def inside(a) -> int:
    out = Path(a.output).resolve()
    record = json.loads((out / "launch.json").read_text())
    r.require(os.getppid() == record["parent_pid"], "Inside mode requires the recorded supervisor")
    launcher.verify_pins(record["frozen_files"])
    profile = r.validate_profile(record["runtime_profile"])
    proof = r.network_proof(a.host_net)
    r.write(out / "network-proof.json", proof)
    inf, _ = r.modules()
    import urllib.request
    inf.OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), inf.NoRedirect)
    config = inf.load_config(out / "config.json", False)
    home = out / "server-home"
    home.mkdir()
    env = r.server_env(profile, home)
    server = None
    deadline = record["wave_deadline_epoch"] - 30
    try:
        with (out / "server.log").open("xb") as log:
            server = subprocess.Popen([profile["ollama_binary"], "serve"], env=env, stdout=log, stderr=subprocess.STDOUT,
                                      start_new_session=True)
        ns = os.readlink(f"/proc/{server.pid}/ns/net")
        r.write(out / "server-pid.json", {"process_group": server.pid, "namespace": ns})
        r.require(ns == proof["isolated_namespace"], "Server namespace mismatch")
        ready = time.monotonic() + 60
        while True:
            r.require(server.poll() is None, "Server exited")
            try:
                version = r.api("version")
                r.require(version.get("version") == profile["ollama_version"], "Runtime version changed")
                tags = r.api("tags")["models"]
                r.require(any(m.get("name") == r.MODEL and m.get("digest") == r.DIGEST for m in tags), "Model tag mismatch")
                break
            except (OSError, ValueError):
                r.require(time.monotonic() < ready, "Readiness timeout")
                time.sleep(0.5)
        r.write(out / "readiness.json", {"version": version, "digest": r.DIGEST, "context": profile["context_length"]})

        def resident():
            models = r.api("ps")["models"]
            r.require(len(models) == 1 and models[0].get("digest") == r.DIGEST and
                      models[0].get("context_length") == profile["context_length"], "Resident digest/context mismatch")

        seq = 0
        families = {a["name"]: a.get("family", record["family"]) for a in record["plan"]["arms"]}

        def call(arm, case_id, role, prompt, images):
            nonlocal seq
            r.require(time.time() < deadline, "Wave deadline reached")
            launcher.verify_pins(record["frozen_files"])
            launcher.worker_guard(server.pid, record["parent_pid"], profile)
            state = read_state()
            u = used(state)
            r.require(u["calls"] + 1 <= CAPS["calls"] and
                      u["requested_tokens"] + config["max_output_tokens"] <= CAPS["requested_tokens"], "Wave cap reached")
            case = {"id": case_id, "prompt": prompt, "images": images}
            tmp = out / f".case-{seq}.jsonl"
            tmp.write_text(json.dumps(case, ensure_ascii=False) + "\n")
            loaded = inf.load_cases(tmp, 1)[0]
            tmp.unlink()
            result = inf.run_case(loaded, config)
            seq += 1
            result.update(arm=arm, role=role, seq=seq, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                          at=now())
            with (out / "raw.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            usage = result.get("usage") or {}
            with LEDGER.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"at": result["at"], "run": out.name, "wave_id": record["wave_id"],
                                    "family": families.get(arm, record["family"]), "arm": arm, "id": case_id, "role": role,
                                    "requested_tokens": config["max_output_tokens"],
                                    "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                                    "latency_seconds": result["latency_seconds"],
                                    "error": (result["error"] or {}).get("type")}) + "\n")
            resident()
            r.require(result["error"] is None or result["error"]["type"] in ("incomplete",),
                      f"Infrastructure failure on {arm}/{case_id}: {result['error']}")
            return result

        def text_of(result):
            try:
                c = result["raw_response"]["choices"][0]["message"]["content"]
                return c if isinstance(c, str) else "".join(p.get("text", "") for p in c if isinstance(p, dict))
            except (KeyError, IndexError, TypeError):
                return ""

        for arm in record["plan"]["arms"]:
            rows = [json.loads(l) for l in Path(arm["input"]).read_text(encoding="utf-8").splitlines() if l.strip()]
            base = Path(arm["input"]).parent
            module = None
            if arm["type"] == "module":
                sys.path.insert(0, str(Path(arm["module"]).parent))
                module = load("wave_module_" + arm["name"].replace("-", "_"), arm["module"])
            for row in rows:
                images = [str((base / i).resolve()) for i in row.get("images", [])]
                if module is None:
                    call(arm["name"], row["id"], "final", row["prompt"], images)
                    continue
                budget = {"left": arm["max_calls_per_case"] - 1}

                def aux(prompt_text, with_images=False, _row=row, _images=images, _arm=arm["name"], _b=budget):
                    r.require(_b["left"] > 0, "Module exceeded max_calls_per_case")
                    _b["left"] -= 1
                    return text_of(call(_arm, _row["id"], "aux", prompt_text, _images if with_images else []))

                final_prompt = getattr(module, arm.get("function", "build"))(row, aux)
                with (out / "module-trace.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"arm": arm["name"], "id": row["id"],
                                        "final_prompt_sha256": hashlib.sha256(final_prompt.encode()).hexdigest(),
                                        "original_is_suffix": final_prompt.endswith(row["prompt"])}) + "\n")
                call(arm["name"], row["id"], "final", final_prompt, images)
        r.write(out / "execution.json", {"stop_reason": "complete", "calls": seq})
        return 0
    finally:
        if server is not None:
            try:
                os.killpg(server.pid, signal.SIGTERM)
                server.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--plan")
    p.add_argument("--runtime-profile")
    p.add_argument("--config")
    p.add_argument("--output", required=True)
    p.add_argument("--wall-seconds", type=int, default=1800)
    p.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--host-net", default="")
    a = p.parse_args(argv)
    if a.inside:
        return inside(a)
    for k in ("plan", "runtime_profile", "config"):
        if getattr(a, k) is None:
            p.error(f"--{k.replace('_', '-')} is required")
    return execute(a)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
