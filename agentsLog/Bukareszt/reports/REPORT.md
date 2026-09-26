# Retrieval report — issue #6 (@Bukareszt), 2026-09-26

All grades below are **provisional** (automatic coverage metric + independent Claude-subagent audits; no human review, no Sol access).

## 1. What was built

- **Corpus:** 107 rights-clear Polish sources, 4.07 MB of text. 100 Polish Wikipedia articles (CC BY-SA 4.0, revision pinned by `oldid` permalink + SHA-256) spanning the formula-2023 history curriculum from antiquity to 2004, and 7 Polish Wikisource public-domain primary documents (Konstytucja 3 maja 1791, akt konfederacji warszawskiej 1573, akt targowicki 1792, manifest 22 I 1863, Akt 5 listopada 1916, konstytucja marcowa 1921, manifest PKWN 1944). Source groups: 27 20c-Poland, 13 medieval Poland, 12 early-modern Poland, 9 19c Poland, 12 20c world, 8 early-modern world, 7 medieval world, 6 antiquity, 6 19c world, 7 primary documents.
- **Index:** section-level chunks (max 1200 chars; navigation/bibliography sections dropped) → 3481 chunks. Pure-Python BM25 (k1=1.5, b=0.75) with two fields: chunk text and title+section path (`--title-weight`, default 1.0). Tokenizer: NFKC lowercase, `\w+`, small stoplist, prefix-6 stem (digits untouched). Build 0.7 s; index 9 MB JSON; deterministic SHA-256 `350800b1…0429`.
- **Modes:** `bm25`; `hybrid` (0.6·BM25 + 0.4·char-4-gram TF-IDF cosine, ~45 ms/query); `chrono` (BM25 + 0.15·top-score boost per matching year/entity from a year→chunk and article-title→chunk graph, `graph.json`); `twostage` (article-major, residual-query re-rank; negative result).
- **Query set:** 40 TRAIN queries (`queries/train_queries.jsonl`), authored from general knowledge, 21 Poland-20c/19c, 11 medieval/early-modern Poland, 8 world. Each has `expected_source_ids`, `expected_locators` (section-path prefixes) and `must_contain` evidence strings verified to occur in the expected source. Labeled synthetic (generator claude-fable-5-1, 2026-09-26), rights-clear, provisional.

## 2. Top-k evidence coverage (automatic; 40 queries)

`source@k` = an expected source in top-k. `evidence@k` = a chunk from an expected source whose section matches an expected locator **or** contains the expected evidence string.

| index | mode | src@1 | src@3 | src@5 | src@10 | ev@1 | ev@3 | ev@5 | ev@10 | MRR(ev) | ms/q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1 (title concatenated) | bm25 | 0.775 | 0.95 | 0.975 | 1.0 | 0.60 | 0.875 | 0.925 | 1.0 | 0.754 | 0.5 |
| v1 | hybrid | 0.85 | 1.0 | 1.0 | 1.0 | 0.65 | 0.95 | 0.95 | 1.0 | 0.795 | 45 |
| v1 | chrono | 0.875 | 1.0 | 1.0 | 1.0 | 0.70 | 0.95 | 0.975 | 1.0 | 0.822 | 0.5 |
| v2 (split fields, tw=1.0) | bm25 | 0.925 | 0.975 | 0.975 | 1.0 | 0.70 | 0.90 | 0.95 | 1.0 | 0.821 | 0.5 |
| v2 | hybrid | 0.95 | 1.0 | 1.0 | 1.0 | 0.725 | 0.90 | 0.975 | 1.0 | 0.830 | 45 |
| v2 | **chrono** | **0.95** | 1.0 | 1.0 | 1.0 | **0.75** | 0.925 | 0.95 | 1.0 | **0.843** | 0.5 |
| v2 | twostage | 0.925 | 0.925 | 0.925 | 0.925 | 0.725 | 0.875 | 0.925 | 0.925 | 0.810 | 1.5 |

Title-weight sweep (v2, `reports/eval_sweep_tw*.json`): tw=1.0 > 0.5 > 0.25 > 0 for every mode (bm25 ev@1: 0.70 / 0.675 / 0.65 / 0.60). Scoring the short title field separately (strong length normalisation) is what lifted v1→v2; down-weighting it hurts.

## 3. Independent citation audit (provisional)

Two fresh-context Claude subagents (claude-fable-5-1, Opus-class reasoning, no access to query authoring) judged each of the top-3 citations **from the chunk text only**: `supported` / `partial` / `unsupported`, plus CONTRADICTS / CLAIM-DOUBT flags. Files: `audit/audit_sample_*.jsonl`, `audit/audit_verdicts*.jsonl`, `reports/audit_score_*.json`.

| audited config | citations | strict precision (supported) | lenient (supported+partial) | top-1 strict | top-1 lenient | queries with ≥1 supported in top-3 | queries with nothing usable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v1 bm25 | 120 | 0.167 (20) | 0.567 (68) | 0.25 (10/40) | 0.625 (25/40) | 18/40 | 3 (q21, q23, q38) |
| v2 chrono | 120 | 0.217 (26) | 0.558 (67) | 0.40 (16/40) | 0.725 (29/40) | 22/40 | 3 (q02, q08, q33) |

