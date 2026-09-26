"""Public export + blind grading packets for the #80 paired native-thinking wave. No model calls.

  export     private run dir -> public results dir: answers (draft/final per arm, raw content,
             pre- and post-cleanup text), per-call ledger (native eval_count as-is), frozen manifest
             (evidence as chunk ids + hashes only). message.thinking is NEVER exported (only its
             character count); prompts stay private (hashes are public).
  packet     24 slots (6 items x {T,N} x {draft,final}) -> shuffled blind packets; graders see only
             the task, the topic number and the essay text. Failed slots are listed in the private
             key and scored 0 in the denominator.
  aggregate  grades + key -> paired per-topic table, draft vs final, per arm (all 6 in denominator).
             Grade files are named grades_<rater_id>.json; rater_id is taken from the filename, NEVER
             from a field inside the file, so ratings can never be silently misattributed. Each rater
             must rate every gradable code exactly once (missing or duplicate -> hard error, no silent
             drop). One rater file behaves exactly as before (single-rater legacy mode). Two or more
             rater files keep every rater's score separately per cell (never overwritten) and flag any
             cell whose raters disagree by more than TOTAL_DISAGREEMENT_MAX points for adjudication;
             nothing is auto-resolved by averaging or by picking the higher score.
  adjudicate resolved totals (one per flagged cell) -> aggregate_adjudicated.json (the original
             aggregate.json, and every rater's original score, is left untouched for audit)

  python scripts/Pewciu6/essay_think_export.py export --run-dir R --batch t1 --out agentsLog/Pewciu6/essay/results/think-...
  python scripts/Pewciu6/essay_think_export.py packet --run-dir R --batch t1 --out R/grading/g1 --seed 80 --parts 2
  python scripts/Pewciu6/essay_think_export.py aggregate --grading R/grading/g1
  python scripts/Pewciu6/essay_think_export.py adjudicate --grading R/grading/g1 --resolutions R/grading/g1/resolutions.json
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_contract as ec  # noqa: E402
import essay_wave_run as wr  # noqa: E402

SLOTS = [(arm, stage) for arm in ("T", "N") for stage in ("draft", "final")]


def load(run_dir: Path, batch: str):
    b = run_dir / "batches" / batch
    return (json.loads((run_dir / "bundle.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "ledger.json").read_text(encoding="utf-8")),
            wr.read_jsonl(b / "records.jsonl"), json.loads((b / "batch_manifest.json").read_text(encoding="utf-8")))


def public_version(v: dict | None) -> dict | None:
    if v is None:
        return None
    chk = v.get("check") or {}
    val = chk.get("validation") or {}
    return {"stage": v["stage"], "error": v.get("error"), "eval_count": v.get("eval_count"),
            "prompt_eval_count": v.get("prompt_eval_count"), "done_reason": v.get("done_reason"),
            "thinking_chars": v.get("thinking_chars"), "content_chars": v.get("content_chars"),
            "raw_content": v.get("raw"), "pre_cleanup_body": v.get("pre_cleanup_body"),
            "post_cleanup_text": v.get("post_cleanup_text"), "review_note_uwagi": (v.get("extras") or {}).get("uwagi"),
            "contract_ok": chk.get("ok"), "triggers": chk.get("triggers"), "advisory": val.get("advisory"),
            "cleanup_ops": chk.get("ops"), "words": val.get("words")}


def cmd_export(args) -> int:
    run_dir, out = Path(args.run_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    bundle, ledger, records, manifest = load(run_dir, args.batch)
    with open(out / "answers.jsonl", "w", encoding="utf-8") as h:
        for r in records:
            row = {"item": r["item"], "arm": r["arm"], "arm_name": wr_arm(r["arm"]), "topic_id": r.get("topic_id"),
                   "status": r.get("status"), "stop_reason": r.get("stop_reason"),
                   "draft_answer": r.get("draft_answer"), "final_answer": r.get("final_answer"),
                   "draft": public_version(r.get("draft")), "review": public_version(r.get("review")),
                   "review_input": r.get("review_input"), "unsent": r.get("unsent")}
            h.write(json.dumps(row, ensure_ascii=False) + "\n")
    pub_ledger = {k: v for k, v in ledger.items() if k not in ("base_url",)}
    (out / "ledger.json").write_text(json.dumps(pub_ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    items = [{k: v for k, v in i.items() if k not in ("evidence", "draft_prompt")} |
             {"evidence": [{k: e[k] for k in ("chunk_id", "source_id", "title", "locator", "score")}
                           for e in i["evidence"]]} for i in bundle["items"]]
    man = {k: v for k, v in bundle.items() if k != "items"} | {"items": items, "batch": manifest}
    (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(out), "records": len(records)}, indent=1))
    return 0


def wr_arm(arm: str) -> str:
    return {"T": "K-think", "N": "K-nothink"}[arm]


def cmd_packet(args) -> int:
    run_dir, out = Path(args.run_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    bundle, _l, records, _m = load(run_dir, args.batch)
    items = {i["item"]: i for i in bundle["items"]}
    recs = {(r["item"], r["arm"]): r for r in records}
    slots, missing = [], []
    for item in items:
        for arm, stage in SLOTS:
            r = recs.get((item, arm)) or {}
            ans = r.get(f"{stage}_answer")
            entry = {"item": item, "arm": arm, "stage": stage}
            (slots if ans else missing).append({**entry, "answer": ans} if ans else
                                               {**entry, "reason": r.get("stop_reason") or "failed/unsent"})
    random.Random(args.seed).shuffle(slots)
    key, packets = [], [[] for _ in range(args.parts)]
    for n, s in enumerate(slots, 1):
        code = f"E{n:02d}"
        key.append({"code": code, "item": s["item"], "arm": s["arm"], "stage": s["stage"]})
        packets[(n - 1) % args.parts].append({"code": code, "task": items[s["item"]]["full_task"],
                                              "topic_written": items[s["item"]]["topic"], "essay": s["answer"],
                                              "body_words": ec.words(s["answer"].split("\n", 2)[-1])})
    (out / "key.private.json").write_text(json.dumps({"key": key, "not_gradable": missing}, ensure_ascii=False,
                                                     indent=1), encoding="utf-8")
    for p, rows in enumerate(packets, 1):
        with open(out / f"packet_part{p}.jsonl", "w", encoding="utf-8") as h:
            for row in rows:
                h.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"gradable": len(slots), "not_gradable": len(missing), "parts": args.parts}, indent=1))
    return 0


TOTAL_DISAGREEMENT_MAX = 2  # a gap larger than this (points, on the A+B total) needs adjudication


def rater_id_from_path(path: Path) -> str:
    stem = path.stem
    prefix = "grades_"
    if not stem.startswith(prefix) or len(stem) <= len(prefix):
        raise ValueError(f"{path}: grade files must be named grades_<rater_id>.json")
    return stem[len(prefix):]


def load_grades(g: Path) -> dict[tuple[str, str], dict]:
    """{(rater_id, code): row}. rater_id comes ONLY from the filename (never a field inside the
    file), so a rater can never be misattributed. A rater rating the same code twice is an error,
    never a silent overwrite (that was the #80 bug: grades[row["code"]]=row lost every rater but
    the last one written for a shared code)."""
    grades: dict[tuple[str, str], dict] = {}
    for path in sorted(g.glob("grades_*.json")):
        rater_id = rater_id_from_path(path)
        for row in json.loads(path.read_text(encoding="utf-8")):
            key = (rater_id, row["code"])
            if key in grades:
                raise ValueError(f"{path}: rater {rater_id} rated {row['code']} more than once")
            grades[key] = row
    return grades


def validate_coverage(grades: dict[tuple[str, str], dict], gradable_codes: list[str], raters: list[str]) -> None:
    for rater_id in raters:
        missing = [c for c in gradable_codes if (rater_id, c) not in grades]
        if missing:
            raise ValueError(f"rater {rater_id} is missing ratings for {missing}")


def score_row(gr: dict) -> dict:
    return {"total": gr["A"] + gr["B"], "A": gr["A"], "B": gr["B"], "format": gr.get("format_score"),
            "factual_errors": len(gr.get("factual_errors", [])), "claims": len(gr.get("claims", [])),
            "claims_incorrect": sum(1 for c in gr.get("claims", []) if str(c.get("verdict", "")).startswith("incorrect")),
            "claims_unverifiable": sum(1 for c in gr.get("claims", [])
                                       if str(c.get("verdict", "")).startswith("unverif"))}


def cmd_aggregate(args) -> int:
    g = Path(args.grading)
    key = json.loads((g / "key.private.json").read_text(encoding="utf-8"))
    grades = load_grades(g)
    raters = sorted({r for r, _c in grades})
    if not raters:
        raise ValueError(f"{g}: no grades_<rater_id>.json files found")
    gradable_codes = [k["code"] for k in key["key"]]
    validate_coverage(grades, gradable_codes, raters)
    cells = {}
    for k in key["key"]:
        by_rater = {r: score_row(grades[(r, k["code"])]) for r in raters}
        cell = {"graded": True, "code": k["code"], "raters": raters, "ratings": by_rater}
        if len(raters) == 1:
            cell.update(by_rater[raters[0]])  # legacy single-rater shape: total/A/B/... at the top level
            cell["needs_adjudication"] = False
        else:
            totals = [by_rater[r]["total"] for r in raters]
            cell["needs_adjudication"] = (max(totals) - min(totals)) > TOTAL_DISAGREEMENT_MAX
            # Within tolerance (identical, or a small gap the lead's threshold already treats as
            # agreement) resolves to the mean, never to either rater's own number specifically, so
            # nothing here ever "picks the favourable score". Only a real disagreement (flagged
            # needs_adjudication) is left as total=None, to be filled in only via cmd_adjudicate.
            cell["total"] = (round(statistics.mean(totals), 2) if not cell["needs_adjudication"] else None)
        cells[(k["item"], k["arm"], k["stage"])] = cell
    for k in key["not_gradable"]:
        cells[(k["item"], k["arm"], k["stage"])] = {"total": 0, "A": 0, "B": 0, "format": 0, "factual_errors": None,
                                                    "graded": False, "reason": k["reason"], "raters": raters,
                                                    "ratings": {}, "needs_adjudication": False}
    items = sorted({c[0] for c in cells})
    multi_rater = len(raters) > 1
    summary = {}
    for arm, stage in SLOTS:
        cs = [cells[(i, arm, stage)] for i in items]
        graded = [c for c in cs if c["graded"]]
        if not multi_rater:
            summary[f"{arm}-{stage}"] = {
                "n": len(cs), "graded": len(graded),
                "mean_total_all_n": round(sum(c["total"] for c in cs) / len(cs), 2),
                "mean_A_all_n": round(sum(c["A"] for c in cs) / len(cs), 2),
                "mean_B_all_n": round(sum(c["B"] for c in cs) / len(cs), 2),
                "mean_format_all_n": round(sum(c["format"] or 0 for c in cs) / len(cs), 2),
                "factual_errors_graded": sum(c["factual_errors"] for c in graded),
                "claims_checked": sum(c["claims"] for c in graded),
                "claims_incorrect": sum(c["claims_incorrect"] for c in graded),
                "claims_unverifiable": sum(c["claims_unverifiable"] for c in graded),
                "median_total_graded": statistics.median(c["total"] for c in graded) if graded else None}
        else:
            # Multi-rater: each rater's mean is kept separate; nothing is auto-resolved by
            # averaging or by picking the higher score, so an unresolved cell (needs_adjudication)
            # is excluded from mean_total_resolved_only until an adjudicate run fills it in.
            per_rater_mean = {}
            for r in raters:
                vals = [c["ratings"][r]["total"] for c in graded if r in c["ratings"]]
                per_rater_mean[r] = round(sum(vals) / len(vals), 2) if vals else None
            resolved = [c["total"] for c in cs if c["total"] is not None]
            summary[f"{arm}-{stage}"] = {
                "n": len(cs), "graded": len(graded), "raters": raters,
                "needs_adjudication": sum(1 for c in cs if c.get("needs_adjudication")),
                "resolved_n": len(resolved),
                "mean_total_resolved_only": round(sum(resolved) / len(resolved), 2) if resolved else None,
                "per_rater_mean_total": per_rater_mean}
    paired = []
    for i in items:
        row = {"item": i}
        for a, s in SLOTS:
            c = cells[(i, a, s)]
            row[f"{a}-{s}"] = c["total"]
            if multi_rater:
                row[f"{a}-{s}_ratings"] = {r: c["ratings"][r]["total"] for r in raters if r in c["ratings"]}
                row[f"{a}-{s}_needs_adjudication"] = c.get("needs_adjudication", False)
            else:
                row[f"{a}-{s}_errors"] = c["factual_errors"]
        paired.append(row)
    result = {"label": "DEVELOPMENT grading (fresh blind Opus agent graders; not promotion evidence)",
              "raters": raters, "summary": summary, "paired": paired,
              "cells": {f"{i}|{a}|{s}": v for (i, a, s), v in sorted(cells.items())}}
    (g / "aggregate.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result["summary"], indent=1))
    print("| item | T-draft | T-final | N-draft | N-final |")
    for p in paired:
        if multi_rater:
            cells_text = " | ".join(f"{p[f'{a}-{s}']} {p[f'{a}-{s}_ratings']}"
                                    + (" [ADJUDICATE]" if p[f"{a}-{s}_needs_adjudication"] else "")
                                    for a, s in SLOTS)
        else:
            cells_text = " | ".join(f"{p[f'{a}-{s}']} ({p[f'{a}-{s}_errors']})" for a, s in SLOTS)
        print(f"| {p['item']} | " + cells_text + " |")
    return 0


def cmd_adjudicate(args) -> int:
    """Resolve flagged (needs_adjudication) cells with an explicit, separately recorded decision.
    Never picks the favourable score automatically: each resolution is an independent judgment
    call given by the caller, not derived from the two disagreeing ratings. aggregate.json (and
    every rater's original score inside it) is left untouched; this writes a new file."""
    g = Path(args.grading)
    agg = json.loads((g / "aggregate.json").read_text(encoding="utf-8"))
    resolutions = json.loads(Path(args.resolutions).read_text(encoding="utf-8"))
    cells = agg["cells"]
    resolved_keys = set()
    for r in resolutions:
        key = f"{r['item']}|{r['arm']}|{r['stage']}"
        if key not in cells:
            raise ValueError(f"resolution names an unknown cell {key}")
        cell = cells[key]
        if not cell.get("needs_adjudication"):
            raise ValueError(f"{key} does not need adjudication; refusing to overwrite an agreed/legacy score")
        if key in resolved_keys:
            raise ValueError(f"{key} has more than one resolution")
        resolved_keys.add(key)
        cell["resolved_total"] = r["resolved_total"]
        cell["resolution_note"] = r.get("note", "")
    still_open = [k for k, c in cells.items() if c.get("needs_adjudication") and "resolved_total" not in c]
    agg["adjudication"] = {"resolved": sorted(resolved_keys), "still_needs_adjudication": sorted(still_open)}
    (g / "aggregate_adjudicated.json").write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(agg["adjudication"], indent=1))
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
    p.add_argument("--parts", type=int, default=2)
    p.set_defaults(func=cmd_packet)
    p = sub.add_parser("aggregate")
    p.add_argument("--grading", required=True)
    p.set_defaults(func=cmd_aggregate)
    p = sub.add_parser("adjudicate")
    p.add_argument("--grading", required=True)
    p.add_argument("--resolutions", required=True)
    p.set_defaults(func=cmd_adjudicate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
