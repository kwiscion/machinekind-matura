"""Bounded contract-first essay loop for issue #80 (family K "contract", distinct structural family).

Per item (caps and the per-item call budget are declared in the run manifest BEFORE any call):
  1. select   one permitted topic, frozen as topic_id (model one-liner parsed strictly, or a
              deterministic policy; an unparsable/ambiguous choice falls back to the declared
              deterministic policy, recorded, never a silent pick)
  2. draft    the writer sees ONLY the selected topic + every global/selected-topic requirement;
              the full original task is stored separately (task_audit.jsonl)
  3. contract mechanical check after EVERY call (essay_contract.contract_check): parse {topic_id,
              body}, deterministic wrapper cleanup, single topic / minimum length / aspects
  4. critic   optional grounded factual/argument critic + rewrite (C3's prompts, reused); it is a
              separate stage from the mechanical check and needs 2 calls of headroom to start
  5. repair   at most MAX_REPAIRS=2 conditional revision calls per item, each triggered by a
              recorded contract failure, each rechecked
  final       the last version that passed the hard contract; none -> item failed (no answer)

Bounds reuse essay_wave_run.Wave: a ledger reloaded before every call (calls, requested-token caps,
family cap, an absolute deadline fixed at init), per-call timeout, watchdog hard exit, no retries,
no reused batch ids, run.lock.

  python scripts/Pewciu6/essay_contract_run.py init --run-dir agentsLog/Pewciu6/essay/private/contract-X \\
      --max-calls 4 --max-tokens 74240 --deadline-utc 2026-09-26T19:05:20Z
  python scripts/Pewciu6/essay_contract_run.py run --run-dir ... --batch k1 --source S --items id1,id2 \\
      [--select model|first|most-aspects] [--critic] [--soft-repair] [--check]
  python scripts/Pewciu6/essay_contract_run.py offline --source S --answers A.jsonl   # legacy outputs, no calls
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_contract as ec  # noqa: E402
import essay_route as er  # noqa: E402
import essay_wave_run as wr  # noqa: E402

FAMILY = "K"
FAMILY_NAME = "contract-first"
CAPS = {"select": 128, "draft": 2048, "critic": 1024, "rewrite": 2048, "repair": 2048}


def item_budget(select_model: bool, critic: bool) -> dict:
    stages = (["select"] if select_model else []) + ["draft"] + (["critic", "rewrite"] if critic else [])
    stages += [f"repair{i}" for i in range(1, ec.MAX_REPAIRS + 1)]
    caps = {s: CAPS["repair" if s.startswith("repair") else s] for s in stages}
    return {"stages": stages, "caps": caps, "max_calls": len(stages), "max_tokens": sum(caps.values()),
            "min_calls": 1 + int(select_model)}


def version(stage: str, result: dict, check: dict | None) -> dict:
    return {"stage": stage, "raw": result.get("text"), "error": result.get("error"),
            "eval_count": result.get("eval_count"), "check": check}


def run_item(send, task: dict, info: dict, item_id: str, select: str, critic: bool, calls_left, retrieve=None,
             soft_repair: bool = False) -> dict:
    """One item through the contract loop. `send(stage, prompt)` performs one bounded call.

    soft_repair=False (default): a below-400 soft trigger alone does not spend a repair call; the
    blind grader found a length-only repair added filler and a new factual error (probe k1).
    """
    rec = {"item": item_id, "select_policy": select, "versions": [], "repairs": [], "unsent": [], "status": None}
    fallback_policy = "most-aspects"
    if select == "model":
        s = send("select", ec.select_prompt(info["body"]))
        chosen, why = ec.parse_selection(s.get("text", ""), sorted(task["topics"])) if not s.get("error") else (None, s["error"])
        rec["selection"] = {"raw": s.get("text"), "parse": why}
        if chosen is None:
            chosen = ec.select_deterministic(task, fallback_policy)
            rec["selection"]["fallback"] = fallback_policy
    else:
        chosen = ec.select_deterministic(task, select)
    rec["topic_id"] = chosen
    rec["writer_task_sha256"] = ec.sha256_text(ec.writer_task(task, chosen))

    def attempt(stage, prompt):
        r = send(stage, prompt)
        chk = None if r.get("error") and not r.get("text") else ec.contract_check(r.get("text", ""), task, chosen)
        if r.get("error") and chk is not None:
            chk = {**chk, "ok": False, "triggers": [f"call_error:{r['error']}"] + chk["triggers"]}
        v = version(stage, r, chk)
        rec["versions"].append(v)
        return v

    def repair_loop(latest):
        while (latest["check"] is not None and latest["check"]["triggers"] and len(rec["repairs"]) < ec.MAX_REPAIRS
               and (soft_repair or not latest["check"]["ok"])):
            hard = not latest["check"]["ok"]
            n = len(rec["repairs"]) + 1
            if calls_left() < 1:
                rec["unsent"].append({"stage": f"repair{n}", "reason": "budget_exhausted"})
                break
            rec["repairs"].append({"round": n, "after": latest["stage"], "triggers": latest["check"]["triggers"],
                                   "hard": hard})
            prev = latest["check"]["clean"] or (latest["raw"] or "")
            latest = attempt(f"repair{n}", ec.repair_prompt(task, chosen, prev, latest["check"], n))
        return latest

    latest = attempt("draft", ec.writer_prompt(task, chosen))
    if latest["check"] is None:
        rec["status"] = "failed"
        rec["failure"] = f"draft_call_error:{latest['error']}"
        return finish(rec)
    latest = repair_loop(latest)
    if critic:
        base = best_version(rec)
        if base is None:
            rec["unsent"] += [{"stage": s, "reason": "no_contract_passing_version"} for s in ("critic", "rewrite")]
        elif calls_left() < 2:
            rec["unsent"] += [{"stage": s, "reason": "budget_below_2_calls"} for s in ("critic", "rewrite")]
        else:
            short = {"body": ec.writer_task(task, chosen)}
            excerpts = retrieve(info, chosen) if retrieve else []
            rec["retrieval"] = [{k: e[k] for k in ("chunk_id", "source_id", "locator", "score")} for e in excerpts]
            cprompt = (wr.grounded_critic_prompt(short, chosen, base["check"]["clean"], excerpts) if excerpts
                       else wr.critic_prompt(short, chosen, base["check"]["clean"]))
            c = send("critic", cprompt)
            rec["critique"] = {"raw": c.get("text"), "error": c.get("error")}
            if c.get("error"):
                rec["unsent"].append({"stage": "rewrite", "reason": f"failed_critic:{c['error']}"})
            else:
                extra = ("POPRAWA MERYTORYCZNA: popraw błędy rzeczowe wskazane przez egzaminatora, pogłęb słabo "
                         "uzasadnione aspekty konkretnymi faktami i powiąż każdy argument z tezą. Nie wprowadzaj faktów, "
                         "których nie jesteś pewien; błędne uwagi egzaminatora pomiń.\n\nPIERWSZA WERSJA:\n"
                         + base["check"]["clean"] + "\n\nUWAGI EGZAMINATORA:\n" + c["text"].strip() + "\n"
                         + (wr.excerpts_block(excerpts) + wr.NO_CITATIONS if excerpts else ""))
                latest = attempt("rewrite", ec.writer_prompt(task, chosen, extra))
                if latest["check"] is not None:
                    latest = repair_loop(latest)
    return finish(rec)


def best_version(rec: dict) -> dict | None:
    passing = [v for v in rec["versions"] if v["check"] and v["check"]["ok"]]
    return passing[-1] if passing else None


def finish(rec: dict) -> dict:
    best = best_version(rec)
    if best is None:
        rec["status"] = rec["status"] or "failed"
        rec.setdefault("failure", "no_version_passed_contract")
        rec["final_stage"] = None
        rec["answer"] = None
    else:
        rec["status"] = "ok"
        rec["final_stage"] = best["stage"]
        rec["answer"] = ec.render_answer(rec["topic_id"], best["check"]["clean"])
        rec["final_words"] = best["check"]["validation"]["words"]
        rec["final_soft"] = best["check"]["validation"]["soft"]
    rec["initial_ok"] = bool(rec["versions"] and rec["versions"][0]["check"] and rec["versions"][0]["check"]["ok"])
    return rec


# ---------------------------------------------------------------- cli

def iso_to_epoch(s: str) -> float:
    return float(calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")))


def cmd_init(args) -> int:
    run_dir = Path(args.run_dir)
    er.require_private_dir(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    now = time.time()
    deadline = iso_to_epoch(args.deadline_utc)
    if deadline - now < wr.MIN_START_S:
        raise SystemExit("deadline already passed")
    env = {"max_calls": args.max_calls, "max_tokens": args.max_tokens, "max_families": 1,
           "wall_seconds": round(deadline - now), "per_call_max_s": 420, "retries": 0, "prior_calls": 0,
           "prior_tokens": 0}
    ledger = {"revision": ec.CONTRACT_REVISION, "wave_id": run_dir.name, "envelope": env, "caps": CAPS,
              "template_sha256": ec.template_sha256(), "model": args.model, "num_ctx": args.num_ctx, "think": False,
              "temperature": None, "base_url": args.base_url, "wave_start": now, "deadline": deadline,
              "wave_start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "deadline_iso": args.deadline_utc,
              "families": [], "entries": [], "created": now, "allowance_source": args.allowance_source}
    wr.write_json_atomic(run_dir / "ledger.json", ledger)
    print(json.dumps({"run_dir": str(run_dir), "envelope": env, "deadline": args.deadline_utc}, indent=1))
    return 0


def cmd_run(args) -> int:
    run_dir = Path(args.run_dir)
    items = wr.load_items(Path(args.source), [i.strip() for i in args.items.split(",") if i.strip()])
    wave = wr.Wave(run_dir)
    ledger = wave.load()
    budget = item_budget(args.select == "model", args.critic)
    calls, tokens = wr.Wave.totals(ledger)
    env = ledger["envelope"]
    left_calls, left_tokens = env["max_calls"] - calls, env["max_tokens"] - tokens
    declared = {"family": FAMILY, "family_name": FAMILY_NAME, "per_item": budget, "items": len(items),
                "worst_case_calls": budget["max_calls"] * len(items), "worst_case_tokens": budget["max_tokens"] * len(items),
                "ledger_calls_left": left_calls, "ledger_tokens_left": left_tokens,
                "seconds_left": round(wave.seconds_left(ledger), 1),
                "note": "worst case may exceed the ledger: the ledger stops the run (exhausted budget is recorded)"}
    declared["min_fits"] = budget["min_calls"] * len(items) <= left_calls
    print(json.dumps(declared, indent=1))
    if args.check or not declared["min_fits"]:
        return 0 if declared["min_fits"] else 2
    lock = run_dir / "run.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, f"{os.getpid()} {args.batch}\n".encode())
    os.close(fd)
    batch_dir = run_dir / "batches" / args.batch
    batch_dir.mkdir(parents=True, exist_ok=False)
    source = Path(args.source)
    manifest = {"batch": args.batch, "declared": declared, "select": args.select, "critic": args.critic,
                "soft_repair": args.soft_repair,
                "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "template_sha256": ec.template_sha256(), "caps": CAPS, "status": "running", "started": time.time()}
    wr.write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    wave.backend = wr.ollama_backend(args.base_url, ledger["model"], ledger["num_ctx"])
    stop = threading.Event()
    wr.start_watchdog(wave, stop)
    retrieve = wr.retrieve if (args.critic and wr.RETRIEVER) else None
    stop_reason = None
    try:
        for row, info in items:
            task = ec.parse_task(info["body"])
            wr.append_jsonl(batch_dir / "task_audit.jsonl", {"item": row["id"], "full_task": info["body"],
                            "full_task_sha256": task["full_task_sha256"], "parsed": {k: task[k] for k in
                            ("global", "topics", "aspects", "sources", "global_sources", "min_words")}})

            def send(stage, prompt, _id=row["id"]):
                cap = CAPS["repair" if stage.startswith("repair") else stage]
                entry, timeout = wave.reserve(args.batch, FAMILY, _id, stage, cap, prompt)
                started = time.time()
                result, overran = wr.call_with_timeout(wave.backend, prompt, cap, timeout)
                elapsed = round(time.time() - started, 2)
                wave.settle(entry["seq"], "error" if result.get("error") else "ok", elapsed_s=elapsed,
                            error=result.get("error"), eval_count=result.get("eval_count"),
                            prompt_eval_count=result.get("prompt_eval_count"), done_reason=result.get("done_reason"))
                wr.append_jsonl(batch_dir / "raw.jsonl", {"item": _id, "stage": stage, "cap": cap, "prompt": prompt,
                                                          **result, "elapsed_s": elapsed})
                if overran:
                    raise wr.StopWave("call_overran")
                if result.get("error") in wr.TRANSPORT_ERRORS:
                    raise wr.StopWave(f"transport_error:{result['error']}")
                return result

            def calls_left():
                c, _t = wr.Wave.totals(wave.load())
                return env["max_calls"] - c

            try:
                rec = run_item(send, task, info, row["id"], args.select, args.critic, calls_left, retrieve,
                               soft_repair=args.soft_repair)
            except wr.StopWave as exc:
                stop_reason = str(exc)
                rec = {"item": row["id"], "status": "stopped", "stop_reason": stop_reason, "answer": None}
            wr.append_jsonl(batch_dir / "records.jsonl", rec)
            wr.append_jsonl(batch_dir / "answers.jsonl", {"id": f"{row['id']}__{FAMILY}", "item": row["id"],
                            "family": FAMILY, "topic": rec.get("topic_id"), "answer": rec.get("answer"),
                            "error_type": None if rec.get("answer") else (rec.get("failure") or rec.get("stop_reason")),
                            "batch": args.batch})
            if stop_reason:
                break
    finally:
        stop.set()
        lock.unlink()
    manifest.update(status="stopped" if stop_reason else "complete", stop_reason=stop_reason, finished=time.time())
    wr.write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    calls, tokens = wr.Wave.totals(wave.load())
    print(json.dumps({"batch": args.batch, "status": manifest["status"], "stop_reason": stop_reason,
                      "ledger_calls": calls, "ledger_tokens": tokens}, indent=1))
    return 0 if not stop_reason else 1


def cmd_offline(args) -> int:
    """Contract check of legacy plain-text answers (no calls): original vs cleaned, per row."""
    rows = {r["id"]: r for r in er.read_jsonl(Path(args.source))}
    out = []
    for ans in wr.read_jsonl(Path(args.answers)):
        if not ans.get("answer"):
            continue
        info = er.detect_essay(rows[ans["item"]]["prompt"])
        task = ec.parse_task(info["body"])
        chk = ec.check_body(ans["answer"], task, ans["topic"])
        out.append({"id": ans["id"], "family": ans.get("family"), "topic": ans["topic"], "ok": chk["ok"],
                    "triggers": chk["triggers"], "words_original": ec.words(ans["answer"]),
                    "words_body_before": chk["body_words_before_cleanup"],
                    "words_clean": chk["validation"]["words"] if chk["validation"] else None,
                    "ops": [o["op"] for o in chk["ops"]]})
    for r in out:
        print(json.dumps(r, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--max-calls", type=int, required=True)
    p.add_argument("--max-tokens", type=int, required=True)
    p.add_argument("--deadline-utc", required=True)
    p.add_argument("--allowance-source", default="")
    p.add_argument("--model", default="gemma4:12b-it-q4_K_M")
    p.add_argument("--num-ctx", type=int, default=32768)
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("run")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--items", required=True)
    p.add_argument("--select", default="model", help="model | first | fixed:N | most-aspects")
    p.add_argument("--critic", action="store_true")
    p.add_argument("--soft-repair", action="store_true", help="also repair below-400 outputs that pass the hard contract (probe k1 used this)")
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("offline")
    p.add_argument("--source", required=True)
    p.add_argument("--answers", required=True)
    p.set_defaults(func=cmd_offline)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
