# Contamination check: PR #18 re-run at new head (delta)

- **Target:** [PR #18](https://github.com/kwiscion/machinekind-matura/pull/18) (@przemeknowak781, issue #4, branch `issue-4-przemeknowak781-data`), head `c5009a5e...` (was `64d69815` for the [prior run](2026-09-26T0420-contamination-pr18.md)). Same method, mechanical re-run only.
- **Owner:** @Pewciu6 (eval worker). Run 2026-09-26 ~05:00–05:20 Europe/Warsaw.
- **Branch:** `issue-13-Pewciu6-contam-pr18-r2`, from `origin/main`.
- **Scope:** PR #18 was fetched read-only (`git fetch origin pull/18/head:pr18b`). Nothing on their branch was changed. SEALED_TEST (May 2025) was not opened.
- **Public content:** aggregates, record IDs and scores only. No exam text and no answers. Per-unit detail is in git-ignored `private/validation_2024/`.

## Verdict

**Still clean. No training record is flagged, and nothing needs to be dropped from PR #18.**

- 0 exact-hash hits, 0 flagged units (prompt or excerpt) — unchanged from the prior run.
- The same 3 records remain in the review band, unchanged scores: `pn781-train-0013`, `pn781-hk-04-012`, `pn781-hk-04-001`.
- **New in this corpus vs. `64d69815`:** 10 essay-plan files (`generated/essay-01..10.jsonl`, 60 records, `audit.status = pending`, none yet in `train.jsonl`) and a derived SFT export (`scripts/przemeknowak781/export_sft.py`, not committed — regenerated locally from `train.jsonl` for this check). `train.jsonl`, `examples.jsonl` and the other 12 `generated/*.jsonl` files are byte-identical to the prior run (hashes match).
- **Answer-key angle delta:** the essay-plan files add 2 new short-key string matches, both single historical facts on-topic with their own essay prompt (an uprising's name; a date), same category as the 4 already-noted matches from the first run. No long-key prose reproduction, no new fact-match hits.
- This is a warning signal, not a proof of absence. It is lexical only (see Limits in the prior report).

## What's new vs. `64d69815`

| Item | `64d69815` | `c5009a5e` |
| --- | --- | --- |
| Corpus files | 14 (train, examples, 12 generated) | 24 committed + 4 SFT export (regenerated, not committed) |
| Corpus records (raw, incl. duplicates across files) | 519 | 579 committed + 394 SFT-derived (re-wraps already-counted `train.jsonl` records, no new prompts/answers) |
| Corpus unique IDs | 288 | 348 (+60, all `essay-*` `pending`) |
| Flagged units | 0 | 0 |
| Review-band records | 3 | 3 (same 3, same scores) |
| Short-key answer matches (unique IDs) | 3 | 5 (+2, both from `essay-08.jsonl`, both single on-topic historical facts) |
| Fact-match records | 4 (1 key) | 4 (1 key) — unchanged |

Full run: `harness/contamination_check.py --corpus-jsonl` over `train.jsonl`, `examples.jsonl`, all 22 `generated/*.jsonl` (incl. the 10 new essay files), plus the 4 SFT export files converted to the `{id,prompt,answer}` schema the harness expects (`messages`-format chat records are not a corpus schema change to the harness itself — a local scratch conversion only, discarded after the run). Positive control repeated on this corpus (see below): still discriminative.

### Review-band records (not flagged, no action needed) — unchanged from the first run

| id | max c13 | max reverse c13 | longest run | shared text (described, not quoted) |
| --- | --- | --- | --- | --- |
| pn781-train-0013 | 0.006 | 0.265 | 0 | an uprising's name |
| pn781-hk-04-012 | 0.082 | 0.113 | 28 | "arrange events chronologically" instruction |
| pn781-hk-04-001 | 0.082 | 0.037 | 19 | "the statement is false" wording |

All 3 are `audit.status = verified` in `train.jsonl`, same as before.

### Answer-key angle (aggregates only; keys stay private)

| Category | Keys | Train IDs (unique) | New in this run |
| --- | --- | --- | --- |
| Long-key prose reproduced (flag / review) | 24 checked | 0 / 0 | — |
| Short key string contained in a training answer | 2 of 10 | 5 | +2, both `essay-08.jsonl`, `pending` |
| Same-topic salient-term match (BM25 top-10) | 1 of 28 | 1 | unchanged |

The 2 new short-key matches: one essay plan whose prompt is explicitly about a named 19th-century uprising (the key is that uprising's name — the essay topic and the key are the same event, not a leak); one essay plan about a WWII-era military organization whose answer states a well-known date connected to that organization's 1944 operation (the key is that date). Both are single historical facts that any general source states, matching the same "general historical reference facts are allowed" category SOURCE.md permits, and the same pattern as the 4 matches already noted in the prior run. **No drop required.** If the lead wants the conservative zero-overlap TRAIN set, the exclusion list grows from 4 to 6 records (all still outside `train.jsonl` except the original 3): `pn781-hk-04-037`, `pn781-train-0013`, `pn781-train-0015`, `pn781-hk-10-006`, `pn781-es-08-003`, `pn781-es-08-006`.

## Positive control (repeated on this corpus, not committed)

Same method as the first run, reduced set, planted into a scratch copy of the full corpus (train + examples + all 22 generated + SFT export):

- A ~300-char verbatim slice of a VALIDATION prompt planted in filler: **flagged**, c13 0.54, reverse c13 0.79, LCS 281.
- A 90-char verbatim stem used as a whole training prompt: **flagged** by reverse c13 1.00 (forward c13 only 0.15).
- A 220-char slice of a long key planted in an answer: **flagged** by the answer-key lexical rule.
- A full short key planted as an answer: **matched**, score 1.00.

All 4 fired as expected; the 3 real review-band records kept their unchanged scores in the same run. The harness remains discriminative on the extended corpus.

## Leakcheck and answer-string scan

```
python3 agentsLog/Pewciu6/harness/matura_harness.py leakcheck \
  --inputs agentsLog/Pewciu6/private/validation_2024/runner_input.jsonl \
  --keys agentsLog/Pewciu6/private/validation_2024/eval_keys.jsonl
```

`errors: 0`. Same 3 pre-existing warnings as documented in `README.md` (`own_answer_string_in_prompt`, "may be legitimate (term in source text); review") — unchanged, no new warnings.

`python3 -m unittest discover -s agentsLog/Pewciu6/harness`: 28 tests, OK.

## Inputs and hashes

| Input | Value |
| --- | --- |
| VALIDATION prompts `private/validation_2024/runner_input.jsonl` (40 items) | `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7` (verified present, unchanged) |
| VALIDATION keys `eval_keys.jsonl` (private) | `f66e387793c5dfad2bac8723a73716e434a9d6ecab40c544f8b529723f512123` (verified present, unchanged) |
| PR #18 `data/przemeknowak781/train.jsonl` (231 records) | `52df361cefca4d20a99b0795c766740e7df9f5fb935b6c7911d70914a3acbd7f` — **unchanged from `64d69815`** |
| PR #18 `data/przemeknowak781/examples.jsonl` (20) | `9e45649c0e99c73f57209411307095c814087f0165a4553e7e2f80ab01efeefd` — **unchanged** |
| PR #18 `generated/batch-*.jsonl`, `generated/r2-*.jsonl` (12 files, 268 records) | **unchanged, hashes match the prior run** (see `results/contamination_pr18_r2.json`) |
| PR #18 `generated/essay-01..10.jsonl` (10 files, 60 records, new) | per-file SHA-256 in `results/contamination_pr18_r2.json` |
| SFT export (`scripts/przemeknowak781/export_sft.py`, regenerated locally, not committed) | per-file SHA-256 in `results/contamination_pr18_r2.json` |

Full per-file hashes, distributions, histograms and the answer-key breakdown are in `results/contamination_pr18_r2.json`.

## Commands (macOS arm64, Python 3.9.6)

```bash
P=agentsLog/Pewciu6; H=$P/harness; SP=<scratchpad>
git fetch origin main && git checkout -b issue-13-Pewciu6-contam-pr18-r2 origin/main
git fetch origin pull/18/head:pr18b        # read-only; c5009a5e
for f in train.jsonl examples.jsonl generated/*.jsonl; do
  git show pr18b:data/przemeknowak781/$f > $SP/pr18b/data/przemeknowak781/$f
done
python3 scripts/przemeknowak781/export_sft.py --input $SP/pr18b/data/przemeknowak781/train.jsonl  # local, not committed
python3 $SP/sft_to_corpus.py $SP/pr18b/data/przemeknowak781/sft/*.jsonl  # messages -> {id,prompt,answer}, scratch only

python3 $H/contamination_check.py --issue "PR#18 r2 @ c5009a5e" \
  --corpus-jsonl $SP/pr18b/data/przemeknowak781/train.jsonl \
    $SP/pr18b/data/przemeknowak781/examples.jsonl \
    $SP/pr18b/data/przemeknowak781/generated/*.jsonl \
    $SP/pr18b/data/przemeknowak781/sft/*.corpus.jsonl \
  --corpus-root $SP/pr18b/data/przemeknowak781 --corpus-prefix data/przemeknowak781/ \
  --keys $P/private/validation_2024/eval_keys.jsonl \
  --private-out $P/private/validation_2024/contamination_pr18_r2_units.jsonl \
  --out $P/results/contamination_pr18_r2.json   # 1.7 s

python3 $H/matura_harness.py leakcheck --inputs $P/private/validation_2024/runner_input.jsonl \
  --keys $P/private/validation_2024/eval_keys.jsonl   # errors 0
python3 -m unittest discover -s $H   # 28 OK
```

No models were run, no purchases were made, no paid APIs were used.

## Rights

Same as the [prior report](2026-09-26T0420-contamination-pr18.md): CKE PDFs `unknown`-licensed, reference-only, private; PR #18 data is Wikipedia-derived (CC BY-SA 4.0) synthetic records by @przemeknowak781, read locally and not republished; this report and the JSON contain only record IDs, file paths, field names and numbers.

## Limits

Same as the [prior report](2026-09-26T0420-contamination-pr18.md) (text-only lexical checks, no semantic-paraphrase detection, heuristic thresholds, tiny keys not checked). **Fixed snapshot.** This result covers PR #18 head `c5009a5e` only. Re-run (~2 s) if the PR changes again.
