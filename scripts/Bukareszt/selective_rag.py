#!/usr/bin/env python3
"""Selective RAG for issue #96: query decontamination, question-only evidence router, relevance gate.

Opt-in only. The shared `scripts/prepare_rag.py`, `infer.py`, the pinned corpus/index and the #57 bounded builder
are untouched; their retrieval default (whole original prompt as the chrono query) is preserved.

    # CPU rank ablations over fixtures (no model calls)
    python3 scripts/Bukareszt/selective_rag.py ablate \
        --fixtures agentsLog/Bukareszt/issue96/fixtures/synthetic_fixtures.jsonl \
        --controls agentsLog/Bukareszt/queries/train_queries.jsonl --out agentsLog/Bukareszt/issue96/ablation.json

    # opt-in runner input: routed cases get <= one compact passage, everything else stays byte-identical
    python3 scripts/Bukareszt/selective_rag.py prepare --input <keyfree.jsonl> \
        --output agentsLog/Bukareszt/private/selective/<name>.jsonl [--pairs 12]

Query variants (each rank ablation isolates one change against `base`, the production chrono query):
  * header removal: exact generic answer-instruction templates (bare validation header, organizer header/footer,
    the organizer "Wymagany format odpowiedzi" section) are dropped from the QUERY only;
  * publication-number masking: digits inside detected bibliography lines (city+year, "s. 12", "Za:", "red.") are
    masked, the words (titles, authors) stay;
  * BCE-aware years: the graph has no era sign, so a query year followed by "p.n.e."/"przed Chr." boosts only chunks
    where that number is also written as BCE, and a plain (CE) year only chunks where it is not; centuries and
    implied periods are never converted into invented years;
  * chrono year boost off / all chrono boosts off (plain BM25).
The answering prompt always keeps the complete original task, sources and bibliography as a verbatim suffix.

Router (question text only; no evaluator task_type, keys, answers or IDs): essay | supplied_source |
external_fact | mixed | ambiguous. Only external_fact and mixed may retrieve; everything else stays bare.
Gate: distinctive query terms = idf >= GATE_MIN_IDF, not digits, not generic exam-instruction words. The top-1 hit of
the decontaminated query passes if one of them is in its article title, or >= GATE_MIN_TERMS of them are in the chunk
covering >= GATE_MIN_COVERAGE of them; otherwise zero hits.
The passed chunk is reduced to one compact sentence window (<= WINDOW_CHARS) around the matched terms.
Stdlib only; socket-guarded; zero model calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prepare_bounded_rag as pbr  # noqa: E402 -- pinned identity, socket guard, evidence block, safe targets
import stage_index as si  # noqa: E402

TITLE_WEIGHT = 1.0
RANK_K = 5
GATE_MIN_IDF = 3.0
GATE_MIN_TERMS = 2
GATE_MIN_COVERAGE = 0.2
GATE_MIN_TITLE_TERMS = 1
WINDOW_CHARS = 480
BUDGET_CHARS = 800  # whole evidence block incl. #57 header/footer; one passage only

# generic exam-instruction vocabulary: never counts as topical evidence in the gate (not derived from any exam item)
GENERIC_WORDS = (
    "podaj podać nazwę nazwa nazwy nazwisko imię imienia rok roku datę data zadanie zadania tekst tekstu tekście tekstów "
    "źródło źródła źródłowy źródle źródeł materiał ilustracja ilustracji mapa mapy wyjaśnij określ wymień oceń uzasadnij "
    "rozstrzygnij porównaj wskaż przedstaw napisz wypisz zaznacz odpowiedź odpowiedzi jeden jedna jedną jedno dwa dwie trzy "
    "który która które którego której opisany opisana opisane opisanej opisanego opisanym przytoczono fragment fragmentu "
    "własnej wiedzy podstawie mowa czego tego tej wtedy później następnie zbudowano zawarto odwołaj przyczynę przyczyny "
    "skutek skutki dlaczego przykład przykłady wydarzenie wydarzenia postać postaci państwo państwa okres okresu"
)

BARE_HEADER = (
    "Rozwiąż poniższe zadanie z egzaminu maturalnego z historii (poziom rozszerzony). "
    "Odpowiadaj po polsku, zwięźle i na podstawie źródeł zamieszczonych w zadaniu oraz własnej wiedzy. "
    "Jeżeli zadanie wymaga rozstrzygnięcia, zacznij odpowiedź od linii 'Rozstrzygnięcie: ...', "
    "a następnie podaj 'Uzasadnienie: ...'. W zadaniach typu prawda/fałsz podaj numer zdania i literę P albo F. "
    "W zadaniach zamkniętych podaj literę wybranej odpowiedzi. Obrazy stron arkusza są dołączone, jeśli zadanie "
    "zawiera materiał ikonograficzny lub kartograficzny.\n\n"
)
ORG_HEADER = "Egzamin maturalny. Odpowiedz na jedno zadanie."
ORG_FOOTER = ("Przykłady w formacie odpowiedzi pokazują tylko składnię, nie są rozwiązaniem.\n"
              "Zwróć wyłącznie końcową odpowiedź po polsku, bez rozumowania i komentarzy.")
TEMPLATES = (BARE_HEADER, ORG_FOOTER, ORG_HEADER)
ORG_FORMAT_RE = re.compile(r"(?:^|\n\n)Wymagany format odpowiedzi:\n.*?(?=\n\n|\Z)", re.S)

CITY = (r"(?:Warszawa|Warszawie|Kraków|Krakowie|Wrocław|Poznań|Lublin|Łódź|Gdańsk|Toruń|Katowice|Lwów|Wilno|"
        r"Gniezno|Olsztyn|Białystok|Opole|Rzeszów|Szczecin|Kielce|Bydgoszcz|Paryż|Londyn|Berlin|Wiedeń|Moskwa|"
        r"London|Paris|Oxford|New York)")
BIB_RE = re.compile(
    r"^\s*(?:Za|Źródło|Źródła|Cyt\. za|Oprac\.|Opracowano na podstawie|Na podstawie)\s*:"
    rf"|\b{CITY},?\s+(?:1[4-9]\d\d|20[0-2]\d)\b"
    r"|,\s*s\.\s*\d+|\b(?:red|oprac|tłum|wyd)\.\s|\bt\.\s*[IVX\d]+,")
BCE_AFTER_RE = re.compile(r"^\s*(?:r\.\s*)?(?:p\.\s*n\.\s*e\.|przed\s+(?:naszą\s+erą|Chr))", re.I)

# router cues (question text only)
MATERIAL_RE = re.compile(
    r"Tekst źródłowy|Materiał źródłowy:|Tekst\s+\d|Źródło\s+\d|Ilustracj|Mapa\b|Mapy\b|Fotografi|Tabel|Wykres|Plakat|"
    r"Karykatur", re.I)
ESSAY_RE = re.compile(r"wypracowani|\(0\s*[–-]\s*1[0-9]\)|maks\.\s*1[0-9]\s*pkt", re.I)
SOURCE_CUE_RE = re.compile(
    r"na podstawie (?:tekstu|tekstów|źródła|źródeł|ilustracji|mapy|tabeli|wykresu|fotografii|plakatu|obu|materiału)"
    r"|z tekstu|w tekście|w źródle|wypisz|porównaj|według autor|ile\b", re.I)
EXTERNAL_CUE_RE = re.compile(
    r"własnej wiedzy|podaj (?:nazwę|imię|rok|datę|nazwisko)|o którym mowa|o której mowa|którego fragment|"
    r"wyjaśnij|dlaczego|przyczyn|skutk|oceń|rozstrzygnij", re.I)
COMMAND_RE = re.compile(
    r"\b(?:Podaj|Wyjaśnij|Określ|Wymień|Oceń|Rozstrzygnij|Uzasadnij|Zaznacz|Przyporządkuj|Uporządkuj|Porównaj|"
    r"Scharakteryzuj|Napisz|Wybierz|Wpisz|Wypisz|Wskaż|Przedstaw|Na podstawie)\b")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------
# query construction (query only; the answering prompt is never changed)
# --------------------------------------------------------------------------------------

def strip_templates(prompt: str) -> str:
    text = prompt
    for tpl in TEMPLATES:
        text = text.replace(tpl, "\n")
    return ORG_FORMAT_RE.sub("\n", text).strip()


def is_bibliography(line: str) -> bool:
    return bool(BIB_RE.search(line))


def mask_bibliography_numbers(text: str) -> tuple[str, int]:
    out, n = [], 0
    for line in text.split("\n"):
        if is_bibliography(line):
            line, k = re.subn(r"\d+", " ", line)
            n += k
        out.append(line)
    return "\n".join(out), n


def drop_bibliography(text: str) -> str:
    return "\n".join(line for line in text.split("\n") if not is_bibliography(line))


def extract_years(retrieval, text: str, bce_aware: bool) -> tuple[set[int], set[int]]:
    """Years the production regex would boost. With bce_aware, a year followed by p.n.e./przed Chr. is returned in
    the second (BCE) set instead of the CE set; nothing is inferred from centuries or context."""
    ce, bce = set(), set()
    for m in retrieval._YEAR_RE.finditer(text):
        y = int(m.group(1))
        (bce if bce_aware and BCE_AFTER_RE.match(text[m.end():m.end() + 24]) else ce).add(y)
    return ce, bce


def chunk_has_year(retrieval, text: str, year: int, bce: bool) -> bool:
    """True when `year` occurs in the chunk text with the requested era marking (BCE = followed by p.n.e.)."""
    for m in retrieval._YEAR_RE.finditer(text):
        if int(m.group(1)) == year and bool(BCE_AFTER_RE.match(text[m.end():m.end() + 24])) == bce:
            return True
    return False


VARIANTS = {
    # name: (strip_header, mask_bib, drop_bib, bce_aware, year_boost, entity_boost)
    "base":            (False, False, False, False, True, True),
    "A_header_off":    (True, False, False, False, True, True),
    "B_pubnum_mask":   (False, True, False, False, True, True),
    "C_yearboost_off": (False, False, False, False, False, True),
    "C2_bm25":         (False, False, False, False, False, False),
    "D_bib_drop":      (False, False, True, False, True, True),
    "E_bce_aware":     (False, False, False, True, True, True),
    "F_A+B+E":         (True, True, False, True, True, True),
    "G_A+B_bm25":      (True, True, False, False, False, False),
    "H_A+B":           (True, True, False, False, True, True),
}
SELECTED_VARIANT = "H_A+B"


def build_query(retrieval, prompt: str, variant: str) -> dict:
    strip, mask, drop, bce, year_boost, entity_boost = VARIANTS[variant]
    text, masked = prompt, 0
    if strip:
        text = strip_templates(text)
    if mask:
        text, masked = mask_bibliography_numbers(text)
    if drop:
        text = drop_bibliography(text)
    years, bce_years = extract_years(retrieval, text, bce)
    return {"variant": variant, "text": text, "years": sorted(years) if year_boost else [],
            "bce_years": sorted(bce_years) if year_boost else [], "bce_aware": bce,
            "masked_numbers": masked, "year_boost": year_boost, "entity_boost": entity_boost,
            "sha256": sha256_text(text), "chars": len(text)}


def rank(retrieval, idx, graph, query: dict, k: int = RANK_K) -> list[dict]:
    """Chrono ranking with explicit year set and boost switches. With years = production regex on the same text and
    both boosts on, this is exactly `retrieval.rank(mode="chrono")` (verified by test)."""
    text = query["text"]
    bm = idx.scores(text, TITLE_WEIGHT)
    combined = dict(bm)
    boost_ids: Counter = Counter()
    if query["year_boost"]:
        for era_bce, years in ((False, query["years"]), (True, query["bce_years"])):
            for y in years:
                for cid in graph["year_to_chunks"].get(str(y), []):
                    if not query["bce_aware"] or chunk_has_year(retrieval, idx.chunks[cid]["text"], y, era_bce):
                        boost_ids[cid] += 1
    if query["entity_boost"]:
        qtoks = set(retrieval.tokenize(text))
        for ent, cids in graph["entity_to_chunks"].items():
            etoks = set(retrieval.tokenize(ent))
            if etoks and etoks <= qtoks:
                for cid in cids:
                    boost_ids[cid] += 1
    if boost_ids:
        top = max(bm.values()) if bm else 1.0
        for i, hits in boost_ids.items():
            combined[i] = combined.get(i, 0.0) + 0.15 * top * hits
    order = sorted(combined.items(), key=lambda x: -x[1])[:k]
    out = []
    for r, (i, s) in enumerate(order, 1):
        ch = idx.chunks[i]
        out.append({"rank": r, "score": round(s, 4), "bm25": round(bm.get(i, 0.0), 4), "year_boosted": boost_ids.get(i, 0),
                    "idx": i, "chunk_id": ch["chunk_id"], "source_id": ch["source_id"], "title": ch["title"],
                    "locator": ch["locator"], "text": ch["text"]})
    return out


# --------------------------------------------------------------------------------------
# question-only evidence router
# --------------------------------------------------------------------------------------

def route(prompt: str) -> dict:
    text = strip_templates(prompt)
    commands = [s for s in re.split(r"(?<=[.?!:])\s+|\n", text) if COMMAND_RE.search(s)]
    command = " ".join(commands)
    material = bool(MATERIAL_RE.search(text)) or any(is_bibliography(line) for line in text.split("\n"))
    signals = {"material": material, "commands": len(commands),
               "essay": bool(ESSAY_RE.search(prompt)), "source_cue": bool(SOURCE_CUE_RE.search(command)),
               "external_cue": bool(EXTERNAL_CUE_RE.search(command))}
    if signals["essay"]:
        r = "essay"
    elif not commands:
        r = "ambiguous"
    elif signals["source_cue"] and not signals["external_cue"]:
        r = "supplied_source"
    elif material:
        r = "mixed" if signals["external_cue"] else "ambiguous"
    else:
        r = "external_fact"
    if not commands and not material and "?" in text and not signals["essay"]:
        r = "external_fact"  # a plain question with no supplied material
    return {"route": r, "retrieve": r in ("external_fact", "mixed"), "signals": signals}


# --------------------------------------------------------------------------------------
# relevance gate and compact passage
# --------------------------------------------------------------------------------------

def distinctive_terms(retrieval, idx, text: str) -> set[str]:
    generic = set(retrieval.tokenize(GENERIC_WORDS))
    return {t for t in set(retrieval.tokenize(text))
            if not t.isdigit() and t not in generic and idx.idf(t) >= GATE_MIN_IDF}


def gate(retrieval, idx, query: dict, hits: list[dict]) -> dict:
    """Pass the top-1 hit only with lexical support: a distinctive question term in its article title, or
    >= GATE_MIN_TERMS distinctive terms in the chunk covering >= GATE_MIN_COVERAGE of them. Otherwise zero hits."""
    terms = distinctive_terms(retrieval, idx, query["text"])
    if not hits or not terms:
        return {"pass": False, "reason": "no hits" if not hits else "no distinctive query terms",
                "query_terms": len(terms), "matched": [], "title_matched": [], "coverage": 0.0}
    top = hits[0]
    title_terms = set(retrieval.tokenize(top["title"]))
    matched = sorted(terms & (set(retrieval.tokenize(top["text"])) | title_terms))
    title_matched = sorted(terms & title_terms)
    coverage = round(len(matched) / len(terms), 3)
    ok = len(title_matched) >= GATE_MIN_TITLE_TERMS or (len(matched) >= GATE_MIN_TERMS and coverage >= GATE_MIN_COVERAGE)
    return {"pass": ok, "reason": ("title match" if title_matched else "chunk terms") if ok else "weak lexical support",
            "query_terms": len(terms), "matched": matched, "title_matched": title_matched, "coverage": coverage}


def compact_window(retrieval, text: str, matched: list[str], limit: int = WINDOW_CHARS) -> str:
    """Best contiguous sentence window (<= limit chars) by count of matched distinctive terms; no new text."""
    sents = [s for s in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if s]
    want = set(matched)
    best, best_score = "", -1
    for i in range(len(sents)):
        window = ""
        for j in range(i, len(sents)):
            cand = (window + " " + sents[j]).strip()
            if len(cand) > limit:
                break
            window = cand
            score = len(want & set(retrieval.tokenize(window)))
            if score > best_score or (score == best_score and len(window) < len(best)):
                best, best_score = window, score
    return best or text[:limit]


def select_evidence(retrieval, idx, graph, prompt: str) -> dict:
    r = route(prompt)
    out = {"route": r, "query": None, "ranked": [], "gate": None, "passage": None}
    if not r["retrieve"]:
        return out
    q = build_query(retrieval, prompt, SELECTED_VARIANT)
    hits = rank(retrieval, idx, graph, q)
    g = gate(retrieval, idx, q, hits)
    out.update(query=q, ranked=hits, gate=g)
    if g["pass"]:
        top = hits[0]
        out["passage"] = {"chunk_id": top["chunk_id"], "source_id": top["source_id"], "title": top["title"],
                          "locator": top["locator"], "text": compact_window(retrieval, top["text"], g["matched"])}
    return out


# --------------------------------------------------------------------------------------
# ablation over fixtures
# --------------------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fixture_set(fixtures: Path, controls: Path | None) -> list[dict]:
    rows = []
    for f in load_jsonl(fixtures):
        rows.append({"id": f["id"], "category": f["category"], "prompt": f["prompt"], "relevant": f["relevant_source_ids"],
                     "expected_route": f["expected_route"], "expected_gate": f["expected_gate"]})
    if controls:
        for c in load_jsonl(controls):
            if c.get("split") != "TRAIN":
                raise ValueError(f"control {c.get('id')} is not TRAIN")
            rel = c["expected_source_ids"]
            # regression controls: the question alone, and wrapped in the bare answer-instruction header
            rows.append({"id": c["id"], "category": "control_train", "prompt": c["prompt"], "relevant": rel,
                         "expected_route": "external_fact", "expected_gate": "retrieve"})
            rows.append({"id": c["id"] + "+hdr", "category": "control_train_hdr", "prompt": BARE_HEADER + c["prompt"],
                         "relevant": rel, "expected_route": "external_fact", "expected_gate": "retrieve"})
    return rows


def first_relevant(hits: list[dict], relevant: list[str]) -> int | None:
    return next((h["rank"] for h in hits if h["source_id"] in relevant), None)


def ablate(retrieval, idx, graph, rows: list[dict]) -> dict:
    per_case, table = [], {}
    for v in VARIANTS:
        stats = Counter()
        for row in rows:
            q = build_query(retrieval, row["prompt"], v)
            hits = rank(retrieval, idx, graph, q)
            fr = first_relevant(hits, row["relevant"]) if row["relevant"] else None
            rec = {"variant": v, "id": row["id"], "category": row["category"], "query_sha256": q["sha256"],
                   "years": q["years"], "bce_years": q["bce_years"], "masked_numbers": q["masked_numbers"],
                   "top5": [h["chunk_id"] for h in hits], "first_relevant_rank": fr,
                   "top1_year_boosted": hits[0]["year_boosted"] if hits else 0}
            per_case.append(rec)
            if row["relevant"]:
                stats["n"] += 1
                stats["hit1"] += fr == 1
                stats["hit3"] += fr is not None and fr <= 3
                stats["hit5"] += fr is not None
                stats["rr"] += 1 / fr if fr else 0
                stats["top1_irrelevant_yearboosted"] += fr != 1 and rec["top1_year_boosted"] > 0
            stats["cases_with_years"] += bool(q["years"] or q["bce_years"])
        n = stats["n"] or 1
        table[v] = {"n_relevant": stats["n"], "hit@1": stats["hit1"], "hit@3": stats["hit3"], "hit@5": stats["hit5"],
                    "MRR@5": round(stats["rr"] / n, 3), "top1_wrong_and_year_boosted": stats["top1_irrelevant_yearboosted"],
                    "cases_with_boost_years": stats["cases_with_years"]}
    # per-category breakdown and wins/losses against base at hit@1
    by = {(r["variant"], r["id"]): r for r in per_case}
    cats = sorted({row["category"] for row in rows if row["relevant"]})
    breakdown = {v: {c: sum(1 for row in rows if row["category"] == c and row["relevant"]
                            and by[(v, row["id"])]["first_relevant_rank"] == 1) for c in cats} for v in VARIANTS}
    cat_n = {c: sum(1 for row in rows if row["category"] == c and row["relevant"]) for c in cats}
    changes = {}
    for v in VARIANTS:
        if v == "base":
            continue
        wins, losses = [], []
        for row in rows:
            if not row["relevant"]:
                continue
            b, x = by[("base", row["id"])]["first_relevant_rank"], by[(v, row["id"])]["first_relevant_rank"]
            bb, xx = b or 99, x or 99
            if xx < bb:
                wins.append(f"{row['id']} {b}->{x}")
            elif xx > bb:
                losses.append(f"{row['id']} {b}->{x}")
        changes[v] = {"better_rank": wins, "worse_rank": losses}
    return {"table": table, "hit@1_by_category": breakdown, "category_n": cat_n, "changes_vs_base": changes,
            "per_case": per_case}


def evaluate_pipeline(retrieval, idx, graph, rows: list[dict]) -> dict:
    res, conf = [], Counter()
    for row in rows:
        sel = select_evidence(retrieval, idx, graph, row["prompt"])
        passed = sel["passage"] is not None
        relevant_pass = passed and sel["passage"]["source_id"] in row["relevant"]
        exp_retrieve = row["expected_gate"] == "retrieve"
        outcome = ("inserted_relevant" if relevant_pass else "inserted_irrelevant" if passed
                   else "abstained_correct" if not exp_retrieve else "abstained_missed")
        conf[outcome] += 1
        conf["route_ok"] += sel["route"]["route"] == row["expected_route"]
        res.append({"id": row["id"], "category": row["category"], "expected_route": row["expected_route"],
                    "route": sel["route"]["route"], "gate": sel["gate"], "outcome": outcome,
                    "passage": {k: sel["passage"][k] for k in ("chunk_id", "source_id")} | {"chars": len(sel["passage"]["text"])}
                    if passed else None})
    return {"summary": dict(conf), "n": len(rows), "cases": res}


# --------------------------------------------------------------------------------------
# prepare an opt-in runner input
# --------------------------------------------------------------------------------------

def pair_order(case_id: str) -> str:
    return sha256_text("issue96-pairs:" + case_id)


def cmd_prepare(args) -> dict:
    guard = pbr.guard_network()
    root = Path(args.root).resolve()
    input_path = Path(args.input)
    output = Path(args.output)
    trace = Path(args.trace) if args.trace else output.with_name(output.name + ".trace.json")
    manifest_path = Path(args.manifest) if args.manifest else root / "staging" / "manifest.json"
    pair_files = []
    if args.pairs:
        pair_files = [output.with_name(output.stem + ".pairs-bare.jsonl"),
                      output.with_name(output.stem + ".pairs-selective.jsonl")]
    protected = [input_path, manifest_path, root / "index" / "bm25_index.json", root / "index" / "graph.json",
                 root / "sources" / "sources.jsonl", root / "scripts" / "retrieval.py"]
    input_bytes = input_path.read_bytes()
    cases = pbr.parse_cases(input_bytes)
    for case in cases:
        protected += [input_path.parent / img for img in case.get("images", [])]
    pbr.check_targets(output, trace, protected)
    for pf in pair_files:
        pbr.check_targets(pf, trace, protected + [output])
    retrieval, idx, graph, identity = pbr.load_pinned_assets(root, manifest_path, args.allow_unpinned)

    rows, per_case = [], []
    for case in cases:
        sel = select_evidence(retrieval, idx, graph, case["prompt"])
        block, stats = "", {"included": [], "evidence_chars": 0}
        if sel["passage"]:
            p = sel["passage"]
            block, stats = pbr.build_evidence([{"title": p["title"], "text": p["text"], "chunk_id": p["chunk_id"]}],
                                              BUDGET_CHARS)
        images, image_records = pbr.map_images(case, input_path.parent, output.parent)
        row = dict(case)
        row["prompt"] = pbr.compose(case["prompt"], block, None)
        if "images" in case:
            row["images"] = images
        assert row["prompt"].endswith(case["prompt"]) and row["id"] == case["id"]
        rows.append(row)
        q = sel["query"]
        per_case.append({
            "id": case["id"], "route": sel["route"], "changed": bool(block),
            "query": None if q is None else {k: q[k] for k in ("variant", "sha256", "chars", "years", "bce_years",
                                                               "masked_numbers", "year_boost", "entity_boost")},
            "ranked": [{k: h[k] for k in ("rank", "chunk_id", "source_id", "score", "bm25", "year_boosted")} for h in sel["ranked"]],
            "gate": sel["gate"], "included_chunk_ids": stats["included"], "evidence_chars": stats["evidence_chars"],
            "input_prompt_sha256": sha256_text(case["prompt"]), "output_prompt_sha256": sha256_text(row["prompt"]),
            "images": image_records,
        })
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    changed = [c["id"] for c in per_case if c["changed"]]
    pairs = sorted(changed, key=pair_order)[: args.pairs] if args.pairs else []
    routes = Counter(c["route"]["route"] for c in per_case)
    report = {
        "status": "prepared_not_launched", "issue": 96, "created_at": si.now_iso(), "model_calls": 0,
        "network": guard, "fetch_or_rebuild": False,
        "settings": {"variant": SELECTED_VARIANT, "variant_flags": VARIANTS[SELECTED_VARIANT], "rank_k": RANK_K,
                     "gate": {"min_idf": GATE_MIN_IDF, "min_terms": GATE_MIN_TERMS, "min_coverage": GATE_MIN_COVERAGE,
                              "min_title_terms": GATE_MIN_TITLE_TERMS, "generic_words_sha256": sha256_text(GENERIC_WORDS)},
                     "window_chars": WINDOW_CHARS, "budget_chars": BUDGET_CHARS, "max_passages": 1,
                     "layout": "[#57 evidence block with one compact passage] + original prompt (verbatim suffix); "
                               "unrouted/gated-out cases byte-identical to input"},
        "input": {"file": str(input_path), "sha256": pbr.sha256_bytes(input_bytes)},
        "output": {"file": str(output), "sha256": pbr.sha256_bytes(payload), "bytes": len(payload)},
        "index": identity,
        "builder": {"file": str(Path(__file__).resolve()), "sha256": pbr.sha256_bytes(Path(__file__).read_bytes()),
                    "prepare_bounded_rag_sha256": pbr.sha256_bytes(Path(pbr.__file__).read_bytes())},
        "summary": {"cases": len(rows), "routes": dict(routes), "changed": len(changed), "unchanged": len(rows) - len(changed)},
        "pairs": {"requested": args.pairs, "ids": pairs, "order": "sha256('issue96-pairs:'+id) ascending over changed cases"},
        "cases": per_case,
    }
    for target in [output, trace] + pair_files:
        target.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "xb") as f:
        f.write(payload)
    if pair_files:
        # bare pair = the output row with the original prompt restored, so image paths resolve from the same dir
        by_id_in = {c["id"]: dict(r, prompt=c["prompt"]) for c, r in zip(cases, rows)}
        by_id_out = {r["id"]: r for r in rows}
        for pf, source in zip(pair_files, (by_id_in, by_id_out)):
            data = "".join(json.dumps(source[i], ensure_ascii=False) + "\n" for i in pairs).encode("utf-8")
            with open(pf, "xb") as f:
                f.write(data)
            report["pairs"][pf.name] = {"file": str(pf), "sha256": pbr.sha256_bytes(data)}
    with open(trace, "x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    report["trace_file"] = str(trace)
    return report


def load_assets(args):
    root = Path(args.root).resolve()
    manifest = Path(args.manifest) if args.manifest else root / "staging" / "manifest.json"
    return pbr.load_pinned_assets(root, manifest, args.allow_unpinned)


def cmd_ablate(args) -> dict:
    guard = pbr.guard_network()
    retrieval, idx, graph, identity = load_assets(args)
    rows = fixture_set(Path(args.fixtures), Path(args.controls) if args.controls else None)
    result = {"issue": 96, "model_calls": 0, "network": guard, "index": identity,
              "fixtures": {"file": args.fixtures, "sha256": pbr.sha256_bytes(Path(args.fixtures).read_bytes())},
              "controls": None if not args.controls else
              {"file": args.controls, "sha256": pbr.sha256_bytes(Path(args.controls).read_bytes())},
              "builder_sha256": pbr.sha256_bytes(Path(__file__).read_bytes()),
              "variants": {k: dict(zip(("strip_header", "mask_bib_numbers", "drop_bib_lines", "bce_aware", "year_boost",
                                        "entity_boost"), v)) for k, v in VARIANTS.items()},
              "ablation": ablate(retrieval, idx, graph, rows),
              "pipeline": evaluate_pipeline(retrieval, idx, graph, rows)}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    per_case = result["ablation"].pop("per_case")
    text = json.dumps(result, ensure_ascii=False, indent=1)
    rows = ",\n".join(json.dumps(r, ensure_ascii=False) for r in per_case)
    out.write_text(text[:-2] + ',\n "per_case": [\n' + rows + "\n ]\n}\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("ablate", "prepare"):
        s = sub.add_parser(name)
        s.add_argument("--root", default=str(pbr.DEFAULT_ROOT))
        s.add_argument("--manifest", default=None)
        s.add_argument("--allow-unpinned", action="store_true", help=argparse.SUPPRESS)  # synthetic test roots only
        if name == "ablate":
            s.add_argument("--fixtures", required=True)
            s.add_argument("--controls", default=None, help="TRAIN retrieval queries used as regression controls")
            s.add_argument("--out", required=True)
        else:
            s.add_argument("--input", required=True, help="key-free runner JSONL {id, prompt, images?}")
            s.add_argument("--output", required=True)
            s.add_argument("--trace", default=None)
            s.add_argument("--pairs", type=int, default=0, help="also write N paired bare/selective cases (max 12)")
    args = p.parse_args(argv)
    if args.cmd == "prepare" and not 0 <= args.pairs <= 12:
        p.error("--pairs must be 0-12")
    t0 = time.perf_counter()
    try:
        if args.cmd == "ablate":
            r = cmd_ablate(args)
            print(json.dumps({"out": args.out, "table": r["ablation"]["table"], "pipeline": r["pipeline"]["summary"],
                              "seconds": round(time.perf_counter() - t0, 2)}, ensure_ascii=False, indent=1))
        else:
            r = cmd_prepare(args)
            print(json.dumps({"status": r["status"], "output": r["output"], "trace": r["trace_file"],
                              "summary": r["summary"], "pairs": r["pairs"]["ids"],
                              "seconds": round(time.perf_counter() - t0, 2)}, ensure_ascii=False))
    except (pbr.PrepError, OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
