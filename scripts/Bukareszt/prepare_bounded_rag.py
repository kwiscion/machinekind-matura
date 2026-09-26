#!/usr/bin/env python3
"""Build a bounded, offline retrieval-augmented runner input from key-free original cases (issue #57).

    python3 scripts/Bukareszt/prepare_bounded_rag.py --input <keyfree.jsonl> \
        --output agentsLog/Bukareszt/private/rag_input/<name>.jsonl [--policy-file <policy.txt>] \
        [--top-k 3] [--budget-chars 1600]

What it does, per case (`{"id", "prompt", "images"?, ...}`, the shape `infer.py` consumes):
  * the retrieval query is the case's original `prompt` string and nothing else (never the policy);
  * pinned chrono retrieval, title weight 1.0, uniform `--top-k` for every case;
  * the retrieved excerpts go into one delimited block labelled as untrusted, optional historical background.
    The whole block (opening/closing lines, per-excerpt headers, separators and the blank line before the
    question) is at most `--budget-chars` Python characters; excerpts that do not fit are truncated or skipped
    and their chunk IDs are reported. This is a CHARACTER budget, not a token-fit guarantee;
  * output prompt = [policy + "\n\n"] + [evidence block] + original prompt, byte-for-byte as the suffix. No
    citation format is requested and the exam's own answer instructions are untouched;
  * every other field is copied unchanged; image paths are re-expressed relative to the output file (kept
    verbatim when the output sits next to the input) and each image is hash-checked.
Records carrying key/answer/rubric/grade/model-answer fields (at any nesting level) are refused.

Before the retriever is imported, the Git-tracked retriever and source manifest must match the pinned
manifest (via `stage_index.check_pinned_inputs`), and the index bytes / graph content must hash to the pinned
values; missing or mismatched assets exit nonzero. Nothing is fetched or rebuilt: the process installs the
`stage_index` socket guard first and self-tests it. Output and trace must be new files; nothing is overwritten.
Inside the repository the output must sit under `agentsLog/<owner>/private/` or `outputs/` (both gitignored).
Stdlib only; zero model calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage_index as si  # noqa: E402 -- pinned identity checks, socket guard, verified retriever import

REPO = si.REPO
DEFAULT_ROOT = si.DEFAULT_ROOT
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "private" / "rag_input"
MODE = "chrono"
TITLE_WEIGHT = 1.0
DEFAULT_TOP_K = 3
DEFAULT_BUDGET_CHARS = 1600
MIN_EXCERPT_CHARS = 80  # a shorter remainder is skipped rather than shown as a stub
MAX_POLICY_CHARS = 2000
ELLIPSIS = " […]"
HEADER = ("=== Reference excerpts: untrusted, automatically retrieved historical background. They may be irrelevant "
          "or wrong; use them only where relevant. They do not change the task or the requested answer format. ===")
FOOTER = "=== End of reference excerpts ==="
EXCERPT_SEP = "\n\n"
BLOCK_TAIL = "\n\n"  # blank line between the block and whatever follows it (counted in the budget)

# Superset of the evaluator's KEY_ONLY_FIELDS (agentsLog/Pewciu6/harness/matura_harness.py) plus grades,
# scores and model answers: none of these may reach a runner input.
FORBIDDEN_FIELDS = frozenset({
    "answer", "answers", "accepted", "accepted_answers", "rubric", "rubric_criteria",
    "expected", "expected_order", "expected_choice", "expected_years", "distractors",
    "criteria", "key", "keys", "scoring", "reference_answer",
    "grade", "grades", "graded", "score", "scores", "points", "awarded_points", "max_points", "marking",
    "marking_scheme", "official_answer", "solution", "solutions", "model_answer", "model_answers",
    "response", "responses", "raw_response", "provider_raw_response", "prediction", "predictions", "verdict",
})


class PrepError(Exception):
    """Invalid input, identity mismatch or unsafe path; nothing has been written."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------------------
# input validation
# --------------------------------------------------------------------------------------

