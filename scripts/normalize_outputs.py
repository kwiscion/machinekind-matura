"""Convert infer.py JSONL into the merged evaluator's model-output format."""

import argparse
import json
import sys
from pathlib import Path


def final_text(raw):
    if not isinstance(raw, dict):
        return ""
    for choice in raw.get("choices", []):
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            continue
        content = choice["message"].get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict) and isinstance(part.get("text"), str))
            if text.strip():
                return text
    return ""


def normalize(row, trace=None):
    backend = row.get("backend") or {}
    raw = row.get("raw_response")
    content = final_text(raw)
    error = row.get("error")
    if not error and not content.strip():
        error = "No final answer text"
    out = {
        "id": row["id"],
        "backend": backend.get("name"),
        "model": backend.get("response_model") or backend.get("model"),
        "raw_response": content,
        "provider_raw_response": raw,
        "error": json.dumps(error, ensure_ascii=False) if isinstance(error, dict) else error,
    }
    if backend.get("model_revision"):
        out["model_revision"] = backend["model_revision"]
    if isinstance(row.get("usage"), dict):
        out["usage"] = row["usage"]
    if isinstance(row.get("latency_seconds"), (int, float)):
        out["latency_s"] = row["latency_seconds"]
    if trace:
        out["retrieval_evidence"] = trace.get("retrieved_evidence", [])
        out["retrieval_index_sha256"] = trace.get("index_sha256")
    return out


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="infer.py output JSONL")
    parser.add_argument("--output", required=True, type=Path, help="new evaluator-format JSONL")
    parser.add_argument("--trace", type=Path, help="prepare_rag.py trace JSONL, if used")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.resolve() == args.input.resolve():
        parser.error(f"Output must be a new path: {args.output}")
    try:
        rows = read_jsonl(args.input)
        trace_rows = read_jsonl(args.trace) if args.trace else []
        traces = {row["id"]: row for row in trace_rows}
        if len(traces) != len(trace_rows):
            raise ValueError("Duplicate trace id")
        if not rows:
            raise ValueError("Input has no results")
        if args.trace and {row["id"] for row in rows} != set(traces):
            raise ValueError("Trace ids must match inference result ids")
        seen = set()
        converted = []
        for row in rows:
            if row["id"] in seen:
                raise ValueError(f"Duplicate id: {row['id']}")
            seen.add(row["id"])
            converted.append(normalize(row, traces.get(row["id"])))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as f:
            for row in converted:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Normalized {len(converted)} results to {args.output}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
