#!/usr/bin/env python3
"""Context selection for complete answer support (issue #15, @Bukareszt).

Additive, standalone candidate on top of the frozen #6 retrieval (`retrieval.py`, mode chrono).
It does NOT change the corpus, the index, the graph or the 40 TRAIN queries; it only re-selects
which chunks (and optionally which sentences) go into the answerer's context.

Baseline  = `retrieval.rank(..., mode="chrono")` top-k chunks, full text (what #6 audited and what
            scripts/prepare_rag.py consumes).
Candidate = section-aware re-ranking of a chrono candidate pool + budgeted multi-chunk assembly:
            score = wa * article prior (best chrono score of the chunk's article)
                  + wr * residual content BM25 (query terms minus the article-title terms)
                  + wc * non-title query-term coverage of the chunk
            then greedy assembly under a character budget with at most `per_article` chunks per
            article, and an optional evidence-retaining sentence compression (`--compress`).

Subcommands
  select        one query -> context (baseline or candidate), JSON or text
  eval          automatic proxies on the 40 TRAIN queries for baseline and candidate variants
  audit-sample  blind A/B pairs (baseline vs candidate context) for an independent auditor
  audit-score   un-blind auditor verdicts and compute complete-answer-support numbers

Examples
  python3 agentsLog/Bukareszt/scripts/context_select.py select "Kiedy zawarto unię lubelską?" --variant candidate
  python3 agentsLog/Bukareszt/scripts/context_select.py eval
  python3 agentsLog/Bukareszt/scripts/context_select.py audit-sample --tag ctx15
  python3 agentsLog/Bukareszt/scripts/context_select.py audit-score --tag ctx15
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import retrieval as rt  # noqa: E402  (frozen #6 implementation; imported, not modified)

ROOT = rt.ROOT
REPORTS_DIR = rt.REPORTS_DIR
AUDIT_DIR = rt.AUDIT_DIR

# ----------------------------------------------------------------------------------------------
# variants (frozen after the first eval; see reports/REPORT_15.md for the tiny sweep that chose them)
# ----------------------------------------------------------------------------------------------
VARIANTS: dict[str, dict] = {
    # baseline: exactly the #6 recommendation, top-k chrono chunks, full text
    "baseline3": {"kind": "baseline", "k": 3},
    "baseline5": {"kind": "baseline", "k": 5},
    # candidate: section-aware re-rank + budgeted assembly (budget ~ 3 full chunks)
    "candidate": {"kind": "candidate", "pool": 40, "wa": 0.6, "wr": 0.5, "wc": 0.3, "anchor": True,
                  "budget": 3000, "per_article": 3, "max_chunks": 6, "compress": False},
    # same selection, sentence compression that keeps query-term / year sentences (+ chunk lead sentence)
    "candidate_c": {"kind": "candidate", "pool": 40, "wa": 0.6, "wr": 0.5, "wc": 0.3, "anchor": True,
                    "budget": 3000, "per_article": 3, "max_chunks": 8, "compress": True},
    # UNAUDITED (added after the blind audit sample was frozen): same as candidate, but a chunk is only added
    # when its article prior is >= min_article (drops "filler" chunks from distant articles)
    "candidate_t": {"kind": "candidate", "pool": 40, "wa": 0.6, "wr": 0.5, "wc": 0.3, "anchor": True,
                    "budget": 3000, "per_article": 3, "max_chunks": 6, "compress": False, "min_article": 0.5},
}

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9„(])")


def _sha(path: str) -> str:
    return rt.sha256_file(path)


def _title_tokens(idx: rt.BM25Index) -> dict[str, set[str]]:
    return {sid: set(rt.tokenize(t)) for sid, t in {c["source_id"]: c["title"] for c in idx.chunks}.items()}


def compress_chunk(text: str, qtoks: set[str], min_keep: int = 1) -> str:
    """Evidence-retaining compression: keep sentences with a query token or a year, plus the
    chunk's first sentence; drop the rest. Never returns an empty string."""
    sents = [s.strip() for s in _SENT_RE.split(text.replace("\n", " ")) if s.strip()]
    if len(sents) <= 2:
        return text
    keep = []
    for j, s in enumerate(sents):
        stoks = set(rt.tokenize(s))
        if j == 0 or (stoks & qtoks) or rt._YEAR_RE.search(s):
            keep.append(j)
    if len(keep) < min_keep:
        keep = [0]
    out, prev = [], None
    for j in keep:
        if prev is not None and j != prev + 1:
            out.append("[…]")
        out.append(sents[j])
        prev = j
    return " ".join(out)


