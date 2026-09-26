"""Constrained claim-edit essay wave for issue #80 (lead declaration 5849201046). Stdlib only.

Six DEV fixtures (001,003,004,005,009,010), preselected topic 1. Per topic, three calls:
  T-draft   think:true,  num_predict 20480 TOTAL generation tokens
  N-draft   think:false, num_predict 4096
  verify    ONE grounded call on the T-draft ONLY: think:true, num_predict 20480. It never
            rewrites the essay. It returns a small JSON list of exact original spans plus a
            replacement/deletion and a separately stored reason. Only unambiguous
            once-occurring, non-overlapping spans are applied (see evaluate_edits/apply_edits).
Drafts return PLAIN PROSE via the existing essay-contract-v2 {topic_id, body} JSON envelope; the
"Temat nr N" header is rendered once by code (ec.render_answer), never by the model.

No full rewrite ever happens at the verify stage. On any verify/parse/apply failure, or if the
patched text fails revalidation (length/topic/clean prose), final = the already-validated
T-draft, labelled FALLBACK. No extra calls or retries. A missing/invalid T-draft stays failed
(nothing to fall back to). Successful edits and fallbacks are counted separately in the export.

Schema-constrained ("format": <json schema>) output was NOT used: verifying native support would
need a throwaway probe call, and the wave allows 0 smokes. The verify stage instead uses the same
strict text-JSON parser style as every other stage in this codebase (parse_edit_response below).

A separately labelled known-VALIDATION essay diagnostic (thinking draft only) is declared in the
authorization but is NOT executed by this run: no frozen VALIDATION-split essay item (task text)
exists in any locally reachable private/validation_2024 artifact as of this wave (checked: none of
runner_input.jsonl, eval_keys.jsonl, arkusz.txt/arkusz_raw.txt across every reachable worktree
contain an essay-type row or "wypracowanie" topic text). Building one now would mean transcribing
a fresh exam page, which is new work outside this run's frozen manifest. The ledger reserves the
19th call / 20,480 tokens for it; this run only spends 18 calls / 270,336 tokens.

  python scripts/Pewciu6/essay_edit_run.py freeze --run-dir agentsLog/Pewciu6/essay/private/edit-X \\
      --retriever <path> --index <path>
  python scripts/Pewciu6/essay_edit_run.py init   --run-dir ... --deadline-utc 2026-09-26T20:35:00Z \\
      --declared-start-utc 2026-09-26T19:35:00Z
  python scripts/Pewciu6/essay_edit_run.py run    --run-dir ... --batch t1 [--check]
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
import essay_think_run as tr  # noqa: E402  (shared backend/guard helpers only; not modified)

REVISION = "essay-edit-v1"
ARMS = {"T": {"name": "K-think", "think": True, "cap": 20480},
        "N": {"name": "K-nothink", "think": False, "cap": 4096}}
VERIFY_CAP = 20480
VERIFY_THINK = True
N_ITEMS = 6
FIXTURE_IDS = ("dev-essay-001", "dev-essay-003", "dev-essay-004", "dev-essay-005", "dev-essay-009", "dev-essay-010")
TOPIC = 1
MAX_CALLS = N_ITEMS * 3 + 1                                                    # 19 (18 this run + 1 deferred)
MAX_TOKENS = N_ITEMS * (ARMS["T"]["cap"] + ARMS["N"]["cap"] + VERIFY_CAP) + VERIFY_CAP  # 290,816
THIS_RUN_MAX_CALLS = N_ITEMS * 3                                               # 18
THIS_RUN_MAX_TOKENS = N_ITEMS * (ARMS["T"]["cap"] + ARMS["N"]["cap"] + VERIFY_CAP)  # 270,336
WALL_S = 3600
MODEL = tr.MODEL
MODEL_DIGEST = tr.MODEL_DIGEST
OLLAMA_VERSION = tr.OLLAMA_VERSION
NUM_CTX = tr.NUM_CTX
FIXTURES = HERE.parents[1] / "agentsLog" / "Pewciu6" / "essay" / "dev_fixtures.jsonl"
MIN_START_S_BY_STAGE = {"T": 240, "N": 60, "verify": 240}
PINNED_FILES = ("essay_edit_run.py", "essay_contract.py", "essay_wave_run.py", "essay_route.py", "essay_think_run.py")

VERIFY_RULES = """\
ETAP: WERYFIKACJA FAKTÓW. Poniżej masz zatwierdzoną wersję wypracowania na temat nr {topic} oraz WYCIĄGI źródłowe. Sprawdź w tekście każdą datę, nazwę własną, przypisanie osoby do wydarzenia i związek przyczynowo-skutkowy, porównując je z WYCIĄGAMI; za błąd uznaj też twierdzenia, których wyciągi nie potwierdzają i które wyglądają na wymyślone, oraz fakty spoza zakresu chronologicznego tematu.

