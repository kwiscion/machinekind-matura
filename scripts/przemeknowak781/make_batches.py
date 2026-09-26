"""Split cached sources into generation batches with trimmed section text.

Usage: python scripts/przemeknowak781/make_batches.py [--batches 10] [--chars 6000] [--skip ID ...]
Writes data/przemeknowak781/cache/batches/batch-NN.txt (git-ignored).
"""
import argparse
import json
from pathlib import Path

MIN_SECTION_CHARS = 200


def trimmed(doc, budget):
    parts, used = [], 0
    for sec in doc["sections"]:
        if len(sec["text"]) < MIN_SECTION_CHARS and sec["heading"] != "lead":
            continue
        text = sec["text"][: max(0, budget - used)]
        if not text:
            break
        parts.append(f"[sekcja '{sec['heading']}']\n{text}")
        used += len(text)
    return "\n\n".join(parts)


def main():
    base = Path(__file__).resolve().parents[2] / "data/przemeknowak781"
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", type=int, default=10)
    ap.add_argument("--chars", type=int, default=6000)
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--only-file", help="file with one source_id per line")
    ap.add_argument("--prefix", default="batch")
    args = ap.parse_args()

    sources = [json.loads(l) for l in open(base / "sources.jsonl", encoding="utf-8") if l.strip()]
    sources = [s for s in sources if s["source_id"] not in args.skip]
    if args.only_file:
        only = set(Path(args.only_file).read_text(encoding="utf-8").split())
        sources = [s for s in sources if s["source_id"] in only]
    out = base / "cache/batches"
    out.mkdir(parents=True, exist_ok=True)
    for b in range(args.batches):
        chunk = sources[b :: args.batches]
        blocks = []
        for s in chunk:
            doc = json.loads((base / s["local_path"]).read_text(encoding="utf-8"))
            header = (f"##### SOURCE source_id={s['source_id']} source_group_id={s['source_group_id']} "
                      f"era={doc['era']} title={doc['title']}")
            blocks.append(header + "\n" + trimmed(doc, args.chars))
        name = f"{args.prefix}-{b + 1:02d}"
        (out / f"{name}.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        print(f"{name}: {len(chunk)} sources")


if __name__ == "__main__":
    main()