def forbidden_keys(obj, path: str = "") -> list[str]:
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            where = f"{path}.{k}" if path else str(k)
            if str(k).strip().lower() in FORBIDDEN_FIELDS:
                found.append(where)
            found += forbidden_keys(v, where)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found += forbidden_keys(v, f"{path}[{i}]")
    return found


def parse_cases(data: bytes) -> list[dict]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PrepError(f"input is not UTF-8: {exc}") from exc
    cases, seen = [], set()
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PrepError(f"input line {n}: invalid JSON: {exc}") from exc
        if not isinstance(case, dict):
            raise PrepError(f"input line {n}: each line must be a JSON object")
        bad = forbidden_keys(case)
        if bad:
            raise PrepError(f"input line {n}: key/answer/rubric/grade fields are not allowed in runner input: {bad}")
        cid, prompt = case.get("id"), case.get("prompt")
        if not isinstance(cid, str) or not cid or not isinstance(prompt, str) or not prompt.strip():
            raise PrepError(f"input line {n}: every case needs a nonempty string id and prompt")
        if cid in seen:
            raise PrepError(f"input line {n}: duplicate id {cid!r}")
        seen.add(cid)
        images = case.get("images", [])
        if not isinstance(images, list) or any(not isinstance(p, str) or not p for p in images):
            raise PrepError(f"{cid}: images must be a list of nonempty local path strings")
        cases.append(case)
    if not cases:
        raise PrepError("input has no cases")
    return cases


def load_policy(path: Path | None, cases: list[dict]) -> tuple[str | None, dict | None]:
    if path is None:
        return None, None
    data = path.read_bytes()
    try:
        policy = data.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise PrepError(f"policy is not UTF-8: {exc}") from exc
    if not policy:
        raise PrepError("policy file is empty")
    if len(policy) > MAX_POLICY_CHARS:
        raise PrepError(f"policy has {len(policy)} characters; a generic policy must be at most {MAX_POLICY_CHARS}")
    hinted = [c["id"] for c in cases if c["id"] in policy]
    if hinted:
        raise PrepError(f"policy names case IDs {hinted}; only a generic, case-independent policy is allowed")
    return policy, {"file": str(path), "file_sha256": sha256_bytes(data), "text_sha256": sha256_bytes(policy.encode("utf-8")),
                    "chars": len(policy)}


# --------------------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------------------

def check_private_location(path: Path) -> None:
    """Exam-derived prompts stay out of Git: inside the repo only agentsLog/<owner>/private/ or outputs/."""
    p = Path(os.path.abspath(path))
    repo = REPO.resolve()
    if not p.resolve().is_relative_to(repo) and not p.is_relative_to(repo):
        return
    rel = (p.resolve() if p.resolve().is_relative_to(repo) else p).relative_to(repo).parts
    ok = (len(rel) >= 4 and rel[0] == "agentsLog" and rel[2] == "private") or (len(rel) >= 2 and rel[0] == "outputs")
    if not ok:
        raise PrepError(f"refusing to write exam-derived data to {p}: inside the repository use agentsLog/<owner>/private/ or outputs/")


def check_targets(output: Path, trace: Path, protected: list[Path]) -> None:
    out_r, trace_r = output.resolve(), trace.resolve()
    if out_r == trace_r:
        raise PrepError("output and trace must be different files")
    for target in (output, trace):
        if target.exists() or target.is_symlink():
            raise PrepError(f"refusing to overwrite existing file: {target}")
        if target.resolve() in {p.resolve() for p in protected}:
            raise PrepError(f"refusing to write over an input/source file: {target}")
        check_private_location(target)


def map_images(case: dict, input_dir: Path, output_dir: Path) -> tuple[list[str], list[dict]]:
    """Return image strings valid relative to the output file plus a hash record; content is never altered."""
    same_dir = input_dir.resolve() == output_dir.resolve()
    written, records = [], []
    for original in case.get("images", []):
        src = (input_dir / original).resolve()
        if not src.is_file():
            raise PrepError(f"{case['id']}: image {original!r} not found at {src}")
        if same_dir:
            new = original
        else:
            try:
                new = Path(os.path.relpath(src, output_dir.resolve())).as_posix()
            except ValueError:  # different drive on Windows
                new = str(src)
        if (output_dir / new).resolve() != src:
            raise PrepError(f"{case['id']}: image path {original!r} does not resolve identically from the output")
        written.append(new)
        records.append({"original": original, "written": new, "sha256": sha256_bytes(src.read_bytes()), "bytes": src.stat().st_size})
    return written, records


