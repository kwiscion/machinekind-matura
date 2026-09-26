"""Export verified records to chat-format SFT files for LoRA training.

Writes two variants to data/przemeknowak781/sft/:
  closed_book_{train,holdout}.jsonl  user = question only
  grounded_{train,holdout}.jsonl     user = question + source passages (the record's claims
                                     plus distractor claims from other topics, shuffled)
The holdout is chosen by source_group_id so no topic appears in both parts. It is an internal
overfitting check only, not an exam split.

Usage: python scripts/przemeknowak781/export_sft.py [--input PATH] [--holdout 0.1] [--distractors 2] [--seed 13]
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "data/przemeknowak781"
SYSTEM = ("Jesteś asystentem przygotowującym do matury z historii Polski. Odpowiadasz po polsku, "
          "zwięźle i precyzyjnie, w stylu odpowiedzi maturalnej. Podajesz tylko fakty, które wynikają "
          "z wiedzy historycznej lub z podanych fragmentów; nie dopisujesz dat, nazwisk ani ocen bez podstaw.")
GROUNDED_HINT = "Odpowiedz na podstawie fragmentów źródeł; nie wszystkie muszą dotyczyć pytania."


def in_holdout(group, fraction, seed):
    h = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(), 16)
    return (h % 10_000) / 10_000 < fraction


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=BASE / "train_strict.jsonl")
    ap.add_argument("--holdout", type=float, default=0.1)
    ap.add_argument("--distractors", type=int, default=2)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.input, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("audit", {}).get("status") == "verified" and r["split"] == "TRAIN"]
    rng = random.Random(args.seed)
    pool = [(r["source_group_id"], e["claim"]) for r in rows for e in r["evidence"]]
    out = BASE / "sft"
    out.mkdir(exist_ok=True)
    files = {f"{v}_{p}": open(out / f"{v}_{p}.jsonl", "w", encoding="utf-8", newline="\n")
             for v in ("closed_book", "grounded") for p in ("train", "holdout")}
    counts = {k: 0 for k in files}
    for r in rows:
        part = "holdout" if in_holdout(r["source_group_id"], args.holdout, args.seed) else "train"
        meta = {"id": r["id"], "task_type": r["task_type"], "era": r.get("era"),
                "source_group_id": r["source_group_id"], "source_ids": r["source_ids"]}
        closed = {"messages": [{"role": "system", "content": SYSTEM},
                               {"role": "user", "content": r["prompt"]},
                               {"role": "assistant", "content": r["answer"]}], **meta}
        others = [c for g, c in pool if g != r["source_group_id"]]
        passages = [e["claim"] for e in r["evidence"]] + rng.sample(others, min(args.distractors, len(others)))
        rng.shuffle(passages)
        context = "\n".join(f"[{i + 1}] {p}" for i, p in enumerate(passages))
        grounded = {"messages": [{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": f"{GROUNDED_HINT}\n\nFragmenty źródeł:\n{context}\n\nPytanie: {r['prompt']}"},
                                 {"role": "assistant", "content": r["answer"]}], **meta}
        for variant, rec in (("closed_book", closed), ("grounded", grounded)):
            files[f"{variant}_{part}"].write(json.dumps(rec, ensure_ascii=False) + "\n")
            counts[f"{variant}_{part}"] += 1
    for f in files.values():
        f.close()
    print(json.dumps({"verified_input": len(rows), **counts}, indent=1))


if __name__ == "__main__":
    main()
