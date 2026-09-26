# Context selection for complete answer support — issue #15 (@Bukareszt), 2026-09-26

All grades below are **provisional** (automatic proxies on 40 self-authored TRAIN queries + a blind, independent Claude-subagent audit; no human review, no Sol access, no exam questions or keys involved). Started 03:10 Europe/Warsaw, worked in branch `issue-15-Bukareszt-context`.

## 1. Frozen baseline

- Corpus, BM25 index and year/entity graph from #6, rebuilt locally with `retrieval.py fetch` / `index` / `graph`: 107 sources, 3481 chunks, **0 revision drift**, index SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429` (identical to `reports/index_meta.json`). The three files `fetch` rewrites with new timestamps (`sources.jsonl`, `fetch_failures.json`, `index_meta.json`) were restored from git so the committed manifest stays the audited one.
- Queries: `queries/train_queries.jsonl`, 40 TRAIN queries, SHA-256 `b2e359bf2501469a216f178ad76511d45604e61ad42d4257fca34d15f82f024d`; per-query prompt hashes in `queries/query_hashes.json`. Unchanged.
- Baseline context = `retrieval.rank(mode="chrono", title_weight=1.0)` top-k chunks with full text: `baseline3` (k=3, the configuration audited in #6: 16/40 top-1 and 22/40 "≥1 supported chunk in top-3") and `baseline5` (k=5, what `scripts/prepare_rag.py` uses, though that adapter also truncates each hit to ≤1000 chars).

## 2. Candidate (`scripts/context_select.py`, additive, imports the frozen `retrieval.py`)

Section-aware re-ranking of a chrono candidate pool + budgeted multi-chunk assembly:

1. pool = chrono top-40;
2. **anchor**: the chrono top-1 chunk always goes first (no regression at rank 1 by construction);
3. **article prior** `A(article) = best chrono score of the article / top score` decides *across* articles;
4. **within-article section score** = 0.5 · residual BM25 (query minus the article's own title terms, normalised inside the article) + 0.3 · non-title query-term coverage + 0.2 · chrono score; combined `0.6·A + 0.4·within`;
5. greedy assembly under a **3000-char budget**, ≤3 chunks per article, ≤6 chunks;
6. `candidate_c`: same selection with evidence-retaining sentence compression (keep sentences with a query term or a year plus the chunk's first sentence, `[…]` between gaps), ≤8 chunks;
7. `candidate_t` (**unaudited**, added after the audit sample was frozen): like `candidate` but a non-anchor chunk needs `A ≥ 0.5`, which drops "filler" chunks from distant articles.

Output hits keep the `retrieval.rank` shape (`rank`, `score`, `chunk_id`, `source_id`, `title`, `locator`, `text`, plus `text_full` and `why`), so a `prepare_rag.py`-style consumer could use them unchanged. Nothing in the runner, contracts, index, graph or queries was modified.

A first design that applied the residual score *across* articles was worse than the baseline (evidence-in-context 0.775 vs 0.925): removing the title terms penalises exactly the right article, since siblings keep those terms. It was dropped before any audit. A small sweep (article weight 0.5–0.8, per-article 2–3, compression on/off, residual/coverage weights) is flat on the automatic proxies; the anchor and the article prior dominate, so the defaults are not tuned to the query set beyond that choice.

## 3. Automatic proxies (40 TRAIN queries; `reports/ctx_eval_ctx15.json`, `reports/ctx_eval_per_query_ctx15.jsonl`)

`evidence in context` = at least one selected chunk is from the expected source and (expected section prefix or `must_contain` string) — it accepts any chunk of the expected section, so it overstates support. `must_contain all` = every `must_contain` string occurs in the concatenated context.

| variant | evidence in context | must_contain all | expected source in context | MRR(evidence) | mean chars (max) | mean chunks | mean articles | ms/query |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline3 | 0.925 | 0.850 | 1.000 | 0.829 | 2919 (4343) | 3.00 | 1.43 | 0.5 |
| baseline5 | 0.950 | 0.925 | 1.000 | 0.835 | 4992 (7044) | 5.00 | 1.77 | 0.5 |
| **candidate** | **0.975** | 0.850 | 1.000 | 0.852 | 2861 (2999) | 3.62 | 1.90 | 4.5 |
| candidate_c (compressed) | 0.975 | 0.875 | 1.000 | 0.852 | 2897 (2996) | 4.60 | 2.38 | 5.9 |
| candidate_t (unaudited, thresholded) | 0.975 | 0.850 | 1.000 | 0.852 | 2739 (2999) | 3.23 | 1.48 | 4.5 |

Per query, candidate vs baseline3: 1/40 identical contexts, on average 1.9 shared chunks and 1.7 new chunks. Proxy wins: q02 (ostracyzm: the Kleisthenes-reforms section enters), q08 (Grunwald: "Przebieg bitwy" enters). Proxy loss: q36 loses a `must_contain` string. The candidate reaches the same evidence at equal or shorter length than baseline3 and ~43 % shorter than baseline5. Runtime is pure Python, ≈4.5 ms/query (vs 0.5 ms), negligible next to model inference.

## 4. Blind independent audit of complete answer support (provisional)

Setup: `audit-sample --tag ctx15 --baseline baseline3 --candidate candidate --seed 15` writes 40 blind pairs (`audit/ctx_audit_sample_ctx15.jsonl`, SHA-256 `a992e3e6f08ccbb9f96cd8cbf0b5eca761f74d0dd2ac7ad5640d11c69ec4a958`); which side is the candidate is randomised per query (19 swaps) and recorded only in `audit/ctx_audit_key_ctx15.json`. Two fresh-context Claude subagents (claude-fable-5-1, q01–20 and q21–40) saw only their half of the sample, not the key, queries, reports or scripts, and judged each **whole context** from passage text only: `complete` (every claim element confirmable, combining passages allowed) / `partial` / `none`, plus unsupported claim elements, contradictions and a preferred side. Verdicts: `audit/ctx_audit_verdicts_ctx15{,_part1,_part2}.jsonl` (merged SHA-256 `72a496fb2e2ac91b9a81a8a2eb0c4b5c7174cdd06596a6ed9a6790b95155829e`); score: `reports/ctx_audit_score_ctx15.json`.

| context (40 queries) | complete | partial | none | complete or partial | unsupported claim elements | preferred | mean chars |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline3 (chrono top-3) | **14** | 24 | 2 | 38 | 51 | 6 | 2919 |
| candidate | **13** | 26 | 1 | 39 | 51 | 8 | 2861 |
| tie | | | | | | 26 | |

**Result: no measurable gain.** Complete support 13 vs 14 of 40 is within auditor noise (±2 is one borderline call); the candidate changes the outcome class for only 2 queries (1 win, 1 regression) and is "preferred" 8 vs 6 times with 26 ties. The unsupported-claim-element count is identical (51 each). The candidate is ~2 % shorter than baseline3 and ~43 % shorter than the k=5 context that `prepare_rag.py` builds.

Examples (chunk ids are `retrieval.py` chunk numbers):

- **Win, q02 "Na czym polegał ostracyzm?"**: baseline3 = intro + "Ateny" + "Zgromadzenie Ludowe" chunks → `none` (ostracism never mentioned). Candidate keeps the intro anchor and adds the "reformy Klejstenesa" section (#0019, residual score 1.0) which says "Wprowadzono ostracyzm (tzw. sąd skorupkowy)" → `partial` (10-year exile and purpose still absent: the corpus article never states them compactly).
- **Regression, q39 "Dlaczego Polska nie przystąpiła do planu Marshalla?"**: baseline3's rank-2 intro chunk #3219 ("latem 1947 … odrzucony przez Stalina, a na jego polecenie także przez rządy Polski i Czechosłowacji") gives `complete`. The candidate's within-article re-rank prefers "Przymusowa odmowa bloku wschodniego" #3242 (higher coverage of *polska*, *odrzuci-*, *nacisk-*), which supports the reason but dates Cyrankiewicz's reversal to 1948 → `partial` **with a contradiction flag** against the claim's 1947. Both statements are true of different events; this is the same corpus inconsistency noted in #6.
- **Preferred but same class, q09 (II pokój toruński)**: candidate swaps the second intro chunk for "Postanowienia II pokoju toruńskiego > Zmiany terytorialne" #0765, which lists Malbork/Elbląg and Prusy Zakonne as fief; still `partial` because the label "Prusy Królewskie" is never stated.
- **Baseline preferred, q16 (three partitions)**: the candidate drops the intro chunk #1207 (span 1772–1795 and the three states) for "Granice między zaborcami" and a filler chunk from a different article; both `partial`.
- **Unsupported claims that no context fixes** (both sides `partial`/`none`): q13 (sejm consent for taxes), q20 (attack on the cavalry barracks), q33 (nothing usable in either context), q38 (9 Nov 1989 only inferable), q40 ("cuius regio, eius religio" never named), q31 (only "dwumiesięcznych walk"). These are corpus/phrasing gaps, not selection errors.
- **Claim doubt raised by an auditor**: q26 ("Wileńszczyzna nie była przedmiotem traktatu" is imprecise: the Riga line placed the Wilno region on the Polish side; only the Polish–Lithuanian dispute lay outside the treaty). The query file already carries the #6 correction note for q26; wording kept as is for reproducibility of the sample.

## 5. Audit uncertainty

- The whole-context "complete" standard here (every claim element) is stricter than the #6 per-chunk "supported" standard, and the auditors differ: baseline3 gets 14/40 complete contexts here vs "22/40 queries with ≥1 supported chunk in top-3" in #6 for the same chunks. Treat absolute numbers as auditor-dependent; the paired comparison on identical queries is the meaningful part.
- Auditors reported borderline calls applied to both sides (q04 entailment from a general ban, q07 "poślubić Jadwigę" via framing, q14 "wezyr" vs "wielki wezyr", q15 free election via "dziedziczny", q27/q35 completeness by combining passages, q31 partial on one phrase, q36 preference as a judgment call). ±2 complete counts is noise.
- Same model family as the query author and the candidate designer (no Sol access, no human), so independence is partial; the blind randomised sides remove the most obvious bias (knowing which context is "new").
- In most queries both contexts share their decisive passage (mean 1.9 shared chunks), which is why 26/40 are ties; the audit had little room to separate the variants.
- `candidate_c` (compression) and `candidate_t` (filler threshold) were **not audited**; compression alters the text the auditor sees and was left out to keep the auditor load at one pair per query.

## 6. Failures and limitations

- **Why no gain:** chrono top-1 is already the right article in 38/40 cases and the right passage in ~30/40 on the automatic proxy; the remaining misses are mostly *the corpus never states the fact compactly* (q02, q13, q20, q31, q33, q38, q40), which no re-selection over the same 3481 chunks can fix. Where a better section exists (q02, q08, q09) the candidate finds it; where the intro was the best summary (q16, q39) the section re-rank displaces it.
- **Filler chunks:** with a 3000-char budget and ≤3 chunks per article, the 4th–6th slots often go to low-scoring chunks from unrelated articles (q02 got a French-Revolution chunk, q16 a Wehrmacht-crimes chunk). `candidate_t` (article prior ≥ 0.5) removes them on the proxy at −120 chars with identical evidence numbers, but is unaudited.
- **Within-article re-rank can displace the intro** (q16, q39): coverage rewards sections that repeat the query's nouns, while the intro sentence that states the fact once scores lower. A "keep the intro if it contains a query year" rule would fix q39 but is a post-hoc patch on 40 queries; not applied.
- **Tuning risk:** all decisions used the 40 TRAIN queries; no VALIDATION/SEALED_TEST data was read. The sweep was flat, so little was tuned, but the query set is small and author-biased.
- Pure Python, 4.5 ms/query; no model, no paid API, no purchases; nothing outside `agentsLog/Bukareszt/` touched.

## 7. Recommendation and next steps (lead's decision)

- **Do not wire the candidate into the answerer on this evidence.** Keep `retrieval.py --mode chrono --k 5` as the retrieval baseline; the candidate is equivalent on complete support and only ~2 % shorter at k=3-equivalent length.
- The one thing worth taking: the **blind A/B whole-context audit protocol** (`audit-sample` / `audit-score`) is reusable for the lead's separate model-output comparison and for any future context change.
- If context length matters for the local Qwen runner, `candidate_t` at a 3000-char budget delivers the same automatic evidence as chrono top-5 at 55 % of the characters; it should be audited the same way before use.
- Real gains need corpus work, not selection work: more sources on the failure topics (Athenian institutions, PRL-era decisions, 1989), and possibly sentence-level chunks for intro paragraphs.
