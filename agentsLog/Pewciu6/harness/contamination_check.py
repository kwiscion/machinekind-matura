#!/usr/bin/env python3
"""Contamination check (#13): May 2024 VALIDATION prompts / source-pack excerpts vs the #6 BM25 corpus.

Stdlib only, CPU, read-only on agentsLog/Bukareszt/. Units compared against every chunk:
  - prompt:  the full normalized runner prompt of each VALIDATION item (40);
  - excerpt: each distinct blank-line-separated paragraph of the prompts (the arkusz source packs,
             question stems) with >= --min-excerpt-chars normalized chars, deduplicated.
Signals per unit:
  - exact:    SHA-256 of normalized unit == SHA-256 of a normalized chunk, or normalized substring either way;
  - ngram:    char 8-gram and 13-gram sets: Jaccard and containment |U & C| / |U| for the best chunk,
              and corpus-wide 13-gram containment (fraction of the unit's 13-grams found in any chunk);
  - bm25:     top-5 chunks from Bukareszt's BM25Index (title_weight 1.0) with the unit as query,
              and the best 13-gram containment among them.
Flag rule (fixed before looking at results): 13-gram containment >= --flag (0.20) in a single chunk, or any exact hit;
longest common normalized substring >= --flag-lcs (80 chars) with the best chunk was added after a first run.
Review band: 13-gram containment >= --review (0.08).

Writes restricted per-unit detail to private/ and an aggregate JSON (no exam text, no answers) to results/.

  python3 agentsLog/Pewciu6/harness/contamination_check.py
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OWN = os.path.join(REPO, "agentsLog", "Pewciu6")
PRIV = os.path.join(OWN, "private", "validation_2024")
BUK = os.path.join(REPO, "agentsLog", "Bukareszt")
INDEX = os.path.join(BUK, "index", "bm25_index.json")

BINS = [0.0, 0.01, 0.02, 0.05, 0.08, 0.10, 0.20, 0.50, 1.01]


def norm(text):
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"\[miejsce na odpowiedź\]", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def grams(t, n):
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def hist(vals):
    out = []
    for lo, hi in zip(BINS, BINS[1:]):
        label = "[%.2f,%.2f)" % (lo, hi) if hi <= 1.0 else "[%.2f,1.00]" % lo
        out.append({"bin": label, "count": sum(1 for v in vals if lo <= v < hi)})
    return out


def quantiles(vals):
    s = sorted(vals)
    if not s:
        return {}
    q = lambda p: s[min(len(s) - 1, int(round(p * (len(s) - 1))))]
    return {"min": s[0], "p50": q(0.5), "p90": q(0.9), "p99": q(0.99), "max": s[-1], "mean": sum(s) / len(s)}


def load_units(path, min_chars):
    items = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    units, seen = [], {}
    for it in items:
        units.append({"unit_id": "prompt:" + it["id"], "kind": "prompt", "items": [it["id"]], "norm": norm(it["prompt"])})
    for it in items:
        for k, para in enumerate(re.split(r"\n\s*\n", it["prompt"])):
            n = norm(para)
            if len(n) < min_chars:
                continue
            h = sha(n)
            if h in seen:
                seen[h]["items"].append(it["id"])
                continue
            u = {"unit_id": "excerpt:%s:%d" % (it["id"], k), "kind": "excerpt", "items": [it["id"]], "norm": n}
            seen[h] = u
            units.append(u)
    return items, units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default=os.path.join(PRIV, "runner_input.jsonl"))
    ap.add_argument("--index", default=INDEX)
    ap.add_argument("--min-excerpt-chars", type=int, default=100)
    ap.add_argument("--flag", type=float, default=0.20)
    ap.add_argument("--review", type=float, default=0.08)
    ap.add_argument("--flag-lcs", type=int, default=80)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--private-out", default=os.path.join(PRIV, "contamination_units.jsonl"))
    ap.add_argument("--out", default=os.path.join(OWN, "results", "contamination_13.json"))
    args = ap.parse_args()
    if "/private/" not in os.path.abspath(args.private_out).replace(os.sep, "/"):
        sys.exit("per-unit output must stay under a git-ignored private/ path")
    t0 = time.time()

    sys.path.insert(0, os.path.join(BUK, "scripts"))
    import retrieval  # read-only use of Bukareszt's BM25 implementation

    raw = json.load(open(args.index, encoding="utf-8"))
    idx = retrieval.BM25Index.from_json(raw)
    chunks = idx.chunks
    items, units = load_units(args.prompts, args.min_excerpt_chars)

    cnorm = [norm(c["text"]) for c in chunks]
    chash = defaultdict(list)
    for i, t in enumerate(cnorm):
        chash[sha(t)].append(i)

    # inverted maps: unit n-gram -> unit indices; then one pass over chunks counts shared n-grams
    ugrams = {n: [grams(u["norm"], n) for u in units] for n in (8, 13)}
    inter = {n: [Counter() for _ in units] for n in (8, 13)}
    anywhere13 = [set() for _ in units]
    for n in (8, 13):
        inv = defaultdict(list)
        for ui, gs in enumerate(ugrams[n]):
            for g in gs:
                inv[g].append(ui)
        for ci, t in enumerate(cnorm):
            for g in grams(t, n):
                for ui in inv.get(g, ()):
                    inter[n][ui][ci] += 1
                    if n == 13:
                        anywhere13[ui].add(g)
    clen = {n: [max(0, len(t) - n + 1) for t in cnorm] for n in (8, 13)}  # upper bound on distinct grams

    csets_cache = {}

    def cgrams(ci, n):
        key = (ci, n)
        if key not in csets_cache:
            csets_cache[key] = len(grams(cnorm[ci], n))
        return csets_cache[key]

    rows = []
    for ui, u in enumerate(units):
        r = {"unit_id": u["unit_id"], "kind": u["kind"], "items": u["items"], "norm_chars": len(u["norm"]),
             "norm_sha256": sha(u["norm"])}
        r["exact_hash_chunks"] = [chunks[i]["chunk_id"] for i in chash.get(sha(u["norm"]), [])]
        r["substring_chunks"] = [chunks[i]["chunk_id"] for i, t in enumerate(cnorm)
                                 if len(t) >= 40 and (u["norm"] in t or t in u["norm"])]
        for n in (8, 13):
            un = len(ugrams[n][ui]) or 1
            best_c, best_j, best_ci, best_ji = 0.0, 0.0, None, None
            for ci, sh in inter[n][ui].items():
                c = sh / un
                j = sh / (un + cgrams(ci, n) - sh)
                if c > best_c:
                    best_c, best_ci = c, ci
                if j > best_j:
                    best_j, best_ji = j, ci
            r["c%d_max" % n] = round(best_c, 4)
            r["c%d_chunk" % n] = chunks[best_ci]["chunk_id"] if best_ci is not None else None
            r["c%d_shared" % n] = inter[n][ui][best_ci] if best_ci is not None else 0
            r["j%d_max" % n] = round(best_j, 4)
            r["j%d_chunk" % n] = chunks[best_ji]["chunk_id"] if best_ji is not None else None
        bc = r["c13_chunk"]
        if bc is None:
            r["lcs_chars"] = 0
        else:
            sm = SequenceMatcher(None, u["norm"], cnorm[[c["chunk_id"] for c in chunks].index(bc)], autojunk=False)
            r["lcs_chars"] = sm.find_longest_match(0, len(u["norm"]), 0, len(sm.b)).size
        r["c13_corpus"] = round(len(anywhere13[ui]) / (len(ugrams[13][ui]) or 1), 4)
        sc = idx.scores(u["norm"], title_weight=1.0)
        top = sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))[:args.k]
        un13 = len(ugrams[13][ui]) or 1
        r["bm25_top"] = [{"chunk_id": chunks[ci]["chunk_id"], "score": round(s, 3),
                          "c13": round(inter[13][ui].get(ci, 0) / un13, 4)} for ci, s in top]
        r["bm25_top_c13_max"] = max((t["c13"] for t in r["bm25_top"]), default=0.0)
        r["flag"] = bool(r["exact_hash_chunks"] or r["substring_chunks"] or r["c13_max"] >= args.flag
                         or r["lcs_chars"] >= args.flag_lcs)
        r["review"] = (not r["flag"]) and r["c13_max"] >= args.review
        rows.append(r)

    os.makedirs(os.path.dirname(args.private_out), exist_ok=True)
    with open(args.private_out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    by_id = {c["chunk_id"]: c for c in chunks}
    flagged = defaultdict(lambda: {"units": 0, "prompt_units": 0, "excerpt_units": 0, "max_c13": 0.0, "max_j13": 0.0,
                                   "max_c8": 0.0, "max_lcs_chars": 0, "exact_or_substring": False, "in_bm25_top5": False, "band": "review"})
    for r in rows:
        if not (r["flag"] or r["review"]):
            continue
        cid = r["c13_chunk"]
        f = flagged[cid]
        f["units"] += 1
        f["%s_units" % r["kind"]] += 1
        f["max_c13"] = max(f["max_c13"], r["c13_max"])
        f["max_j13"] = max(f["max_j13"], r["j13_max"] if r["j13_chunk"] == cid else 0.0)
        f["max_c8"] = max(f["max_c8"], r["c8_max"] if r["c8_chunk"] == cid else 0.0)
        f["max_lcs_chars"] = max(f["max_lcs_chars"], r["lcs_chars"])
        f["exact_or_substring"] |= bool(r["exact_hash_chunks"] or r["substring_chunks"])
        f["in_bm25_top5"] |= any(t["chunk_id"] == cid for t in r["bm25_top"])
        if r["flag"]:
            f["band"] = "flag"
    flag_list = [dict(chunk_id=cid, source_id=by_id[cid]["source_id"], section=by_id[cid]["section"], **v)
                 for cid, v in sorted(flagged.items(), key=lambda kv: (-kv[1]["max_c13"], kv[0]))]

    agg = {"issue": 13, "split": "VALIDATION (May 2024, aggregate only)",
           "inputs": {"prompts_sha256": sha_file(args.prompts), "index_sha256": sha_file(args.index),
                      "n_chunks": len(chunks), "n_sources": len({c["source_id"] for c in chunks}),
                      "n_items": len(items)},
           "params": {"normalization": "NFKC, lowercase, drop answer placeholders, punctuation->space, collapse ws",
                      "min_excerpt_chars": args.min_excerpt_chars, "ngrams": [8, 13], "bm25_k": args.k,
                      "bm25_title_weight": 1.0, "flag_c13": args.flag, "flag_lcs_chars": args.flag_lcs, "review_c13": args.review},
           "units": {k: sum(1 for r in rows if r["kind"] == k) for k in ("prompt", "excerpt")},
           "exact_hash_hits": sum(1 for r in rows if r["exact_hash_chunks"]),
           "substring_hits": sum(1 for r in rows if r["substring_chunks"]),
           "flagged_units": {k: sum(1 for r in rows if r["kind"] == k and r["flag"]) for k in ("prompt", "excerpt")},
           "review_units": {k: sum(1 for r in rows if r["kind"] == k and r["review"]) for k in ("prompt", "excerpt")},
           "distributions": {}, "histograms": {}, "flagged_chunks": flag_list, "runtime_s": None}
    for kind in ("prompt", "excerpt"):
        sub = [r for r in rows if r["kind"] == kind]
        for key in ("c13_max", "c8_max", "j13_max", "j8_max", "c13_corpus", "bm25_top_c13_max", "lcs_chars"):
            agg["distributions"]["%s.%s" % (kind, key)] = {k: round(v, 4) for k, v in quantiles([r[key] for r in sub]).items()}
        for key in ("c13_max", "c8_max", "c13_corpus", "bm25_top_c13_max"):
            agg["histograms"]["%s.%s" % (kind, key)] = hist([r[key] for r in sub])
    agg["runtime_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: agg[k] for k in ("units", "exact_hash_hits", "substring_hits", "flagged_units",
                                          "review_units", "runtime_s")}, ensure_ascii=False))
    print("flagged/review chunks:", len(flag_list))
    for f in flag_list:
        print("  %-6s %-45s c13=%.3f lcs=%d units=%d bm25top5=%s" % (f["band"], f["chunk_id"], f["max_c13"],
                                                                     f["max_lcs_chars"], f["units"], f["in_bm25_top5"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
