"""Paired native-thinking essay wave for issue #80 (lead declaration 5848780385). Stdlib only.

Two arms on the SAME frozen items/topics/evidence, exactly 2 stages per item and arm:
  T  K-think    think:true,  num_predict 20480 TOTAL generation tokens per call
  N  K-nothink  think:false, num_predict 4096 per call
  stage1 draft     essay-contract-v2 writer prompt (selected topic only), no evidence
  stage2 review    ONE grounded review-and-rewrite call on EVERY draft that returned any text: the
                   precomputed #6 BM25 excerpts + the draft (+ its mechanical failures, if any);
                   returns the final essay. No other critic/selector/repair calls exist.

Accounting (never fabricated): Ollama's native eval_count is recorded as-is. With thinking on it
counts thinking + final tokens together; no split is derived. The essay is ONLY message.content:
message.thinking is kept privately and never used as, or merged into, the essay. A call that
ends with done_reason=length (truncated) or an empty content is a FAILED stage.

  freeze  (CPU) deterministic items + topics + retrieval -> <run>/bundle.json (+ sha256)
  init    ledger: 24 calls, 294,912 requested tokens, 2 arms, ABSOLUTE deadline, 0 retries
  guard   read-only host checks (version, model digest, thinking capability, loaded context)
  run     sequential dispatch; guard + pins re-checked before the first call and context after each

  python scripts/Pewciu6/essay_think_run.py freeze --run-dir agentsLog/Pewciu6/essay/private/think-X
  python scripts/Pewciu6/essay_think_run.py init   --run-dir ... --deadline-utc 2026-09-26T20:05:00Z
  python scripts/Pewciu6/essay_think_run.py run    --run-dir ... --batch t1 [--check]
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import essay_contract as ec  # noqa: E402
import essay_route as er  # noqa: E402
import essay_wave_run as wr  # noqa: E402

REVISION = "essay-think-v1"
ARMS = {"T": {"name": "K-think", "think": True, "cap": 20480},
        "N": {"name": "K-nothink", "think": False, "cap": 4096}}
STAGES = ("draft", "review")
N_ITEMS = 6
MAX_CALLS = N_ITEMS * len(ARMS) * len(STAGES)                                   # 24
MAX_TOKENS = N_ITEMS * len(STAGES) * sum(a["cap"] for a in ARMS.values())       # 294,912
WALL_S = 3600
PER_CALL_MAX_S = 420
MIN_CALL_START_S = 60
MODEL = "gemma4:12b-it-q4_K_M"
MODEL_DIGEST = "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"
OLLAMA_VERSION = "0.34.4"
NUM_CTX = 32768
# conservative prompt-size bound for the context guard (Polish is > 2.5 bytes/token for Gemma)
BYTES_PER_TOKEN_LOWER = 2.0
SELECTION_SALT = "issue80-think-v1"
ERAS = (("medieval", -10_000, 1500), ("early_modern", 1500, 1795), ("modern_1795_plus", 1795, 10_000))
FIXTURES = HERE.parents[1] / "agentsLog" / "Pewciu6" / "essay" / "dev_fixtures.jsonl"
TOPIC_POLICY = "most-aspects"
PINNED_FILES = ("essay_think_run.py", "essay_contract.py", "essay_wave_run.py", "essay_route.py")

REVIEW_RULES = """\
ETAP 2 z 2: RECENZJA I POPRAWA. Poniżej jest pierwsza wersja Twojego wypracowania oraz WYCIĄGI z encyklopedii. Najpierw sprawdź pierwszą wersję jak surowy egzaminator:
- każdą datę, nazwę własną, przypisanie osoby do wydarzenia i związek przyczynowo-skutkowy porównaj z WYCIĄGAMI; za błąd uznaj też twierdzenia, których wyciągi nie potwierdzają i które wyglądają na wymyślone, oraz fakty spoza zakresu chronologicznego tematu;
- wskaż aspekty potraktowane powierzchownie i fakty z wyciągów, które je wzmocnią.
Potem napisz poprawioną, pełną wersję: usuń lub popraw każdy błąd, pogłęb słabe aspekty konkretnymi faktami (rok, nazwa własna, związek z tezą) i powiąż każdy argument z tezą. Nie dopisuj ogólników ani powtórzeń tylko po to, by wydłużyć tekst; nie wprowadzaj faktów, których nie potwierdzają wyciągi ani nie jesteś pewien.

