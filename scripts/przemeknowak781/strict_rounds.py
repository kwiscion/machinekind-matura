"""Strict dual-lens verification rounds (rubric prompts/verify_strict_v2.md).

extract JOURNAL PREFIX       workflow journal -> agentsLog/przemeknowak781/strict/PREFIX_{S,Q,repairs}.jsonl
apply RECORDS PREFIX [--extra FILES...]
                             records passing both lenses -> cache/strict/PREFIX_accepted.jsonl;
                             repaired records (and --extra records) that pass validate.py
                             -> cache/strict/PREFIX_candidates.jsonl
batch RECORDS TAG [--n 12]   judge payloads -> cache/strict/sbatch-TAG-NN.jsonl
finalize ACCEPTED...         -> data/przemeknowak781/train_strict.jsonl + summary

Run from scripts/przemeknowak781.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from validate import check, load_context, load_jsonl

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/przemeknowak781"
STRICT = BASE / "cache/strict"
LOG = ROOT / "agentsLog/przemeknowak781/strict"
KINDS = {"judge-S": "S", "judge-Q": "Q", "repair": "repairs"}
REVIEWER = "claude-opus-5-5 dual-lens (S evidence support, Q exam quality), rubric verify_strict_v2"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def extract(args):
    rows = load_jsonl(args.journal)
    label = {r["key"]: r["label"] for r in rows if r.get("type") == "started"}
    out = {k: {} for k in KINDS.values()}
    for r in rows:
        if r.get("type") != "result" or not isinstance(r.get("result"), dict):
            continue
        kind = KINDS.get(label[r["key"]].split(" ")[0])
        if kind:
            items = r["result"].get("verdicts") or r["result"].get("items") or []
            out[kind].update({v["id"]: v for v in items})
    for kind, d in out.items():
        write_jsonl(LOG / f"{args.prefix}_{kind}.jsonl", [d[k] for k in sorted(d)])
    print({k: len(v) for k, v in out.items()})


def apply(args):
    sources, texts = load_context(BASE / "sources.jsonl")
    S = {v["id"]: v for v in load_jsonl(LOG / f"{args.prefix}_S.jsonl")}
    Q = {v["id"]: v for v in load_jsonl(LOG / f"{args.prefix}_Q.jsonl")}
    rep_path = LOG / f"{args.prefix}_repairs.jsonl"
    R = {v["id"]: v for v in load_jsonl(rep_path)} if rep_path.exists() else {}
    accepted, candidates, counts = [], [], Counter()
    for ex in load_jsonl(args.records):
        s, q = S.get(ex["id"]), Q.get(ex["id"])
        if s and q and s["pass"] and q["pass"]:
            ex["audit"] = {"reviewer": REVIEWER, "status": "verified", "notes": f"{args.prefix}: passed both lenses"}
            accepted.append(ex)
            counts["accepted"] += 1
            continue
        r = R.get(ex["id"])
        if not r or r.get("action") != "repair" or not r.get("prompt") or not r.get("answer"):
            counts["dropped_or_unrepaired"] += 1
            continue
        ex["prompt"], ex["answer"] = r["prompt"], r["answer"]
        ex["generator"]["prompt_revision"] += "+repair_v2"
        if check(ex, sources, texts):
            counts["repair_failed_gate"] += 1
            continue
        candidates.append(ex)
        counts["repaired_candidates"] += 1
    for path in args.extra:
        for ex in load_jsonl(path):
            if check(ex, sources, texts):
                counts["extra_failed_gate"] += 1
            else:
                candidates.append(ex)
                counts["extra_candidates"] += 1
    write_jsonl(STRICT / f"{args.prefix}_accepted.jsonl", accepted)
    write_jsonl(STRICT / f"{args.prefix}_candidates.jsonl", candidates)
    print(dict(counts))


def batch(args):
    titles = {s["source_id"]: s["title"] for s in load_jsonl(BASE / "sources.jsonl")}
    rows = load_jsonl(args.records)
    for b in range(args.n):
        write_jsonl(STRICT / f"sbatch-{args.tag}-{b + 1:02d}.jsonl", [
            {"id": r["id"], "task_type": r["task_type"], "source_titles": [titles[s] for s in r["source_ids"]],
             "era": r.get("era", ""), "prompt": r["prompt"], "answer": r["answer"],
             "evidence": [{"locator": e["locator"], "claim": e["claim"]} for e in r["evidence"]]}
            for r in rows[b :: args.n]])
    print(f"{len(rows)} records in {args.n} batches")


def finalize(args):
    rows, seen = [], set()
    for path in args.accepted:
        for ex in load_jsonl(path):
            if ex["id"] not in seen:
                seen.add(ex["id"])
                rows.append(ex)
    write_jsonl(BASE / "train_strict.jsonl", rows)
    summary = {"verified_strict": len(rows),
               "by_era": dict(Counter(r.get("era") for r in rows)),
               "by_task_type": dict(Counter(r["task_type"] for r in rows)),
               "by_round": dict(Counter(r["audit"]["notes"].split(":")[0] for r in rows)),
               "sources_covered": len({s for r in rows for s in r["source_ids"]})}
    (STRICT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("journal")
    e.add_argument("prefix")
    a = sub.add_parser("apply")
    a.add_argument("records")
    a.add_argument("prefix")
    a.add_argument("--extra", nargs="*", default=[])
    b = sub.add_parser("batch")
    b.add_argument("records")
    b.add_argument("tag")
    b.add_argument("--n", type=int, default=12)
    f = sub.add_parser("finalize")
    f.add_argument("accepted", nargs="+")
    args = ap.parse_args()
    {"extract": extract, "apply": apply, "batch": batch, "finalize": finalize}[args.cmd](args)


if __name__ == "__main__":
    main()