NIE przepisuj całego wypracowania. Zamiast tego zwróć WYŁĄCZNIE jeden obiekt JSON z listą drobnych, punktowych poprawek, bez żadnego tekstu przed nim ani po nim:
{{"edits": [{{"original": "<dokładny fragment WYPRACOWANIA poniżej, skopiowany bez zmian, występujący w nim dokładnie raz>", "replacement": "<poprawiony fragment, albo pusty ciąg jeśli fragment należy usunąć>", "reason": "<krótkie uzasadnienie, z odwołaniem do wyciągu>"}}], "notes": "<opcjonalne krótkie uwagi ogólne; nie część wypracowania>"}}

Zasady:
- "original" musi być fragmentem WYPRACOWANIA skopiowanym dosłownie (bez zmian w ortografii, spacjach czy interpunkcji) i występować w nim dokładnie raz.
- Nie wolno wymyślać fragmentów, których nie ma w tekście, ani poprawiać dwóch miejsc jednym wpisem.
- Popraw lub usuń tylko to, co jest błędne; nie dopisuj nowych akapitów, nowych faktów spoza wyciągów ani ogólników.
- Jeśli nie znajdziesz żadnego błędu, zwróć {{"edits": [], "notes": "brak błędów"}}.

WYPRACOWANIE:
{draft}

