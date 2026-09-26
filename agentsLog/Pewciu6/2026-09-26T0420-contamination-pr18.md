# Contamination check: PR #18 training data vs May 2024 VALIDATION

- **Target:** [PR #18](https://github.com/kwiscion/machinekind-matura/pull/18) (@przemeknowak781, issue #4, branch `issue-4-przemeknowak781-data`), head `64d69815613f75c55399de12b4a5308757bfd547`. Same method as [#13](https://github.com/kwiscion/machinekind-matura/issues/13), extended to a JSONL corpus.
- **Owner:** @Pewciu6 (eval worker). Run 2026-09-26 04:15–04:30 Europe/Warsaw.
- **Branch:** `issue-13-Pewciu6-contam-pr18`.
- **Scope:** PR #18 was fetched read-only (`git fetch origin pull/18/head:pr18`, files read with `git show`, materialized in a scratchpad outside the repo). Nothing on their branch or paths was changed. SEALED_TEST (May 2025) was not opened.
- **Public content:** aggregates, record IDs and scores only. There is no exam text and there are no answers. Per-unit and per-key detail is in git-ignored `private/validation_2024/`.

## Verdict

**Clean. No training record is flagged, and nothing needs to be dropped from PR #18.**

- There are 0 exact-hash hits and 0 normalized-substring hits, in either direction.
- 0 of 99 VALIDATION units (40 prompts, 59 excerpts) reach the flag threshold against any of the 2,502 record/field chunks.
- 3 records fall in the review band: `pn781-train-0013`, `pn781-hk-04-012` and `pn781-hk-04-001`. I read all 3 privately. The shared text is stock phrasing: an event name in one case, and generic task-instruction wording ("arrange chronologically" / "is false") in the other two. The longest common normalized run is 19–28 chars.
- **Answer-key angle, aggregates only:**
  - 0 training answers reproduce the prose of any long VALIDATION key (0 flag, 0 review).
  - 3 unique training IDs contain the answer string of 2 short VALIDATION keys. These keys are a named event and a full date.
  - 1 more ID matches ≥ 50% of one key's salient terms on the same topic (BM25 rank 1). That key is a named legal act.
  - All 4 are single historical facts (a name or a date), not rubric wording. SOURCE.md allows general historical facts. See the answer-key section for the optional conservative exclusion.

This is a warning signal, not a proof of absence. It is lexical only (see Limits).

## Inputs and hashes

| Input | Value |
| --- | --- |
| VALIDATION prompts `private/validation_2024/runner_input.jsonl` (40 items) | `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7` |
| VALIDATION keys `eval_keys.jsonl` (private; used only by the answer-key angle) | `f66e387793c5dfad2bac8723a73716e434a9d6ecab40c544f8b529723f512123` |
| CKE arkusz / karta / zasady PDFs | `ad66a7c4…3d21` / `12f9bc04…bb5e` / `95c275b9…cd4c` (3/3 OK against the manifest) |
| PR #18 `data/przemeknowak781/train.jsonl` (231 records) | `52df361cefca4d20a99b0795c766740e7df9f5fb935b6c7911d70914a3acbd7f` |
| PR #18 `data/przemeknowak781/examples.jsonl` (20) | `9e45649c0e99c73f57209411307095c814087f0165a4553e7e2f80ab01efeefd` |
| PR #18 `data/przemeknowak781/generated/*.jsonl` (12 files, 268 records) | per-file SHA-256 in `results/contamination_pr18.json` |

Corpus: 519 records (288 unique IDs; `train.jsonl` repeats the gated generator outputs). They yield 2,502 chunks: 519 `all`, 519 `prompt`, 519 `answer` and 945 `claim`. Rejected and draft generator outputs are included, so the check covers everything the PR commits, not only `train.jsonl`.

## Method (`harness/contamination_check.py --corpus-jsonl`, stdlib only)

This is an additive extension of the #13 script. The default mode, with no `--corpus-jsonl`, is unchanged apart from extra keys in its output.

- **Pseudo-chunks.** Each training record becomes one `all` chunk (prompt + answer + evidence claims) plus one chunk per field (`prompt`, `answer`, `claim<k>`).
- **Queries.** The #13 units: 40 full prompts and 59 distinct paragraphs of ≥ 100 normalized chars. These cover the source-pack excerpts and question stems. The #13 normalization is used.
- **Signals.**
  - Exact SHA-256 and normalized substring, either direction, for chunks ≥ 40 chars.
  - Char 8/13-gram Jaccard and containment |U∩C|/|U|.
  - Corpus-wide 13-gram containment.
  - LCS with the best chunk.
  - BM25 top-5. This uses Bukareszt's `BM25Index`, built in memory over the `all` chunks, with title weight 0.
- **New signal: reverse containment** |U∩C|/|C| on 13-grams, for chunks ≥ 60 normalized chars. A short training prompt copied from a long VALIDATION stem has tiny forward containment but high reverse containment.
- **Thresholds.** The #13 rules still hold: flag at c13 ≥ 0.20, LCS ≥ 80 or any exact hit, and review at c13 ≥ 0.08. Reverse containment adds flag ≥ 0.50 and review ≥ 0.25. These were set before the first run.
- **Every chunk counts.** In JSONL mode, every chunk above a threshold is reported, not only the best chunk per unit. The positive control showed that a best-only report let one strong record mask others, so this was fixed before the final run.
- **Answer-key angle (`--keys`).** Each of the 40 VALIDATION reference answers is compared with every training answer.
  - *Long keys* (≥ 60 normalized chars, 24 keys) use the prose-leak thresholds on 13-grams, in both directions.
  - *Short keys* (13–59 chars, 10 keys) are names, dates and short phrases. A training answer containing ≥ 50% of the key's 13-grams counts as a fact-level string match.
  - *Tiny keys* (< 13 chars, 6 keys) are letters, numbers and single words. They are not n-gram checked.
  - *Same-topic fact match.* Among the BM25 top-10 training records for the VALIDATION prompt plus key, I count answers containing ≥ 50% of the key's salient terms, with at least 3 matched. Salient terms are years and ≥ 5-letter words, cut to a 5-char prefix, minus key boilerplate. 28 keys have at least 3 salient terms.
  - *Changed after the first run.* The first run applied the long-key rule (forward c13 ≥ 0.20) to short keys as well. It fired on 17–41-char keys where 1–4 shared 13-grams spell a name or date. I split long and short keys after that run, and I report this change openly.

**Positive control.** Synthetic records were kept in the scratchpad and not committed. I added 10 planted records to the real PR #18 corpus:

- 6 slices (150–400 chars) of random VALIDATION excerpts between filler: **6/6 flagged**, c13 0.22–0.73, reverse c13 0.60–0.77.
- A light paraphrase that dropped every fifth word: **flagged**, c13 0.47, reverse c13 0.64.
- A 90-char verbatim stem used as a whole training prompt: **flagged** by substring and reverse c13 1.00. Its forward c13 was only 0.10, which shows why the reverse signal is needed.
- A 220-char slice of a long key planted in an answer: **flagged** by the answer-key lexical rule, score 0.94.
- A full short key planted as an answer: **matched**, score 1.00.

All 44 flagged units had a planted record as BM25 top-1. The real records kept their review-band scores unchanged.

## Results (JSONL mode, real corpus)

| Metric (best chunk per unit) | Units | p50 | p90 | max |
| --- | --- | --- | --- | --- |
| 13-gram containment | prompt (40) | 0.006 | 0.009 | 0.014 |
| 13-gram containment | excerpt (59) | 0.014 | 0.056 | 0.082 |
| reverse 13-gram containment | prompt | 0.089 | 0.148 | 0.265 |
| reverse 13-gram containment | excerpt | 0.042 | 0.104 | 0.216 |
| 8-gram containment | excerpt | 0.053 | 0.108 | 0.173 |
| corpus-wide 13-gram containment | excerpt | 0.034 | 0.133 | 0.180 |
| BM25 top-5 best c13 | excerpt | 0.000 | 0.025 | 0.082 |
| longest common run (chars) | prompt / excerpt | 20 / 18 | 23 / 21 | 28 / 28 |

Reverse containment is naturally higher for prompt units. A 2,000+ char VALIDATION prompt contains many generic Polish phrases, and a 60–150 char training prompt shares a few of them. The positive-control stem scored 1.00 against a real-data maximum of 0.265.

### Review-band records (not flagged, no action needed)

| id | files | field | max c13 | max reverse c13 | longest run | shared text (described, not quoted) |
| --- | --- | --- | --- | --- | --- | --- |
| pn781-train-0013 | train, examples | prompt | 0.006 | 0.265 | 26 | an uprising's name |
| pn781-hk-04-012 | train, generated/batch-04 | all, prompt | 0.082 | 0.113 | 28 | "arrange events chronologically" instruction |
| pn781-hk-04-001 | train, generated/batch-04 | all | 0.082 | 0.025 | 19 | "the statement is false" wording |

All 3 are `audit.status = verified` in `train.jsonl`.

### Answer-key angle (aggregates only; keys stay private)

| Category | Keys | Train IDs | IDs |
| --- | --- | --- | --- |
| Long-key prose reproduced (flag / review) | 24 checked | 0 / 0 | — |
| Short key string contained in a training answer (≥ 50% of key 13-grams) | 2 of 10 | 3 | `pn781-hk-04-037` (a date), `pn781-train-0013`, `pn781-train-0015` (an event name) |
| Same-topic salient-term match (BM25 top-10, ≥ 50%, ≥ 3 terms) | 1 of 28 | 1 | `pn781-hk-10-006` (a named legal act, BM25 rank 1) |

The BM25 topic proxy put none of the 3 short-key matches in the item's top 10. I checked privately, and `pn781-train-0013` / `-0015` are about the same event as their VALIDATION item. Each overlap is one fact that any source on the event states. None of them reproduces the item's question, source pack or rubric. **No drop is required.** If the lead wants a conservative zero-overlap TRAIN set, the optional exclusion list is `pn781-hk-04-037`, `pn781-train-0013`, `pn781-train-0015` and `pn781-hk-10-006`: 4 of 231 records, all `verified`.

## Commands (macOS arm64, Python 3.9.6)

```bash
P=agentsLog/Pewciu6; H=$P/harness; SP=<scratchpad>
cp <earlier private dir>/MHIP-R0-100-*.pdf* $P/private/validation_2024/
python3 $H/fetch_validation_2024.py        # 3/3 sha256 OK
python3 $H/build_validation_2024.py        # keys f66e3877..., prompts f4df6bcb... (3.4 s)
git fetch origin pull/18/head:pr18         # read-only; 64d69815
for f in train.jsonl examples.jsonl generated/*.jsonl; do git show pr18:data/przemeknowak781/$f > $SP/pr18/$f; done
python3 $H/contamination_check.py --issue "PR#18 (issue #4 data)" \
  --corpus-jsonl $SP/pr18/train.jsonl $SP/pr18/examples.jsonl $SP/pr18/generated/*.jsonl \
  --corpus-root $SP/pr18 --corpus-prefix data/przemeknowak781/ \
  --keys $P/private/validation_2024/eval_keys.jsonl \
  --private-out $P/private/validation_2024/contamination_pr18_units.jsonl \
  --out $P/results/contamination_pr18.json   # 0.7 s
python3 -m unittest discover -s $H         # 28 OK (2 new JSONL-mode tests)
```

The default #13 mode was smoke-tested against a small synthetic index. It ran, and its output schema only gained keys. No models were run, no purchases were made, and no paid APIs were used.

## Rights

- **CKE PDFs.** License `unknown`: reference use only, kept in `private/`.
- **PR #18 data.** Wikipedia-derived (CC BY-SA 4.0) synthetic records by @przemeknowak781. They were read locally and not republished here.
- **This report and the JSON.** They contain only record IDs, file paths, field names and numbers.

## Limits

- **Text only.** 29 of 40 VALIDATION items are image-modality. Map, photo and scan source packs cannot be compared lexically.
- **No semantic paraphrase detection.** A training item that restates a VALIDATION question in different words would not be caught. The BM25 top-5 and the same-topic fact match are only weak proxies.
- **Thresholds are heuristic.** The reverse-containment and short-key thresholds are new. The short-key split was made after the first run (see Method).
- **Tiny keys are not checked.** 6 keys under 13 chars (letters, numbers, single words) were not string-compared.
- **Fixed snapshot.** The result covers PR #18 head `64d69815` only. Re-run the command (under 1 s) if the PR changes.
