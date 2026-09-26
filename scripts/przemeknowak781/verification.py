"""Prepare semantic-verification batches and apply verdicts.

prepare: gate all inputs with validate.py rules, write passed examples to cache/gated.jsonl and
         verifier payloads to cache/verify/vbatch-NN.jsonl.
repair-prep:  write `minor` items with the verifier's issue to cache/verify/rbatch-NN.jsonl.
repair-apply: take cache/verify/repairs-NN.jsonl, re-gate, write cache/repaired.jsonl and vbatch-r-NN.jsonl.
apply:   merge all verdicts (later r-verdicts override) into data/przemeknowak781/train.jsonl.

Usage (run from scripts/przemeknowak781):
  python verification.py prepare EXAMPLES... [--batches 5]
  python verification.py repair-prep [--batches 3]
  python verification.py repair-apply [--batches 2]
  python verification.py apply --reviewer MODEL
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from validate import check, load_context, load_jsonl

BASE = Path(__file__).resolve().parents[2] / "data/przemeknowak781"
CACHE = BASE / "cache"
VERIFY = CACHE / "verify"
STATUS = {"supported": "verified", "minor": "draft", "unsupported": "rejected"}


def prepare(args):
    sources, texts = load_context(BASE / "sources.jsonl")
    existing = load_jsonl(CACHE / "gated.jsonl") if args.append else []
    seen_ids = {ex["id"] for ex in existing}
    seen_prompts = {" ".join(ex["prompt"].lower().split()) for ex in existing}
    gated = []
    for ex in (ex for p in args.examples for ex in load_jsonl(p)):
        key = " ".join(ex.get("prompt", "").lower().split())
        if ex.get("id") in seen_ids or key in seen_prompts or check(ex, sources, texts):
            continue
        seen_prompts.add(key)
        gated.append(ex)
    VERIFY.mkdir(parents=True, exist_ok=True)
    with open(CACHE / "gated.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for ex in existing + gated:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    prefix = f"vbatch-{args.tag}-" if args.tag else "vbatch-"
    for b in range(args.batches):
        with open(VERIFY / f"{prefix}{b + 1:02d}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for ex in gated[b :: args.batches]:
                payload = {"id": ex["id"], "task_type": ex["task_type"], "prompt": ex["prompt"],
                           "answer": ex["answer"], "evidence": [e["claim"] for e in ex["evidence"]]}
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(f"gated={len(gated)} batches={args.batches}")


def load_verdicts():
    verdicts = {}
    for path in sorted(VERIFY.glob("verdicts-*.jsonl")):
        for v in load_jsonl(path):
            verdicts[v["id"]] = v
    return verdicts


def repair_prep(args):
    verdicts = load_verdicts()
    drafts = [ex for ex in load_jsonl(CACHE / "gated.jsonl")
              if verdicts.get(ex["id"], {}).get("verdict") == "minor"]
    for b in range(args.batches):
        with open(VERIFY / f"rbatch-{b + 1:02d}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for ex in drafts[b :: args.batches]:
                payload = {"id": ex["id"], "task_type": ex["task_type"], "prompt": ex["prompt"],
                           "answer": ex["answer"], "evidence": [e["claim"] for e in ex["evidence"]],
                           "verifier_issue": verdicts[ex["id"]].get("issues", "")}
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(f"drafts={len(drafts)} batches={args.batches}")


def repair_apply(args):
    sources, texts = load_context(BASE / "sources.jsonl")
    repairs = {r["id"]: r for p in sorted(VERIFY.glob("repairs-*.jsonl")) for r in load_jsonl(p)}
    repaired, dropped, failed = [], 0, 0
    for ex in load_jsonl(CACHE / "gated.jsonl"):
        r = repairs.get(ex["id"])
        if not r:
            continue
        if r.get("drop") or not r.get("answer"):
            dropped += 1
            continue
        ex["answer"] = r["answer"]
        ex["generator"]["prompt_revision"] += "+repair_v1"
        if check(ex, sources, texts):
            failed += 1
            continue
        repaired.append(ex)
    with open(CACHE / "repaired.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for ex in repaired:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    for b in range(args.batches):
        with open(VERIFY / f"vbatch-r-{b + 1:02d}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for ex in repaired[b :: args.batches]:
                payload = {"id": ex["id"], "task_type": ex["task_type"], "prompt": ex["prompt"],
                           "answer": ex["answer"], "evidence": [e["claim"] for e in ex["evidence"]]}
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(f"repaired={len(repaired)} dropped={dropped} failed_gate={failed}")


def apply(args):
    verdicts = load_verdicts()
    gated = load_jsonl(CACHE / "gated.jsonl")
    if (CACHE / "repaired.jsonl").exists():
        fixed = {ex["id"]: ex for ex in load_jsonl(CACHE / "repaired.jsonl")}
        gated = [fixed.get(ex["id"], ex) for ex in gated]
    counts, by_era, by_task = Counter(), Counter(), Counter()
    with open(BASE / "train.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for ex in gated:
            v = verdicts.get(ex["id"])
            status = STATUS.get(v["verdict"], "pending") if v else "pending"
            counts[status] += 1
            if status == "rejected":
                continue
            if status == "verified":
                by_era[ex.get("era", "unknown")] += 1
                by_task[ex["task_type"]] += 1
            ex["audit"] = {"reviewer": args.reviewer, "status": status,
                           "notes": (v or {}).get("issues", "") or "rubric verify_v1"}
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    summary = {"gated": len(gated), "status_counts": dict(counts),
               "verified_by_era": dict(by_era), "verified_by_task_type": dict(by_task),
               "missing_verdicts": sorted(set(e["id"] for e in gated) - set(verdicts))}
    (CACHE / "verification_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("examples", nargs="+")
    p.add_argument("--batches", type=int, default=5)
    p.add_argument("--append", action="store_true", help="keep existing gated.jsonl, add only new items")
    p.add_argument("--tag", default="", help="name verification batches vbatch-<tag>-NN")
    a = sub.add_parser("apply")
    a.add_argument("--reviewer", required=True)
    for name in ("repair-prep", "repair-apply"):
        sub.add_parser(name).add_argument("--batches", type=int, default=3)
    args = ap.parse_args()
    {"prepare": prepare, "apply": apply, "repair-prep": repair_prep,
     "repair-apply": repair_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