# --------------------------------------------------------------------------------------
# bounded evidence block
# --------------------------------------------------------------------------------------

def _truncate(text: str, room: int) -> str:
    cut = text[: max(0, room - len(ELLIPSIS))]
    space = cut.rfind(" ")
    if space >= len(cut) - 40 and space > 0:
        cut = cut[:space]
    return cut.rstrip() + ELLIPSIS


def build_evidence(hits: list[dict], budget: int) -> tuple[str, dict]:
    """Greedy in rank order. Every character added to the prompt (header, footer, excerpt headers, separators,
    trailing blank line) counts toward `budget`. Returns ("", stats) when nothing fits."""
    fixed = len(HEADER) + 1 + 1 + len(FOOTER) + len(BLOCK_TAIL)  # HEADER\n ... \nFOOTER\n\n
    parts, included, truncated, skipped = [], [], [], []
    used = fixed
    for n, hit in enumerate(hits, 1):
        head = f"[{len(parts) + 1}] {hit['title']}\n"
        sep = len(EXCERPT_SEP) if parts else 0
        body = " ".join(hit["text"].split())
        room = budget - used - sep - len(head)
        if len(body) <= room:
            text = body
        elif room >= MIN_EXCERPT_CHARS:
            text = _truncate(body, room)
            truncated.append(hit["chunk_id"])
        else:
            skipped.append(hit["chunk_id"])
            continue
        parts.append(head + text)
        included.append(hit["chunk_id"])
        used += sep + len(head) + len(text)
    if not parts:
        return "", {"included": [], "truncated": [], "skipped": [h["chunk_id"] for h in hits], "evidence_chars": 0}
    block = HEADER + "\n" + EXCERPT_SEP.join(parts) + "\n" + FOOTER + BLOCK_TAIL
    assert len(block) == used <= budget, (len(block), used, budget)
    return block, {"included": included, "truncated": truncated, "skipped": skipped, "evidence_chars": len(block)}


def compose(original_prompt: str, block: str, policy: str | None) -> str:
    return (policy + "\n\n" if policy else "") + block + original_prompt


# --------------------------------------------------------------------------------------
# identity
# --------------------------------------------------------------------------------------