Reading: source-level coverage (≥0.925@1) overstates usefulness. On a strict "could a reader confirm the answer from this one chunk" standard, only 40 % of top-1 chunks fully support the claim in the best configuration; a further ~33 % are on-topic but partial. With k=3 passed to a model, 22/40 queries have a fully supporting chunk and 37/40 have at least a partial one. The v1→v2 gain in the audit (top-1 strict 0.25→0.40) agrees in direction with the automatic metric (ev@1 0.60→0.75).

Audit side-findings (the reason to run an audit at all):
- **Claim errors caught in my own query set:** q20 (Belweder was stormed by civilian conspirators, cadets attacked the cavalry barracks), q26 (Wileńszczyzna was not assigned by the Riga treaty), q09 ("odzyskała Warmię" imprecise). Answers corrected in `train_queries.jsonl` with `audit.status = claim-corrected`; the audit samples keep the original wording so the verdict files stay reproducible.
- **One CONTRADICTS flag (v1 q39, rank 2):** chunk dates Cyrankiewicz's change of mind to 1948, claim says Poland refused the plan in 1947. Both are true of different events; kept as a note.
- Auditors disagree at the margin (v1 rated q02 top-1 "supported", v2 "unsupported" for the same intro chunk): the strict/lenient split is genuinely fuzzy; treat ±0.05 as noise.

## 4. Failures and unsupported cases (v2 chrono, top-1 not supported: 24/40)

| pattern | queries | what happens |
| --- | --- | --- |
| Right article, wrong section (entity name swamps the discriminative term) | q02 ostracyzm, q08 Ulrich von Jungingen, q13, q17, q19, q25, q27, q28, q31, q34, q36, q37, q38 | Query terms that equal the article title score in every chunk; the intro or a memorial/controversy section outranks the section that holds the asked fact. The `twostage` residual re-rank attacks exactly this but lost on other queries (unfair across articles; article cap at 3). |
| Wrong article with overlapping vocabulary | q15 (Konstytucja marcowa "zasady ustrojowe" beats Konstytucja 3 maja), q26 (Traktat wersalski beats Traktat ryski), q32, q33 | Generic question words ("postanowienia", "zasady ustrojowe", "traktat") match a sibling article's section heading. |
| Fact is in the source but phrased differently / spread across chunks | q03 (800 coronation), q16 (three partitions listed in separate sections), q18 (only "król saski"), q21 (czerwoni/biali), q23 | The chunk boundary cuts the answer; or Wikipedia does not state the fact compactly. |
| Primary documents rarely retrieved | q12, q15, q21, q24, q33 | Wikisource acts use archaic spelling ("Konstytucya", "Rzczpltej") and no section headings; the prefix stemmer does not bridge them. Only q12/q24 got a Wikisource chunk into the top-3. |
| No expected chunk at all in top-10 | none (ev@10 = 1.0 for chrono) | — |

Fetch failures (fixed): 4 of 104 initial titles were disambiguation/missing pages (`Absolutyzm`, `Traktat ryski`, `Zjednoczenie Niemiec (1871)`, `Referendum ludowe…`); replaced by the exact article titles. `fetch_failures.json` is now empty.

## 5. Rights scan and contamination guard

`scripts/rights_scan.py` (exit 0, `reports/rights_scan.json`): all 107 manifest rows have the CONTRACTS fields and a known license; all raw files match their recorded SHA-256; every committed file that carries a source passage >400 chars is attributed by `source_id` and comes from a redistributable source (CC BY-SA 4.0 or public domain); no repo file has an exam-like name; 40 query prompts hashed (NFKC/lowercase/whitespace) into `queries/query_hashes.json` for a later cross-check against the lead's exam-question hashes (`--exam-hashes` flag). Nothing from the 2023/2024/2025 exams, keys, rubrics or source packs was read or used. No purchases, no paid APIs; ~110 Wikimedia API requests with a descriptive User-Agent.

## 6. Limitations

- **Auditor ≠ Sol.** The issue asks for a Sol evidence audit; no Sol access existed in this session, so the independent check is a separate fresh-context Claude subagent. Same model family as the query author → not fully independent; label stays provisional.
- **Query set is small and author-biased** (40, mostly date/decision questions). ev@k is a proxy: it accepts any chunk of the expected section, which the strict audit shows is often not enough.
- **No exam-style tasks**: no source-analysis tasks over images/maps, no essay planning, no OCR. Retrieval is Polish-only; English Wikipedia was not included.
- **Wikipedia is a tertiary source**; revision pinned but content not fact-checked. Contradictions between chunks exist (q09: 19 Oct vs 31 Dec 1466 for the Toruń treaty signing).
- **Corpus is deliberately small** (107 pages) per the issue's "quality over size" guidance; obvious gaps: Piastowie/Jagiellonowie per-ruler pages, WWII world theatre, PRL economy, ancient Rome details.
- Pure-Python; `hybrid` costs 45 ms/query, fine for 40 queries, not for bulk re-ranking.

## 7. Cheap next steps (not started; for the lead's decision)

1. Pass top-5 `chrono` chunks (≈6 kB) as context to the answerer and measure DEV/VALIDATION deltas in the evaluator's isolated process — retrieval alone cannot be graded against exam keys here.
2. Section-aware scoring: apply the title field once per article (article prior) instead of per chunk, and add a "query-term coverage" bonus; the audit shows this is where 13/24 top-1 misses live.
3. Add ~40 more sources (per-ruler pages, WWII, PRL economy) and a handful of English Wikipedia pages with a translated-query path.
4. Have a human or a different model family re-audit 20 queries to calibrate the strict/lenient boundary.
