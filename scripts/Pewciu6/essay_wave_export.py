"""Export the publishable part of an #80 essay wave (no model calls).

Writes to --out: final answers (DEV and the validation development check, separately), unblinded
per-item grades (DEV with error lists; validation check with scores/counts only, since its grader
notes refer to restricted marking material), per-stage provenance from the ledger (hashes, caps,
token counts, status; no prompts, plans, critiques, fact banks or retrieved text), retrieval
provenance (queries and chunk ids only) and the ledger totals.

  python scripts/Pewciu6/essay_wave_export.py --wave-dir W --out agentsLog/Pewciu6/essay/results/<wave_id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> str:
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--valcheck-batch", default="v1-valcheck")
    args = parser.parse_args(argv)
    wave, out = Path(args.wave_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}

    dev, val, retrieval, batches = [], [], [], {}
    for bdir in sorted((wave / "batches").iterdir()):
        manifest = json.loads((bdir / "batch_manifest.json").read_text(encoding="utf-8"))
        batches[bdir.name] = {k: manifest.get(k) for k in ("status", "stop_reason", "attempted", "failed", "unsent",
                                                           "families", "items", "topic", "source_sha256",
                                                           "template_sha256", "template_sha256_grounded",
                                                           "answers_sha256")}
        batches[bdir.name]["source"] = "private validation runner input" if bdir.name == args.valcheck_batch \
            else Path(manifest["source"]).name
        for row in read_jsonl(bdir / "answers.jsonl"):
            (val if bdir.name == args.valcheck_batch else dev).append(row)
        if (bdir / "retrieval.jsonl").exists():
            retrieval += [dict(r, batch=bdir.name) for r in read_jsonl(bdir / "retrieval.jsonl")]
    hashes["answers.dev.jsonl"] = write_jsonl(out / "answers.dev.jsonl", dev)
    hashes["answers.valcheck.jsonl"] = write_jsonl(out / "answers.valcheck.jsonl", val)
    hashes["retrieval_provenance.jsonl"] = write_jsonl(out / "retrieval_provenance.jsonl", retrieval)

    ledger = json.loads((wave / "ledger.json").read_text(encoding="utf-8"))
    stages = [{k: e.get(k) for k in ("seq", "batch", "family", "item", "stage", "cap", "prompt_sha256", "status",
                                     "error", "elapsed_s", "timeout_s", "eval_count", "prompt_eval_count",
                                     "done_reason")} for e in ledger["entries"]]
    hashes["stage_provenance.jsonl"] = write_jsonl(out / "stage_provenance.jsonl", stages)
    env = ledger["envelope"]
    totals = {
        "wave_start": ledger.get("wave_start_iso"), "deadline": ledger.get("deadline_iso"),
        "wave_calls": len(stages), "prior_calls": env["prior_calls"], "total_calls": env["prior_calls"] + len(stages),
        "max_calls": env["max_calls"], "wave_requested_tokens": sum(e["cap"] for e in stages),
        "prior_tokens": env["prior_tokens"],
        "total_requested_tokens": env["prior_tokens"] + sum(e["cap"] for e in stages),
        "max_tokens": env["max_tokens"], "actual_output_tokens": sum(e["eval_count"] or 0 for e in stages),
        "failed": sum(1 for e in stages if e["status"] != "ok"), "retries": 0,
        "mechanism_families": ledger["families"], "max_families": env["max_families"],
        "unsent": sum(len(b["unsent"] or []) for b in batches.values()), "batches": batches,
    }

    grades_dev, grades_val = [], []
    for gdir in sorted((wave / "grading").iterdir()):
        if not gdir.is_dir() or not (gdir / "key.private.json").exists():
            continue
        key = {k["code"]: k for k in json.loads((gdir / "key.private.json").read_text(encoding="utf-8"))["key"]}
        agg = json.loads((gdir / "aggregate.json").read_text(encoding="utf-8")) if (gdir / "aggregate.json").exists() else {}
        words = {(r["item"], r["family"]): r["words"] for r in agg.get("per_item", [])}
        for path in sorted(gdir.glob("grades*.json")):
            for g in json.loads(path.read_text(encoding="utf-8")):
                k = key[g["code"]]
                base = {"round": gdir.name, "grader_file": path.name, "item": k["item"], "family": k["family"],
                        "batch": k["batch"], "topic": k["topic"], "words": words.get((k["item"], k["family"])),
                        "A": g["A"], "B": g["B"], "total": g["A"] + g["B"],
                        "n_factual_errors": len(g.get("factual_errors", []))}
                if k["batch"] == args.valcheck_batch:
                    grades_val.append(base)
                else:
                    grades_dev.append(dict(base, levels=[e.get("level") for e in g.get("elements", [])],
                                           A_before_deduction=g.get("A_before_deduction"),
                                           A_deduction=g.get("A_deduction"),
                                           factual_errors=g.get("factual_errors", []), comment=g.get("comment")))
    hashes["grades.dev.jsonl"] = write_jsonl(out / "grades.dev.jsonl", grades_dev)
    hashes["grades.valcheck.jsonl"] = write_jsonl(out / "grades.valcheck.jsonl", grades_val)
    totals["published_sha256"] = hashes
    (out / "ledger_totals.json").write_text(json.dumps(totals, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in totals.items() if k != "batches"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
