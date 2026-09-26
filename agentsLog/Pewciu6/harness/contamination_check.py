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

JSONL-corpus mode (PR #18 audit, additive): --corpus-jsonl FILE [FILE ...] replaces the BM25 index with training
examples (prompt + answer + evidence claims). Each record becomes one "all" chunk plus one chunk per field
(prompt, answer, claim<k>); BM25 (Bukareszt's BM25Index built in memory, title weight 0) ranks "all" chunks only.
Short training fields can sit inside a long VALIDATION prompt, so this mode adds reverse containment
|U & C| / |C| on 13-grams for chunks with >= --min-rev-chars normalized chars:
flag >= --flag-rev (0.50), review >= --review-rev (0.25). With --keys, it also compares training answers with the
VALIDATION reference answers (aggregate only; keys never leave private/).

  python3 agentsLog/Pewciu6/harness/contamination_check.py --corpus-jsonl data/.../train.jsonl ... \
      --keys agentsLog/Pewciu6/private/validation_2024/eval_keys.jsonl --out agentsLog/Pewciu6/results/x.json
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


def corpus_label(path, root, prefix):
    return prefix + os.path.relpath(os.path.abspath(path), os.path.abspath(root)).replace(os.sep, "/")


def load_jsonl_corpus(paths, root=REPO, prefix=""):
    """Training JSONL -> pseudo-chunks. chunk_id '<file>:<id>#<field>'; source_id carries the record key."""
    chunks, records = [], []
    for path in paths:
        rel = corpus_label(path, root, prefix)
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            key = "%s:%s" % (rel, rec.get("id"))
            fields = [("prompt", rec.get("prompt") or ""), ("answer", rec.get("answer") or "")]
            fields += [("claim%d" % k, (e or {}).get("claim") or "") for k, e in enumerate(rec.get("evidence") or [])]
            allt = "\n".join(t for _, t in fields if t)
            records.append({"record": key, "file": rel, "id": rec.get("id"), "answer": rec.get("answer") or "",
                            "prompt": rec.get("prompt") or "", "era": rec.get("era"), "topic": rec.get("topic")})
            for field, text in [("all", allt)] + fields:
                if text:
                    chunks.append({"chunk_id": "%s#%s" % (key, field), "source_id": key, "record_id": rec.get("id"),
                                   "file": rel, "section": field, "title": "", "text": text})
    return chunks, records


KEY_BOILER = {"rozstrzygnięcie", "przykładowe", "przykładowa", "przykładowy", "uzasadnienie", "odpowiedź", "odpowiedzi",
              "poprawna", "poprawne", "prawidłowa", "należy", "uznać", "również", "które", "który", "która", "oraz",
              "przez", "było", "została", "został", "zostały", "źródło", "źródła", "źródle", "tekst", "tekście"}


def salient(text):
    """Years and >= 5-letter words (5-char prefixes as a crude Polish stem), minus key boilerplate."""
    toks = re.findall(r"\w+", norm(text))
    return {t if t.isdigit() else t[:5] for t in toks
            if (t.isdigit() and 3 <= len(t) <= 4) or (len(t) >= 5 and not t.isdigit() and t not in KEY_BOILER)}


def answer_key_check(keys_path, items, records, bm25_idx, all_ids, chunks, args):
    """Train answers vs VALIDATION reference answers. Returns (aggregate, private rows)."""
    keys = {k["id"]: k for k in (json.loads(l) for l in open(keys_path, encoding="utf-8") if l.strip())}
    rec_by_key = {r["record"]: r for r in records}
    rnorm = {r["record"]: norm(r["answer"]) for r in records}
    rsal = {r["record"]: salient(r["answer"]) for r in records}
    r13 = {k: grams(v, 13) for k, v in rnorm.items()}
    prompts = {it["id"]: it["prompt"] for it in items}
    priv, lex_flag, lex_review, short_hits, fact_hits, eligible = [], {}, {}, {}, {}, 0
    n_long = n_short = n_tiny = 0
    for kid, k in sorted(keys.items()):
        kn = norm(k.get("reference_answer") or "")
        ksal = salient(k.get("reference_answer") or "")
        k13 = grams(kn, 13)
        sc = bm25_idx.scores(norm(prompts.get(kid, "")) + " " + kn, title_weight=0.0)
        top = sorted(((s, ci) for ci, s in sc.items() if ci in all_ids), key=lambda x: (-x[0], x[1]))[:args.topic_k]
        topic_rank = {chunks[ci]["source_id"]: rank + 1 for rank, (s, ci) in enumerate(top)}
        # lexical, 13-gram containment both ways over every training answer. Long keys (>= min_rev_chars) use the
        # prose-leak thresholds; short keys (13..min_rev_chars) are names/dates, counted as fact-level string matches.
        kind = "long" if len(kn) >= args.min_rev_chars else ("short" if k13 else "tiny")
        n_long += kind == "long"; n_short += kind == "short"; n_tiny += kind == "tiny"
        for rk, g in r13.items():
            if not g or not k13:
                continue
            sh = len(g & k13)
            if not sh:
                continue
            rev, fwd = sh / len(g), sh / len(k13)
            longa = len(rnorm[rk]) >= args.min_rev_chars
            if kind == "long" and ((longa and rev >= args.flag_rev) or fwd >= args.flag):
                lex_flag.setdefault(rk, []).append(round(max(rev, fwd), 4))
            elif kind == "long" and ((longa and rev >= args.review_rev) or fwd >= args.review):
                lex_review.setdefault(rk, []).append(round(max(rev, fwd), 4))
            elif kind == "short" and fwd >= args.short_key_frac:
                short_hits.setdefault(rk, []).append({"fwd": round(fwd, 4), "same_topic": rk in topic_rank})
            priv.append({"key_id": kid, "key_kind": kind, "record": rk, "rev_c13": round(rev, 4), "fwd_c13": round(fwd, 4),
                         "topic_rank": topic_rank.get(rk)})
        # same-topic fact match: training records in BM25 top-N for the VALIDATION prompt + key
        if len(ksal) < args.min_key_salient:
            continue
        eligible += 1
        for rank, (s, ci) in enumerate(top):
            rk = chunks[ci]["source_id"]
            m = len(ksal & rsal[rk])
            frac = m / len(ksal)
            if m >= args.min_key_salient and frac >= args.fact_frac:
                fact_hits.setdefault(rk, []).append({"frac": round(frac, 3), "matched": m, "bm25_rank": rank + 1})
                priv.append({"key_id": kid, "record": rk, "fact_frac": round(frac, 3), "fact_matched": m,
                             "bm25_rank": rank + 1})

    def ids(d):
        return sorted({rec_by_key[rk]["id"] for rk in d})

    def per_id(d, fn):
        out = defaultdict(lambda: {"files": set(), "score": 0.0, "n_keys": 0})
        for rk, v in d.items():
            o = out[rec_by_key[rk]["id"]]
            o["files"].add(rec_by_key[rk]["file"])
            o["score"] = max(o["score"], fn(v))
            o["n_keys"] = max(o["n_keys"], len(v))
        return [{"id": i, "files": sorted(o["files"]), "score": round(o["score"], 4), "n_keys": o["n_keys"]}
                for i, o in sorted(out.items(), key=lambda kv: (-kv[1]["score"], kv[0]))]

    agg = {"n_keys": len(keys), "keys_sha256": sha_file(keys_path),
           "params": {"lex_flag_rev_c13": args.flag_rev, "lex_flag_fwd_c13": args.flag, "lex_review_rev_c13": args.review_rev,
                      "lex_review_fwd_c13": args.review, "min_rev_chars": args.min_rev_chars,
                      "topic_proxy": "BM25 top-%d training records for the VALIDATION prompt + key" % args.topic_k,
                      "fact_frac": args.fact_frac, "min_key_salient": args.min_key_salient,
                      "salient": "years + >=5-letter words (5-char prefix), boilerplate removed"},
           "keys_by_length": {"long_ge_min_rev_chars": n_long, "short_13_to_min_rev_chars": n_short,
                              "tiny_lt_13_not_ngram_checked": n_tiny},
           "short_key_frac": args.short_key_frac,
           "short_key_match_records": len(short_hits), "short_key_match_unique_ids": len(ids(short_hits)),
           "short_key_match_keys": len({p["key_id"] for p in priv if p.get("key_kind") == "short" and p["fwd_c13"] >= args.short_key_frac}),
           "short_key_match_same_topic_unique_ids": len(ids({rk: v for rk, v in short_hits.items() if any(x["same_topic"] for x in v)})),
           "short_key_match_ids": per_id(short_hits, lambda v: max(x["fwd"] for x in v)),
           "lexical_flag_records": len(lex_flag), "lexical_flag_ids": per_id(lex_flag, max),
           "lexical_review_records": len(lex_review), "lexical_review_ids": per_id(lex_review, max),
           "keys_eligible_for_fact_match": eligible,
           "fact_match_records": len(fact_hits), "fact_match_unique_ids": len(ids(fact_hits)),
           "fact_match_keys": len({p["key_id"] for p in priv if "fact_frac" in p}),
           "fact_match_ids": per_id(fact_hits, lambda v: max(x["frac"] for x in v))}
    return agg, priv


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
    ap.add_argument("--corpus-jsonl", nargs="+", help="training JSONL files used as the corpus instead of --index")
    ap.add_argument("--corpus-root", default=REPO, help="corpus file labels are relative to this dir")
    ap.add_argument("--corpus-prefix", default="", help="prepended to corpus file labels (e.g. the PR's data path)")
    ap.add_argument("--min-rev-chars", type=int, default=60)
    ap.add_argument("--flag-rev", type=float, default=0.50)
    ap.add_argument("--review-rev", type=float, default=0.25)
    ap.add_argument("--keys", help="VALIDATION eval_keys.jsonl for the answer-key check (JSONL mode only)")
    ap.add_argument("--topic-k", type=int, default=10)
    ap.add_argument("--short-key-frac", type=float, default=0.5)
    ap.add_argument("--fact-frac", type=float, default=0.5)
    ap.add_argument("--min-key-salient", type=int, default=3)
    ap.add_argument("--issue", default="13")
    args = ap.parse_args()
    if "/private/" not in os.path.abspath(args.private_out).replace(os.sep, "/"):
        sys.exit("per-unit output must stay under a git-ignored private/ path")
    t0 = time.time()

    sys.path.insert(0, os.path.join(BUK, "scripts"))
    import retrieval  # read-only use of Bukareszt's BM25 implementation

    jsonl = bool(args.corpus_jsonl)
    if jsonl:
        chunks, records = load_jsonl_corpus(args.corpus_jsonl, args.corpus_root, args.corpus_prefix)
        idx = retrieval.BM25Index(chunks)
        tw = 0.0
    else:
        raw = json.load(open(args.index, encoding="utf-8"))
        idx = retrieval.BM25Index.from_json(raw)
        chunks, records, tw = idx.chunks, [], 1.0
    all_ids = {i for i, c in enumerate(chunks) if c.get("section") == "all"} if jsonl else None
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
        best_rc, best_rci = 0.0, None
        for ci, sh in inter[13][ui].items():
            cg = cgrams(ci, 13)
            if len(cnorm[ci]) >= args.min_rev_chars and cg and sh / cg > best_rc:
                best_rc, best_rci = sh / cg, ci
        if jsonl:  # every chunk over a threshold, not only the best one, so one strong record cannot mask another
            ex = set(r["exact_hash_chunks"]) | set(r["substring_chunks"])
            un13 = len(ugrams[13][ui]) or 1
            sc_by = {}
            for ci, sh in inter[13][ui].items():
                c, rc = sh / un13, (sh / (cgrams(ci, 13) or 1) if len(cnorm[ci]) >= args.min_rev_chars else 0.0)
                if c >= args.review or rc >= args.review_rev:
                    sc_by[chunks[ci]["chunk_id"]] = (round(c, 4), round(rc, 4))
            for cid in ex:
                sc_by.setdefault(cid, (0.0, 0.0))
            r["hit_scores"] = sc_by
            r["hit_chunks"] = sorted(sc_by)
            r["hit_flag_chunks"] = sorted(cid for cid, (c, rc) in sc_by.items()
                                          if c >= args.flag or rc >= args.flag_rev or cid in ex)
        r["rc13_max"] = round(best_rc, 4)
        r["rc13_chunk"] = chunks[best_rci]["chunk_id"] if best_rci is not None else None
        bc = r["c13_chunk"]
        if bc is None:
            r["lcs_chars"] = 0
        else:
            sm = SequenceMatcher(None, u["norm"], cnorm[[c["chunk_id"] for c in chunks].index(bc)], autojunk=False)
            r["lcs_chars"] = sm.find_longest_match(0, len(u["norm"]), 0, len(sm.b)).size
        r["c13_corpus"] = round(len(anywhere13[ui]) / (len(ugrams[13][ui]) or 1), 4)
        sc = idx.scores(u["norm"], title_weight=tw)
        top = sorted(((ci, s) for ci, s in sc.items() if all_ids is None or ci in all_ids),
                     key=lambda kv: (-kv[1], kv[0]))[:args.k]
        un13 = len(ugrams[13][ui]) or 1
        r["bm25_top"] = [{"chunk_id": chunks[ci]["chunk_id"], "score": round(s, 3),
                          "c13": round(inter[13][ui].get(ci, 0) / un13, 4)} for ci, s in top]
        r["bm25_top_c13_max"] = max((t["c13"] for t in r["bm25_top"]), default=0.0)
        r["flag"] = bool(r["exact_hash_chunks"] or r["substring_chunks"] or r["c13_max"] >= args.flag
                         or r["lcs_chars"] >= args.flag_lcs or (jsonl and r["rc13_max"] >= args.flag_rev))
        r["review"] = (not r["flag"]) and (r["c13_max"] >= args.review or (jsonl and r["rc13_max"] >= args.review_rev))
        rows.append(r)

    os.makedirs(os.path.dirname(args.private_out), exist_ok=True)
    with open(args.private_out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    by_id = {c["chunk_id"]: c for c in chunks}
    flagged = defaultdict(lambda: {"units": 0, "prompt_units": 0, "excerpt_units": 0, "max_c13": 0.0, "max_j13": 0.0,
                                   "max_c8": 0.0, "max_lcs_chars": 0, "exact_or_substring": False, "in_bm25_top5": False, "band": "review"})
    hits = []
    for r in rows:
        if not (r["flag"] or r["review"]):
            continue
        if jsonl:
            hits.extend((r, cid) for cid in r["hit_chunks"])
            if not r["hit_chunks"]:  # LCS-only flag
                hits.append((r, r["c13_chunk"]))
        else:
            hits.append((r, r["c13_chunk"]))
    for r, cid in hits:
        f = flagged[cid]
        f["units"] += 1
        f["%s_units" % r["kind"]] += 1
        c_rc = r["hit_scores"].get(cid, (0.0, 0.0)) if jsonl else (r["c13_max"], 0.0)
        f["max_c13"] = max(f["max_c13"], c_rc[0] if jsonl else r["c13_max"])
        f["max_j13"] = max(f["max_j13"], r["j13_max"] if r["j13_chunk"] == cid else 0.0)
        f["max_c8"] = max(f["max_c8"], r["c8_max"] if r["c8_chunk"] == cid else 0.0)
        f["max_lcs_chars"] = max(f["max_lcs_chars"], r["lcs_chars"] if r["c13_chunk"] == cid else 0)
        f["max_rc13"] = max(f.get("max_rc13", 0.0), c_rc[1])
        f["exact_or_substring"] |= (cid in r["exact_hash_chunks"] or cid in r["substring_chunks"]) if jsonl else \
            bool(r["exact_hash_chunks"] or r["substring_chunks"])
        f["in_bm25_top5"] |= any(t["chunk_id"] == cid for t in r["bm25_top"])
        lcs_flag = cid == r["c13_chunk"] and r["lcs_chars"] >= args.flag_lcs
        if (cid in r["hit_flag_chunks"] or lcs_flag) if jsonl else r["flag"]:
            f["band"] = "flag"
    flag_list = [dict(chunk_id=cid, source_id=by_id[cid]["source_id"], section=by_id[cid]["section"], **v)
                 for cid, v in sorted(flagged.items(), key=lambda kv: (-kv[1]["max_c13"], kv[0]))]

    agg = {"issue": args.issue, "corpus": "jsonl" if jsonl else "bm25_index", "split": "VALIDATION (May 2024, aggregate only)",
           "inputs": {"prompts_sha256": sha_file(args.prompts),
                      "index_sha256": None if jsonl else sha_file(args.index),
                      "corpus_jsonl": [{"path": lab, "sha256": sha_file(p), "records": sum(1 for x in records if x["file"] == lab)}
                                       for p, lab in ((p, corpus_label(p, args.corpus_root, args.corpus_prefix))
                                                      for p in args.corpus_jsonl)] if jsonl else None,
                      "n_chunks": len(chunks), "n_sources": len({c["source_id"] for c in chunks}),
                      "n_items": len(items)},
           "params": {"normalization": "NFKC, lowercase, drop answer placeholders, punctuation->space, collapse ws",
                      "min_excerpt_chars": args.min_excerpt_chars, "ngrams": [8, 13], "bm25_k": args.k,
                      "bm25_title_weight": tw, "flag_c13": args.flag,
                      "flag_rev_c13": args.flag_rev if jsonl else None, "review_rev_c13": args.review_rev if jsonl else None,
                      "min_rev_chars": args.min_rev_chars if jsonl else None, "flag_lcs_chars": args.flag_lcs, "review_c13": args.review},
           "units": {k: sum(1 for r in rows if r["kind"] == k) for k in ("prompt", "excerpt")},
           "exact_hash_hits": sum(1 for r in rows if r["exact_hash_chunks"]),
           "substring_hits": sum(1 for r in rows if r["substring_chunks"]),
           "flagged_units": {k: sum(1 for r in rows if r["kind"] == k and r["flag"]) for k in ("prompt", "excerpt")},
           "review_units": {k: sum(1 for r in rows if r["kind"] == k and r["review"]) for k in ("prompt", "excerpt")},
           "distributions": {}, "histograms": {}, "flagged_chunks": flag_list, "runtime_s": None}
    for kind in ("prompt", "excerpt"):
        sub = [r for r in rows if r["kind"] == kind]
        for key in ("c13_max", "c8_max", "j13_max", "j8_max", "c13_corpus", "bm25_top_c13_max", "lcs_chars", "rc13_max"):
            agg["distributions"]["%s.%s" % (kind, key)] = {k: round(v, 4) for k, v in quantiles([r[key] for r in sub]).items()}
        for key in ("c13_max", "c8_max", "c13_corpus", "bm25_top_c13_max", "rc13_max"):
            agg["histograms"]["%s.%s" % (kind, key)] = hist([r[key] for r in sub])
    if jsonl:
        recs = defaultdict(lambda: {"files": set(), "fields": set(), "band": "review", "max_c13": 0.0, "max_rc13": 0.0,
                                    "max_lcs_chars": 0, "units": 0, "exact_or_substring": False})
        for f in flag_list:
            c = by_id[f["chunk_id"]]
            o = recs[c["record_id"]]
            o["files"].add(c["file"]); o["fields"].add(c["section"]); o["units"] += f["units"]
            for k in ("max_c13", "max_rc13", "max_lcs_chars"):
                o[k] = max(o[k], f.get(k, 0))
            o["exact_or_substring"] |= f["exact_or_substring"]
            if f["band"] == "flag":
                o["band"] = "flag"
        agg["corpus_records"] = len(records)
        agg["corpus_unique_ids"] = len({r["id"] for r in records})
        agg["corpus_chunks"] = {k: sum(1 for c in chunks if c["section"].rstrip("0123456789") == k) for k in ("all", "prompt", "answer", "claim")}
        agg["flagged_records"] = [dict(id=i, files=sorted(v["files"]), fields=sorted(v["fields"]),
                                       **{k: v[k] for k in ("band", "max_c13", "max_rc13", "max_lcs_chars", "units", "exact_or_substring")})
                                  for i, v in sorted(recs.items(), key=lambda kv: (kv[1]["band"] != "flag", -kv[1]["max_c13"] - kv[1]["max_rc13"], kv[0]))]
        for f in agg["flagged_chunks"]:  # record keys, not exam text; drop the repo-path prefix noise
            f["source_id"] = by_id[f["chunk_id"]]["record_id"]
        if args.keys:
            akagg, akpriv = answer_key_check(args.keys, items, records, idx, all_ids, chunks, args)
            agg["answer_key"] = akagg
            with open(os.path.join(os.path.dirname(args.private_out), "answer_key_matches.jsonl"), "w", encoding="utf-8") as fh:
                for p in akpriv:
                    fh.write(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n")
    agg["runtime_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: agg[k] for k in ("units", "exact_hash_hits", "substring_hits", "flagged_units",
                                          "review_units", "runtime_s")}, ensure_ascii=False))
    if jsonl:
        print("flagged/review records:", len(agg["flagged_records"]),
              [(f["id"], f["band"], f["max_c13"], f["max_rc13"]) for f in agg["flagged_records"]][:30])
        if "answer_key" in agg:
            print("answer_key:", json.dumps({k: v for k, v in agg["answer_key"].items() if not k.endswith("_ids")}, ensure_ascii=False))
    print("flagged/review chunks:", len(flag_list))
    for f in flag_list:
        print("  %-6s %-45s c13=%.3f lcs=%d units=%d bm25top5=%s" % (f["band"], f["chunk_id"], f["max_c13"],
                                                                     f["max_lcs_chars"], f["units"], f["in_bm25_top5"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