Odpowiedz WYŁĄCZNIE jednym obiektem JSON, bez tekstu przed nim ani po nim, z polami w tej kolejności:
{{"uwagi": "<zwięzła lista znalezionych błędów i poprawek, najwyżej 120 słów>", "topic_id": {topic}, "body": "<pełna poprawiona treść wypracowania>"}}
Pole "body" podlega tym samym wymaganiom co wcześniej (sama treść, bez nagłówków, {tmin}–{tmax} słów, akapity oddzielone \\n\\n). Pole "uwagi" nie jest częścią wypracowania.
{mechanical}
PIERWSZA WERSJA:
{draft}

"""
MECHANICAL_NOTE = "Pierwsza wersja miała też usterki formalne, które musisz naprawić:\n{items}\n"
DRAFT_CUT_CHARS = 8000  # ~1,100 Polish words: every 400-500-word draft fits whole; keeps the review prompt small
MIN_START_S_BY_ARM = {"T": 240, "N": 60}  # never start a call the deadline would cut off (an overrun stops the wave)
TRUNCATED_NOTE = "- Pierwsza wersja była niekompletna albo niepoprawnie zakończona; zwróć pełną, zakończoną wersję."
REVIEW_EXTRA_KEYS = ("uwagi",)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def template_sha256() -> str:
    return sha256_text("\x00".join([REVISION, ec.template_sha256(), REVIEW_RULES, MECHANICAL_NOTE, TRUNCATED_NOTE,
                                    wr.excerpts_block([]), wr.NO_CITATIONS,
                                    json.dumps(ARMS, sort_keys=True), str(NUM_CTX)]))


# ---------------------------------------------------------------- freeze (CPU, deterministic)

def topic_start_year(text: str) -> int:
    years = [int(y) for y in ec.YEAR.findall(text) if 900 <= int(y) <= 2100]
    return min(years) if years else 10_000


def select_items(rows: list[dict]) -> list[dict]:
    """2 items per era bucket (by the selected topic's first year), lowest salted sha256 first."""
    picked = []
    for era, lo, hi in ERAS:
        cands = []
        for row in rows:
            task = ec.parse_task(er.detect_essay(row["prompt"])["body"])
            topic = ec.select_deterministic(task, TOPIC_POLICY)
            year = topic_start_year(task["topics"][topic])
            if lo <= year < hi:
                cands.append((sha256_text(f"{SELECTION_SALT}|{row['id']}"), row["id"], topic, year))
        cands.sort()
        if len(cands) < 2:
            raise SystemExit(f"era {era} has {len(cands)} candidates, need 2")
        picked += [{"item": c[1], "topic": c[2], "topic_start_year": c[3], "era": era,
                    "selection_hash": c[0]} for c in cands[:2]]
    return picked


def review_prompt(task: dict, topic: int, draft_text: str, triggers: list[str], excerpts: list[dict]) -> str:
    mech_triggers = [t for t in triggers if not t.startswith("call_error:")]
    items = ec.repair_instructions(mech_triggers, topic, None, [])
    if any(t.startswith(("call_error:truncated", "call_error:empty", "call_error:done_reason")) for t in triggers):
        items = (items + "\n" if items else "") + TRUNCATED_NOTE
    mech = MECHANICAL_NOTE.format(items=items) if items else ""
    extra = REVIEW_RULES.format(topic=topic, tmin=ec.TARGET_MIN, tmax=ec.TARGET_MAX, mechanical=mech,
                                draft=(draft_text or "").strip()[:DRAFT_CUT_CHARS])
    extra += wr.excerpts_block(excerpts) + wr.NO_CITATIONS
    return ec.writer_prompt(task, topic, extra)


def cmd_freeze(args) -> int:
    run_dir = Path(args.run_dir)
    er.require_private_dir(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    wr.RETRIEVER = args.retriever
    rows = {r["id"]: r for r in er.read_jsonl(FIXTURES)}
    items = []
    for sel in select_items(list(rows.values())):
        info = er.detect_essay(rows[sel["item"]]["prompt"])
        task = ec.parse_task(info["body"])
        excerpts = wr.retrieve(info, sel["topic"])
        items.append({**sel, "full_task": info["body"], "full_task_sha256": task["full_task_sha256"],
                      "writer_task_sha256": sha256_text(ec.writer_task(task, sel["topic"])),
                      "draft_prompt": ec.writer_prompt(task, sel["topic"]),
                      "draft_prompt_sha256": sha256_text(ec.writer_prompt(task, sel["topic"])),
                      "evidence": excerpts, "evidence_sha256": sha256_text(json.dumps(excerpts, ensure_ascii=False,
                                                                                      sort_keys=True))})
    bundle = {"revision": REVISION, "contract_revision": ec.CONTRACT_REVISION, "template_sha256": template_sha256(),
              "fixtures_sha256": sha256_file(FIXTURES), "selection": {"salt": SELECTION_SALT, "eras": ERAS,
              "per_era": 2, "topic_policy": TOPIC_POLICY}, "retriever": args.retriever,
              "retriever_sha256": sha256_file(args.retriever), "index_sha256": sha256_file(args.index),
              "arms": ARMS, "items": items, "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    wr.write_json_atomic(run_dir / "bundle.json", bundle)
    print(json.dumps({"bundle_sha256": sha256_file(run_dir / "bundle.json"),
                      "items": [(i["item"], i["topic"], i["era"], len(i["evidence"])) for i in items]}, indent=1))
    return 0


# ---------------------------------------------------------------- backend

def http_json(url: str, body: dict | None, timeout: float):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def think_backend(base_url: str, model: str, num_ctx: int, think: bool):
    """One /api/chat call. The essay is message.content only; thinking is returned separately."""
    url = base_url.rstrip("/") + "/api/chat"

    def call(prompt: str, cap: int, timeout: float) -> dict:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                "think": think, "options": {"num_predict": cap, "num_ctx": num_ctx}}
        try:
            data = http_json(url, body, timeout)
        except urllib.error.HTTPError as exc:
            return {"error": f"http_{exc.code}"}
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
            return {"error": type(exc).__name__}
        return interpret(data, think)

    return call


def interpret(data: dict, think: bool) -> dict:
    msg = data.get("message") or {}
    text = msg.get("content") or ""
    thinking = msg.get("thinking") or ""
    out = {"text": text, "thinking": thinking, "thinking_chars": len(thinking), "content_chars": len(text),
           "think_requested": think, "done_reason": data.get("done_reason"), "eval_count": data.get("eval_count"),
           "prompt_eval_count": data.get("prompt_eval_count"), "model": data.get("model"),
           "eval_duration_ns": data.get("eval_duration"), "total_duration_ns": data.get("total_duration")}
    if data.get("done_reason") == "length":
        out["error"] = "truncated"  # the final may be partial or absent: a failure, never repaired from thinking
    elif data.get("done_reason") != "stop":
        out["error"] = f"done_reason:{data.get('done_reason')}"
    elif not text.strip():
        out["error"] = "empty_final_after_thinking" if thinking.strip() else "empty"
    elif not think and thinking.strip():
        out["error"] = "unexpected_thinking_when_off"
    out["thinking_absent_when_on"] = bool(think and not thinking.strip())
    return out


def guard_host(base_url: str, timeout: float = 20) -> dict:
    """Read-only checks; raises SystemExit (fail closed) on any mismatch or missing value."""
    base = base_url.rstrip("/")
    ver = http_json(base + "/api/version", None, timeout).get("version")
    tags = http_json(base + "/api/tags", None, timeout).get("models", [])
    match = [m for m in tags if m.get("name") == MODEL or m.get("model") == MODEL]
    show = http_json(base + "/api/show", {"model": MODEL}, timeout)
    ps = http_json(base + "/api/ps", None, timeout).get("models", [])
    loaded = [m for m in ps if m.get("name") == MODEL or m.get("model") == MODEL]
    others = [m.get("name") for m in ps if m not in loaded]
    rec = {"version": ver, "digest": match[0].get("digest") if len(match) == 1 else None,
           "capabilities": show.get("capabilities"), "loaded": [{"context_length": m.get("context_length"),
           "size_vram": m.get("size_vram")} for m in loaded], "other_loaded_models": others}
    problems = []
    if ver != OLLAMA_VERSION:
        problems.append(f"ollama_version:{ver}")
    if rec["digest"] != MODEL_DIGEST:
        problems.append(f"model_digest:{rec['digest']}")
    if "thinking" not in (rec["capabilities"] or []):
        problems.append("no_thinking_capability")
    if others:
        problems.append(f"other_models_loaded:{others}")
    for m in rec["loaded"]:
        if not isinstance(m["context_length"], int) or m["context_length"] != NUM_CTX:
            problems.append(f"loaded_context:{m['context_length']}")
    rec["problems"] = problems
    return rec


def check_loaded_context(base_url: str) -> int | None:
    ps = http_json(base_url.rstrip("/") + "/api/ps", None, 20).get("models", [])
    loaded = [m for m in ps if m.get("name") == MODEL or m.get("model") == MODEL]
    if len(loaded) != 1 or not isinstance(loaded[0].get("context_length"), int):
        return None
    return loaded[0]["context_length"]


def prompt_fits(prompt: str, cap: int, num_ctx: int = NUM_CTX) -> tuple[bool, int]:
    bound = int(len(prompt.encode("utf-8")) / BYTES_PER_TOKEN_LOWER) + 64
    return bound + cap <= num_ctx, bound


# ---------------------------------------------------------------- one item, one arm

def version(stage: str, result: dict, check: dict | None, allow=()) -> dict:
    parsed = ec.parse_output(result.get("text") or "", allow_keys=allow) if result.get("text") else None
    return {"stage": stage, "error": result.get("error"), "eval_count": result.get("eval_count"),
            "prompt_eval_count": result.get("prompt_eval_count"), "done_reason": result.get("done_reason"),
            "thinking_chars": result.get("thinking_chars"), "content_chars": result.get("content_chars"),
            "raw": result.get("text"),
            "pre_cleanup_body": parsed.get("body") if parsed and parsed.get("ok") else None,
            "extras": parsed.get("extras") if parsed and parsed.get("ok") else None,
            "post_cleanup_text": check.get("clean") if check else None,
            "check": check}


def stage_check(result: dict, task: dict, topic: int, allow=()) -> dict | None:
    """Contract check of the final text; a call error (truncated/empty) makes the stage fail."""
    if not (result.get("text") or "").strip():
        return None
    chk = ec.contract_check(result["text"], task, topic, allow_keys=allow)
    if result.get("error"):
        chk = {**chk, "ok": False, "triggers": [f"call_error:{result['error']}"] + chk["triggers"]}
    return chk


def run_arm(send, arm: str, item: dict, rec: dict | None = None) -> dict:
    """Exactly draft -> review. The review runs on every draft that returned any content.

    `rec` is filled in place, so a StopWave mid-item still leaves the completed draft on record.
    """
    task = ec.parse_task(item["full_task"])
    topic = item["topic"]
    rec = rec if rec is not None else {}
    rec.update({"item": item["item"], "arm": arm, "arm_name": ARMS[arm]["name"], "topic_id": topic, "unsent": []})
    d = send("draft", item["draft_prompt"])
    dchk = stage_check(d, task, topic)
    rec["draft"] = version("draft", d, dchk)
    rec["draft_answer"] = ec.render_answer(topic, dchk["clean"]) if dchk and dchk["ok"] else None
    if not (d.get("text") or "").strip():
        rec["unsent"].append({"stage": "review", "reason": f"no_draft_text:{d.get('error')}"})
        rec["review"] = None
    else:
        if dchk and dchk["ok"]:
            draft_text, triggers = dchk["clean"], []
        else:
            parsed = ec.parse_output(d["text"])
            draft_text = parsed["body"] if parsed.get("ok") else d["text"]
            triggers = (dchk or {}).get("triggers", []) or [f"call_error:{d.get('error')}"]
        prompt = review_prompt(task, topic, draft_text, triggers, item["evidence"])
        rec["review_input"] = {"draft_passed_contract": bool(dchk and dchk["ok"]), "triggers_given": triggers,
                               "prompt_sha256": sha256_text(prompt)}
        r = send("review", prompt)
        if r.get("unsent"):
            rec["unsent"].append({"stage": "review", "reason": r["error"]})
        rchk = stage_check(r, task, topic, REVIEW_EXTRA_KEYS)
        rec["review"] = version("review", r, rchk, REVIEW_EXTRA_KEYS)
    rchk = (rec["review"] or {}).get("check")
    rec["final_answer"] = ec.render_answer(topic, rchk["clean"]) if rchk and rchk["ok"] else None
    rec["draft_status"] = "ok" if rec["draft_answer"] else "failed"
    rec["final_status"] = "ok" if rec["final_answer"] else "failed"
    return rec


# ---------------------------------------------------------------- cli

def iso_to_epoch(s: str) -> float:
    return float(calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")))


def cmd_init(args) -> int:
    run_dir = Path(args.run_dir)
    er.require_private_dir(run_dir)
    if (run_dir / "ledger.json").exists():
        raise SystemExit("ledger exists; never re-initialize a wave")
    bundle_sha = sha256_file(run_dir / "bundle.json")
    now = time.time()
    deadline = iso_to_epoch(args.deadline_utc)
    if not 0 < deadline - now <= WALL_S:
        raise SystemExit(f"deadline must be within {WALL_S}s from now (got {deadline - now:.0f}s)")
    env = {"max_calls": MAX_CALLS, "max_tokens": MAX_TOKENS, "max_families": len(ARMS),
           "wall_seconds": round(deadline - now), "per_call_max_s": PER_CALL_MAX_S, "retries": 0, "smokes": 0,
           "prior_calls": 0, "prior_tokens": 0}
    ledger = {"revision": REVISION, "wave_id": run_dir.name, "envelope": env, "arms": ARMS,
              "bundle_sha256": bundle_sha, "template_sha256": template_sha256(), "model": MODEL,
              "model_digest": MODEL_DIGEST, "num_ctx": NUM_CTX, "temperature": None, "base_url": args.base_url,
              "declared_start_utc": args.declared_start_utc, "wave_start": now, "deadline": deadline,
              "wave_start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
              "deadline_iso": args.deadline_utc, "families": [], "entries": [], "created": now,
              "pins": {f: sha256_file(HERE / f) for f in PINNED_FILES},
              "rate": "3.28 USD/h UNVERIFIED planning proxy (60-min estimate 3.28 USD, not a bill)"}
    wr.write_json_atomic(run_dir / "ledger.json", ledger)
    print(json.dumps({k: ledger[k] for k in ("envelope", "bundle_sha256", "template_sha256", "pins",
                                             "wave_start_iso", "deadline_iso")}, indent=1))
    return 0


def order(items: list[dict]) -> list[tuple[dict, str]]:
    """Item-major, arm order alternating by item index (T first on even, N first on odd)."""
    out = []
    for n, item in enumerate(items):
        for arm in (("T", "N") if n % 2 == 0 else ("N", "T")):
            out.append((item, arm))
    return out


def cmd_run(args) -> int:
    run_dir = Path(args.run_dir)
    wave = wr.Wave(run_dir)
    ledger = wave.load()
    bundle_path = run_dir / "bundle.json"
    problems = []
    if sha256_file(bundle_path) != ledger["bundle_sha256"]:
        problems.append("bundle_sha256")
    for f, h in ledger["pins"].items():
        if sha256_file(HERE / f) != h:
            problems.append(f"pin:{f}")
    if template_sha256() != ledger["template_sha256"]:
        problems.append("template_sha256")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    calls, tokens = wr.Wave.totals(ledger)
    left_s = ledger["deadline"] - time.time()
    host = guard_host(args.base_url)
    problems += host["problems"]
    if left_s < MIN_CALL_START_S:
        problems.append("deadline")
    report = {"calls_used": calls, "tokens_reserved": tokens, "seconds_left": round(left_s), "host": host,
              "problems": problems, "plan": [(i["item"], a) for i, a in order(bundle["items"])]}
    print(json.dumps(report, indent=1, ensure_ascii=False))
    if problems:
        return 2
    if args.check:
        return 0
    batch_dir = run_dir / "batches" / args.batch
    batch_dir.mkdir(parents=True, exist_ok=False)
    lock = run_dir / "run.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, f"{os.getpid()} {args.batch}\n".encode())
    os.close(fd)
    manifest = {"batch": args.batch, "bundle_sha256": ledger["bundle_sha256"], "guard": host, "status": "running",
                "started": time.time(), "order": report["plan"]}
    wr.write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    stop = threading.Event()
    wr.start_watchdog(wave, stop)
    stop_reason = None
    try:
        for item, arm in order(bundle["items"]):
            backend = think_backend(args.base_url, MODEL, NUM_CTX, ARMS[arm]["think"])
            cap = ARMS[arm]["cap"]

            def send(stage, prompt, _id=item["item"], _arm=arm, _cap=cap, _backend=backend):
                fits, bound = prompt_fits(prompt, _cap)
                if not fits:  # this stage only: recorded unsent, never reserved, the wave continues
                    return {"error": f"context_guard_unsent:{bound}+{_cap}>{NUM_CTX}", "unsent": True, "text": ""}
                if wave.seconds_left(wave.load()) < MIN_START_S_BY_ARM[_arm]:
                    raise wr.StopWave("deadline")
                entry, timeout = wave.reserve(args.batch, _arm, _id, stage, _cap, prompt)
                started = time.time()
                result, overran = wr.call_with_timeout(_backend, prompt, _cap, timeout)
                elapsed = round(time.time() - started, 2)
                ctx = None
                if not overran and result.get("error") not in wr.TRANSPORT_ERRORS:
                    try:
                        ctx = check_loaded_context(args.base_url)
                    except Exception as exc:  # noqa: BLE001 - settle + raw first, then stop via ctx != NUM_CTX
                        ctx = f"ps_error:{type(exc).__name__}"
                wave.settle(entry["seq"], "error" if result.get("error") else "ok", elapsed_s=elapsed,
                            error=result.get("error"), eval_count=result.get("eval_count"),
                            prompt_eval_count=result.get("prompt_eval_count"), done_reason=result.get("done_reason"),
                            thinking_chars=result.get("thinking_chars"), content_chars=result.get("content_chars"),
                            think=ARMS[_arm]["think"], loaded_context=ctx, prompt_bound_tokens=bound,
                            thinking_absent_when_on=result.get("thinking_absent_when_on"))
                wr.append_jsonl(batch_dir / "raw.jsonl", {"item": _id, "arm": _arm, "stage": stage, "cap": _cap,
                                                          "prompt": prompt, **result, "elapsed_s": elapsed,
                                                          "loaded_context": ctx})
                if overran:
                    raise wr.StopWave("call_overran")
                if result.get("error") in wr.TRANSPORT_ERRORS or str(result.get("error")).startswith(("http_", "exception:")):
                    raise wr.StopWave(f"transport_error:{result['error']}")  # systematic: never burn one per item
                if result.get("thinking_absent_when_on"):
                    raise wr.StopWave("thinking_absent_when_on")  # the T arm would silently be a no-think arm
                if ctx != NUM_CTX:
                    raise wr.StopWave(f"loaded_context:{ctx}")
                pe = result.get("prompt_eval_count")
                if isinstance(pe, int) and pe + _cap > NUM_CTX:
                    result = {**result, "context_overflow": f"{pe}+{_cap}>{NUM_CTX}"}  # recorded; guard makes it unreachable
                return result

            rec = {}
            try:
                run_arm(send, arm, item, rec)
            except wr.StopWave as exc:
                stop_reason = str(exc)
                rec.update(status="stopped", stop_reason=stop_reason, final_answer=None)
                rec.setdefault("draft_answer", None)
            wr.append_jsonl(batch_dir / "records.jsonl", rec)
            for stage in ("draft", "final"):
                ans = rec.get(f"{stage}_answer")
                wr.append_jsonl(batch_dir / "answers.jsonl", {
                    "id": f"{item['item']}__{arm}-{stage}", "item": item["item"], "family": f"{arm}-{stage}",
                    "topic": item["topic"], "answer": ans, "batch": args.batch,
                    "error_type": None if ans else (rec.get("stop_reason") or failure_reason(rec, stage))})
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


def failure_reason(rec: dict, stage: str) -> str:
    v = rec.get("draft" if stage == "draft" else "review")
    if v is None:
        return "unsent:" + ",".join(u["reason"] for u in rec.get("unsent", [])) if rec.get("unsent") else "missing"
    if v.get("check") is None:
        return f"no_final_text:{v.get('error')}"
    return "contract:" + ",".join(v["check"]["triggers"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--retriever", required=True)
    p.add_argument("--index", required=True)
    p.set_defaults(func=cmd_freeze)
    p = sub.add_parser("init")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--deadline-utc", required=True)
    p.add_argument("--declared-start-utc", required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("run")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("guard")
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.set_defaults(func=lambda a: print(json.dumps(guard_host(a.base_url), indent=1)) or 0)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