def load_pinned_assets(root: Path, manifest_path: Path, allow_unpinned: bool):
    """Validate retriever, sources, index and graph before import/use; return (retrieval, idx, graph, identity)."""
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = si.load_manifest(manifest_path, allow_unpinned)
        inputs = si.check_pinned_inputs(root, manifest)  # retriever + sources.jsonl, before any import
        index_path, graph_path = root / "index" / "bm25_index.json", root / "index" / "graph.json"
        for p in (index_path, graph_path):
            if not p.is_file():
                raise PrepError(f"missing local asset {p}; stage it with `python3 scripts/Bukareszt/stage_index.py stage` "
                                "(this script never fetches or rebuilds)")
        index_bytes = index_path.read_bytes()
        index_sha = sha256_bytes(index_bytes)
        if index_sha != manifest["index_sha256"]:
            raise PrepError(f"index {index_path} expected {manifest['index_sha256']} actual {index_sha}; refusing to use it")
        payload = json.loads(index_bytes)
        meta = payload.get("meta", {})
        if meta.get("n_sources") != manifest["n_sources"] or meta.get("n_chunks") != manifest["n_chunks"]:
            raise PrepError(f"index meta {meta.get('n_sources')}/{meta.get('n_chunks')} != pinned {manifest['n_sources']}/{manifest['n_chunks']}")
        rows = si.read_jsonl(root / "sources" / "sources.jsonl")
        embedded = meta.get("raw_sha256", {})
        drift = [r["source_id"] for r in rows if embedded.get(r["source_id"]) != r["sha256"]]
        if len(rows) != manifest["n_sources"] or drift:
            raise PrepError(f"index does not match sources.jsonl (rows {len(rows)}, drift {drift})")
        graph = json.loads(graph_path.read_bytes())
        graph_sha = si.graph_content_sha256(graph)
        if graph_sha != manifest["graph_content_sha256"]:
            raise PrepError(f"graph {graph_path} expected {manifest['graph_content_sha256']} actual {graph_sha}")
        retrieval = si.load_retrieval(root, manifest["retrieval_script_sha256"])  # verified bytes only
        idx = retrieval.BM25Index.from_json(payload)
    except si.StageError as exc:
        raise PrepError(str(exc)) from exc
    except (KeyError, json.JSONDecodeError) as exc:
        raise PrepError(f"malformed manifest/index/graph: {exc!r}") from exc
    identity = {
        "manifest": str(manifest_path), "manifest_sha256": sha256_bytes(manifest_bytes), "pinned": not allow_unpinned,
        "index_sha256": index_sha, "index_bytes": len(index_bytes), "n_sources": meta["n_sources"], "n_chunks": meta["n_chunks"],
        "graph_content_sha256": graph_sha,
        "sources_sha256": inputs["sources_sha256"]["actual"], "retrieval_script_sha256": inputs["retrieval_script_sha256"]["actual"],
        "hash_note": "sources/retriever: SHA-256 of CRLF->LF normalized text; index: raw bytes; graph: content without built_at",
    }
    return retrieval, idx, graph, identity


def guard_network() -> str:
    si.install_socket_guard()
    import socket  # noqa: PLC0415

    for probe in (lambda: socket.create_connection(("127.0.0.1", 9), timeout=1), lambda: socket.socket(),
                  lambda: socket.getaddrinfo("example.invalid", 80)):
        try:
            probe()
        except RuntimeError:
            continue
        raise PrepError("socket guard self-test failed: a socket operation did not raise")
    return "stage_index socket guard (self-tested)"


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------

