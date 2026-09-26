# Issue #96: retrieval query decontamination, evidence router, relevance gate

Worker: @Bukareszt (Greg's issue watcher, Orca worktree `issue-96-Bukareszt-selective-rag`), 26 September 2026, 18:41–19:30 CEST.
**CPU only. Zero model calls, no GPU, no network** (the `stage_index` socket guard is installed and self-tested before any asset is read), no May 2025 data, no validation keys/answers/rubrics/IDs, no new corpus or retriever, no classifier training. The pinned 107-source / 3,481-chunk index `350800b1…0429` was staged from the #44 bundle and is unchanged.

Everything is **opt-in** in `scripts/Bukareszt/selective_rag.py`. The shared `scripts/prepare_rag.py`, `infer.py`, the evaluator, the #57 bounded builder and the production retrieval default (whole original prompt, chrono, as-is) are not modified.

## Reproduce

```bash
python3 scripts/Bukareszt/stage_index.py stage                      # once per worktree (bundle from #44)
python3 agentsLog/Bukareszt/issue96/fixtures/make_fixtures.py       # rewrites the 37 synthetic fixtures (deterministic)
python3 scripts/Bukareszt/selective_rag.py ablate \
  --fixtures agentsLog/Bukareszt/issue96/fixtures/synthetic_fixtures.jsonl \
  --controls agentsLog/Bukareszt/queries/train_queries.jsonl \
  --out agentsLog/Bukareszt/issue96/ablation.json                   # ~1.3 s
python3 -m unittest -v scripts.Bukareszt.test_selective_rag          # 16 tests; pinned tests skip without a staged index
```

Hashes (SHA-256): fixtures `b6bf4160…f077`, TRAIN controls `b2e359bf…024d`, `ablation.json` result embeds the builder hash and index identity. CI does not discover `scripts/Bukareszt/` tests; they were run locally (`test_selective_rag` 16, with `test_prepare_bounded_rag` and `test_stage_index`: 67 tests OK).

## Fixtures

`fixtures/synthetic_fixtures.jsonl`: **37 original synthetic items** (28 initial + 9 added after root's review) written for #96 (generator `fixtures/make_fixtures.py`). Source passages, questions and bibliographic entries are invented (authors, titles and editions are fictitious); none are copied or paraphrased from any matura sheet, key, rubric or source pack. Relevance labels (`relevant_source_ids`, `expected_route`, `expected_gate`) were fixed before the first ablation run. Categories: publication-year contamination (5), bibliography whose title carries the topic (3), BCE dates (4), ambiguous/century-only dates (3), plain external facts with bare/organizer headers (4), supplied-source-only (3+2), outside the pinned corpus (4), essays (2+3), same-entity/wrong-relation (4).
Regression controls: the 40 TRAIN retrieval queries from #6 (`queries/train_queries.jsonl`, split TRAIN, `expected_source_ids`), both raw and wrapped in the generic bare validation header. Relevance is judged at source level (any `relevant_source_ids` article), top-5.

## 1. Isolated query ablations (ranking only)

`base` is the production chrono query (whole original prompt). Each other row changes one thing; the answering prompt is never changed.

| variant | pub-year contam. (5) | useful bibliography (3) | BCE (4) | ambiguous date (3) | ext. fact (4) | TRAIN (40) | TRAIN+header (40) | hit@1 / hit@3 / MRR@5 (99) | wins / losses vs base |
|---|---|---|---|---|---|---|---|---|---|
| base | 2 | 3 | 4 | 3 | 4 | 38 | 36 | 90 / 95 / 0.939 | – |
| A header removal | 3 | 3 | 4 | 3 | 4 | 38 | 38 | **93 / 98 / 0.961** | 6 / 2 |
| B publication-number masking | 2 | 3 | 4 | 3 | 4 | 38 | 36 | 90 / 96 / 0.939 | 1 / 0 |
| C year boost off (entity boost kept) | 2 | 3 | 3 | 3 | 4 | 38 | 35 | 88 / 95 / 0.927 | 1 / 2 |
| C2 all chrono boosts off (BM25) | 2 | 3 | 3 | 3 | 4 | 37 | 34 | 86 / 93 / 0.906 | 1 / 7 |
| D whole-bibliography deletion | 2 | 2 | 4 | 3 | 4 | 38 | 36 | 89 / 95 / 0.936 | 2 / 2 |
| E BCE-aware year matching | 2 | 3 | 3 | 3 | 4 | 38 | 36 | 89 / 94 / 0.931 | 0 / 1 |
| F = A+B+E | 3 | 3 | 3 | 3 | 4 | 38 | 38 | 92 / 98 / 0.955 | 6 / 3 |
| G = A+B, BM25 | 3 | 3 | 3 | 3 | 4 | 37 | 37 | 90 / 96 / 0.939 | 5 / 6 |
| **H = A+B (selected query)** | 3 | 3 | 4 | 3 | 4 | 38 | 38 | **93 / 98 / 0.961** | 6 / 2 |

Wins/losses (first relevant rank, base → variant) are listed per case in `ablation.json` (`changes_vs_base`).

- **A, header removal, is the main effect.** Wins: syn-pub-03 3→1, syn-pub-04 miss→2, four header-wrapped TRAIN controls (4→3, 2→1, 2→1, 4→1). Losses: syn-pub-02 (Grunwald) 4→miss, one control 1→2. The generic header's words (`źródeł`, `ikonograficzny`, `kartograficzny`, `prawda/fałsz`…) steer BM25 toward unrelated chunks.
- **B, publication-number masking** (digits inside detected bibliography lines only; titles and authors kept) is low-risk: 1 win (4→3), 0 losses. It also removes page numbers that the year regex treats as years (`s. 112`, `s. 233` → pseudo-years 112 and 233).
- **D, deleting whole bibliography lines,** reproduces the root diagnostic's trade-off: fixes Grunwald 4→1 but loses the useful-title Luther/Worms case 1→2 and a Warsaw-Confederation hit 1→4. Not selected.
- **C/C2, disabling chrono boosts, hurts** (2 and 7 losses). Keep chrono.
- **E, BCE handling (negative result).** The pinned corpus often writes ancient years without an era marker (e.g. a king's reign given as `(534* – 509*)`), so the unsigned number collision helps ancient queries; strict BCE-aware matching loses the Roman Republic case. No chronology is invented in either variant (centuries are never converted to years). The selected query keeps production year handling; BCE years are recorded in the trace.

Selected query **H = A+B**: generic header/footer/answer-format templates removed and bibliography numbers masked, chrono boosts on. On these fixtures it equals A; B is kept because it removes the demonstrated publication-year/page-number boost path at zero observed cost.

## 2. Question-only evidence router (revised after root's review of `e19d3c4`)

`route(prompt)` sees the prompt string only (no evaluator `task_type`, keys, answers, IDs or grades; these labels derive from marking rules and are never features). Template text is removed first; command sentences are found by imperative verbs or a closing `?`.

| route | rule (summary) | retrieval |
|---|---|---|
| essay | `wypracowanie`, `rozprawka`, `esej`, `dłuższa wypowiedź`, `wypowiedź argumentacyjna/pisemna`, any word-count requirement (`co najmniej 300 słów`, `około 250 słów`), a 10+ point range, or ≥ 2 long-form cues (thesis / arguments / conclusion / introduction) | never (excluded initially) |
| supplied_source | the command is restricted to the material (`na podstawie tekstu/źródła/ilustracji…`) **without** `własnej wiedzy`, whatever the answer verb (`podaj nazwę`, `wyjaśnij`…); or cites the material with no external cue | never |
| mixed | supplied material present, the command is not restricted to it, and it asks beyond it (`własnej wiedzy`, `podaj nazwę`, `o którym mowa`, `wyjaśnij`, `oceń`…) | gated, one passage |
| external_fact | no supplied material; also plain questions ending in `?` | gated, one passage |
| ambiguous | material but no recognised command/cue | never (bare fallback) |

Router agreement with the fixture labels: 117/117. The rules were written alongside these fixtures, so this is an implementation check, not an accuracy estimate.

## 3. Relation-aware relevance gate on one compact passage (revised)

The review showed that an entity match (e.g. a title) is not relation evidence. The gate is now evaluated on the **final compact window** that would be inserted, not on the whole chunk or the title:

1. Distinctive terms: idf ≥ 3.0, not digits, not generic exam-instruction/question words (`GENERIC_WORDS`, a fixed vocabulary list not derived from any item).
2. From the question's command sentences, three kinds of term are removed:
   - the **answer-type noun** after `nazwę/imię/nazwisko/rok/datę` (`nazwę konfliktu`: the passage need not say "konflikt");
   - **capitalised entity names**;
   - the hit's **article-title terms**.
   What remains are **relation terms** (e.g. `żeglarstwa` in "imię nauczyciela żeglarstwa X").
3. The top-1 chunk is cut to the best contiguous sentence window ≤ 480 characters, preferring relation terms (verbatim corpus text only).
4. Pass conditions:
   - **If relation terms exist:** the window must contain ≥ 1 of them, and ≥ 2 question/description terms must be supported in window + title (≥ 3 for mixed).
   - **If not** (identify-what-is-described questions): ≥ 2 distinctive description terms must be in the window itself (≥ 3 for mixed).
   - **Date requests** also need a 3–4 digit number in the window.
5. Otherwise **zero hits**, and the prompt is unchanged.

A passing window goes into the #57 untrusted-reference block (≤ 800 characters in total), followed by the complete original prompt as a verbatim suffix.

New independent fixtures, labels fixed when written: 4 same-entity/wrong-relation/no-answer distractors, 2 source-only prompts with answer verbs, 3 essays phrased without "wypracowanie". Disclosure: the capitalised-name exclusion was added *after* these fixtures showed syn-rel-01 (Stefan Batory + lute teacher) passing on the name terms, so the wrong-relation row is not a clean held-out test. The fixture set is now 37 items; SHA-256 `b6bf4160f705a0c8b941354668229772fb52e26363856a3df24b407ed0a6f077`.

| category | n | inserted relevant | inserted irrelevant | abstained (correct) | abstained (missed) |
|---|---|---|---|---|---|
| pub-year contamination | 5 | 1 | 1 | 0 | 3 |
| useful bibliography | 3 | 1 | 0 | 0 | 2 |
| BCE | 4 | 4 | 0 | 0 | 0 |
| ambiguous date | 3 | 2 | 0 | 0 | 1 |
| external fact | 4 | 2 | 0 | 0 | 2 |
| supplied source | 5 | 0 | 0 | **5** | 0 |
| out of corpus | 4 | 0 | 0 | **4** | 0 |
| essay | 5 | 0 | 0 | **5** | 0 |
| wrong relation | 4 | 0 | 1 | **3** | 0 |
| TRAIN | 40 | 21 | 1 | 0 | 18 |
| TRAIN + header | 40 | 21 | 1 | 0 | 18 |

**Totals:**

| | before review (`e19d3c4`) | after review |
|---|---|---|
| relevant insertions | 80 | 52 |
| irrelevant insertions | 5 | 4 |
| correct abstentions | 9 | 17 |
| missed abstentions | 14 | 44 |

The revision deliberately trades recall for precision. That follows the full bounded-RAG result, where irrelevant context hurt.

The remaining irrelevant insertions:
- **Two top-1 ranking errors** that also contain the requested relation words: syn-pub-04 (Duchy of Warsaw instead of the Congress of Vienna) and one TRAIN control.
- **syn-rel-02:** the passage lists monuments of Bolesław Chrobry in Gniezno and names one sculptor, but not the maker of the *oldest* monument. This near-relation distractor is the residual risk of a lexical gate.

Thresholds and the vocabulary lists were set on these fixtures and controls, so all numbers are **in-sample**.

## Limitations

- Fixtures are small and author-written; all are rank/relevance checks, not score evidence. No generated answer has been produced or graded.
- Source-level relevance: a relevant article does not prove the passage contains what the question needs.
- Router and gate are lexical rules (a near-relation passage can still pass, see syn-rel-02); the organizer package prompt and the validation bare prompt use different templates, both removed from the query. Unknown future templates would stay in the query (same as production today).
- The coverage of the real 40-item source-v2 input is not measured here: that input is private to root. The `prepare` trace reports route counts, the number of changed cases and per-case gate evidence before any call (see the proposal).

## GPU proposal (run only when root declares a host and a bounded launch)

Hypothesis: on external-fact/mixed questions, one gated compact passage retrieved with a decontaminated query improves or preserves answers against the unchanged bare prompt, without the irrelevant-context damage seen in the full bounded-RAG arm (27/60).

1. **CPU, root-side, before any call** (source-v2 input SHA-256 `6615fea2…15a4`, private):
   ```bash
   python3 scripts/Bukareszt/stage_index.py stage
   python3 scripts/Bukareszt/selective_rag.py prepare \
     --input <private source-v2 runner input> \
     --output agentsLog/kwiscion/private/selective-rag-96/selective.jsonl --pairs 12
   ```
   Writes `selective.jsonl` (all 40; unrouted/gated-out prompts identical, only image-path strings may be re-expressed relative to the output directory), `selective.pairs-bare.jsonl` and `selective.pairs-selective.jsonl` (≤ 12 changed cases, identical IDs/images, order `sha256("issue96-pairs:"+id)`, independent of outcomes), and a trace with input/output/pair hashes, route counts, per-case query hash, ranks, gate evidence and included chunk ID. Inspect the trace coverage first; if fewer than 12 cases change, run only those. Essays are never changed.
2. **GPU:** same frozen base as root's matched bare control on the declared host (Gemma 4 12B Q4, pinned model/projector hashes, same `infer.py` config, context, thinking off, 1024-token output cap, same sampling/temperature setting as the control). Only the input file differs:
   ```bash
   python3 infer.py --config <root's frozen control config> --input …/selective.pairs-bare.jsonl --output …/pairs-bare.raw.jsonl --max-calls 12
   python3 infer.py --config <same config> --input …/selective.pairs-selective.jsonl --output …/pairs-selective.raw.jsonl --max-calls 12
   ```
   Cap: **24 calls**, 24,576 requested output tokens, no retries/warmup/resume. Time: the RTX control ran 40 calls in 146.6 s, so ≈ 2–5 min expected; stop at 20 min wall time. Cost: at the H100's stated $3.28/hour, ≤ 20 min ≈ **$1.10**; $0 on a local GPU.
3. **Review:** independent reviewer(s) grade both arms blind to arm where feasible; I do not grade my own track. A full 40-item candidate only if the paired review shows gains without regressions on previously correct items.

Root owns launch and merge. I do not use the central H100 or Piotrek's RTX.
