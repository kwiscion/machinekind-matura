"""Prepare bounded retrieval-augmented inputs for infer.py from a local index."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RETRIEVAL_DIR = REPO / "agentsLog" / "Bukareszt" / "scripts"
sys.path.insert(0, str(RETRIEVAL_DIR))
import retrieval  # noqa: E402 -- use the merged retrieval implementation


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare(case, input_dir, idx, graph, mode, k, max_chars):
    if not isinstance(case.get("id"), str) or not isinstance(case.get("prompt"), str):
        raise ValueError("Every input needs string id and prompt")
    if not case["id"] or not case["prompt"]:
        raise ValueError("id and prompt must be nonempty")
    hits = retrieval.rank(idx, case["prompt"], k, mode=mode, graph=graph, title_weight=1.0)
    passages = []
    evidence = []
    corpus = []
    for hit in hits:
        sid, chunk_id = hit["source_id"], hit["chunk_id"]
        excerpt = hit["text"][:max_chars]
        passages.append(f"[[{sid}#{chunk_id}]] {hit['title']}: {excerpt}")
        evidence.append({key: hit[key] for key in ("chunk_id", "source_id", "locator", "rank")})
        corpus.append({"source_id": sid, "locator": chunk_id, "text": excerpt})
    context = "\n".join(passages) if passages else "No reference passages were retrieved."
    prompt = (
        "Answer the question using the reference passages when they support the answer. "
        "If a passage supports a claim, cite its exact [[source_id#locator]] marker. "
        "Do not invent citations; say when the passages do not support an answer.\n\n"
        f"Reference passages:\n{context}\n\nQuestion:\n{case['prompt']}"
    )
    images = case.get("images", [])
    if not isinstance(images, list) or any(not isinstance(p, str) for p in images):
        raise ValueError(f"{case['id']}: images must be local path strings")
    output = {"id": case["id"], "prompt": prompt}
    if images:
        output["images"] = [str((input_dir / p).resolve()) for p in images]
    return output, {"id": case["id"], "retrieved_evidence": evidence}, corpus


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path, help="passage corpus for evaluator citation audit")
    parser.add_argument("--index", type=Path, default=REPO / "agentsLog/Bukareszt/index/bm25_index.json")
    parser.add_argument("--graph", type=Path, default=REPO / "agentsLog/Bukareszt/index/graph.json")
    parser.add_argument("--mode", choices=("bm25", "chrono"), default="chrono")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--max-chars-per-hit", type=int, default=400)
    args = parser.parse_args(argv)
    if not 1 <= args.k <= 5 or not 50 <= args.max_chars_per_hit <= 1000:
        parser.error("--k must be 1-5 and --max-chars-per-hit must be 50-1000")
    targets = (args.output, args.trace, args.corpus)
    if len({target.resolve() for target in targets}) != 3:
        parser.error("Output, trace, and corpus paths must be distinct")
    for target in targets:
        if target.exists() or target.resolve() == args.input.resolve():
            parser.error(f"Output must be a new path: {target}")
    try:
        index_bytes = args.index.read_bytes()
        idx = retrieval.BM25Index.from_json(json.loads(index_bytes))
        graph = json.loads(args.graph.read_text(encoding="utf-8")) if args.mode == "chrono" else None
        cases = read_jsonl(args.input)
        if not cases:
            raise ValueError("Input has no cases")
        prepared, traces, corpus = [], [], {}
        seen = set()
        for case in cases:
            row, trace, passages = prepare(case, args.input.parent, idx, graph, args.mode, args.k, args.max_chars_per_hit)
            if row["id"] in seen:
                raise ValueError(f"Duplicate id: {row['id']}")
            seen.add(row["id"])
            trace.update(index_sha256=hashlib.sha256(index_bytes).hexdigest(), mode=args.mode, k=args.k)
            prepared.append(row)
            traces.append(trace)
            for passage in passages:
                corpus[(passage["source_id"], passage["locator"])] = passage
        for target, rows in ((args.output, prepared), (args.trace, traces), (args.corpus, corpus.values())):
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Prepared {len(prepared)} cases; index SHA-256 {traces[0]['index_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