def select(idx: rt.BM25Index, graph: dict, query: str, variant: str = "candidate",
           title_weight: float = 1.0) -> dict:
    """Return {"variant", "chunks": [hit...], "chars", "n_chunks", "n_articles", "ms"}.
    Each hit has the retrieval.rank shape (rank, score, chunk_id, source_id, title, locator, text)
    so scripts/prepare_rag.py-style consumers can use it unchanged; `text_full` keeps the
    uncompressed chunk when compression is on."""
    cfg = VARIANTS[variant]
    t0 = time.time()
    if cfg["kind"] == "baseline":
        hits = rt.rank(idx, query, cfg["k"], "chrono", graph, title_weight)
        for h in hits:
            h["why"] = "chrono top-k"
    else:
        pool = rt.rank(idx, query, cfg["pool"], "chrono", graph, title_weight)
        if not pool:
            hits = []
        else:
            top = pool[0]["score"] or 1.0
            by_id = {c["chunk_id"]: i for i, c in enumerate(idx.chunks)}
            qcount = Counter(rt.tokenize(query))
            qtoks = set(qcount)
            ttoks = _title_tokens(idx)
            # article prior: best chrono score of the article, normalised (decides ACROSS articles)
            art: dict[str, float] = defaultdict(float)
            for h in pool:
                art[h["source_id"]] = max(art[h["source_id"]], h["score"] / top)
            # within-article section score: residual content BM25 (query minus the article's own title
            # terms, normalised inside the article) + non-title query-term coverage + a little chrono score
            resid_cache: dict[str, dict[int, float]] = {}
            per_art_rows: dict[str, list] = defaultdict(list)
            for h in pool:
                sid = h["source_id"]
                i = by_id[h["chunk_id"]]
                if sid not in resid_cache:
                    residual = Counter({t: c for t, c in qcount.items() if t not in ttoks[sid]}) or qcount
                    resid_cache[sid] = idx._field_scores(residual, idx.postings, idx.doc_len, idx.avgdl)
                r = resid_cache[sid].get(i, 0.0)
                ctoks = set(rt.tokenize(h["text"]))
                non_title = qtoks - ttoks[sid]
                cov = (len(non_title & ctoks) / len(non_title)) if non_title else (len(qtoks & ctoks) / max(1, len(qtoks)))
                per_art_rows[sid].append([h, r, cov])
            ranked = []
            for sid, rows in per_art_rows.items():
                rmax = max(r for _, r, _ in rows) or 1.0
                for h, r, cov in rows:
                    within = cfg["wr"] * (r / rmax) + cfg["wc"] * cov + (1 - cfg["wr"] - cfg["wc"]) * (h["score"] / top)
                    s = cfg["wa"] * art[sid] + (1 - cfg["wa"]) * within
                    ranked.append((s, art[sid], r / rmax, cov, h))
            ranked.sort(key=lambda x: -x[0])
            if cfg.get("anchor", True):  # chrono top-1 always leads: no regression at rank 1 vs baseline
                j = next(n for n, x in enumerate(ranked) if x[4]["chunk_id"] == pool[0]["chunk_id"])
                ranked.insert(0, ranked.pop(j))
            # greedy budgeted assembly
            hits, used, per_art = [], 0, Counter()
            for s, a, r, cov, h in ranked:
                if len(hits) >= cfg["max_chunks"]:
                    break
                if per_art[h["source_id"]] >= cfg["per_article"]:
                    continue
                if hits and a < cfg.get("min_article", 0.0):
                    continue
                text = compress_chunk(h["text"], qtoks) if cfg["compress"] else h["text"]
                if hits and used + len(text) > cfg["budget"]:
                    continue
                hh = dict(h)
                hh.update(score=round(s, 4), text=text, text_full=h["text"],
                          why=f"article={a:.2f} residual={r:.2f} coverage={cov:.2f} chrono_rank={h['rank']}")
                hits.append(hh)
                used += len(text)
                per_art[h["source_id"]] += 1
            for n, h in enumerate(hits, 1):
                h["rank"] = n
    return {"variant": variant, "chunks": hits, "chars": sum(len(h["text"]) for h in hits),
            "n_chunks": len(hits), "n_articles": len({h["source_id"] for h in hits}),
            "ms": round((time.time() - t0) * 1000, 1)}


