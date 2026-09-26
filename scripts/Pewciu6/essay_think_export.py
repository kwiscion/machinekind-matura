"""Public export + blind grading packets for the #80 paired native-thinking wave. No model calls.

  export     private run dir -> public results dir: answers (draft/final per arm, raw content,
             pre- and post-cleanup text), per-call ledger (native eval_count as-is), frozen manifest
             (evidence as chunk ids + hashes only). message.thinking is NEVER exported (only its
             character count); prompts stay private (hashes are public).
  packet     24 slots (6 items x {T,N} x {draft,final}) -> shuffled blind packets; graders see only
             the task, the topic number and the essay text. Failed slots are listed in the private
             key and scored 0 in the denominator.
  aggregate  grades + key -> paired per-topic table, draft vs final, per arm (all 6 in denominator)

  python scripts/Pewciu6/essay_think_export.py export --run-dir R --batch t1 --out agentsLog/Pewciu6/essay/results/think-...
  python scripts/Pewciu6/essay_think_export.py packet --run-dir R --batch t1 --out R/grading/g1 --seed 80 --parts 2
  python scripts/Pewciu6/essay_think_export.py aggregate --grading R/grading/g1
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


def cmd_aggregate(args) -> int:
    g = Path(args.grading)
    key = json.loads((g / "key.private.json").read_text(encoding="utf-8"))
    grades = {}
    for path in sorted(g.glob("grades_part*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            grades[row["code"]] = row
    cells = {}
    for k in key["key"]:
        gr = grades[k["code"]]
        cells[(k["item"], k["arm"], k["stage"])] = {
            "total": gr["A"] + gr["B"], "A": gr["A"], "B": gr["B"], "format": gr.get("format_score"),
            "factual_errors": len(gr.get("factual_errors", [])), "graded": True, "code": k["code"],
            "claims": len(gr.get("claims", [])),
            "claims_incorrect": sum(1 for c in gr.get("claims", []) if str(c.get("verdict", "")).startswith("incorrect")),
            "claims_unverifiable": sum(1 for c in gr.get("claims", []) if str(c.get("verdict", "")).startswith("unverif"))}
    for k in key["not_gradable"]:
        cells[(k["item"], k["arm"], k["stage"])] = {"total": 0, "A": 0, "B": 0, "format": 0, "factual_errors": None,
                                                    "graded": False, "reason": k["reason"]}
    items = sorted({c[0] for c in cells})
    summary = {}
    for arm, stage in SLOTS:
        cs = [cells[(i, arm, stage)] for i in items]
        graded = [c for c in cs if c["graded"]]
        summary[f"{arm}-{stage}"] = {
            "n": len(cs), "graded": len(graded), "mean_total_all_n": round(sum(c["total"] for c in cs) / len(cs), 2),
            "mean_A_all_n": round(sum(c["A"] for c in cs) / len(cs), 2),
            "mean_B_all_n": round(sum(c["B"] for c in cs) / len(cs), 2),
            "mean_format_all_n": round(sum(c["format"] or 0 for c in cs) / len(cs), 2),
            "factual_errors_graded": sum(c["factual_errors"] for c in graded),
            "claims_checked": sum(c["claims"] for c in graded),
            "claims_incorrect": sum(c["claims_incorrect"] for c in graded),
            "claims_unverifiable": sum(c["claims_unverifiable"] for c in graded),
            "median_total_graded": statistics.median(c["total"] for c in graded) if graded else None}
    paired = [{"item": i, **{f"{a}-{s}": cells[(i, a, s)]["total"] for a, s in SLOTS},
               **{f"{a}-{s}_errors": cells[(i, a, s)]["factual_errors"] for a, s in SLOTS}} for i in items]
    result = {"label": "DEVELOPMENT grading (fresh blind Opus agent graders; not promotion evidence)",
              "summary": summary, "paired": paired,
              "cells": {f"{i}|{a}|{s}": v for (i, a, s), v in sorted(cells.items())}}
    (g / "aggregate.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result["summary"], indent=1))
    print("| item | T-draft | T-final | N-draft | N-final |")
    for p in paired:
        print(f"| {p['item']} | " + " | ".join(f"{p[f'{a}-{s}']} ({p[f'{a}-{s}_errors']})" for a, s in SLOTS) + " |")
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
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
