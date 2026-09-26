#!/usr/bin/env python3
"""Licensed offline historical retrieval (BM25) for the Polish history matura assistant.

Standalone, stdlib-only except `requests` for the fetch step (`pip install requests`).
Owner: @Bukareszt (issue #6). Everything lives under agentsLog/Bukareszt/.

Subcommands
  fetch          download Polish Wikipedia / Wikisource sources listed in sources/source_list.json,
                 write raw text to raw/ (gitignored) and the contract manifest sources.jsonl
  index          chunk raw text by section, build the BM25 index in index/ (gitignored) + index hash
  query          run one query against the index (BM25 by default; --mode hybrid|chrono for stretch)
  eval           run queries/train_queries.jsonl, compute top-k coverage, write reports/
  audit-sample   materialise the top-1 evidence for an independent audit (audit/audit_sample.jsonl)
  audit-score    compute citation precision from audit/audit_verdicts.jsonl
  graph          build a simple year/entity graph over chunks (index/graph.json, stretch)

Examples
  python3 agentsLog/Bukareszt/scripts/retrieval.py fetch
  python3 agentsLog/Bukareszt/scripts/retrieval.py index
  python3 agentsLog/Bukareszt/scripts/retrieval.py query "Kiedy zawarto unię lubelską?" --k 5
  python3 agentsLog/Bukareszt/scripts/retrieval.py eval --k 10
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # agentsLog/Bukareszt
SOURCE_LIST = os.path.join(ROOT, "sources", "source_list.json")
SOURCES_JSONL = os.path.join(ROOT, "sources", "sources.jsonl")
RAW_DIR = os.path.join(ROOT, "raw")
INDEX_DIR = os.path.join(ROOT, "index")
INDEX_FILE = os.path.join(INDEX_DIR, "bm25_index.json")
GRAPH_FILE = os.path.join(INDEX_DIR, "graph.json")
QUERIES_FILE = os.path.join(ROOT, "queries", "train_queries.jsonl")
REPORTS_DIR = os.path.join(ROOT, "reports")
AUDIT_DIR = os.path.join(ROOT, "audit")

MODES = ["bm25", "hybrid", "chrono", "twostage"]
USER_AGENT = "machinekind-matura-retrieval/0.1 (overnight hackathon; contact: piotrowskigrzegorz2000@gmail.com)"
API = {
    "wikipedia_pl": "https://pl.wikipedia.org/w/api.php",
    "wikisource_pl": "https://pl.wikisource.org/w/api.php",
}
PAGE_URL = {
    "wikipedia_pl": "https://pl.wikipedia.org/wiki/{title}",
    "wikisource_pl": "https://pl.wikisource.org/wiki/{title}",
}
PERMALINK = {
    "wikipedia_pl": "https://pl.wikipedia.org/w/index.php?title={title}&oldid={revid}",
    "wikisource_pl": "https://pl.wikisource.org/w/index.php?title={title}&oldid={revid}",
}

# Sections of Polish Wikipedia articles that are navigation/bibliography, not evidence.
DROP_SECTIONS = {
    "przypisy", "bibliografia", "linki zewnętrzne", "zobacz też", "uwagi", "literatura",
    "źródła", "zobacz również", "galeria", "filmografia", "dyskografia",
}

# Small Polish + English stoplist (function words only; keeps years and names).
STOPWORDS = set("""
a aby ale albo ani aż bardzo bez by być był była było były będzie bo co coś czy czyli dla do gdy gdyż gdzie go
i ich ile im ja jak jako je jego jej jest jeszcze jeśli już ją każdy kiedy kto która które który którego której
którym których lub ma mają mi mieć mnie mu można na nad nam nas nich nie niej nim niż no o od oraz po pod ponad
ponieważ przed przez przy raz się są sobie swoje ta tak także tam te tego tej ten też to tu tych tym tylko u w
we wszystko z za ze że żeby the of and in to is was for on with as by at from that this an be or are it
roku r rok lat latach wieku wiek
""".split())

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_YEAR_RE = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-2][0-9]|[1-9][0-9]{2})(?!\d)")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def stem(tok: str) -> str:
    """Very light Polish stemmer: digits untouched, otherwise truncate long tokens.

    Prefix truncation handles most Polish inflection (unia/unii/unię -> unia..., lubelska/lubelskiej -> lubels).
    """
    if tok.isdigit():
        return tok
    if len(tok) > 6:
        return tok[:6]
    if len(tok) >= 4:
        # drop the final vowel of medium tokens (unia/unii/unię -> uni, sejmu -> sejm)
        return tok[:-1] if tok[-1] in "aąeęioóuy" else tok
    return tok


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).lower()
    out = []
    for t in _TOKEN_RE.findall(text):
        if len(t) < 2 or t in STOPWORDS:
            continue
        out.append(stem(t))
    return out


def read_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------------------

def _strip_html(h: str) -> str:
    h = re.sub(r"(?s)<(script|style|table)[^>]*>.*?</\1>", "", h)
    h = re.sub(r'(?s)<span class="pagenum[^"]*"[^>]*>.*?</span>', "", h)
    h = re.sub(r'(?s)<sup class="reference"[^>]*>.*?</sup>', "", h)
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"</(p|div|h\d|li|tr)>", "\n", h)
    t = re.sub(r"<[^>]+>", "", h)
    t = html.unescape(t)
    t = t.replace(" ", " ").replace("\xa0", " ")
    t = re.sub(r"\[\d+\]", "", t)  # page numbers / footnote markers
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    return t.strip()


def fetch_one(session, site: str, title: str) -> dict:
    """Return {title, revid, timestamp, text, method}. Raises on API error."""
    if site == "wikipedia_pl":
        r = session.get(API[site], params={
            "action": "query", "prop": "extracts|revisions|info", "explaintext": 1,
            "exsectionformat": "wiki", "rvprop": "ids|timestamp", "titles": title,
            "format": "json", "formatversion": 2, "redirects": 1,
        }, timeout=60)
        r.raise_for_status()
        page = r.json()["query"]["pages"][0]
        if page.get("missing"):
            raise RuntimeError(f"missing page: {title}")
        rev = page["revisions"][0]
        return {"title": page["title"], "revid": rev["revid"], "timestamp": rev["timestamp"],
                "text": page.get("extract", ""), "method": "api:query/extracts"}
    if site == "wikisource_pl":
        r = session.get(API[site], params={
            "action": "parse", "page": title, "prop": "text|revid", "format": "json",
            "formatversion": 2, "redirects": 1,
        }, timeout=60)
        r.raise_for_status()
        d = r.json()
        if "error" in d:
            raise RuntimeError(f"{title}: {d['error'].get('info')}")
        p = d["parse"]
        return {"title": p["title"], "revid": p["revid"], "timestamp": None,
                "text": _strip_html(p["text"]), "method": "api:parse/text(html-stripped)"}
    raise ValueError(site)


def cmd_fetch(args) -> None:
    import requests  # local import so the offline steps do not need it

    spec = json.load(open(SOURCE_LIST, encoding="utf-8"))
    os.makedirs(RAW_DIR, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    existing = {r["source_id"]: r for r in read_jsonl(SOURCES_JSONL)} if os.path.exists(SOURCES_JSONL) else {}
    manifest, failures = [], []
    entries = [("wikipedia_pl", *e) for e in spec["wikipedia_pl"]] + [("wikisource_pl", *e) for e in spec["wikisource_pl"]]
    for entry in entries:
        site, source_id, title, group = entry[:4]
        rights_note = entry[4] if len(entry) > 4 else ""
        local_path = os.path.join("raw", f"{source_id}.txt")
        abs_path = os.path.join(ROOT, local_path)
        selected = not args.only or source_id in args.only
        cached = source_id in existing and os.path.exists(abs_path)
        if cached and (not selected or not args.refresh):
            manifest.append(existing[source_id])
            continue
        if not selected:
            continue
        try:
            got = fetch_one(session, site, title)
        except Exception as exc:  # noqa: BLE001
            failures.append({"source_id": source_id, "title": title, "error": str(exc)})
            print(f"FAIL {source_id}: {exc}", file=sys.stderr)
            continue
        if len(got["text"]) < 200:
            failures.append({"source_id": source_id, "title": title, "error": f"text too short ({len(got['text'])} chars)"})
            print(f"FAIL {source_id}: text too short", file=sys.stderr)
            continue
        data = got["text"].encode("utf-8")
        with open(abs_path, "wb") as f:
            f.write(data)
        title_q = got["title"].replace(" ", "_")
        if site == "wikipedia_pl":
            license_ = "CC BY-SA 4.0 (Wikipedia text); revision recorded"
            allowed = ["reference", "retrieve", "redistribute-with-attribution-sharealike"]
            publisher = "Wikimedia Foundation / Polish Wikipedia editors"
        else:
            license_ = "Public domain (primary document); Wikisource transcription layer CC BY-SA 4.0"
            allowed = ["reference", "retrieve", "redistribute"]
            publisher = "Wikimedia Foundation / Polish Wikisource editors"
        rec = {
            "source_id": source_id,
            "url": PERMALINK[site].format(title=title_q, revid=got["revid"]),
            "canonical_url": PAGE_URL[site].format(title=title_q),
            "title": got["title"],
            "publisher": publisher,
            "retrieved_at": now_iso(),
            "revision_or_sha256": f"revid:{got['revid']}; sha256:{sha256_bytes(data)}",
            "revision_id": got["revid"],
            "revision_timestamp": got["timestamp"],
            "sha256": sha256_bytes(data),
            "bytes": len(data),
            "license": license_,
            "allowed_use": allowed,
            "local_path": local_path,
            "source_group_id": f"{site}:{group}",
            "site": site,
            "fetch_method": got["method"],
            "notes": (rights_note + " " if rights_note else "") + "Raw text kept locally (gitignored); rebuild with `retrieval.py fetch`.",
        }
        manifest.append(rec)
        print(f"ok   {source_id} rev={got['revid']} bytes={len(data)}")
        time.sleep(args.sleep)
    # revision drift: live fetch vs the previously committed manifest (Wikipedia pages keep changing;
    # the committed manifest + index hash are the reference, drift is reported, not hidden)
    drift = []
    for rec in manifest:
        prev = existing.get(rec["source_id"])
        if prev and (prev.get("revision_id") != rec.get("revision_id") or prev.get("sha256") != rec.get("sha256")):
            drift.append({"source_id": rec["source_id"], "manifest_revid": prev.get("revision_id"), "fetched_revid": rec.get("revision_id"),
                          "manifest_sha256": prev.get("sha256"), "fetched_sha256": rec.get("sha256")})
    write_jsonl(SOURCES_JSONL, manifest)
    fail_path = os.path.join(ROOT, "sources", "fetch_failures.json")
    json.dump({"fetched_at": now_iso(), "failures": failures, "revision_drift": drift}, open(fail_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"manifest: {len(manifest)} sources -> {SOURCES_JSONL}; failures: {len(failures)}; revision drift vs previous manifest: {len(drift)} -> {fail_path}")


# --------------------------------------------------------------------------------------
# chunking + index
# --------------------------------------------------------------------------------------

def chunk_wikipedia(text: str, max_chars: int) -> list[tuple[str, str]]:
    """Split TextExtracts output into (section_path, chunk_text) pairs."""
    lines = text.split("\n")
    path = ["Wstęp"]
    sections: list[tuple[str, list[str]]] = [("Wstęp", [])]
    for line in lines:
        m = re.match(r"^(={2,6})\s*(.+?)\s*\1\s*$", line)
        if m:
            level = len(m.group(1)) - 1
            path = path[: level - 1] + [m.group(2)] if level > 1 else [m.group(2)]
            sections.append((" > ".join(path), []))
        else:
            sections[-1][1].append(line)
    out = []
    for sec_path, sec_lines in sections:
        top = sec_path.split(" > ")[0].strip().lower()
        if top in DROP_SECTIONS:
            continue
        body = "\n".join(sec_lines).strip()
        if len(body) < 40:
            continue
        out.extend((sec_path, c) for c in split_paragraphs(body, max_chars))
    return out


def split_paragraphs(body: str, max_chars: int) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 2 > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
        while len(cur) > max_chars * 1.5:  # very long paragraph: hard split on sentence boundary
            cut = cur.rfind(". ", 0, max_chars)
            cut = cut + 1 if cut > max_chars // 3 else max_chars
            chunks.append(cur[:cut].strip())
            cur = cur[cut:].strip()
    if cur:
        chunks.append(cur)
    return chunks


def chunk_wikisource(text: str, max_chars: int) -> list[tuple[str, str]]:
    return [("document", c) for c in split_paragraphs(text, max_chars)]


def build_chunks(manifest: list[dict], max_chars: int) -> list[dict]:
    chunks = []
    for src in manifest:
        path = os.path.join(ROOT, src["local_path"])
        if not os.path.exists(path):
            print(f"skip {src['source_id']}: raw text missing (run fetch)", file=sys.stderr)
            continue
        text = open(path, encoding="utf-8").read()
        pairs = chunk_wikipedia(text, max_chars) if src["site"] == "wikipedia_pl" else chunk_wikisource(text, max_chars)
        counter: Counter = Counter()
        for sec_path, ctext in pairs:
            counter[sec_path] += 1
            n = counter[sec_path]
            chunk_id = f"{src['source_id']}#{len(chunks):04d}"
            chunks.append({
                "chunk_id": chunk_id,
                "source_id": src["source_id"],
                "title": src["title"],
                "locator": f"{sec_path} [part {n}]",
                "section": sec_path,
                "text": ctext,
                "years": sorted({int(y) for y in _YEAR_RE.findall(ctext)}),
            })
    return chunks


class BM25Index:
    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        # content field: chunk text only; title field: article title + section path (scored separately)
        self.postings: dict[str, dict[int, int]] = defaultdict(dict)
        self.title_postings: dict[str, dict[int, int]] = defaultdict(dict)
        self.doc_len: list[int] = []
        self.title_len: list[int] = []
        for i, ch in enumerate(chunks):
            toks = tokenize(ch["text"])
            self.doc_len.append(len(toks))
            for t, c in Counter(toks).items():
                self.postings[t][i] = c
            ttoks = tokenize(ch["title"] + " " + ch["section"])
            self.title_len.append(len(ttoks))
            for t, c in Counter(ttoks).items():
                self.title_postings[t][i] = c
        self.n = len(chunks)
        self.avgdl = sum(self.doc_len) / max(1, self.n)
        self.avgtl = sum(self.title_len) / max(1, self.n)

    def idf(self, term: str, postings=None) -> float:
        df = len((postings if postings is not None else self.postings).get(term, {}))
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def _field_scores(self, qterms: Counter, postings, lens, avg) -> dict[int, float]:
        sc: dict[int, float] = defaultdict(float)
        for term in qterms:
            plist = postings.get(term)
            if not plist:
                continue
            idf = self.idf(term, postings)
            for i, tf in plist.items():
                sc[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * lens[i] / avg))
        return sc

    def scores(self, query: str, title_weight: float = 1.0) -> dict[int, float]:
        """BM25 over chunk text plus `title_weight` x BM25 over the title/section field.

        title_weight=1.0 approximates the audited v1 index (title tokens concatenated into every chunk);
        lower weights stop an article's title from lifting all of its sections equally.
        """
        q = Counter(tokenize(query))
        sc = self._field_scores(q, self.postings, self.doc_len, self.avgdl)
        if title_weight:
            for i, s in self._field_scores(q, self.title_postings, self.title_len, self.avgtl).items():
                sc[i] += title_weight * s
        return sc

    def to_json(self) -> dict:
        return {
            "k1": self.k1, "b": self.b, "avgdl": self.avgdl, "avgtl": self.avgtl,
            "doc_len": self.doc_len, "title_len": self.title_len,
            "postings": {t: list(p.items()) for t, p in self.postings.items()},
            "title_postings": {t: list(p.items()) for t, p in self.title_postings.items()},
            "chunks": self.chunks,
        }

    @classmethod
    def from_json(cls, d: dict) -> "BM25Index":
        obj = cls.__new__(cls)
        obj.chunks, obj.k1, obj.b = d["chunks"], d["k1"], d["b"]
        obj.avgdl, obj.avgtl, obj.doc_len, obj.title_len = d["avgdl"], d["avgtl"], d["doc_len"], d["title_len"]
        obj.postings = {t: {int(i): c for i, c in p} for t, p in d["postings"].items()}
        obj.title_postings = {t: {int(i): c for i, c in p} for t, p in d["title_postings"].items()}
        obj.n = len(obj.chunks)
        return obj


def cmd_index(args) -> None:
    manifest = read_jsonl(SOURCES_JSONL)
    chunks = build_chunks(manifest, args.max_chars)
    idx = BM25Index(chunks, k1=args.k1, b=args.b)
    os.makedirs(INDEX_DIR, exist_ok=True)
    payload = idx.to_json()
    # deterministic payload: no timestamps inside the index file, so identical raw text => identical SHA-256
    payload["meta"] = {
        "n_sources": len({c["source_id"] for c in chunks}), "n_chunks": len(chunks),
        "max_chars": args.max_chars,
        "raw_sha256": {r["source_id"]: r["sha256"] for r in manifest},  # content hashes only (no timestamps)
        "tokenizer": "NFKC lowercase, \\w+, stoplist, prefix-6 stem", "k1": args.k1, "b": args.b,
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, sort_keys=True)
    meta = {k: v for k, v in payload["meta"].items() if k != "raw_sha256"}
    meta.update(built_at=now_iso(), sources_sha256=sha256_file(SOURCES_JSONL),
                index_sha256=sha256_file(INDEX_FILE), index_bytes=os.path.getsize(INDEX_FILE))
    json.dump(meta, open(os.path.join(REPORTS_DIR, "index_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


def load_index() -> BM25Index:
    if not os.path.exists(INDEX_FILE):
        sys.exit(f"index missing: {INDEX_FILE} (run `retrieval.py fetch` then `retrieval.py index`)")
    return BM25Index.from_json(json.load(open(INDEX_FILE, encoding="utf-8")))


# --------------------------------------------------------------------------------------
# query modes: bm25 | hybrid (bm25 + char n-gram tf-idf) | chrono (bm25 + year/entity graph boost)
# --------------------------------------------------------------------------------------

_NGRAM_CACHE: dict[str, list[dict[str, float]]] = {}


def char_ngrams(text: str, n: int = 4) -> Counter:
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).lower())
    return Counter(t[i:i + n] for i in range(max(0, len(t) - n + 1)))


def ngram_vectors(idx: BM25Index) -> tuple[list[dict[str, float]], dict[str, float]]:
    key = str(id(idx))
    if key in _NGRAM_CACHE:
        return _NGRAM_CACHE[key]  # type: ignore[return-value]
    docs = [char_ngrams(c["title"] + " " + c["text"][:1500]) for c in idx.chunks]
    df: Counter = Counter()
    for d in docs:
        df.update(d.keys())
    n = len(docs)
    idf = {g: math.log((n + 1) / (c + 1)) + 1 for g, c in df.items()}
    vecs = []
    for d in docs:
        v = {g: (1 + math.log(c)) * idf[g] for g, c in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({g: x / norm for g, x in v.items()})
    _NGRAM_CACHE[key] = (vecs, idf)  # type: ignore[assignment]
    return vecs, idf


def ngram_scores(idx: BM25Index, query: str) -> dict[int, float]:
    vecs, idf = ngram_vectors(idx)
    q = char_ngrams(query)
    qv = {g: (1 + math.log(c)) * idf.get(g, 1.0) for g, c in q.items()}
    qn = math.sqrt(sum(x * x for x in qv.values())) or 1.0
    out = {}
    for i, v in enumerate(vecs):
        s = sum(w * v[g] for g, w in qv.items() if g in v)
        if s > 0:
            out[i] = s / qn
    return out


def _normalize(sc: dict[int, float]) -> dict[int, float]:
    if not sc:
        return {}
    m = max(sc.values()) or 1.0
    return {i: s / m for i, s in sc.items()}


def rank(idx: BM25Index, query: str, k: int, mode: str = "bm25", graph: dict | None = None,
         title_weight: float = 1.0) -> list[dict]:
    bm = idx.scores(query, title_weight)
    if mode == "bm25":
        combined = bm
    elif mode == "twostage":
        # stage 1: article score = best chunk score (title-weighted); stage 2: re-rank chunks of the
        # top articles by content-only BM25 so the section that actually answers wins.
        by_src: dict[str, float] = defaultdict(float)
        for i, s in bm.items():
            sid = idx.chunks[i]["source_id"]
            by_src[sid] = max(by_src[sid], s)
        top_src = {sid for sid, _ in sorted(by_src.items(), key=lambda x: -x[1])[:3]}
        # residual query: drop the query terms already satisfied by the article title, so the
        # discriminative terms (ostracyzm, Ulrich, Wieprz) decide the section within the article
        qtoks = Counter(tokenize(query))
        title_toks = {sid: set(tokenize(t)) for sid, t in {c["source_id"]: c["title"] for c in idx.chunks}.items()}
        combined = {}
        for sid in top_src:
            residual = Counter({t: c for t, c in qtoks.items() if t not in title_toks[sid]}) or qtoks
            rs = idx._field_scores(residual, idx.postings, idx.doc_len, idx.avgdl)
            # article-major ordering: stage-1 article score decides the article, residual decides the section
            for i, s in bm.items():
                if idx.chunks[i]["source_id"] == sid:
                    combined[i] = 1000.0 * by_src[sid] + rs.get(i, 0.0) + 0.1 * s
    elif mode == "hybrid":
        a, b = _normalize(bm), _normalize(ngram_scores(idx, query))
        combined = {i: 0.6 * a.get(i, 0.0) + 0.4 * b.get(i, 0.0) for i in set(a) | set(b)}
    elif mode == "chrono":
        combined = dict(bm)
        graph = graph or load_graph()
        years = {int(y) for y in _YEAR_RE.findall(query)}
        boost_ids: Counter = Counter()
        for y in years:
            for cid in graph["year_to_chunks"].get(str(y), []):
                boost_ids[cid] += 1
        qtoks = set(tokenize(query))
        for ent, cids in graph["entity_to_chunks"].items():
            etoks = set(tokenize(ent))
            if etoks and etoks <= qtoks:
                for cid in cids:
                    boost_ids[cid] += 1
        if boost_ids:
            top = max(bm.values()) if bm else 1.0
            for i, hits in boost_ids.items():
                combined[i] = combined.get(i, 0.0) + 0.15 * top * hits
    else:
        raise ValueError(mode)
    order = sorted(combined.items(), key=lambda x: -x[1])[:k]
    out = []
    for r, (i, s) in enumerate(order, 1):
        ch = idx.chunks[i]
        out.append({"rank": r, "score": round(s, 4), "chunk_id": ch["chunk_id"], "source_id": ch["source_id"],
                    "title": ch["title"], "locator": ch["locator"], "text": ch["text"]})
    return out


def cmd_query(args) -> None:
    idx = load_index()
    res = rank(idx, args.text, args.k, args.mode, title_weight=args.title_weight)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    for r in res:
        snippet = re.sub(r"\s+", " ", r["text"])[: args.snippet]
        print(f"{r['rank']:>2}. {r['score']:7.3f}  {r['source_id']}  [{r['locator']}]\n    {snippet}")


# --------------------------------------------------------------------------------------
# graph (stretch): year -> chunks, entity(title) -> chunks
# --------------------------------------------------------------------------------------

def cmd_graph(args) -> None:
    idx = load_index()
    year_to_chunks: dict[str, list[int]] = defaultdict(list)
    entity_to_chunks: dict[str, list[int]] = defaultdict(list)
    titles = {c["title"] for c in idx.chunks}
    title_stems = {t: set(tokenize(t)) for t in titles}
    for i, ch in enumerate(idx.chunks):
        for y in ch["years"]:
            if 476 <= y <= 2026:
                year_to_chunks[str(y)].append(i)
        ctoks = set(tokenize(ch["text"]))
        for t, ts in title_stems.items():
            if ts and ts <= ctoks:
                entity_to_chunks[t].append(i)
    # year timeline from titles: which years co-occur most with each source's own intro chunk
    timeline = []
    for ch in idx.chunks:
        if ch["section"] == "Wstęp" and ch["locator"].endswith("[part 1]") and ch["years"]:
            timeline.append({"title": ch["title"], "source_id": ch["source_id"], "years": ch["years"][:6]})
    graph = {"built_at": now_iso(), "year_to_chunks": year_to_chunks, "entity_to_chunks": entity_to_chunks,
             "timeline": sorted(timeline, key=lambda t: t["years"][0])}
    json.dump(graph, open(GRAPH_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"graph: {len(year_to_chunks)} years, {len(entity_to_chunks)} entities, {len(timeline)} timeline rows -> {GRAPH_FILE}")


def load_graph() -> dict:
    if not os.path.exists(GRAPH_FILE):
        sys.exit(f"graph missing: {GRAPH_FILE} (run `retrieval.py graph`)")
    return json.load(open(GRAPH_FILE, encoding="utf-8"))


# --------------------------------------------------------------------------------------
# eval
# --------------------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).lower())


def evidence_hit(r: dict, q: dict) -> bool:
    """Chunk-level hit: right source AND (expected section prefix matches OR must_contain string present)."""
    if r["source_id"] not in q["expected_source_ids"]:
        return False
    loc_ok = any(_norm(r["locator"]).startswith(_norm(loc)) for loc in q.get("expected_locators", []))
    text_ok = any(_norm(m) in _norm(r["text"]) for m in q.get("must_contain", []))
    return loc_ok or text_ok


def evaluate(idx: BM25Index, queries: list[dict], k: int, mode: str, title_weight: float = 1.0) -> dict:
    graph = load_graph() if mode == "chrono" else None
    ks = [1, 3, 5, 10]
    src_hits = {kk: 0 for kk in ks}
    ev_hits = {kk: 0 for kk in ks}
    rr_src, rr_ev, per_query = 0.0, 0.0, []
    t0 = time.time()
    for q in queries:
        res = rank(idx, q["prompt"], max(k, 10), mode, graph, title_weight)
        first_src = next((r["rank"] for r in res if r["source_id"] in q["expected_source_ids"]), None)
        first_ev = next((r["rank"] for r in res if evidence_hit(r, q)), None)
        for kk in ks:
            src_hits[kk] += int(first_src is not None and first_src <= kk)
            ev_hits[kk] += int(first_ev is not None and first_ev <= kk)
        rr_src += 1 / first_src if first_src else 0.0
        rr_ev += 1 / first_ev if first_ev else 0.0
        per_query.append({
            "id": q["id"], "first_source_rank": first_src, "first_evidence_rank": first_ev,
            "top1": {"source_id": res[0]["source_id"], "locator": res[0]["locator"]} if res else None,
            "expected_source_ids": q["expected_source_ids"],
        })
    n = len(queries)
    return {
        "mode": mode, "title_weight": title_weight, "n_queries": n, "k_max": max(k, 10), "seconds": round(time.time() - t0, 2),
        "source_hit_at_k": {str(kk): round(v / n, 3) for kk, v in src_hits.items()},
        "evidence_hit_at_k": {str(kk): round(v / n, 3) for kk, v in ev_hits.items()},
        "source_hit_counts": {str(kk): v for kk, v in src_hits.items()},
        "evidence_hit_counts": {str(kk): v for kk, v in ev_hits.items()},
        "mrr_source": round(rr_src / n, 3), "mrr_evidence": round(rr_ev / n, 3),
        "per_query": per_query,
    }


def cmd_eval(args) -> None:
    idx = load_index()
    queries = read_jsonl(args.queries)
    modes = args.modes.split(",")
    meta = json.load(open(os.path.join(REPORTS_DIR, "index_meta.json"), encoding="utf-8"))
    summary = {"evaluated_at": now_iso(), "queries_file": os.path.relpath(args.queries, ROOT),
               "queries_sha256": sha256_file(args.queries), "index_sha256": meta["index_sha256"],
               "n_chunks": meta["n_chunks"], "n_sources": meta["n_sources"], "results": {}}
    for mode in modes:
        res = evaluate(idx, queries, args.k, mode, args.title_weight)
        summary["results"][mode] = res
        write_jsonl(os.path.join(REPORTS_DIR, f"eval_per_query_{mode}.jsonl"), res["per_query"])
        print(f"[{mode} tw={args.title_weight}] n={res['n_queries']} source_hit@1/3/5/10 = "
              f"{res['source_hit_at_k']['1']}/{res['source_hit_at_k']['3']}/{res['source_hit_at_k']['5']}/{res['source_hit_at_k']['10']}"
              f"  evidence_hit@1/3/5/10 = {res['evidence_hit_at_k']['1']}/{res['evidence_hit_at_k']['3']}/{res['evidence_hit_at_k']['5']}/{res['evidence_hit_at_k']['10']}"
              f"  MRR(src)={res['mrr_source']} MRR(ev)={res['mrr_evidence']}  {res['seconds']}s")
        misses = [p["id"] for p in res["per_query"] if p["first_evidence_rank"] is None or p["first_evidence_rank"] > 5]
        if misses:
            print(f"   evidence miss (>5 or none): {misses}")
    out = os.path.join(REPORTS_DIR, "eval_summary.json")
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"-> {out}")


# --------------------------------------------------------------------------------------
# audit sample + scoring
# --------------------------------------------------------------------------------------

def cmd_audit_sample(args) -> None:
    idx = load_index()
    queries = read_jsonl(args.queries)
    rows = []
    for q in queries:
        res = rank(idx, q["prompt"], args.k, args.mode, title_weight=args.title_weight)
        rows.append({
            "id": q["id"], "prompt": q["prompt"], "claim": q["answer"],
            "citations": [{"rank": r["rank"], "chunk_id": r["chunk_id"], "source_id": r["source_id"],
                           "title": r["title"], "locator": r["locator"], "text": r["text"]} for r in res],
            "auditor_instructions": "For each citation decide: supported | partial | unsupported. Judge ONLY from the cited text; do not use your own knowledge to fill gaps.",
        })
    os.makedirs(AUDIT_DIR, exist_ok=True)
    out = os.path.join(AUDIT_DIR, f"audit_sample_{args.tag or args.mode}.jsonl")
    write_jsonl(out, rows)
    print(f"audit sample: {len(rows)} queries x top-{args.k} ({args.mode}) -> {out}")


def cmd_audit_score(args) -> None:
    verdicts = read_jsonl(args.verdicts)
    counts = Counter()
    top1 = Counter()
    for v in verdicts:
        for c in v["citations"]:
            counts[c["verdict"]] += 1
            if c["rank"] == 1:
                top1[c["verdict"]] += 1
    total = sum(counts.values())
    n1 = sum(top1.values())
    report = {
        "status": "provisional",
        "auditor": verdicts[0].get("auditor", "unknown") if verdicts else "unknown",
        "n_queries": len(verdicts), "n_citations": total,
        "citation_precision_strict": round(counts["supported"] / total, 3) if total else None,
        "citation_precision_lenient": round((counts["supported"] + counts["partial"]) / total, 3) if total else None,
        "top1_precision_strict": round(top1["supported"] / n1, 3) if n1 else None,
        "top1_precision_lenient": round((top1["supported"] + top1["partial"]) / n1, 3) if n1 else None,
        "counts": dict(counts), "top1_counts": dict(top1),
        "unsupported": [{"id": v["id"], "rank": c["rank"], "chunk_id": c["chunk_id"], "note": c.get("note", "")}
                        for v in verdicts for c in v["citations"] if c["verdict"] != "supported"],
    }
    report["verdicts_file"] = os.path.relpath(args.verdicts, ROOT)
    report["verdicts_sha256"] = sha256_file(args.verdicts)
    out = os.path.join(REPORTS_DIR, args.out)
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "unsupported"}, ensure_ascii=False, indent=2))
    print(f"-> {out}")


# --------------------------------------------------------------------------------------

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch"); p.add_argument("--refresh", action="store_true"); p.add_argument("--sleep", type=float, default=0.3)
    p.add_argument("--only", nargs="*", help="source_ids to (re)fetch"); p.set_defaults(fn=cmd_fetch)

    p = sub.add_parser("index"); p.add_argument("--max-chars", type=int, default=1200)
    p.add_argument("--k1", type=float, default=1.5); p.add_argument("--b", type=float, default=0.75); p.set_defaults(fn=cmd_index)

    p = sub.add_parser("query"); p.add_argument("text"); p.add_argument("--k", type=int, default=5)
    p.add_argument("--mode", default="bm25", choices=MODES); p.add_argument("--json", action="store_true")
    p.add_argument("--title-weight", type=float, default=1.0)
    p.add_argument("--snippet", type=int, default=220); p.set_defaults(fn=cmd_query)

    p = sub.add_parser("graph"); p.set_defaults(fn=cmd_graph)

    p = sub.add_parser("eval"); p.add_argument("--queries", default=QUERIES_FILE); p.add_argument("--k", type=int, default=10)
    p.add_argument("--modes", default="bm25"); p.add_argument("--title-weight", type=float, default=1.0); p.set_defaults(fn=cmd_eval)

    p = sub.add_parser("audit-sample"); p.add_argument("--queries", default=QUERIES_FILE); p.add_argument("--k", type=int, default=3)
    p.add_argument("--mode", default="bm25", choices=MODES); p.add_argument("--title-weight", type=float, default=1.0)
    p.add_argument("--tag", default="", help="output name suffix (default: mode)"); p.set_defaults(fn=cmd_audit_sample)

    p = sub.add_parser("audit-score"); p.add_argument("--verdicts", default=os.path.join(AUDIT_DIR, "audit_verdicts.jsonl"))
    p.add_argument("--out", default="audit_score.json", help="file name under reports/"); p.set_defaults(fn=cmd_audit_score)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