# ----------------------------------------------------------------------------------------------
# automatic proxies (TRAIN only; they accept any chunk of the expected section, so they overstate)
# ----------------------------------------------------------------------------------------------

def auto_metrics(ctx: dict, q: dict) -> dict:
    text = rt._norm(" ".join(h["text"] for h in ctx["chunks"]))
    ev_ranks = [h["rank"] for h in ctx["chunks"] if rt.evidence_hit(h, q)]
    must = q.get("must_contain", [])
    return {
        "evidence_in_context": bool(ev_ranks),
        "first_evidence_rank": ev_ranks[0] if ev_ranks else None,
        "must_contain_all": all(rt._norm(m) in text for m in must) if must else None,
        "expected_source_in_context": any(h["source_id"] in q["expected_source_ids"] for h in ctx["chunks"]),
        "chars": ctx["chars"], "n_chunks": ctx["n_chunks"], "n_articles": ctx["n_articles"], "ms": ctx["ms"],
    }


def cmd_eval(args) -> None:
    idx, graph = rt.load_index(), rt.load_graph()
    queries = rt.read_jsonl(args.queries)
    meta = json.load(open(os.path.join(REPORTS_DIR, "index_meta.json"), encoding="utf-8"))
    variants = args.variants.split(",")
    summary = {"evaluated_at": rt.now_iso(), "queries_file": os.path.relpath(args.queries, ROOT),
               "queries_sha256": _sha(args.queries), "index_sha256": meta["index_sha256"],
               "n_chunks": meta["n_chunks"], "n_sources": meta["n_sources"], "variants": {}}
    per_query_rows = []
    for v in variants:
        rows = []
        for q in queries:
            ctx = select(idx, graph, q["prompt"], v, args.title_weight)
            m = auto_metrics(ctx, q)
            m.update(id=q["id"], variant=v, chunk_ids=[h["chunk_id"] for h in ctx["chunks"]])
            rows.append(m)
        n = len(rows)
        agg = {
            "config": VARIANTS[v], "n_queries": n,
            "evidence_in_context": sum(r["evidence_in_context"] for r in rows) / n,
            "must_contain_all": sum(bool(r["must_contain_all"]) for r in rows) / n,
            "expected_source_in_context": sum(r["expected_source_in_context"] for r in rows) / n,
            "mrr_evidence": sum(1 / r["first_evidence_rank"] for r in rows if r["first_evidence_rank"]) / n,
            "mean_chars": sum(r["chars"] for r in rows) / n, "max_chars": max(r["chars"] for r in rows),
            "mean_chunks": sum(r["n_chunks"] for r in rows) / n, "mean_articles": sum(r["n_articles"] for r in rows) / n,
            "mean_ms": sum(r["ms"] for r in rows) / n,
            "evidence_miss_ids": [r["id"] for r in rows if not r["evidence_in_context"]],
        }
        agg = {k: (round(x, 3) if isinstance(x, float) else x) for k, x in agg.items()}
        summary["variants"][v] = agg
        per_query_rows.extend(rows)
        print(f"[{v:<12}] evidence_in_ctx={agg['evidence_in_context']:.3f} must_all={agg['must_contain_all']:.3f} "
              f"src={agg['expected_source_in_context']:.3f} MRR(ev)={agg['mrr_evidence']:.3f} "
              f"chars={agg['mean_chars']:.0f} (max {agg['max_chars']}) chunks={agg['mean_chunks']:.2f} "
              f"articles={agg['mean_articles']:.2f} {agg['mean_ms']:.1f} ms/q  miss={agg['evidence_miss_ids']}")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out = os.path.join(REPORTS_DIR, f"ctx_eval_{args.tag}.json")
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rt.write_jsonl(os.path.join(REPORTS_DIR, f"ctx_eval_per_query_{args.tag}.jsonl"), per_query_rows)
    print(f"-> {out}")


