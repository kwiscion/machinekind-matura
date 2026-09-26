"""Public export + blind grading packets for the #80 constrained claim-edit wave. No model calls.

Three families per item (not the 2-arm/2-stage shape of the K-think wave): N-draft, T-draft,
T-patched (the T-draft's FINAL answer, whether actually patched or fallback-to-unchanged-T-draft;
`final_status` records which). Equal denominators: 6 topics / 90 points for each family; a failed
final is zero in its family's denominator, never invented.

Grading reuses the already-reviewed rater-keyed aggregation core from essay_think_export.py
(load_grades/validate_coverage/score_row/cmd_adjudicate): a cell key is "item|family|score" so
that generic machinery applies unchanged (rater id from filename only, missing/duplicate ratings
hard-error, disagreement >TOTAL_DISAGREEMENT_MAX is flagged needs_adjudication and never
auto-resolved by picking a score, a within-tolerance gap resolves to the mean).

  python scripts/Pewciu6/essay_edit_export.py export --run-dir R --batch t1 --out agentsLog/Pewciu6/essay/results/edit-...
  python scripts/Pewciu6/essay_edit_export.py packet --run-dir R --batch t1 --out R/grading/g1 --seed 80
  python scripts/Pewciu6/essay_edit_export.py aggregate --grading R/grading/g1
  python scripts/Pewciu6/essay_edit_export.py adjudicate --grading R/grading/g1 --resolutions R/grading/g1/resolutions.json
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_think_export as te  # noqa: E402  (reuse the reviewed rater-keyed aggregation core)
import essay_wave_run as wr  # noqa: E402

FAMILIES = ("N-draft", "T-draft", "T-patched")
ASPECT_LEVELS = (0, 1, 3, 4)
COHERENCE_MAX = 3
POINTS_PER_TOPIC = 15  # 3 aspects x 4 + coherence(0-3), per the published grading-calibration.md


def score_row_v2(gr: dict) -> dict:
    """Score a grader row under the published calibration protocol (3 aspects 0/1/3/4 + coherence
    0-3 - error_deduction, /15). The total is ALWAYS recomputed from the components here, never
    trusted from a model-supplied "total" field, so grader arithmetic mistakes can't silently
    change the score."""
    aspects = gr.get("aspects")
    if not isinstance(aspects, list) or len(aspects) != 3:
        raise ValueError("grade row must have exactly 3 aspects")
    levels = []
    for a in aspects:
        level = a.get("level")
        if level not in ASPECT_LEVELS:
            raise ValueError(f"aspect level must be one of {ASPECT_LEVELS}, got {level!r}")
        levels.append(level)
    coherence = gr.get("coherence")
    if not isinstance(coherence, int) or not 0 <= coherence <= COHERENCE_MAX:
        raise ValueError(f"coherence must be an int in 0..{COHERENCE_MAX}, got {coherence!r}")
    deduction = gr.get("error_deduction", 0)
    if not isinstance(deduction, int) or deduction < 0:
        raise ValueError(f"error_deduction must be a non-negative int, got {deduction!r}")
    total = max(0, min(POINTS_PER_TOPIC, sum(levels) + coherence - deduction))
    return {"total": total, "aspect_levels": levels, "coherence": coherence, "error_deduction": deduction,
            "factual_errors": len(gr.get("factual_errors") or [])}


def load(run_dir: Path, batch: str):
    b = run_dir / "batches" / batch
    return (json.loads((run_dir / "bundle.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "ledger.json").read_text(encoding="utf-8")),
            wr.read_jsonl(b / "records.jsonl"), json.loads((b / "batch_manifest.json").read_text(encoding="utf-8")))


def public_verify(v: dict | None) -> dict | None:
    if v is None:
        return None
    return {"error": v.get("error"), "eval_count": v.get("eval_count"), "prompt_eval_count": v.get("prompt_eval_count"),
            "done_reason": v.get("done_reason"), "thinking_chars": v.get("thinking_chars"),
            "content_chars": v.get("content_chars"), "raw": v.get("raw"), "parse_ok": v.get("parse_ok"),
            "parse_error": v.get("parse_error"), "edits_proposed": v.get("edits_proposed"),
            "edits_accepted": v.get("edits_accepted"), "edits_rejected": v.get("edits_rejected"),
            "notes": v.get("notes"), "outcome_status": v.get("outcome_status"), "outcome_reason": v.get("outcome_reason")}


def cmd_export(args) -> int:
    run_dir, out = Path(args.run_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    bundle, ledger, records, manifest = load(run_dir, args.batch)
    with open(out / "answers.jsonl", "w", encoding="utf-8") as h:
        for r in records:
            row = {"item": r["item"], "topic_id": r.get("topic_id"), "draft_T_status": r.get("draft_T_status"),
                   "draft_N_status": r.get("draft_N_status"), "final_status": r.get("final_status"),
                   "fallback_reason": r.get("fallback_reason"),
                   "draft_T_answer": r.get("draft_T_answer"), "draft_N_answer": r.get("draft_N_answer"),
                   "final_answer": r.get("final_answer"), "draft_order": r.get("draft_order"),
                   "verify": public_verify(r.get("verify")), "stop_reason": r.get("stop_reason")}
            h.write(json.dumps(row, ensure_ascii=False) + "\n")
    pub_ledger = {k: v for k, v in ledger.items() if k not in ("base_url",)}
    (out / "ledger.json").write_text(json.dumps(pub_ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    items = [{k: v for k, v in i.items() if k not in ("evidence", "draft_prompt")} |
             {"evidence": [{k: e[k] for k in ("chunk_id", "source_id", "title", "locator", "score")}
                           for e in i["evidence"]]} for i in bundle["items"]]
    man = {k: v for k, v in bundle.items() if k != "items"} | {"items": items, "batch": manifest}
    (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {"items": len(records), "patched": sum(1 for r in records if r.get("final_status") == "patched"),
              "fallback": sum(1 for r in records if r.get("final_status") == "fallback"),
              "failed": sum(1 for r in records if r.get("final_status") not in ("patched", "fallback")),
              "edits_accepted_total": sum((r.get("verify") or {}).get("edits_accepted", 0) or 0 for r in records)}
    print(json.dumps({"out": str(out), "records": len(records), "counts": counts}, indent=1))
    return 0


def cmd_packet(args) -> int:
    run_dir, out = Path(args.run_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    bundle, _l, records, _m = load(run_dir, args.batch)
    items = {i["item"]: i for i in bundle["items"]}
    recs = {r["item"]: r for r in records}
    field = {"N-draft": "draft_N_answer", "T-draft": "draft_T_answer", "T-patched": "final_answer"}
    slots, missing = [], []
    for item in items:
        r = recs.get(item) or {}
        for family in FAMILIES:
            ans = r.get(field[family])
            entry = {"item": item, "family": family}
            if ans:
                slots.append({**entry, "answer": ans})
            else:
                reason = (r.get("fallback_reason") if family == "T-patched" else None) or r.get("stop_reason") or "failed/unsent"
                missing.append({**entry, "reason": reason})
    random.Random(args.seed).shuffle(slots)
    key, packet = [], []
    for n, s in enumerate(slots, 1):
        code = f"E{n:02d}"
        key.append({"code": code, "item": s["item"], "family": s["family"]})
        packet.append({"code": code, "task": items[s["item"]]["full_task"], "topic_written": items[s["item"]]["topic"],
                       "essay": s["answer"]})
    (out / "key.private.json").write_text(json.dumps({"key": key, "not_gradable": missing}, ensure_ascii=False,
                                                     indent=1), encoding="utf-8")
    with open(out / "packet.jsonl", "w", encoding="utf-8") as h:
        for row in packet:
            h.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"gradable": len(slots), "not_gradable": len(missing),
                      "denominator_per_family": len(items)}, indent=1))
    return 0


def cmd_aggregate(args) -> int:
    g = Path(args.grading)
    key = json.loads((g / "key.private.json").read_text(encoding="utf-8"))
    grades = te.load_grades(g)
    raters = sorted({r for r, _c in grades})
    if not raters:
        raise ValueError(f"{g}: no grades_<rater_id>.json files found")
    gradable_codes = [k["code"] for k in key["key"]]
    te.validate_coverage(grades, gradable_codes, raters)
    multi_rater = len(raters) > 1
    cells = {}
    for k in key["key"]:
        by_rater = {r: score_row_v2(grades[(r, k["code"])]) for r in raters}
        cell = {"graded": True, "code": k["code"], "raters": raters, "ratings": by_rater}
        if not multi_rater:
            cell.update(by_rater[raters[0]])
            cell["needs_adjudication"] = False
        else:
            totals = [by_rater[r]["total"] for r in raters]
            # Per the calibration protocol: adjudicate on >2 total points OR any 1-vs-3 aspect
            # disagreement, even when the totals happen to land close together.
            total_gap = (max(totals) - min(totals)) > te.TOTAL_DISAGREEMENT_MAX
            aspect_levels = [by_rater[r]["aspect_levels"] for r in raters]
            aspect_1v3 = any({levels[i] for levels in aspect_levels} == {1, 3}
                             for i in range(len(aspect_levels[0])))
            cell["needs_adjudication"] = total_gap or aspect_1v3
            cell["disagreement_reason"] = (("total_gap" if total_gap else "") +
                                           ("+aspect_1v3" if aspect_1v3 else "")) or None
            cell["total"] = round(statistics.mean(totals), 2) if not cell["needs_adjudication"] else None
        cells[f"{k['item']}|{k['family']}|score"] = cell
    for k in key["not_gradable"]:
        cells[f"{k['item']}|{k['family']}|score"] = {"total": 0, "graded": False, "reason": k["reason"],
                                                     "raters": raters, "ratings": {}, "needs_adjudication": False}
    # 6 topics, 15 points max each (per the authorization's "6 topics / 90 points" denominator).
    # A cell that is not graded (missing final/draft) or still needs_adjudication contributes 0 to
    # the resolved sum, exactly like a failed final -- never invented, never estimated.
    N_TOPICS = 6
    summary = {}
    for family in FAMILIES:
        cs = [cells[c] for c in cells if c.split("|")[1] == family]
        graded = [c for c in cs if c["graded"]]
        needs = sum(1 for c in cs if c.get("needs_adjudication"))
        resolved = [c["total"] for c in cs if c["total"] is not None]
        summary[family] = {"n": len(cs), "graded": len(graded), "needs_adjudication": needs,
                           "resolved_n": len(resolved),
                           "mean_resolved_only": round(sum(resolved) / len(resolved), 2) if resolved else None,
                           "sum_over_denominator": f"{round(sum(resolved), 2)}/{N_TOPICS * POINTS_PER_TOPIC}"}
    result = {"label": "DEVELOPMENT grading (fresh blind Opus agent graders; not promotion evidence)",
              "raters": raters, "families": list(FAMILIES), "summary": summary,
              "note": "successful-edit and fallback counts live in the export step's answers.jsonl, not here",
              "cells": dict(sorted(cells.items()))}
    (g / "aggregate.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("packet")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=80)
    p.set_defaults(func=cmd_packet)
    p = sub.add_parser("aggregate")
    p.add_argument("--grading", required=True)
    p.set_defaults(func=cmd_aggregate)
    p = sub.add_parser("adjudicate")
    p.add_argument("--grading", required=True)
    p.add_argument("--resolutions", required=True)
    p.set_defaults(func=te.cmd_adjudicate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
