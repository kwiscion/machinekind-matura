# Pewciu6: CPU evaluation harness and May 2024 validation audit

- **Issue:** [#7](https://github.com/kwiscion/machinekind-matura/issues/7) (`overnight:eval`)
- **Branch:** `issue-7-Pewciu6-eval`
- **Started:** 2026-09-26 01:58 Europe/Warsaw (23:58 UTC, 2026-09-25)
- **First slice:** 2026-09-26 02:06 Warsaw (00:06 UTC)
- **Split used:** synthetic fixtures (labelled `DEV` for the split guard) plus a VALIDATION (May 2024) acquisition manifest. SEALED_TEST (May 2025) was not opened.

## Artifact inventory

| Path | What it is |
| --- | --- |
| `harness/matura_harness.py` | Stdlib-only, CPU-only CLI. Subcommands are `score`, `audit-citations`, `leakcheck`, and `validate`. |
| `harness/test_matura_harness.py` | unittest checks against the synthetic fixtures (7 tests). |
| `harness/fetch_validation_2024.py` | Re-downloads or verifies the May 2024 PDFs into the git-ignored `private/` path and checks their SHA-256. |
| `schemas/eval_key_rubric.schema.json` | JSON Schema for one restricted `eval_keys.jsonl` record with an item-level rubric (`criteria`, `choice`, and `order` modes). |
| `schemas/model_output.schema.json` | JSON Schema for one raw output record: `id`, `backend`, `model`, `model_revision`, `raw_response`, `usage`, `latency_s`, `error`, optional `citations`. |
| `schemas/error_taxonomy.json` | Error categories, their automatic triggers, and review hints. |
| `sources/validation_2024_sources.jsonl` | May 2024 history, formula 2023, VALIDATION acquisition manifest: 1 index page and 3 PDFs. |
| `fixtures/synthetic_*.jsonl` | Synthetic keys (11), outputs (10 plus 1 orphan), labels (9 classified, 2 exclusions), a citation corpus (4 passages), and runner input (4). |
| `results/fixture_scorecard.json`, `results/fixture_items.jsonl` | Scorecard and item-level results from the fixture run. |
| `private/` (git-ignored) | Downloaded CKE PDFs. Never committed. |

## Commands (all run on CPU, Python 3.9.6, macOS arm64)

```bash
# checks
python3 -m unittest discover -s agentsLog/Pewciu6/harness -v          # Ran 7 tests ... OK
# score synthetic fixtures
python3 agentsLog/Pewciu6/harness/matura_harness.py score \
  --outputs agentsLog/Pewciu6/fixtures/synthetic_outputs.jsonl \
  --keys    agentsLog/Pewciu6/fixtures/synthetic_eval_keys.jsonl \
  --corpus  agentsLog/Pewciu6/fixtures/synthetic_corpus.jsonl \
  --split DEV --run-id fixture-20260926 \
  --scorecard agentsLog/Pewciu6/results/fixture_scorecard.json \
  --items-out agentsLog/Pewciu6/results/fixture_items.jsonl
# guard: model-facing input must not carry key fields or answer strings
python3 agentsLog/Pewciu6/harness/matura_harness.py leakcheck --inputs <runner_input.jsonl> --keys <eval_keys.jsonl>
# verify validation PDFs (downloads to private/ if missing)
python3 agentsLog/Pewciu6/harness/fetch_validation_2024.py
python3 agentsLog/Pewciu6/harness/matura_harness.py validate sources agentsLog/Pewciu6/sources/validation_2024_sources.jsonl
```

Ready-to-run command for real VALIDATION outputs, once someone has written the keys (restricted, under `private/`):

```bash
python3 agentsLog/Pewciu6/harness/matura_harness.py score --split VALIDATION \
  --outputs <model_outputs.jsonl> --keys agentsLog/Pewciu6/private/validation_2024/eval_keys.jsonl \
  --corpus <licensed_retrieval_corpus.jsonl> --run-id <run> --model-manifest <candidate manifest> \
  --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json \
  --items-out agentsLog/Pewciu6/private/<run>_items.jsonl
```

## Measurements (synthetic fixtures only; these are not model scores)

Fixture run `fixture-20260926`: 9 scored items and 2 exclusions (`inference_error` for syn-010, `missing_output` for syn-011). One orphan output (syn-999) was ignored.

| Metric | Value |
| --- | --- |
| correct / partial / incorrect | 3 / 2 / 4 |
| points | 8 / 14 (0.5714 lenient) |
| strict (exclusions scored as 0) | 8 / 16 = 0.5 |
| errors | chronology 2, entity_confusion 1, essay_structure 1, abstention 1, citation_unsupported 1, image_ocr 1 |

All 9 labelled fixture classifications match the expected status, points, and categories.

## Source hashes (May 2024 history, formula 2023: VALIDATION)

| File | SHA-256 | Bytes |
| --- | --- | --- |
| MHIP-R0-100-A-2405-arkusz.pdf | `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21` | 3767602 |
| MHIP-R0-100-A-2405-karta.pdf | `12f9bc044132d0754f4f1f423781435d9d9aa6697e30d2b5188c273be7d9bb5e` | 1406273 |
| MHIP-R0-100-2405-zasady.pdf (answer key) | `95c275b9546611c1f8cd45b7973c436625fd0ee5643b778dcc8bb566db56cd4c` | 423212 |

Publisher: CKE. Retrieved 2026-09-25T23:58Z from cke.gov.pl. HTTP Last-Modified is 14 Apr 2026. License is `unknown`, so these files are for reference only and are not redistributed. The sheet includes third-party source excerpts.

## Rights

- Code and schemas are original work. No license file has been added, because that needs the owner's approval.
- The fixtures are synthetic text written for this harness. They contain general historical facts, no exam content, and no third-party passages.
- CKE PDFs stay in the git-ignored `private/` path. The marking rules (`zasady`) are a restricted key and are used only in isolated scoring.

## Failures and limits

- **Heuristic grading.** Grades come from lexical rubric matching and are provisional. Essay, source-analysis, and open answers need a blind human or independent review.
- **Citation audit.** It checks prefix-stem token overlap of at least 0.5, and that every year in the claim appears in the cited passage. It can miss paraphrase and negation.
- **No real outputs yet.** No real model outputs were available at the first slice, so no model scores are claimed.
- **Environment workaround.** The sandbox guard refuses shell commands that contain the token `eval` as a path component, so the harness directory is named `harness/`.

## Next action

1. Write the VALIDATION `eval_keys.jsonl` from `zasady` into `private/` (restricted).
2. Add the essay and vision slices.
3. Audit real model outputs if any appear in other owners' PRs or issues.