"""
EDIT_KEYS = ("edits", "notes")
EDIT_ITEM_KEYS = {"original", "replacement", "reason"}
MAX_EDIT_SPAN_CHARS = 500
MAX_EDIT_SPAN_SHARE = 0.30
MAX_REPLACEMENT_EXPANSION = 1.5  # replacement chars <= 1.5x original chars + 80 (tightened after review)
MAX_REPLACEMENT_EXTRA_CHARS = 80
MAX_EDIT_COUNT = 8                    # too many small edits can add up to a disguised rewrite
MAX_CUMULATIVE_SPAN_SHARE = 0.25      # sum(len(original)) over accepted edits, share of the draft
MAX_CUMULATIVE_NET_GROWTH_SHARE = 0.15  # sum(len(replacement) - len(original)), share of the draft


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def template_sha256() -> str:
    return sha256_text("\x00".join([REVISION, ec.template_sha256(), VERIFY_RULES, wr.excerpts_block([]),
                                    wr.NO_CITATIONS, json.dumps(ARMS, sort_keys=True), str(VERIFY_CAP),
                                    str(NUM_CTX)]))


# ---------------------------------------------------------------- freeze (CPU, deterministic)

def cmd_freeze(args) -> int:
    run_dir = Path(args.run_dir)
    er.require_private_dir(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    wr.RETRIEVER = args.retriever
    rows = {r["id"]: r for r in er.read_jsonl(FIXTURES)}
    missing = [i for i in FIXTURE_IDS if i not in rows]
    if missing:
        raise SystemExit(f"fixtures missing from {FIXTURES}: {missing}")
    items = []
    for item_id in FIXTURE_IDS:
        info = er.detect_essay(rows[item_id]["prompt"])
        if not info["is_essay"]:
            raise SystemExit(f"{item_id} is not routed as an essay; refusing")
        task = ec.parse_task(info["body"])
        if TOPIC not in task["topics"]:
            raise SystemExit(f"{item_id}: topic {TOPIC} not among {sorted(task['topics'])}")
        excerpts = wr.retrieve(info, TOPIC)
        draft_prompt = ec.writer_prompt(task, TOPIC)
        items.append({"item": item_id, "topic": TOPIC, "full_task": info["body"],
                      "full_task_sha256": task["full_task_sha256"],
                      "draft_prompt": draft_prompt, "draft_prompt_sha256": sha256_text(draft_prompt),
                      "evidence": excerpts,
                      "evidence_sha256": sha256_text(json.dumps(excerpts, ensure_ascii=False, sort_keys=True))})
    bundle = {"revision": REVISION, "contract_revision": ec.CONTRACT_REVISION, "template_sha256": template_sha256(),
              "fixtures_sha256": sha256_file(FIXTURES), "fixture_ids": list(FIXTURE_IDS), "topic": TOPIC,
              "retriever": args.retriever, "retriever_sha256": sha256_file(args.retriever),
              "index_sha256": sha256_file(args.index), "arms": ARMS, "verify_cap": VERIFY_CAP,
              "verify_think": VERIFY_THINK, "items": items,
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    wr.write_json_atomic(run_dir / "bundle.json", bundle)
    print(json.dumps({"bundle_sha256": sha256_file(run_dir / "bundle.json"),
                      "items": [(i["item"], i["topic"], len(i["evidence"])) for i in items]}, indent=1))
    return 0


# ---------------------------------------------------------------- verify: parse + apply (CPU only)

def parse_edit_response(raw: str) -> dict:
    """-> {ok, edits, notes, error}. Strict: one JSON object, only the two declared top-level keys."""
    text = (raw or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    fence = ec.FENCE.match(text)
    if fence:
        text = fence.group(1).strip()
    try:
        obj = json.loads(text, strict=False)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json"}
    if not isinstance(obj, dict):
        return {"ok": False, "error": "json_not_object"}
    extra = sorted(set(obj) - set(EDIT_KEYS))
    if extra:
        return {"ok": False, "error": "extra_keys:" + ",".join(extra)}
    edits = obj.get("edits")
    if not isinstance(edits, list):
        return {"ok": False, "error": "missing_edits_list"}
    parsed = []
    for i, e in enumerate(edits):
        if (not isinstance(e, dict) or set(e) - EDIT_ITEM_KEYS or "original" not in e or "replacement" not in e):
            return {"ok": False, "error": f"bad_edit_shape:{i}"}
        orig, repl = e.get("original"), e.get("replacement")
        reason = e.get("reason", "")
        if not isinstance(orig, str) or not orig.strip() or not isinstance(repl, str) or not isinstance(reason, str):
            return {"ok": False, "error": f"bad_edit_value:{i}"}
        parsed.append({"original": orig, "replacement": repl, "reason": reason})
    notes = obj.get("notes")
    return {"ok": True, "edits": parsed, "notes": notes if isinstance(notes, str) else None}


def count_occurrences(haystack: str, needle: str) -> int:
    """Overlap-safe occurrence count (str.count misses overlapping matches of periodic needles)."""
    if not needle:
        return 0
    count, start = 0, 0
    while True:
        idx = haystack.find(needle, start)
        if idx == -1:
            return count
        count += 1
        start = idx + 1


def evaluate_edits(draft: str, topic: int, edits: list[dict]) -> dict:
    """Deterministic acceptance of proposed spans. Never rewrites; only accepts unambiguous,
    non-overlapping, bounded, once-occurring spans, and only up to a cumulative edit budget (many
    small edits could otherwise add up to a disguised full rewrite).
    -> {accepted:[(start,end,edit,replacement)], rejected:[...]}
    """
    candidates, rejected = [], []
    for e in edits:
        orig, repl = e["original"], e["replacement"]
        count = count_occurrences(draft, orig)
        if count == 0:
            rejected.append({**e, "reject_reason": "not_found"})
            continue
        if count > 1:
            rejected.append({**e, "reject_reason": "ambiguous_multiple_occurrences"})
            continue
        if len(orig) > MAX_EDIT_SPAN_CHARS or len(orig) > MAX_EDIT_SPAN_SHARE * max(len(draft), 1):
            rejected.append({**e, "reject_reason": "span_too_large"})
            continue
        if len(repl) > MAX_REPLACEMENT_EXPANSION * len(orig) + MAX_REPLACEMENT_EXTRA_CHARS:
            rejected.append({**e, "reject_reason": "replacement_too_large"})
            continue
        if "\n" in repl or "{" in repl or "```" in repl or "#" in repl:
            rejected.append({**e, "reject_reason": "replacement_not_prose"})
            continue
        if ec.other_topics_marked(repl, topic):
            rejected.append({**e, "reject_reason": "replacement_other_topic"})
            continue
        start = draft.find(orig)
        candidates.append((start, start + len(orig), e, repl))
    candidates.sort(key=lambda c: c[0])
    overlapping = set()
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if candidates[j][0] < candidates[i][1]:
                overlapping.add(i)
                overlapping.add(j)
    accepted = []
    for i, (start, end, e, repl) in enumerate(candidates):
        if i in overlapping:
            rejected.append({**e, "reject_reason": "overlap"})
        else:
            accepted.append((start, end, e, repl))
    if len(accepted) > MAX_EDIT_COUNT:
        rejected += [{**e, "reject_reason": "cumulative_edit_budget_exceeded"} for _s, _en, e, _r in accepted]
        return {"accepted": [], "rejected": rejected}
    span_chars = sum(end - start for start, end, _e, _r in accepted)
    net_growth = sum(len(repl) - (end - start) for start, end, _e, repl in accepted)
    draft_len = max(len(draft), 1)
    if (span_chars > MAX_CUMULATIVE_SPAN_SHARE * draft_len
            or net_growth > MAX_CUMULATIVE_NET_GROWTH_SHARE * draft_len):
        rejected += [{**e, "reject_reason": "cumulative_edit_budget_exceeded"} for _s, _en, e, _r in accepted]
        return {"accepted": [], "rejected": rejected}
    return {"accepted": accepted, "rejected": rejected}


def apply_edits(draft: str, accepted: list) -> str:
    out, pos = [], 0
    for start, end, _e, repl in sorted(accepted, key=lambda a: a[0]):
        out.append(draft[pos:start])
        out.append(repl)
        pos = end
    out.append(draft[pos:])
    return "".join(out)


def revalidate_patch(patched: str, task: dict, topic: int) -> dict:
    """Re-run the SAME contract gate the T-draft already passed. `clean != patched` means the
    patch introduced something the cleanup pass would strip (a heading, a wrapper, non-prose) even
    though evaluate_edits already blocks the obvious cases; this is the second, independent gate."""
    chk = ec.check_body(patched, task, topic)
    ok = chk["ok"] and chk["clean"] == patched
    if not chk["ok"]:
        reasons = list(chk["triggers"])
    elif chk["clean"] != patched:
        reasons = ["patch_altered_by_cleanup"]
    else:
        reasons = []
    words = (chk.get("validation") or {}).get("words", ec.count_words(patched))
    return {"ok": ok, "hard": reasons, "words": words}


def verify_prompt(topic: int, draft_text: str, excerpts: list[dict]) -> str:
    return (VERIFY_RULES.format(topic=topic, draft=draft_text.strip())
            + wr.excerpts_block(excerpts) + wr.NO_CITATIONS)


def run_verify(draft_clean: str, task: dict, topic: int, edit_result: dict) -> dict:
    """Apply the parsed+validated verify response to an already-contract-checked T-draft.

    edit_result is the output of parse_edit_response (called by the caller with the raw text).
    """
    if not edit_result["ok"]:
        return {"status": "fallback", "reason": f"parse:{edit_result['error']}", "patched_text": None,
                "accepted": [], "rejected": []}
    ev = evaluate_edits(draft_clean, topic, edit_result["edits"])
    patched = apply_edits(draft_clean, ev["accepted"])
    val = revalidate_patch(patched, task, topic)
    if not val["ok"]:
        return {"status": "fallback", "reason": "revalidate:" + ",".join(val["hard"]), "patched_text": None,
                "accepted": ev["accepted"], "rejected": ev["rejected"], "revalidation": val}
    return {"status": "patched", "reason": None, "patched_text": patched, "accepted": ev["accepted"],
            "rejected": ev["rejected"], "revalidation": val}


# ---------------------------------------------------------------- one item (T-draft, N-draft, verify)

def version(stage: str, result: dict) -> dict:
    parsed = ec.parse_output(result.get("text") or "") if result.get("text") else None
    return {"stage": stage, "error": result.get("error"), "eval_count": result.get("eval_count"),
            "prompt_eval_count": result.get("prompt_eval_count"), "done_reason": result.get("done_reason"),
            "thinking_chars": result.get("thinking_chars"), "content_chars": result.get("content_chars"),
            "raw": result.get("text"), "extras": parsed.get("extras") if parsed and parsed.get("ok") else None}


def run_item(send, item: dict, rec: dict) -> dict:
    """send(stage, prompt, cap, think) -> result dict. `rec` is filled in place so a mid-item
    StopWave still leaves completed calls on record."""
    task = ec.parse_task(item["full_task"])
    topic = item["topic"]
    rec.update({"item": item["item"], "topic_id": topic})
    drafts = {}
    for arm in rec["draft_order"]:
        r = send(arm, item["draft_prompt"], ARMS[arm]["cap"], ARMS[arm]["think"])
        chk = ec.contract_check(r["text"], task, topic) if (r.get("text") or "").strip() else None
        if r.get("error") and chk:
            chk = {**chk, "ok": False, "triggers": [f"call_error:{r['error']}"] + chk["triggers"]}
        rec[f"draft_{arm}"] = version(f"draft_{arm}", r)
        rec[f"draft_{arm}"]["check"] = chk
        answer = ec.render_answer(topic, chk["clean"]) if chk and chk["ok"] else None
        rec[f"draft_{arm}_answer"] = answer
        rec[f"draft_{arm}_status"] = "ok" if answer else "failed"
        drafts[arm] = {"result": r, "check": chk, "answer": answer}
    t_ok = drafts["T"]["check"] and drafts["T"]["check"]["ok"]
    if not t_ok:
        rec["verify"] = None
        rec["final_status"] = "failed"
        rec["final_answer"] = None
        rec["fallback_reason"] = None
        return rec
    t_clean = drafts["T"]["check"]["clean"]
    vprompt = verify_prompt(topic, t_clean, item["evidence"])
    vresult = send("verify", vprompt, VERIFY_CAP, VERIFY_THINK)
    parsed = parse_edit_response(vresult.get("text") or "") if not vresult.get("error") else {
        "ok": False, "error": f"call_error:{vresult['error']}"}
    outcome = run_verify(t_clean, task, topic, parsed)
    rec["verify"] = {**version("verify", vresult), "parse_ok": parsed["ok"], "parse_error": parsed.get("error"),
                     "edits_proposed": len(parsed["edits"]) if parsed["ok"] else 0,
                     "edits_accepted": len(outcome["accepted"]), "edits_rejected": outcome["rejected"],
                     "notes": parsed.get("notes") if parsed["ok"] else None, "outcome_status": outcome["status"],
                     "outcome_reason": outcome["reason"]}
    if outcome["status"] == "patched":
        rec["final_status"] = "patched"
        rec["final_answer"] = ec.render_answer(topic, outcome["patched_text"])
        rec["fallback_reason"] = None
    else:
        rec["final_status"] = "fallback"
        rec["final_answer"] = drafts["T"]["answer"]
        rec["fallback_reason"] = outcome["reason"]
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
    # The ledger enforces THIS run's actual plan (18 calls / 270,336 tokens): the deferred 19th
    # call / 20,480 tokens (the VALIDATION diagnostic) is recorded only as the declared ceiling
    # below, never added to the hard stop, so nothing can accidentally spend budget reserved for a
    # call this run will never attempt.
    env = {"max_calls": THIS_RUN_MAX_CALLS, "max_tokens": THIS_RUN_MAX_TOKENS, "max_families": 1,
           "wall_seconds": round(deadline - now), "per_call_max_s": 420, "retries": 0, "smokes": 0,
           "prior_calls": 0, "prior_tokens": 0}
    ledger = {"revision": REVISION, "wave_id": run_dir.name, "envelope": env, "families": [], "arms": ARMS,
              "verify_cap": VERIFY_CAP, "declared_ceiling": {"max_calls": MAX_CALLS, "max_tokens": MAX_TOKENS},
              "bundle_sha256": bundle_sha, "template_sha256": template_sha256(),
              "model": MODEL, "model_digest": MODEL_DIGEST, "num_ctx": NUM_CTX, "temperature": None,
              "base_url": args.base_url, "declared_start_utc": args.declared_start_utc, "wave_start": now,
              "deadline": deadline, "wave_start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
              "deadline_iso": args.deadline_utc, "entries": [], "created": now,
              "pins": {f: sha256_file(HERE / f) for f in PINNED_FILES},
              "validation_diagnostic": "deferred: no frozen VALIDATION-split essay item found locally",
              "rate": "3.28 USD/h UNVERIFIED planning proxy (60-min estimate 3.28 USD, not a bill)"}
    wr.write_json_atomic(run_dir / "ledger.json", ledger)
    print(json.dumps({k: ledger[k] for k in ("envelope", "declared_ceiling", "bundle_sha256", "template_sha256",
                                             "pins", "wave_start_iso", "deadline_iso", "validation_diagnostic")},
                     indent=1))
    return 0


def draft_order(index: int) -> list[str]:
    return ["T", "N"] if index % 2 == 0 else ["N", "T"]


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
    calls, tokens = len(ledger["entries"]), sum(e["cap"] for e in ledger["entries"])
    left_s = ledger["deadline"] - time.time()
    host = tr.guard_host(args.base_url)
    problems += host["problems"]
    if left_s < 60:
        problems.append("deadline")
    plan = []
    for n, i in enumerate(bundle["items"]):
        plan += [(i["item"], arm) for arm in draft_order(n)] + [(i["item"], "verify")]
    report = {"calls_used": calls, "tokens_reserved": tokens, "seconds_left": round(left_s), "host": host,
              "problems": problems, "plan": plan}
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
                "started": time.time(), "order": plan}
    wr.write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    stop_event = threading.Event()
    wr.start_watchdog(wave, stop_event)
    stop_reason = None
    try:
        for n, item in enumerate(bundle["items"]):
            order = draft_order(n)

            def send(stage, prompt, cap, think, _id=item["item"]):
                fits, bound = tr.prompt_fits(prompt, cap)
                if not fits:
                    return {"error": f"context_guard_unsent:{bound}+{cap}>{NUM_CTX}", "unsent": True, "text": ""}
                if wave.seconds_left(wave.load()) < MIN_START_S_BY_STAGE.get(stage, 240):
                    raise wr.StopWave("deadline")
                entry, timeout = wave.reserve(args.batch, "edit", _id, stage, cap, prompt)
                backend = tr.think_backend(args.base_url, MODEL, NUM_CTX, think)
                started = time.time()
                result, overran = wr.call_with_timeout(backend, prompt, cap, timeout)
                elapsed = round(time.time() - started, 2)
                ctx = None
                if not overran and result.get("error") not in wr.TRANSPORT_ERRORS:
                    try:
                        ctx = tr.check_loaded_context(args.base_url)
                    except Exception as exc:  # noqa: BLE001 - settle + raw first, stop via ctx mismatch
                        ctx = f"ps_error:{type(exc).__name__}"
                wave.settle(entry["seq"], "error" if result.get("error") else "ok", elapsed_s=elapsed,
                            error=result.get("error"), eval_count=result.get("eval_count"),
                            prompt_eval_count=result.get("prompt_eval_count"), done_reason=result.get("done_reason"),
                            thinking_chars=result.get("thinking_chars"), content_chars=result.get("content_chars"),
                            think=think, loaded_context=ctx, prompt_bound_tokens=bound,
                            thinking_absent_when_on=result.get("thinking_absent_when_on"))
                wr.append_jsonl(batch_dir / "raw.jsonl", {"item": _id, "stage": stage, "cap": cap, "prompt": prompt,
                                                          **result, "elapsed_s": elapsed, "loaded_context": ctx})
                if overran:
                    raise wr.StopWave("call_overran")
                if result.get("error") in wr.TRANSPORT_ERRORS or str(result.get("error")).startswith(("http_", "exception:")):
                    raise wr.StopWave(f"transport_error:{result['error']}")
                if result.get("thinking_absent_when_on"):
                    raise wr.StopWave("thinking_absent_when_on")
                if ctx != NUM_CTX:
                    raise wr.StopWave(f"loaded_context:{ctx}")
                return result

            rec = {"draft_order": order}
            try:
                run_item(send, item, rec)
            except wr.StopWave as exc:
                stop_reason = str(exc)
                rec.setdefault("final_status", "stopped")
                rec.setdefault("final_answer", None)
                rec["stop_reason"] = stop_reason
            wr.append_jsonl(batch_dir / "records.jsonl", rec)
            for arm in ("T", "N"):
                wr.append_jsonl(batch_dir / "answers.jsonl", {
                    "id": f"{item['item']}__{arm}-draft", "item": item["item"], "family": f"{arm}-draft",
                    "topic": item["topic"], "answer": rec.get(f"draft_{arm}_answer"), "batch": args.batch,
                    "error_type": None if rec.get(f"draft_{arm}_answer") else rec.get("stop_reason", "failed")})
            wr.append_jsonl(batch_dir / "answers.jsonl", {
                "id": f"{item['item']}__T-patched", "item": item["item"], "family": "T-patched",
                "topic": item["topic"], "answer": rec.get("final_answer"), "final_status": rec.get("final_status"),
                "batch": args.batch,
                "error_type": None if rec.get("final_answer") else rec.get("stop_reason", "failed")})
            if stop_reason:
                break
    finally:
        stop_event.set()
        lock.unlink()
    manifest.update(status="stopped" if stop_reason else "complete", stop_reason=stop_reason, finished=time.time())
    wr.write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    ledger = wave.load()
    calls, tokens = len(ledger["entries"]), sum(e["cap"] for e in ledger["entries"])
    print(json.dumps({"batch": args.batch, "status": manifest["status"], "stop_reason": stop_reason,
                      "ledger_calls": calls, "ledger_tokens": tokens}, indent=1))
    return 0 if not stop_reason else 1


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
    p.set_defaults(func=lambda a: print(json.dumps(tr.guard_host(a.base_url), indent=1)) or 0)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