def prepare(args) -> dict:
    guard = guard_network()
    if not 1 <= args.top_k <= 5:
        raise PrepError("--top-k must be 1-5")
    if not 300 <= args.budget_chars <= 8000:
        raise PrepError("--budget-chars must be 300-8000")
    root = Path(args.root).resolve()
    input_path = Path(args.input)
    output = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / (input_path.stem + ".bounded-rag.jsonl")
    trace = Path(args.trace) if args.trace else output.with_name(output.name + ".trace.json")
    policy_path = Path(args.policy_file) if args.policy_file else None
    manifest_path = Path(args.manifest) if args.manifest else root / "staging" / "manifest.json"
    protected = [input_path, manifest_path, root / "index" / "bm25_index.json", root / "index" / "graph.json",
                 root / "sources" / "sources.jsonl", root / "scripts" / "retrieval.py"] + ([policy_path] if policy_path else [])
    check_targets(output, trace, protected)

    input_bytes = input_path.read_bytes()
    cases = parse_cases(input_bytes)
    for case in cases:  # an image path may never be a target either
        for img in case.get("images", []):
            protected.append(input_path.parent / img)
    check_targets(output, trace, protected)
    policy, policy_info = load_policy(policy_path, cases)
    retrieval, idx, graph, identity = load_pinned_assets(root, manifest_path, args.allow_unpinned)

    rows, per_case = [], []
    for case in cases:
        query = case["prompt"]  # the original task/source prompt only
        hits = retrieval.rank(idx, query, args.top_k, mode=MODE, graph=graph, title_weight=TITLE_WEIGHT)
        block, stats = build_evidence(hits, args.budget_chars)
        images, image_records = map_images(case, input_path.parent, output.parent)
        row = dict(case)
        row["prompt"] = compose(case["prompt"], block, policy)
        if "images" in case:
            row["images"] = images
        assert row["prompt"].endswith(case["prompt"]) and row["id"] == case["id"]
        rows.append(row)
        per_case.append({
            "id": case["id"], "query_sha256": sha256_bytes(query.encode("utf-8")), "query_chars": len(query),
            "retrieved": [{"rank": h["rank"], "chunk_id": h["chunk_id"], "source_id": h["source_id"], "locator": h["locator"],
                           "score": h["score"]} for h in hits],
            "included_chunk_ids": stats["included"], "truncated_chunk_ids": stats["truncated"],
            "skipped_chunk_ids": stats["skipped"], "evidence_chars": stats["evidence_chars"],
            "prompt_chars_original": len(case["prompt"]), "prompt_chars_output": len(row["prompt"]), "images": image_records,
        })

    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    ev = [c["evidence_chars"] for c in per_case]
    summary = {
        "cases": len(rows), "cases_with_evidence": sum(1 for e in ev if e), "evidence_chars_min": min(ev),
        "evidence_chars_mean": round(statistics.mean(ev), 1), "evidence_chars_max": max(ev),
        "excerpts_retrieved": sum(len(c["retrieved"]) for c in per_case),
        "excerpts_included": sum(len(c["included_chunk_ids"]) for c in per_case),
        "excerpts_truncated": sum(len(c["truncated_chunk_ids"]) for c in per_case),
        "excerpts_skipped": sum(len(c["skipped_chunk_ids"]) for c in per_case),
        "images": sum(len(c["images"]) for c in per_case),
    }
    report = {
        "status": "prepared_not_launched", "issue": 57, "created_at": si.now_iso(), "model_calls": 0,
        "network": guard, "fetch_or_rebuild": False,
        "settings": {"mode": MODE, "title_weight": TITLE_WEIGHT, "top_k": args.top_k, "budget_chars": args.budget_chars,
                     "min_excerpt_chars": MIN_EXCERPT_CHARS, "budget_unit": "Python str characters (Unicode code points), "
                     "whole evidence block incl. headers/separators; NOT a token-fit guarantee",
                     "query": "original case prompt only; policy/answers/grades/keys never enter the query",
                     "layout": "[policy + blank line] + [evidence block] + original prompt (verbatim suffix)"},
        "input": {"file": str(input_path), "sha256": sha256_bytes(input_bytes)},
        "output": {"file": str(output), "sha256": sha256_bytes(payload), "bytes": len(payload)},
        "policy": policy_info, "index": identity,
        "builder": {"file": str(Path(__file__).resolve()), "sha256": sha256_bytes(Path(__file__).read_bytes()),
                    "stage_index_sha256": sha256_bytes(Path(si.__file__).read_bytes())},
        "summary": summary, "cases": per_case,
    }
    for target in (output, trace):
        target.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "xb") as f:
        f.write(payload)
    with open(trace, "x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    report["trace_file"] = str(trace)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="key-free runner JSONL {id, prompt, images?}")
    p.add_argument("--output", default=None, help="new JSONL (default agentsLog/Bukareszt/private/rag_input/<input>.bounded-rag.jsonl)")
    p.add_argument("--trace", default=None, help="new provenance JSON (default <output>.trace.json)")
    p.add_argument("--policy-file", default=None, help="optional generic answer policy (UTF-8 text); never used as a query")
    p.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help=f"uniform excerpts retrieved per case (default {DEFAULT_TOP_K})")
    p.add_argument("--budget-chars", type=int, default=DEFAULT_BUDGET_CHARS,
                   help=f"max characters of the whole evidence block, headers included (default {DEFAULT_BUDGET_CHARS})")
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="retrieval root (default agentsLog/Bukareszt)")
    p.add_argument("--manifest", default=None, help="pinned manifest (default <root>/staging/manifest.json)")
    p.add_argument("--allow-unpinned", action="store_true", help=argparse.SUPPRESS)  # synthetic test roots only
    args = p.parse_args(argv)
    t0 = time.perf_counter()
    try:
        report = prepare(args)
    except (PrepError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "output": report["output"], "trace": report["trace_file"],
                      "index_sha256": report["index"]["index_sha256"], "summary": report["summary"],
                      "seconds": round(time.perf_counter() - t0, 2)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
