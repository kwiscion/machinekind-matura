# Pewciu6: CPU evaluation harness and May 2024 validation audit

- **Issue:** [#7](https://github.com/kwiscion/machinekind-matura/issues/7) (`overnight:eval`)
- **Branch:** `issue-7-Pewciu6-eval`
- **PRs:** [#8](https://github.com/kwiscion/machinekind-matura/pull/8) (first slice, merged) and a follow-up stretch PR
- **Started:** 2026-09-26 01:58 Europe/Warsaw (23:58 UTC on 09-25)
- **First slice:** 02:06 Warsaw
- **Stretch:** about 02:30 Warsaw
- **Splits used:**
  - synthetic fixtures (tagged `DEV` for the split guard);
  - May 2024 **VALIDATION** keys, in an isolated process under `private/` only.
  - SEALED_TEST (May 2025) was **not** opened.
- **Model outputs:** **none existed**, so no model is scored. Every VALIDATION number below is a rubric sanity check (oracle, shotgun, null), not a model result.

## Artifact inventory

| Path | What it is |
| --- | --- |
| `harness/matura_harness.py` | Stdlib-only CPU CLI. Subcommands: `score`, `audit-citations`, `audit-sample`, `audit-summary`, `blind-pack`, `blind-merge`, `leakcheck`, `validate`. |
| `harness/test_matura_harness.py` | 12 unittest checks on synthetic fixtures. |
| `harness/fetch_validation_2024.py` | Downloads or verifies the CKE PDFs into `private/` against the manifest's SHA-256. |
| `harness/build_validation_2024.py` | Builds restricted `eval_keys.jsonl` (40 items, 60 points), `runner_input.jsonl`, and page PNGs under `private/`. Publishes aggregate stats only. |
| `harness/sanity_validation_2024.py` | Oracle, wrapped-oracle, shotgun, and null rubric checks on the VALIDATION keys. Aggregates only. |
| `schemas/eval_key_rubric.schema.json` | Item-level rubric/key schema. Criteria kinds: content, entity, date, structure, decision (gate); plus P/F pairs, graded counts, all-or-nothing, min_words/zeroes, manual_only, review_on_fail. |
| `schemas/model_output.schema.json` | Schema for raw output records. |
| `schemas/error_taxonomy.json` | Error categories: chronology, entity_confusion, essay_structure, abstention, citation_unsupported, image_ocr, content_incorrect. Also exclusions, review flags, and statuses. |
| `sources/validation_2024_sources.jsonl` | May 2024 acquisition manifest: CKE index page plus 3 PDFs, with URLs, retrieved_at, SHA-256, bytes, ETag, and rights. |
| `fixtures/synthetic_*.jsonl` | 15 synthetic keys and 14 outputs plus 1 orphan. Labels: 13 classified items and 2 exclusions. Also a citation corpus (4 passages) and runner input (4). |
| `results/fixture_scorecard.json`, `results/fixture_items.jsonl` | Fixture run. |
| `results/validation_2024_build_stats.json` | VALIDATION item counts by type, modality, era, and scoring mode, plus hashes of the restricted files. |
| `results/validation_2024_sanity.json` | Rubric sanity aggregates. |
| `harness/contamination_check.py` | #13: VALIDATION prompts/excerpts vs the #6 BM25 corpus (exact hash, char 8/13-gram Jaccard/containment, LCS, BM25 top-5). Aggregates to `results/contamination_13.json`, per-unit detail to `private/`. |
| `results/contamination_13.json` | #13 aggregate distributions, histograms, and review/flag chunk IDs (no exam text). |
| `2026-09-26T0250-contamination-13.md` | #13 report: 0 flagged chunks, 6 review-band chunks (stock phrasing), positive control 6/6. |
| `results/contamination_pr18.json` | PR #18 training-data audit: aggregates, flagged/review record IDs and scores, answer-key angle counts (no exam text, no answers). |
| `2026-09-26T0420-contamination-pr18.md` | PR #18 report: 0 flagged records, 3 review-band (stock phrasing), 4 single-fact answer overlaps (optional exclusion), positive control 10/10. |
| `harness/test_contamination_jsonl.py` | Unit tests for the JSONL-corpus mode of `contamination_check.py`. |
| `2026-09-26T0225-audit-procedures.md` | Procedures for the citation-support audit, the 15–20 item independent audit, blind essay review, and the vision/OCR slice. |
| `private/` (git-ignored) | PDFs, `eval_keys.jsonl`, `runner_input.jsonl`, `pages/`, sanity outputs, dry-run audit sheet. **Never commit.** |

## Commands (CPU, Python 3.9.6 stdlib, poppler 24 for build only; macOS arm64)

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024
python3 -m unittest discover -s $H -v                  # Ran 12 tests ... OK
python3 $H/matura_harness.py score --outputs agentsLog/Pewciu6/fixtures/synthetic_outputs.jsonl \
  --keys agentsLog/Pewciu6/fixtures/synthetic_eval_keys.jsonl --corpus agentsLog/Pewciu6/fixtures/synthetic_corpus.jsonl \
  --split DEV --run-id fixture-20260926 --scorecard agentsLog/Pewciu6/results/fixture_scorecard.json \
  --items-out agentsLog/Pewciu6/results/fixture_items.jsonl
python3 $H/fetch_validation_2024.py                    # 3/3 sha256 OK
python3 $H/build_validation_2024.py                    # 40 items, 60 pts, 21 pages rendered
python3 $H/matura_harness.py leakcheck --inputs $P/runner_input.jsonl --keys $P/eval_keys.jsonl   # errors 0
python3 $H/sanity_validation_2024.py                   # oracle auto 18/18
```

Ready to run on real outputs (see the procedures note):

```bash
python3 $H/matura_harness.py score --split VALIDATION --outputs <run>_outputs.jsonl --keys $P/eval_keys.jsonl \
  --run-id <run> --model-manifest <candidate manifest> \
  --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json --items-out $P/<run>_items.jsonl
python3 $H/matura_harness.py audit-sample --items $P/<run>_items.jsonl --keys $P/eval_keys.jsonl \
  --outputs <run>_outputs.jsonl --n 20 --out $P/<run>_audit_sheet.jsonl
```

Runner input image paths are relative to `$P`, per the contract.

## Measurements

### Fixtures (synthetic; not model scores)

- 13 items scored, 2 excluded (`inference_error`, `missing_output`), 1 orphan ignored.
- correct / partial / incorrect / needs_review: 3 / 3 / 5 / 2.
- Points: 9 of 33 (0.273). The upper bound is 22 of 33. The strict rate, with exclusions scored as 0, is 0.257.
- Errors: chronology 2, entity_confusion 1, essay_structure 2, abstention 1, citation_unsupported 1, image_ocr 1, content_incorrect 2.
- All 13 labelled classifications match: status, points, upper bound, categories, and flags.

### VALIDATION structure (aggregate only)

- 40 items, 60 points, matching the official sheet.
- Task types: source_analysis 14, short_answer 20, multiple_choice 5, essay 1.
- Modality: image 29, text 11.
- Scoring mode:

  | Mode | Items | Points |
  | --- | --- | --- |
  | auto | 16 | 18 |
  | gate+manual (decision auto, justification manual) | 14 | 14 |
  | manual (open answers and the essay) | 10 | 28 |

- **The heuristic can fully decide only 18 of 60 points.** The rest needs independent or human review. The harness reports a lower and an upper bound.

### Rubric sanity (no model)

| Run | Auto points | Decision gates |
| --- | --- | --- |
| Oracle (official answers) | 18/18 | 14/14 |
| Oracle wrapped in a sentence | 18/18 | 14/14 |
| Shotgun (hedges every option) | 0/18 | 0/14 |
| Null (empty) | 0 | 0 |

The oracle runs use 39 items; the essay is excluded because it has no example answer. The shotgun and null runs use all 40. Two rubric bugs were found by these runs and fixed (see the procedures note).

### Independent 15–20 item audit

**Not run.** There are no model outputs. `audit-sample` was dry-run on the oracle to prove the sheet (20 items: 10 correct, 10 needs_review). All grades remain provisional.

## Hashes

| File | SHA-256 |
| --- | --- |
| MHIP-R0-100-A-2405-arkusz.pdf (3767602 B) | `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21` |
| MHIP-R0-100-A-2405-karta.pdf (1406273 B) | `12f9bc044132d0754f4f1f423781435d9d9aa6697e30d2b5188c273be7d9bb5e` |
| MHIP-R0-100-2405-zasady.pdf (423212 B, **restricted key**) | `95c275b9546611c1f8cd45b7973c436625fd0ee5643b778dcc8bb566db56cd4c` |
| private `eval_keys.jsonl` (builder v1) | `f66e387793c5dfad2bac8723a73716e434a9d6ecab40c544f8b529723f512123` |
| private `runner_input.jsonl` (prompt v1) | `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7` |

Anyone who rebuilds from the same PDFs should get the same hashes.

## Rights

- **CKE PDFs.** Publisher: Centralna Komisja Egzaminacyjna. Retrieved 2026-09-25T23:58Z. HTTP Last-Modified is 14 Apr 2026. License `unknown`, so reference use only and not redistributed. The sheet contains third-party excerpts and images.
- **Derived files.** Keys, prompts, and page images stay in `private/`.
- **Code and fixtures.** Original work; no license file added (that needs owner approval). The fixture texts were written for this harness and contain general facts only.

## Failures and limits

- **Lexical heuristics.**
  - Closed short answers use exact phrase variants; a miss routes to review rather than failing.
  - Decision parsing expects `Rozstrzygnięcie:` or a leading decision word; the runner prompt asks for that format.
  - Listing many candidate names can still pass short-answer criteria. Shotgun hedging of decisions and P/F is blocked.
- **Era mapping.** Era is approximated from the curriculum section number and should be confirmed.
- **Modality.** The image label is a caption-keyword heuristic.
- **Citation audit.** Lexical plus year check only; it can miss negation and paraphrase.
- **No independent model run.** No independent Sol/other-model audit ran, because nothing existed to audit. The local LM Studio model was not used.
- **Environment workaround.** The sandbox guard rejects shell commands containing the token `eval` as a path, hence the `harness/` name. An empty, untracked leftover directory may exist locally.

## Contamination check (#13)

`python3 agentsLog/Pewciu6/harness/contamination_check.py` (needs the rebuilt `private/` prompts and `agentsLog/Bukareszt/index/bm25_index.json`). Against index `350800b1…`, 0 of 99 units (40 prompts, 59 excerpts) were flagged and 0 exact hits were found. Nothing needs to be excluded. See `2026-09-26T0250-contamination-13.md`.

## Contamination check: PR #18 training data

`contamination_check.py --corpus-jsonl <files> --keys <private eval_keys>` uses training examples (prompt + answer + evidence claims) as the corpus and adds reverse 13-gram containment plus an aggregate-only answer-key angle. Against PR #18 head `64d69815` (519 records, 288 unique IDs), 0 records are flagged and 3 are in the review band (stock phrasing). 0 answers reproduce long-key prose. 4 IDs share a single fact (a name or a date) with a VALIDATION key; excluding them is optional. See `2026-09-26T0420-contamination-pr18.md`.

## Next action

1. Once #5 or another owner produces outputs for `runner_input.jsonl`, run `score`, then `audit-sample` (20 items), then an independent reviewer, then `audit-summary`. Post the aggregates to #7.
2. Blind-pack the essays for two raters.

## Issue #11 sanity pass (2026-09-26, synthetic only)

Report: `2026-09-26T0310-sanity-11.md`. Everything is synthetic; no model is scored and every grade stays provisional.

- `harness/build_adversarial_fixtures.py` builds `fixtures/adversarial_*.jsonl`: 67 invented items with labels covering format variants, diacritics, hedges, JSON/markdown/think wrapping, empty/overlong answers, errors/timeouts/truncation, duplicate/missing/unknown/int ids. It also builds `fixtures/blind_essay_*.jsonl`.
- `harness/test_adversarial.py`: adversarial labels, extractors, adapter-shape ingestion (`fixtures/adapter_contract_sample.jsonl`), and Cohen's kappa. The full suite runs 26 tests. `TestInferNormalizerIngestion` pins the real `infer.py` + `scripts/normalize_outputs.py` shape via `fixtures/infer_*_sample.jsonl`, and a drift test covers it.
- Harness fixes (14 listed in the report): 16 of 67 cases were mis-graded before the fixes. `blind-merge` now reports Cohen's kappa (unweighted, linear, quadratic), within-1 agreement, and a third-rater list.
- `harness/smoke_lmstudio.py` plus `smoke/`: a JSONL-path smoke test with the local LM Studio Qwen. It is a **non-candidate smoke model**, run on synthetic prompts only.
