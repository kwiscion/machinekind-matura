#!/usr/bin/env python3
"""Stage the pinned chrono retrieval index (issue #44) on another machine and prove its identity.

One command from a fresh clone:

    python3 scripts/Bukareszt/stage_index.py stage [--bundle PATH]

Order of attempts (the report records which one ran):
  1. already staged: `agentsLog/Bukareszt/{raw,index}` exist and every hash matches -> verify only;
  2. portable bundle (`--bundle`, or the default file under `agentsLog/Bukareszt/private/`): SHA-256 of the
     archive must equal the committed manifest, every member is hash-checked before it is moved into place;
  3. rebuild from pinned revisions (`--rebuild`, or automatic when no bundle exists): each source is fetched
     from the Wikimedia API, its revision ID and normalized-text SHA-256 must equal `sources/sources.jsonl`;
     any difference is listed per source and the command exits nonzero. Revisions are never refreshed.
Then the index SHA-256 must equal the pinned value, the graph content hash must match, and one existing TRAIN
query is executed with `--mode chrono --k 5 --title-weight 1.0` in a child process whose socket layer is
disabled (plus `unshare -rn` on Linux when available); its ranking must equal the committed proof.

Other subcommands: `bundle` (build the portable archive + committed manifest from verified local assets),
`verify` (hash checks only), `_offline-query` (internal child process).
Stdlib only. Retrieval code is imported unchanged from `agentsLog/Bukareszt/scripts/retrieval.py`.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_ROOT = REPO / "agentsLog" / "Bukareszt"
STAGING_DIR = DEFAULT_ROOT / "staging"
MANIFEST_FILE = STAGING_DIR / "manifest.json"

# Issue #44 acceptance values (also present in the manifest; both must agree).
PINNED_INDEX_SHA256 = "350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429"
PINNED_SOURCES_SHA256 = "8b77a63afd25317d783a3e511e3f1f99f09b6cec3c740bdf101a0d069aadfeed"
PINNED_N_SOURCES = 107
PINNED_N_CHUNKS = 3481
RETRIEVAL_CONFIG = {"mode": "chrono", "k": 5, "title_weight": 1.0}
BUNDLE_NAME = "chrono_index_bundle_350800b1.tar.gz"
BUNDLE_PREFIX = "chrono_index_bundle"
USER_AGENT = "machinekind-matura-stage-index/0.1 (issue #44; contact: piotrowskigrzegorz2000@gmail.com)"
API = {"wikipedia_pl": "https://pl.wikipedia.org/w/api.php", "wikisource_pl": "https://pl.wikisource.org/w/api.php"}
INTEGRATION_COMMAND = (
    "python scripts/prepare_rag.py --input <exam-input.jsonl> --output outputs/rag-input.jsonl "
    "--trace outputs/rag-trace.jsonl --corpus outputs/rag-corpus.jsonl   # defaults: --mode chrono --k 5, "
    "--index agentsLog/Bukareszt/index/bm25_index.json --graph agentsLog/Bukareszt/index/graph.json"
)


class StageError(Exception):
    """A verification failure; the message names the file/source and both hashes."""


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def graph_content_sha256(graph: dict) -> str:
    """Graph hash without the `built_at` timestamp (the only nondeterministic field)."""
    payload = {k: v for k, v in graph.items() if k != "built_at"}
    return sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def load_retrieval(root: Path):
    """Import the pinned retrieval module unchanged and point its paths at `root`."""
    scripts_dir = str(root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import retrieval  # noqa: PLC0415

    retrieval.ROOT = str(root)
    retrieval.SOURCES_JSONL = str(root / "sources" / "sources.jsonl")
    retrieval.RAW_DIR = str(root / "raw")
    retrieval.INDEX_DIR = str(root / "index")
    retrieval.INDEX_FILE = str(root / "index" / "bm25_index.json")
    retrieval.GRAPH_FILE = str(root / "index" / "graph.json")
    return retrieval


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


# --------------------------------------------------------------------------------------
# verification of staged assets
# --------------------------------------------------------------------------------------

def verify_raw(root: Path, manifest_rows: list[dict]) -> list[dict]:
    """Return a list of {source_id, expected, actual} for every raw file that is missing or differs."""
    problems = []
    for r in manifest_rows:
        p = root / r["local_path"]
        if not p.exists():
            problems.append({"source_id": r["source_id"], "expected": r["sha256"], "actual": None, "reason": "missing"})
            continue
        h = sha256_file(p)
        if h != r["sha256"]:
            problems.append({"source_id": r["source_id"], "expected": r["sha256"], "actual": h, "reason": "sha256 differs"})
    return problems


def verify_staged(root: Path, manifest: dict) -> dict:
    """Hash-check sources.jsonl, raw/, index/ and graph. Raises StageError with the first difference list."""
    sources_path = root / "sources" / "sources.jsonl"
    checks: dict = {}
    got = sha256_file(sources_path)
    checks["sources_sha256"] = {"expected": manifest["sources_sha256"], "actual": got}
    if got != manifest["sources_sha256"]:
        raise StageError(f"sources.jsonl differs: expected {manifest['sources_sha256']} actual {got}")
    rows = read_jsonl(sources_path)
    if len(rows) != manifest["n_sources"]:
        raise StageError(f"sources.jsonl has {len(rows)} rows, expected {manifest['n_sources']}")
    raw_problems = verify_raw(root, rows)
    checks["raw_files"] = {"checked": len(rows), "problems": raw_problems}
    if raw_problems and all(p["reason"] == "missing" for p in raw_problems):
        raise StageError(f"raw/ not staged: {len(raw_problems)}/{len(rows)} source files missing under {root / 'raw'}")
    if raw_problems:
        lines = "\n".join(f"  {p['source_id']}: {p['reason']} expected={p['expected']} actual={p['actual']}" for p in raw_problems)
        raise StageError(f"{len(raw_problems)} raw source file(s) differ from sources.jsonl:\n{lines}")
    index_path = root / "index" / "bm25_index.json"
    if not index_path.exists():
        raise StageError(f"index missing: {index_path}")
    got = sha256_file(index_path)
    checks["index_sha256"] = {"expected": manifest["index_sha256"], "actual": got, "bytes": index_path.stat().st_size}
    if got != manifest["index_sha256"]:
        raise StageError(f"index differs: expected {manifest['index_sha256']} actual {got}")
    payload = load_json(index_path)
    meta = payload.get("meta", {})
    checks["index_meta"] = {"n_sources": meta.get("n_sources"), "n_chunks": meta.get("n_chunks")}
    if meta.get("n_sources") != manifest["n_sources"] or meta.get("n_chunks") != manifest["n_chunks"]:
        raise StageError(f"index meta {checks['index_meta']} != expected {manifest['n_sources']}/{manifest['n_chunks']}")
    embedded = meta.get("raw_sha256", {})
    drift = [r["source_id"] for r in rows if embedded.get(r["source_id"]) != r["sha256"]]
    if drift:
        raise StageError(f"index embeds different raw hashes for: {drift}")
    graph_path = root / "index" / "graph.json"
    if not graph_path.exists():
        raise StageError(f"graph missing: {graph_path}")
    got = graph_content_sha256(load_json(graph_path))
    checks["graph_content_sha256"] = {"expected": manifest["graph_content_sha256"], "actual": got, "bytes": graph_path.stat().st_size}
    if got != manifest["graph_content_sha256"]:
        raise StageError(f"graph content differs: expected {manifest['graph_content_sha256']} actual {got}")
    checks["disk_bytes"] = {"raw": dir_bytes(root / "raw"), "index": dir_bytes(root / "index")}
    return checks


# --------------------------------------------------------------------------------------
# portable bundle
# --------------------------------------------------------------------------------------

def attribution_markdown(rows: list[dict], manifest: dict) -> str:
    lines = [
        "# Attribution for the bundled retrieval corpus (issue #44 staging)",
        "",
        f"Bundle of the pinned chrono index `{manifest['index_sha256']}` ({manifest['n_sources']} sources, "
        f"{manifest['n_chunks']} chunks). Raw text files are the normalized plain-text extracts of the revisions "
        "listed below; each revision is pinned by ID and SHA-256 in `sources.jsonl` (same file as "
        "`agentsLog/Bukareszt/sources/sources.jsonl`).",
        "",
        "- Polish Wikipedia text: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), authors are the",
        "  Polish Wikipedia editors of each revision (page history at the permalink).",
        "- Polish Wikisource documents: public-domain primary documents; the transcription layer is CC BY-SA 4.0.",
        "- Redistribution of this bundle must keep this file, `sources.jsonl` and the share-alike terms.",
        "- The bundle contains no exam questions, answers, keys, source packs or model outputs.",
        "",
        "| source_id | title | revision | license | permalink |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(f"| {r['source_id']} | {r['title']} | {r['revision_id']} | {r['license']} | {r['url']} |")
    return "\n".join(lines) + "\n"


def bundle_members(root: Path, rows: list[dict]) -> list[tuple[str, Path]]:
    members = [("sources.jsonl", root / "sources" / "sources.jsonl")]
    members += [(r["local_path"], root / r["local_path"]) for r in rows]
    members += [("index/bm25_index.json", root / "index" / "bm25_index.json"), ("index/graph.json", root / "index" / "graph.json")]
    return sorted(members)


def build_manifest(root: Path, query_proof: dict | None, retrieval_script_sha: str) -> dict:
    rows = read_jsonl(root / "sources" / "sources.jsonl")
    index_path = root / "index" / "bm25_index.json"
    graph_path = root / "index" / "graph.json"
    payload = load_json(index_path)
    return {
        "issue": 44,
        "built_at": now_iso(),
        "sources_sha256": sha256_file(root / "sources" / "sources.jsonl"),
        "n_sources": len(rows),
        "n_chunks": payload["meta"]["n_chunks"],
        "index_sha256": sha256_file(index_path),
        "index_bytes": index_path.stat().st_size,
        "graph_content_sha256": graph_content_sha256(load_json(graph_path)),
        "retrieval_config": dict(RETRIEVAL_CONFIG),
        "retrieval_script_sha256": retrieval_script_sha,
        "licenses": sorted({r["license"] for r in rows}),
        "sites": sorted({r["site"] for r in rows}),
        "files": {name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for name, p in bundle_members(root, rows)},
        "query_proof": query_proof,
    }


def write_bundle(root: Path, manifest: dict, out: Path) -> dict:
    """Deterministic tar.gz (fixed mtimes/owners, sorted members, gzip mtime 0)."""
    rows = read_jsonl(root / "sources" / "sources.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    # the embedded copy omits volatile fields so identical assets give a byte-identical archive
    inner = {k: v for k, v in manifest.items() if k not in ("built_at", "bundle")}
    if inner.get("query_proof"):
        inner["query_proof"] = {k: v for k, v in inner["query_proof"].items() if k not in ("recorded_on", "python")}
    generated = {
        "MANIFEST.json": json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"),
        "ATTRIBUTION.md": attribution_markdown(rows, manifest).encode("utf-8"),
    }
    with open(out, "wb") as raw_f:
        gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw_f, mtime=0)
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for name, data in sorted(generated.items()):
                ti = tarfile.TarInfo(f"{BUNDLE_PREFIX}/{name}")
                ti.size, ti.mtime, ti.mode = len(data), 0, 0o644
                tar.addfile(ti, io.BytesIO(data))
            for name, p in bundle_members(root, rows):
                ti = tarfile.TarInfo(f"{BUNDLE_PREFIX}/{name}")
                ti.size, ti.mtime, ti.mode = p.stat().st_size, 0, 0o644
                with open(p, "rb") as f:
                    tar.addfile(ti, f)
        gz.close()
    return {"path": str(out), "sha256": sha256_file(out), "bytes": out.stat().st_size}


def unpack_bundle(bundle: Path, root: Path, manifest: dict) -> dict:
    """Verify the archive hash, extract to a temp dir, hash every member, then move raw/ and index/ into place."""
    expected = manifest.get("bundle", {}).get("sha256")
    got = sha256_file(bundle)
    if expected and got != expected:
        raise StageError(f"bundle differs: expected {expected} actual {got} ({bundle})")
    with tempfile.TemporaryDirectory(prefix="stage-index-") as tmp:
        with tarfile.open(bundle, "r:gz") as tar:
            names = tar.getnames()
            bad = [n for n in names if not n.startswith(BUNDLE_PREFIX + "/") or ".." in n.split("/")]
            if bad:
                raise StageError(f"bundle has unexpected member names: {bad[:5]}")
            tar.extractall(tmp, filter="data") if hasattr(tarfile, "data_filter") else tar.extractall(tmp)
        base = Path(tmp) / BUNDLE_PREFIX
        problems = []
        for name, info in manifest["files"].items():
            p = base / name
            if not p.exists():
                problems.append(f"{name}: missing from bundle")
                continue
            h = sha256_file(p)
            if h != info["sha256"]:
                problems.append(f"{name}: expected {info['sha256']} actual {h}")
        if problems:
            raise StageError("bundle members differ from manifest:\n  " + "\n  ".join(problems))
        got_sources = sha256_file(base / "sources.jsonl")
        if got_sources != sha256_file(root / "sources" / "sources.jsonl"):
            raise StageError(f"bundle sources.jsonl {got_sources} differs from the clone's sources.jsonl")
        for sub in ("raw", "index"):
            dest = root / sub
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(base / sub), str(dest))
    return {"bundle": str(bundle), "bundle_sha256": got, "bundle_bytes": bundle.stat().st_size, "members": len(manifest["files"])}


# --------------------------------------------------------------------------------------
# rebuild from pinned revisions
# --------------------------------------------------------------------------------------

def api_get(site: str, params: dict, timeout: int = 60) -> dict:
    url = API[site] + "?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pinned(retrieval, row: dict) -> dict:
    """Fetch the text for one pinned source. Returns {revid, text, method}.

    Wikipedia: the TextExtracts API serves only the current revision, so the current revision is fetched and
    must still be the pinned one. Wikisource: `parse` accepts `oldid`, so the pinned revision is requested
    directly (transcluded Page: pages are not pinned by that ID, which the hash check catches).
    """
    site = row["site"]
    if site == "wikipedia_pl":
        d = api_get(site, {"action": "query", "prop": "extracts|revisions|info", "explaintext": 1,
                           "exsectionformat": "wiki", "rvprop": "ids|timestamp", "titles": row["title"], "redirects": 1})
        page = d["query"]["pages"][0]
        if page.get("missing"):
            raise StageError(f"{row['source_id']}: page missing: {row['title']}")
        return {"revid": page["revisions"][0]["revid"], "text": page.get("extract", ""), "method": "api:query/extracts(current)"}
    if site == "wikisource_pl":
        d = api_get(site, {"action": "parse", "oldid": row["revision_id"], "prop": "text|revid"})
        if "error" in d:
            raise StageError(f"{row['source_id']}: {d['error'].get('info')}")
        p = d["parse"]
        return {"revid": p["revid"], "text": retrieval._strip_html(p["text"]), "method": "api:parse/oldid(html-stripped)"}
    raise StageError(f"{row['source_id']}: unknown site {site}")


def rebuild_raw(root: Path, rows: list[dict], fetcher, sleep: float = 0.3, log=print) -> list[dict]:
    """Fetch every pinned source into raw/. Returns the list of per-source differences (empty on success)."""
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    diffs = []
    for i, r in enumerate(rows, 1):
        try:
            got = fetcher(r)
        except Exception as exc:  # noqa: BLE001 -- recorded per source, never hidden
            diffs.append({"source_id": r["source_id"], "reason": f"fetch failed: {exc}", "expected_revid": r["revision_id"],
                          "actual_revid": None, "expected_sha256": r["sha256"], "actual_sha256": None})
            log(f"FAIL {i:3d}/{len(rows)} {r['source_id']}: {exc}")
            continue
        data = got["text"].encode("utf-8")
        h = sha256_bytes(data)
        (root / r["local_path"]).write_bytes(data)
        if got["revid"] != r["revision_id"] or h != r["sha256"]:
            reason = "revision drifted" if got["revid"] != r["revision_id"] else "same revision, normalized text differs"
            diffs.append({"source_id": r["source_id"], "reason": reason, "expected_revid": r["revision_id"], "actual_revid": got["revid"],
                          "expected_sha256": r["sha256"], "actual_sha256": h, "method": got["method"]})
            log(f"DIFF {i:3d}/{len(rows)} {r['source_id']}: {reason} (revid {r['revision_id']} -> {got['revid']})")
        else:
            log(f"ok   {i:3d}/{len(rows)} {r['source_id']} revid={got['revid']} bytes={len(data)}")
        if sleep:
            time.sleep(sleep)
    return diffs


def rebuild_index(retrieval, root: Path) -> None:
    """Run the pinned `index` and `graph` commands; the committed reports/index_meta.json is left untouched."""
    with tempfile.TemporaryDirectory(prefix="stage-index-reports-") as tmp:
        retrieval.REPORTS_DIR = tmp
        retrieval.cmd_index(argparse.Namespace(max_chars=1200, k1=1.5, b=0.75))
        retrieval.cmd_graph(argparse.Namespace())


# --------------------------------------------------------------------------------------
# offline query proof
# --------------------------------------------------------------------------------------

def install_socket_guard() -> None:
    """Make every socket creation / DNS lookup raise, so a retrieval query provably needs no network."""
    import socket  # noqa: PLC0415

    def _blocked(*_a, **_k):
        raise RuntimeError("network disabled by stage_index socket guard")

    class _GuardedSocket(socket.socket):  # type: ignore[misc]
        def __init__(self, *a, **k):  # noqa: D401
            _blocked()

    socket.socket = _GuardedSocket  # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked  # type: ignore[assignment]
    socket.socketpair = _blocked  # type: ignore[assignment]


def cmd_offline_query(args) -> int:
    """Child process: guard sockets, self-test the guard, run the query, print JSON."""
    install_socket_guard()
    import socket  # noqa: PLC0415

    try:
        socket.create_connection(("127.0.0.1", 9), timeout=1)
        print(json.dumps({"error": "socket guard self-test failed: connection attempt did not raise"}))
        return 3
    except RuntimeError:
        pass
    root = Path(args.root)
    retrieval = load_retrieval(root)
    t0 = time.perf_counter()
    idx = retrieval.load_index()
    graph = retrieval.load_graph() if args.mode == "chrono" else None
    t1 = time.perf_counter()
    res = retrieval.rank(idx, args.query, args.k, args.mode, graph=graph, title_weight=args.title_weight)
    t2 = time.perf_counter()
    out = {
        "query": args.query, "mode": args.mode, "k": args.k, "title_weight": args.title_weight,
        "load_seconds": round(t1 - t0, 3), "rank_seconds": round(t2 - t1, 4),
        "results": [{"rank": r["rank"], "chunk_id": r["chunk_id"], "source_id": r["source_id"], "locator": r["locator"],
                     "score": round(float(r["score"]), 4)} for r in res],
        "guard": "socket-guard", "python": platform.python_version(),
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def run_offline_query(root: Path, query: str, mode: str, k: int, title_weight: float) -> dict:
    """Run `_offline-query` in a child with proxies stripped and (on Linux) an unshared network namespace."""
    env = {k_: v for k_, v in os.environ.items() if not k_.lower().endswith("_proxy")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NO_PROXY"] = "*"
    cmd = [sys.executable, "-I", str(Path(__file__).resolve()), "_offline-query", "--root", str(root), "--query", query,
           "--mode", mode, "--k", str(k), "--title-weight", str(title_weight)]
    guards = ["socket-guard", "proxy-env-stripped"]
    unshare = shutil.which("unshare")
    if unshare and platform.system() == "Linux":
        probe = subprocess.run([unshare, "-rn", "true"], capture_output=True)
        if probe.returncode == 0:
            cmd = [unshare, "-rn"] + cmd
            guards.append("unshare -rn")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise StageError(f"offline query failed (exit {proc.returncode}): {proc.stdout.strip()} {proc.stderr.strip()[-2000:]}")
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    out["guards"] = guards
    out["command"] = cmd
    return out


def compare_query_proof(actual: dict, expected: dict) -> None:
    keys = ("chunk_id", "source_id", "locator", "score")
    got = [{k: r[k] for k in keys} for r in actual["results"]]
    want = [{k: r[k] for k in keys} for r in expected["results"]]
    if got != want:
        raise StageError("offline query ranking differs from the committed proof:\n  expected " + json.dumps(want, ensure_ascii=False)
                         + "\n  actual   " + json.dumps(got, ensure_ascii=False))


def pick_train_query(root: Path, query_id: str | None) -> dict:
    rows = read_jsonl(root / "queries" / "train_queries.jsonl")
    for r in rows:
        if r.get("split") == "TRAIN" and (query_id is None or r["id"] == query_id):
            return {"id": r["id"], "text": r["prompt"]}
    raise StageError(f"TRAIN query not found: {query_id}")


# --------------------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------------------

def load_manifest(path: Path, allow_unpinned: bool = False) -> dict:
    if not path.exists():
        raise StageError(f"manifest missing: {path} (run `stage_index.py bundle` on the machine that has the verified assets)")
    m = load_json(path)
    if allow_unpinned:
        return m
    if m["index_sha256"] != PINNED_INDEX_SHA256 or m["sources_sha256"] != PINNED_SOURCES_SHA256 \
            or m["n_sources"] != PINNED_N_SOURCES or m["n_chunks"] != PINNED_N_CHUNKS:
        raise StageError(f"manifest {path} does not carry the issue #44 pinned values")
    return m


def cmd_bundle(args) -> int:
    root = Path(args.root).resolve()
    retrieval_sha = sha256_file(root / "scripts" / "retrieval.py")
    manifest = build_manifest(root, None, retrieval_sha)
    if manifest["index_sha256"] != PINNED_INDEX_SHA256:
        raise StageError(f"local index is not the pinned one: {manifest['index_sha256']} != {PINNED_INDEX_SHA256}")
    verify_staged(root, manifest)
    q = pick_train_query(root, args.query_id)
    proof = run_offline_query(root, q["text"], **RETRIEVAL_CONFIG)
    manifest["query_proof"] = {"query_id": q["id"], "query": q["text"], **RETRIEVAL_CONFIG,
                               "results": proof["results"], "recorded_on": platform.node(), "python": proof["python"]}
    out = Path(args.out) if args.out else root / "private" / BUNDLE_NAME
    info = write_bundle(root, manifest, out)
    manifest["bundle"] = {"name": out.name, "sha256": info["sha256"], "bytes": info["bytes"], "default_path": f"agentsLog/Bukareszt/private/{BUNDLE_NAME}"}
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    (root / "staging").mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest) if args.manifest else root / "staging" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = read_jsonl(root / "sources" / "sources.jsonl")
    (manifest_path.parent / "ATTRIBUTION.md").write_text(attribution_markdown(rows, manifest), encoding="utf-8")
    print(json.dumps({"bundle": manifest["bundle"], "manifest": str(manifest_path), "index_sha256": manifest["index_sha256"],
                      "query_proof_id": q["id"]}, indent=2))
    return 0


def cmd_verify(args) -> int:
    root = Path(args.root).resolve()
    manifest = load_manifest(Path(args.manifest) if args.manifest else root / "staging" / "manifest.json")
    checks = verify_staged(root, manifest)
    print(json.dumps({"status": "PASS", "checks": checks}, indent=2))
    return 0


def cmd_stage(args) -> int:
    t_start = time.perf_counter()
    root = Path(args.root).resolve()
    manifest = load_manifest(Path(args.manifest) if args.manifest else root / "staging" / "manifest.json", args.allow_unpinned)
    report: dict = {"issue": 44, "started_at": now_iso(), "host": platform.node(), "platform": platform.platform(),
                    "python": platform.python_version(), "repo": str(REPO), "root": str(root), "status": "FAIL",
                    "pinned": {"index_sha256": manifest["index_sha256"], "sources_sha256": manifest["sources_sha256"],
                               "n_sources": manifest["n_sources"], "n_chunks": manifest["n_chunks"], **RETRIEVAL_CONFIG},
                    "phases": {}, "path_used": None, "blocker": None}
    report_path = Path(args.report) if args.report else root / "private" / "stage_report.json"
    retrieval = load_retrieval(root)
    report["retrieval_script_sha256"] = {"expected": manifest["retrieval_script_sha256"], "actual": sha256_file(root / "scripts" / "retrieval.py")}

    def phase(name, fn):
        t0 = time.perf_counter()
        try:
            out = fn()
            report["phases"][name] = {"ok": True, "seconds": round(time.perf_counter() - t0, 3), "detail": out}
            return out
        except StageError as exc:
            report["phases"][name] = {"ok": False, "seconds": round(time.perf_counter() - t0, 3), "error": str(exc)}
            raise

    try:
        staged = False
        if not args.rebuild and not args.force:
            try:
                phase("verify_existing", lambda: verify_staged(root, manifest))
                staged, report["path_used"] = True, "already-staged"
            except StageError as exc:
                report["phases"]["verify_existing"]["note"] = "not staged yet; trying bundle/rebuild"
                print(f"existing assets not usable: {str(exc).splitlines()[0]}")
        if not staged and not args.rebuild:
            bundle = Path(args.bundle) if args.bundle else root / "private" / BUNDLE_NAME
            if bundle.exists():
                phase("unpack_bundle", lambda: unpack_bundle(bundle, root, manifest))
                phase("verify_bundle_staged", lambda: verify_staged(root, manifest))
                staged, report["path_used"] = True, "bundle"
            else:
                print(f"no bundle at {bundle}; falling back to rebuild from pinned revisions")
        if not staged:
            rows = read_jsonl(root / "sources" / "sources.jsonl")

            def do_rebuild():
                diffs = rebuild_raw(root, rows, lambda r: fetch_pinned(retrieval, r), sleep=args.sleep)
                if diffs:
                    lines = "\n".join(f"  {d['source_id']}: {d['reason']} revid {d['expected_revid']}->{d['actual_revid']} "
                                      f"sha256 {d['expected_sha256']}->{d['actual_sha256']}" for d in diffs)
                    raise StageError(f"{len(diffs)}/{len(rows)} pinned sources could not be reproduced exactly "
                                     f"(revisions are never refreshed; use the portable bundle):\n{lines}")
                return {"fetched": len(rows), "differences": []}

            phase("rebuild_raw", do_rebuild)
            phase("rebuild_index", lambda: rebuild_index(retrieval, root))
            phase("verify_rebuilt", lambda: verify_staged(root, manifest))
            report["path_used"] = "rebuild-from-pinned-revisions"
        if not args.no_query:
            proof_spec = manifest["query_proof"]
            actual = phase("offline_query", lambda: run_offline_query(root, proof_spec["query"], proof_spec["mode"], proof_spec["k"], proof_spec["title_weight"]))
            phase("compare_query_proof", lambda: compare_query_proof(actual, proof_spec))
        report["status"] = "PASS"
    except StageError as exc:
        report["blocker"] = str(exc)
    finally:
        report["disk_bytes"] = {"raw": dir_bytes(root / "raw"), "index": dir_bytes(root / "index")}
        report["total_seconds"] = round(time.perf_counter() - t_start, 3)
        report["finished_at"] = now_iso()
        report["integration_command"] = INTEGRATION_COMMAND
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"stage_index: {report['status']}  path={report['path_used']}  index_sha256={manifest['index_sha256']}")
    print(f"  raw {report['disk_bytes']['raw']} B, index {report['disk_bytes']['index']} B, {report['total_seconds']} s; report: {report_path}")
    if report["status"] == "PASS":
        q = report["phases"].get("offline_query", {}).get("detail", {})
        if q:
            print(f"  offline TRAIN query proof OK ({', '.join(q['guards'])}): top-1 {q['results'][0]['chunk_id']} [{q['results'][0]['locator']}]")
        print(f"  integration: {INTEGRATION_COMMAND}")
        return 0
    print(f"  BLOCKER: {report['blocker']}")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("stage", cmd_stage), ("bundle", cmd_bundle), ("verify", cmd_verify)):
        p = sub.add_parser(name)
        p.add_argument("--root", default=str(DEFAULT_ROOT), help="retrieval root (default agentsLog/Bukareszt)")
        p.add_argument("--manifest", default=None, help="committed manifest (default <root>/staging/manifest.json)")
        p.set_defaults(fn=fn)
        if name == "stage":
            p.add_argument("--bundle", default=None, help=f"portable bundle (default <root>/private/{BUNDLE_NAME})")
            p.add_argument("--rebuild", action="store_true", help="skip the bundle and rebuild from pinned revisions")
            p.add_argument("--force", action="store_true", help="re-stage even if the local assets already verify")
            p.add_argument("--no-query", action="store_true", help="skip the offline TRAIN query proof")
            p.add_argument("--sleep", type=float, default=0.3, help="seconds between API requests in rebuild mode")
            p.add_argument("--report", default=None, help="report path (default <root>/private/stage_report.json)")
            p.add_argument("--allow-unpinned", action="store_true", help="tests only: accept a manifest that is not the #44 index")
        if name == "bundle":
            p.add_argument("--out", default=None, help=f"bundle path (default <root>/private/{BUNDLE_NAME})")
            p.add_argument("--query-id", default=None, help="TRAIN query id for the proof (default: first TRAIN row)")
    p = sub.add_parser("_offline-query")
    p.add_argument("--root", required=True); p.add_argument("--query", required=True); p.add_argument("--mode", default="chrono")
    p.add_argument("--k", type=int, default=5); p.add_argument("--title-weight", type=float, default=1.0); p.set_defaults(fn=cmd_offline_query)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except StageError as exc:
        print(f"stage_index: FAIL\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