# ----------------------------------------------------------------------------------------------
# blind A/B audit sample + scoring
# ----------------------------------------------------------------------------------------------

AUDITOR_INSTRUCTIONS = (
    "You see a question, a claimed answer, and two candidate contexts A and B (each a list of passages). "
    "Judge ONLY from the passage text; do not use your own knowledge to fill gaps. For EACH context decide "
    "support = complete (every factual element of the claim can be confirmed from the passages, possibly "
    "combining several passages) | partial (some elements confirmed, some missing) | none (nothing usable). "
    "List the claim elements that are NOT supported in `unsupported_claims`. Flag `contradiction` if a passage "
    "contradicts the claim. Then set `preferred` = A | B | tie for which context would let a careful reader "
    "answer the question better. Do not guess which context is the baseline."
)


def cmd_audit_sample(args) -> None:
    idx, graph = rt.load_index(), rt.load_graph()
    queries = rt.read_jsonl(args.queries)
    rng = random.Random(args.seed)
    rows, key = [], []
    for q in queries:
        base = select(idx, graph, q["prompt"], args.baseline, args.title_weight)
        cand = select(idx, graph, q["prompt"], args.candidate, args.title_weight)
        swap = rng.random() < 0.5
        a, b = (cand, base) if swap else (base, cand)
        def _p(ctx):
            return [{"rank": h["rank"], "chunk_id": h["chunk_id"], "source_id": h["source_id"], "title": h["title"],
                     "locator": h["locator"], "text": h["text"]} for h in ctx["chunks"]]
        rows.append({"id": q["id"], "prompt": q["prompt"], "claim": q["answer"],
                     "context_A": _p(a), "context_B": _p(b), "auditor_instructions": AUDITOR_INSTRUCTIONS})
        key.append({"id": q["id"], "A": a["variant"], "B": b["variant"],
                    "A_chars": a["chars"], "B_chars": b["chars"]})
    os.makedirs(AUDIT_DIR, exist_ok=True)
    out = os.path.join(AUDIT_DIR, f"ctx_audit_sample_{args.tag}.jsonl")
    rt.write_jsonl(out, rows)
    kout = os.path.join(AUDIT_DIR, f"ctx_audit_key_{args.tag}.json")
    json.dump({"seed": args.seed, "baseline": args.baseline, "candidate": args.candidate,
               "queries_sha256": _sha(args.queries), "sample_sha256": _sha(out), "pairs": key},
              open(kout, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"blind audit sample: {len(rows)} queries ({args.baseline} vs {args.candidate}) -> {out}\nkey (do not show to auditor) -> {kout}")


def cmd_audit_score(args) -> None:
    key = json.load(open(os.path.join(AUDIT_DIR, f"ctx_audit_key_{args.tag}.json"), encoding="utf-8"))
    vpath = args.verdicts or os.path.join(AUDIT_DIR, f"ctx_audit_verdicts_{args.tag}.jsonl")
    verdicts = {v["id"]: v for v in rt.read_jsonl(vpath)}
    base_name, cand_name = key["baseline"], key["candidate"]
    counts = {base_name: Counter(), cand_name: Counter()}
    pref = Counter()
    wins, regressions, contradictions, unsupported = [], [], [], []
    order = {"none": 0, "partial": 1, "complete": 2}
    n = 0
    for p in key["pairs"]:
        v = verdicts.get(p["id"])
        if not v:
            continue
        n += 1
        side = {p["A"]: v["A"], p["B"]: v["B"]}
        for name, jv in side.items():
            counts[name][jv["support"]] += 1
            for u in jv.get("unsupported_claims", []) or []:
                unsupported.append({"id": p["id"], "variant": name, "claim_element": u})
            if jv.get("contradiction"):
                contradictions.append({"id": p["id"], "variant": name, "note": jv.get("note", "")})
        pv = v.get("preferred", "tie")
        pref[p.get(pv, "tie") if pv in ("A", "B") else "tie"] += 1
        d = order[side[cand_name]["support"]] - order[side[base_name]["support"]]
        rec = {"id": p["id"], "baseline": side[base_name]["support"], "candidate": side[cand_name]["support"],
               "note": side[cand_name].get("note", "")}
        if d > 0:
            wins.append(rec)
        elif d < 0:
            regressions.append(rec)
    report = {
        "status": "provisional", "tag": args.tag, "n_queries": n,
        "auditor": next(iter(verdicts.values())).get("auditor", "unknown") if verdicts else "unknown",
        "baseline": base_name, "candidate": cand_name,
        "complete": {k: c["complete"] for k, c in counts.items()},
        "complete_or_partial": {k: c["complete"] + c["partial"] for k, c in counts.items()},
        "none": {k: c["none"] for k, c in counts.items()},
        "counts": {k: dict(c) for k, c in counts.items()},
        "preferred": dict(pref), "wins": wins, "regressions": regressions,
        "contradictions": contradictions, "unsupported_claims": unsupported,
        "verdicts_file": os.path.relpath(vpath, ROOT), "verdicts_sha256": _sha(vpath),
        "sample_sha256": key["sample_sha256"], "queries_sha256": key["queries_sha256"],
    }
    out = os.path.join(REPORTS_DIR, f"ctx_audit_score_{args.tag}.json")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k not in ("unsupported_claims", "wins", "regressions")},
                     ensure_ascii=False, indent=2))
    print(f"wins={len(wins)} {[w['id'] for w in wins]}\nregressions={len(regressions)} {[r['id'] for r in regressions]}\n-> {out}")


