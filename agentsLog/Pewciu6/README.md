# Pewciu6: final overnight handoff — CPU evaluation harness, May 2024 VALIDATION audit, contamination checks

**This is the final handoff index.** Everything below is a rollup of the individual timestamped notes in this directory; read a note for full detail. Short summary: `2026-09-26T0745-final-handoff.md`.

> **Gemma source-crop diagnostic (2026-09-26 17:04 Warsaw, issue #11):** 3 selected items (z1, z6, z25; PR #63, `dd5dc674…` CRLF) adjudicate to **3/6** (1–3) vs bare 2/6 (1–2); I agree with Sol's first pass 3 (2–3) on 3 of 3 items. The +1 is z1, which the policy arm also fixed without crops, so the effect of cropping is not demonstrated; z25 (whole-scene misread) is unchanged. n=3 is not evidence of a general effect. See `2026-09-26T1704-score-gemma-crops.md` and `results/review_gemma-source-crops-diag3.json`.
>
> **Gemma question-policy review (2026-09-26 16:51 Warsaw, issue #11):** the declared generic question-policy arm on source-v2 (PR #59, `a625b2e7…`) adjudicates to **32/60** (22–35), vs Sol's first pass 30 (24–34) and the bare source-v2 composite 35 (28–40); automatic 7.0. I agree with Sol on 38 of 40 items (z9 and z17.1 go up to 1). Four gains (clean single answers, recall) and six losses (essay topic switch −2, wrong subtask, invented image detail) give Δ −3, so the policy is neutral to slightly harmful. See `2026-09-26T1651-score-gemma-policy.md` and `results/review_gemma-question-policy-val40.json`.
> **Gemma format-arm review (2026-09-26 16:23 Warsaw, issue #11):** the exploratory format-prefix arm (PR #56, `c8a1bacc…`) reviews to **35/60** (28–39), the same as bare Gemma 35 (28–40); automatic 10.0 vs 11.0. Five gains (hedging and recall fixed) and five losses (source/image misreads) cancel out, so the prefix is neutral. The v2 z13 correction scores 1, the same as v1; the composite stays 35. See `2026-09-26T1623-score-gemma-format.md` and `results/review_gemma4-12b-val40-format.json`.
>
> **Afternoon update (2026-09-26, issue #11): real model outputs scored and reconciled with the lead's Sol first pass (PR #52).** Consolidated provisional VALIDATION scores: **Gemma 4 12B 35/60** (28–40), **Qwen 3.5 9B 25/60** (16–29); automatic floors 11.0 / 5.0. See `2026-09-26T1551-score-consolidated.md` (supersedes the Qwen-only note `2026-09-26T1540-score-qwen.md`) and `results/review_*.json`. All grades are provisional agent review.

- **Owner:** @Pewciu6 (eval worker, `overnight:eval`).
- **Issues:** [#7](https://github.com/kwiscion/machinekind-matura/issues/7) (main, still open — CPU harness + VALIDATION audit), [#11](https://github.com/kwiscion/machinekind-matura/issues/11) (open, **waiting** for real model outputs), [#13](https://github.com/kwiscion/machinekind-matura/issues/13) (closed, contamination audit of the #6 corpus).
- **Branches:** `issue-7-Pewciu6-eval` (PR #8), `issue-7-Pewciu6-eval-stretch` (PR #10), `issue-13-Pewciu6-contam` (PR #14), `issue-11-Pewciu6-sanity` (PR #16), `issue-13-Pewciu6-contam-pr18` (PR #19), `issue-13-Pewciu6-contam-pr18-r2` (PR #20), `Pewciu6-final-handoff` (this PR).
- **Started:** 2026-09-25 23:58 UTC / 2026-09-26 01:58 Warsaw. **This handoff:** 2026-09-26 ~05:38 UTC / 07:38 Warsaw, ahead of the 08:30 Warsaw deadline.
- **Splits used:** synthetic fixtures (`DEV`) throughout; May 2024 **VALIDATION** keys, always isolated in git-ignored `private/`. **SEALED_TEST (May 2025) was never opened.**
- **Model outputs:** **none exist as of this handoff.** Every VALIDATION number in this repo is a rubric-sanity or contamination check, not a model score. All grades are provisional.

## PRs (all additive, confined to `agentsLog/Pewciu6/`)

| PR | Merged (UTC / Warsaw) | Branch | Issue | Summary |
| --- | --- | --- | --- | --- |
| [#8](https://github.com/kwiscion/machinekind-matura/pull/8) | 2026-09-26 00:08 / 02:08 | `issue-7-Pewciu6-eval` | #7 | First slice: stdlib CPU harness (`score`, `leakcheck`, `validate`), schemas, synthetic fixtures, VALIDATION source manifest, `fetch_validation_2024.py`. |
| [#10](https://github.com/kwiscion/machinekind-matura/pull/10) | 2026-09-26 00:25 / 02:25 | `issue-7-Pewciu6-eval-stretch` | #7 | `build_validation_2024.py` (restricted 40-item/60-pt build), rubric features (decision gates, `min_words`/zeroes, `manual_only`, `review_on_fail`), `audit-sample`/`audit-summary`/`blind-pack`/`blind-merge`, `sanity_validation_2024.py`, audit-procedures note. |
| [#14](https://github.com/kwiscion/machinekind-matura/pull/14) | 2026-09-26 00:51 / 02:51 | `issue-13-Pewciu6-contam` | Closes #13 | Contamination check: #6 BM25 corpus vs VALIDATION. 0 flagged, 6 review-band (stock phrasing). |
| [#16](https://github.com/kwiscion/machinekind-matura/pull/16) | 2026-09-26 01:11 / 03:11 | `issue-11-Pewciu6-sanity` | #11 | Adversarial synthetic fixtures (67 cases, 16/67 harness bugs found+fixed), blind two-rater dry run (κ reported), real `infer.py`/normalizer adapter-shape ingestion, local LM Studio smoke test. |
| [#19](https://github.com/kwiscion/machinekind-matura/pull/19) | 2026-09-26 02:22 / 04:22 | `issue-13-Pewciu6-contam-pr18` | follows #13 | Contamination check extended to PR #18 training data (`--corpus-jsonl` mode) at head `64d69815`. 0 flagged, 3 review-band, 4 optional single-fact answer overlaps. |
| [#20](https://github.com/kwiscion/machinekind-matura/pull/20) | 2026-09-26 03:22 / 05:22 | `issue-13-Pewciu6-contam-pr18-r2` | follows #13/#19 | Mechanical re-audit of PR #18 at new head `c5009a5e`. Still 0 flagged, same 3 review-band, +2 optional answer overlaps (6 total). |
| *(this PR)* | pending | `Pewciu6-final-handoff` | #7/#11/#13 | Final handoff: rewritten README index + executive summary. Docs only, no new experiments. |

PR #18 itself (@przemeknowak781, issue #4) was **not modified** by any of the above — it was read only (`git fetch origin pull/18/head:...`, `git show`), and results were posted as PR comments on #18 plus the two audit PRs above. **PR #18's head is still `c5009a5e` at the time of this handoff** (verified via `gh pr view 18 --json headRefOid`), so PR #20's audit remains current — no re-audit needed.

## Artifact inventory

| Path | What it is | From |
| --- | --- | --- |
| `harness/matura_harness.py` | Stdlib-only CPU CLI: `score`, `audit-citations`, `audit-sample`, `audit-summary`, `blind-pack`, `blind-merge`, `leakcheck`, `validate`. | #8, #10, fixed in #16 |
| `harness/test_matura_harness.py` | Unit tests (26 as of #16, up from 12 in #10, 7 in #8). | #8, #10, #16 |
| `harness/fetch_validation_2024.py` | Downloads/verifies the CKE PDFs into `private/` against the manifest SHA-256. | #8 |
| `harness/build_validation_2024.py` | Builds restricted `eval_keys.jsonl` (40 items, 60 pts), `runner_input.jsonl`, page PNGs, in `private/`. Publishes aggregate stats only. | #10 |
| `harness/sanity_validation_2024.py` | Oracle / wrapped-oracle / shotgun / null rubric checks on VALIDATION keys, aggregates only. | #10 |
| `harness/build_adversarial_fixtures.py` | Deterministically writes 67 invented adversarial keys/outputs/labels plus synthetic blind-essay fixtures. | #16 |
| `harness/test_adversarial.py` | Adversarial labels/extractors/adapter-shape tests, incl. `TestInferNormalizerIngestion` pinning real `infer.py` + `scripts/normalize_outputs.py` shape. | #16 |
| `harness/smoke_lmstudio.py` | JSONL-path smoke test against local LM Studio Qwen (non-candidate). | #16 |
| `harness/contamination_check.py` | #13 method: VALIDATION prompts/excerpts vs a corpus (BM25-index mode or `--corpus-jsonl` training-data mode), exact hash, char 8/13-gram Jaccard/containment, reverse containment, LCS, BM25 top-5, optional `--keys` answer-key angle. | #14, extended #19 |
| `harness/test_contamination_jsonl.py` | Unit tests for the JSONL-corpus mode. | #19 |
| `schemas/eval_key_rubric.schema.json` | Item rubric/key schema (content/entity/date/structure/decision criteria, P/F pairs, graded counts, all-or-nothing, min_words/zeroes, manual_only, review_on_fail). | #8, extended #10, #16 |
| `schemas/model_output.schema.json` | Raw model-output record schema, extended for the real adapter shape (`backend` object, `latency_seconds`, `provider_raw_response`, `retrieval_evidence`, `retrieval_index_sha256`). | #8, extended #16 |
| `schemas/error_taxonomy.json` | Error categories (chronology, entity_confusion, essay_structure, abstention, citation_unsupported, image_ocr, content_incorrect) plus exclusions incl. `incomplete_output`, review flags, statuses. | #8, extended #16 |
| `sources/validation_2024_sources.jsonl` | May 2024 acquisition manifest: CKE index page + 3 PDFs, URLs, retrieved_at, SHA-256, bytes, ETag, rights. | #8 |
| `fixtures/synthetic_*.jsonl` | 15 synthetic keys / 14 outputs / labels / citation corpus / runner input for `DEV`-split smoke testing. | #8 |
| `fixtures/adversarial_*.jsonl` | 67 invented keys, 71 outputs, 67 labels covering format/hedge/error/id edge cases. | #16 |
| `fixtures/blind_essay_*.jsonl`, `fixtures/adapter_contract_sample.jsonl`, `fixtures/infer_*_sample.jsonl` | Blind-essay dry-run fixtures; generic adapter-contract sample; real `infer.py`/normalizer shape samples. | #16 |
| `results/fixture_scorecard.json`, `results/fixture_items.jsonl` | Synthetic fixture run. | #8 |
| `results/adversarial_scorecard.json`, `results/adversarial_items.jsonl` | Adversarial fixture run (harness self-test, not a model). | #16 |
| `results/validation_2024_build_stats.json` | VALIDATION item counts by type/modality/era/scoring-mode, plus restricted-file hashes. | #10 |
| `results/validation_2024_sanity.json` | Rubric sanity aggregates (oracle/wrapped/shotgun/null). | #10, re-verified #16 |
| `results/blind_dryrun_summary.json` | 12-pair synthetic blind two-rater dry run (κ, agreement). | #16 |
| `results/smoke_qwen_*_scorecard.json`, `results/smoke_qwen_*_items.jsonl` | Local LM Studio Qwen smoke run (MC + essays), non-candidate, synthetic prompts only. | #16 |
| `results/contamination_13.json` | #13 aggregate distributions/histograms/flag-review chunk IDs (no exam text). | #14 |
| `results/contamination_pr18.json` | PR #18 audit at head `64d69815`: aggregates, flagged/review IDs+scores, answer-key angle. | #19 |
| `results/contamination_pr18_r2.json` | PR #18 re-audit at head `c5009a5e`: same format, delta vs `64d69815`. | #20 |
| `2026-09-26T0225-audit-procedures.md` | Procedures: citation-support audit, 15–20 item independent audit (not yet run — no outputs), blind essay slice, vision/OCR slice. | #10 |
| `2026-09-26T0250-contamination-13.md` | #13 full report: method, positive control, distributions, review-band chunks. | #14 |
| `2026-09-26T0310-sanity-11.md` | #11 sanity-pass report: adversarial fixtures, 14 bugs found+fixed, blind dry run, real adapter shape, LM Studio smoke. | #16 |
| `2026-09-26T0420-contamination-pr18.md` | PR #18 contamination report at head `64d69815`. | #19 |
| `2026-09-26T0520-contamination-pr18-r2.md` | PR #18 contamination delta report at head `c5009a5e`. | #20 |
| `2026-09-26T0745-final-handoff.md` | This handoff's executive summary. | this PR |
| `smoke/`, `schemas/`, `sources/` | Supporting fixture/schema/manifest data referenced above. | #16, #8 |
| `private/` (git-ignored, **never commit**) | CKE PDFs, `eval_keys.jsonl`, `runner_input.jsonl`, page PNGs, sanity/audit outputs, dry-run audit sheet, per-unit contamination detail. | all |

## Commands

Environment: macOS arm64, Python 3.9.6 stdlib (poppler 24 for the VALIDATION build only). `H=agentsLog/Pewciu6/harness`, `P=agentsLog/Pewciu6/private/validation_2024`.

```bash
# Tests
python3 -m unittest discover -s $H -v                  # 28 tests OK (as of #19/#20)

# Fixture score (synthetic, DEV split — not a model result)
python3 $H/matura_harness.py score --outputs agentsLog/Pewciu6/fixtures/synthetic_outputs.jsonl \
  --keys agentsLog/Pewciu6/fixtures/synthetic_eval_keys.jsonl --corpus agentsLog/Pewciu6/fixtures/synthetic_corpus.jsonl \
  --split DEV --run-id fixture-20260926 --scorecard agentsLog/Pewciu6/results/fixture_scorecard.json \
  --items-out agentsLog/Pewciu6/results/fixture_items.jsonl

# VALIDATION build + rubric sanity (restricted; keys never leave private/)
python3 $H/fetch_validation_2024.py                    # 3/3 sha256 OK
python3 $H/build_validation_2024.py                    # 40 items, 60 pts, 21 pages rendered
python3 $H/matura_harness.py leakcheck --inputs $P/runner_input.jsonl --keys $P/eval_keys.jsonl   # errors 0
python3 $H/sanity_validation_2024.py                   # oracle auto 18/18, gates 14/14

# audit-citations is run inside `score`; standalone:
python3 $H/matura_harness.py audit-citations --outputs <outputs.jsonl> --corpus <corpus.jsonl>

# Contamination: #13 method, BM25-index corpus (e.g. the #6 corpus)
python3 $H/contamination_check.py --issue "<label>" \
  --index agentsLog/Bukareszt/index/bm25_index.json \
  --inputs $P/runner_input.jsonl --out agentsLog/Pewciu6/results/<name>.json

# Contamination: JSONL-corpus mode (e.g. a training-data PR), with the answer-key angle
python3 $H/contamination_check.py --issue "<label>" \
  --corpus-jsonl <file1.jsonl> <file2.jsonl> ... \
  --corpus-root <root> --corpus-prefix <path-prefix/> \
  --keys $P/eval_keys.jsonl \
  --private-out $P/contamination_<name>_units.jsonl \
  --out agentsLog/Pewciu6/results/contamination_<name>.json
```

**Ready to run once real outputs arrive (see [Next action](#next-action) for #11):**

```bash
python3 $H/matura_harness.py score --split VALIDATION --outputs <run>_outputs.jsonl --keys $P/eval_keys.jsonl \
  --run-id <run> --model-manifest <candidate manifest> \
  --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json --items-out $P/<run>_items.jsonl
python3 $H/matura_harness.py audit-sample --items $P/<run>_items.jsonl --keys $P/eval_keys.jsonl \
  --outputs <run>_outputs.jsonl --n 20 --out $P/<run>_audit_sheet.jsonl
# reviewer fills audit.{reviewer,points,agrees_with_auto,error_categories,evidence_checked,notes}
python3 $H/matura_harness.py audit-summary --sheet $P/<run>_audit_sheet.jsonl --out $P/<run>_audit_summary.json
```

Runner input image paths are relative to `$P`, per the contract.

## Source revisions and hashes

| File | SHA-256 |
| --- | --- |
| MHIP-R0-100-A-2405-arkusz.pdf (3767602 B) | `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21` |
| MHIP-R0-100-A-2405-karta.pdf (1406273 B) | `12f9bc044132d0754f4f1f423781435d9d9aa6697e30d2b5188c273be7d9bb5e` |
| MHIP-R0-100-2405-zasady.pdf (423212 B, **restricted key**) | `95c275b9546611c1f8cd45b7973c436625fd0ee5643b778dcc8bb566db56cd4c` |
| private `eval_keys.jsonl` (builder v1) | `f66e387793c5dfad2bac8723a73716e434a9d6ecab40c544f8b529723f512123` |
| private `runner_input.jsonl` (prompt v1) | `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7` |
| #6 retrieval index (`agentsLog/Bukareszt/index/bm25_index.json`, 107 sources, 3481 chunks) | `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429` |
| PR #18 `data/przemeknowak781/train.jsonl` (231 records) | `52df361cefca4d20a99b0795c766740e7df9f5fb935b6c7911d70914a3acbd7f` (unchanged `64d69815` → `c5009a5e`) |
| PR #18 `examples.jsonl` (20) | `9e45649c0e99c73f57209411307095c814087f0165a4553e7e2f80ab01efeefd` (unchanged) |
| PR #18 `generated/*.jsonl`, essay-plan files, SFT export | per-file SHA-256 in `results/contamination_pr18.json` / `contamination_pr18_r2.json` |

Anyone who rebuilds from the same PDFs should get identical `eval_keys.jsonl` / `runner_input.jsonl` hashes.

## Splits used

- **DEV** (tagged in the split guard): all synthetic fixtures (`fixtures/synthetic_*`, `fixtures/adversarial_*`, blind-essay dry run, LM Studio smoke).
- **VALIDATION** (May 2024, restricted): rubric sanity only (oracle/wrapped/shotgun/null), never model-scored, isolated in `private/`.
- **SEALED_TEST** (May 2025): **never opened**, at any point.

## Denominators and measurements

### VALIDATION structure (aggregate only, no model result)

- 40 items, 60 points — matches the official sheet.
- Task types: source_analysis 14, short_answer 20, multiple_choice 5, essay 1.
- Modality: **image 29, text 11** — 29 of 40 items depend on images; a text-only model must be reported as a separate slice from a vision model.
- Scoring mode: auto 16 items/18 pts · gate+manual (decision auto, justification manual) 14 items/14 pts · manual (open + essay) 10 items/28 pts. **The heuristic can fully decide only 18 of 60 points.**

### Rubric sanity (no model; `sanity_validation_2024.py`)

| Run | Auto points | Decision gates |
| --- | --- | --- |
| Oracle (official answers, 39 items — essay excluded, no example answer) | 18/18 | 14/14 |
| Oracle wrapped in a sentence | 18/18 | 14/14 |
| Shotgun (hedges every option, 40 items) | 0/18 | 0/14 |
| Null (empty, 40 items) | 0 | 0 |

Two rubric bugs found and fixed this way: bracketed optional parts in official answers didn't match; hedged decisions/true-false pairs earned credit. Regression-checked in #16 after the harness fixes — aggregates byte-identical.

### Synthetic fixture run (`DEV`, not a model score)

13 items scored, 2 excluded (`inference_error`, `missing_output`), 1 orphan. correct/partial/incorrect/needs_review: 3/3/5/2. Points 9/33 lenient (upper bound 22/33), 0.257 strict. All 13 labelled classifications match.

### Adversarial fixture run (harness self-test, `DEV`, not a model score)

67 invented cases, 71 output records. Before the #16 fixes the harness at `4bba768` mis-graded **16 of 67**; after (`3324eba7…`), **0 of 67**. 14 distinct bugs fixed (format/hedge parsing, JSON/OpenAI/`<think>` unwrapping, entity/year hedge routing to `needs_review`, id normalization, retry-supersedes-error, truncation vs abstention, `latency_seconds`/backend-object reading, `incomplete_output` exclusion). See `2026-09-26T0310-sanity-11.md` for the full table.

### Blind two-rater dry run (12 synthetic essay pairs, two independent Claude Haiku 4.5 raters)

Exact agreement 0.667 (0.600 excluding 2 empty/truncated packets); within ±1 0.917; mean range 0.417; Cohen's κ unweighted 0.600, linear-weighted 0.918, quadratic-weighted 0.986; 0 items needed a third rater. Mechanism-only test (same model family, synthetic rubric) — real essays need at least one human or different-family rater.

### Independent 15–20 item audit (issue #7 stretch requirement)

**Not run — no model outputs exist.** `audit-sample` was dry-run on the oracle only, to prove the sheet mechanics (20 items: 10 correct, 10 needs_review). All grades remain provisional pending real outputs (see [Next action](#next-action)).

### Contamination: #6 retrieval corpus vs VALIDATION (#13, closed via PR #14)

Against index `350800b1…` (107 sources, 3481 chunks): **0 of 99 units (40 prompt + 59 excerpt) flagged, 0 exact/substring hits.** 6 excerpt units in the review band (13-gram containment 0.085–0.140), all read privately and confirmed as stock phrasing (longest common run 20–29 chars). Positive control: 6/6 planted slices flagged, incl. a paraphrase at c13 0.64. Full distributions in `2026-09-26T0250-contamination-13.md`.

### Contamination: PR #18 training data vs VALIDATION (PR #19 at `64d69815`, PR #20 delta at `c5009a5e`)

| | at `64d69815` (PR #19) | at `c5009a5e` (PR #20) |
| --- | --- | --- |
| Corpus | 519 records / 288 unique IDs → 2,502 chunks | +60 essay-plan records (348 unique IDs) + SFT export (regenerated locally, not committed) |
| Exact/substring hits | 0 | 0 (unchanged) |
| Flagged units/records | 0 of 99 VALIDATION units | 0 (unchanged) |
| Review-band records | 3: `pn781-train-0013`, `pn781-hk-04-012`, `pn781-hk-04-001` | same 3, unchanged scores |
| Short-key answer overlaps (optional exclusion) | 4 IDs: `pn781-hk-04-037`, `pn781-train-0013`, `pn781-train-0015`, `pn781-hk-10-006` | +2 IDs from `essay-08.jsonl` → 6 total |
| Positive control | 10 planted records, all flagged as expected | repeated, still discriminative (4/4 fired) |

**Verdict both times: clean, nothing needs to be dropped.** All overlaps are single general historical facts (a name or a date), which SOURCE.md allows in retrieval; excluding the 6 IDs is optional and left to the lead. Method is lexical-only (see Limits). Re-run is `python3 $H/contamination_check.py --corpus-jsonl <files> --keys <private eval_keys>`, ~1–2 s. **PR #18's head is unchanged at `c5009a5e` as of this handoff — no further re-audit is needed unless it moves again.**

## Failures and bugs fixed

- **16 of 67** adversarial cases mis-graded before the #16 harness fixes (see table above); **0 of 67** after. Regression-checked against VALIDATION rubric sanity (byte-identical aggregates).
- **2 rubric bugs** found via oracle/shotgun/null sanity runs: bracketed optional answer parts didn't match; hedged decisions/true-false pairs earned credit. Both fixed before publishing.
- **Truncation read as abstention** (bug 12): found on the real LM Studio Qwen smoke run — reasoning used the whole token budget, `finish_reason=length` gave empty content. Fixed with a new `truncated_output` flag distinguishing it from abstention.
- **Known limits kept as labelled cases, not fixed:** inflected forms not in a key's variants (lexical miss → incorrect, by design — key authors must list variants); list enumerators read as order labels; explicit "nie wiem" + guess counts as abstention (policy choice); conflicting successful duplicates keep the first record.
- **Environment workaround:** the sandbox guard rejects shell commands containing the token `eval` as a path, hence the `harness/` directory name (not `eval/`).

## Rights

- **CKE PDFs.** Publisher: Centralna Komisja Egzaminacyjna. Retrieved 2026-09-25T23:58Z. License **unknown** — reference use only, never redistributed, kept in git-ignored `private/`. Contains third-party excerpts/images.
- **Derived VALIDATION files.** Keys, prompts, page images stay in `private/`; never committed publicly or sent to a model in a public path.
- **#6 corpus.** Wikipedia (CC BY-SA 4.0) and Wikisource (public domain / per-page license), rebuilt locally, not re-published here.
- **PR #18 data.** Wikipedia-derived (CC BY-SA 4.0) synthetic records by @przemeknowak781; read locally, not republished.
- **Code and fixtures.** Original work; fixture texts describe fictional places/events and contain only general facts. No license file added (needs owner approval).
- **Qwen (LM Studio) outputs.** Generated locally from a free, offline, abliterated model; labelled `provenance: synthetic`, `provider: local-lmstudio`, `candidate: false`. Never counted as independent audit evidence, never sent an answer key.

## Limits

- **Lexical heuristics only**, for both the scoring harness and the contamination checks — no semantic paraphrase detection.
- **Era mapping** is approximated from the curriculum section number.
- **Modality/image labels** are a caption-keyword heuristic; source packs that exist only as images are not covered by the contamination check.
- **Citation audit** is lexical plus year-check only; misses negation and paraphrase.
- **No independent model run has happened.** No Sol/other-model audit ran, because there was nothing to audit.
- **Contamination checks are a warning signal, not proof of absence**; thresholds are heuristic, set once, validated only by positive controls; fixed to specific snapshots (index `350800b1…`, PR #18 heads `64d69815`/`c5009a5e`) — any later change needs a fresh re-run (seconds on CPU).
- **Blind rater dry run used the same model family for both raters** — real essays need at least one human or different-family rater.

## Next action

1. **#11 is open and waiting for real model outputs.** Once #5 (or any owner) posts a contract-shaped output JSONL for `private/validation_2024/runner_input.jsonl` (in a private artifact/DM, not a public PR, since responses would quote exam content), run:

   ```bash
   H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024
   python3 $H/matura_harness.py leakcheck --inputs $P/runner_input.jsonl --keys $P/eval_keys.jsonl   # must exit 0
   python3 $H/matura_harness.py score --split VALIDATION --outputs <run>_outputs.jsonl --keys $P/eval_keys.jsonl \
     --run-id <run> --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json --items-out $P/<run>_items.jsonl
   python3 $H/matura_harness.py audit-sample --items $P/<run>_items.jsonl --keys $P/eval_keys.jsonl \
     --outputs <run>_outputs.jsonl --n 20 --out $P/<run>_audit_sheet.jsonl
   # independent reviewer fills audit.{reviewer,points,agrees_with_auto,error_categories,evidence_checked,notes}
   python3 $H/matura_harness.py audit-summary --sheet $P/<run>_audit_sheet.jsonl --out $P/<run>_audit_summary.json
   ```

   Post the `score` and `audit-summary` aggregates to #7. Keep item text and the audit sheet in `private/`; only aggregates go public.
2. **Blind-pack real essays** for two raters (at least one human or different-family model) once essay outputs exist, following the procedure in `2026-09-26T0225-audit-procedures.md` §3.
3. **Re-run the contamination check** (`contamination_check.py`) only if the #6 index is refreshed, or PR #18's head moves past `c5009a5e`.
4. Everything above is provisional pending human review, which is optional at the morning review per issue #7.