def cmd_select(args) -> None:
    idx, graph = rt.load_index(), rt.load_graph()
    ctx = select(idx, graph, args.text, args.variant, args.title_weight)
    if args.json:
        print(json.dumps(ctx, ensure_ascii=False, indent=2))
        return
    print(f"[{ctx['variant']}] {ctx['n_chunks']} chunks, {ctx['n_articles']} articles, {ctx['chars']} chars, {ctx['ms']} ms")
    for h in ctx["chunks"]:
        snippet = re.sub(r"\s+", " ", h["text"])[: args.snippet]
        print(f"{h['rank']:>2}. {h['score']:7.3f}  {h['source_id']}  [{h['locator']}]  ({h.get('why', '')})\n    {snippet}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("select"); p.add_argument("text"); p.add_argument("--variant", default="candidate", choices=VARIANTS)
    p.add_argument("--title-weight", type=float, default=1.0); p.add_argument("--json", action="store_true")
    p.add_argument("--snippet", type=int, default=220); p.set_defaults(fn=cmd_select)
    p = sub.add_parser("eval"); p.add_argument("--queries", default=rt.QUERIES_FILE)
    p.add_argument("--variants", default=",".join(VARIANTS)); p.add_argument("--title-weight", type=float, default=1.0)
    p.add_argument("--tag", default="ctx15"); p.set_defaults(fn=cmd_eval)
    p = sub.add_parser("audit-sample"); p.add_argument("--queries", default=rt.QUERIES_FILE)
    p.add_argument("--baseline", default="baseline3", choices=VARIANTS); p.add_argument("--candidate", default="candidate", choices=VARIANTS)
    p.add_argument("--seed", type=int, default=15); p.add_argument("--title-weight", type=float, default=1.0)
    p.add_argument("--tag", default="ctx15"); p.set_defaults(fn=cmd_audit_sample)
    p = sub.add_parser("audit-score"); p.add_argument("--tag", default="ctx15"); p.add_argument("--verdicts", default=None)
    p.set_defaults(fn=cmd_audit_score)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
