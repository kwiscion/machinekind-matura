# Essay lab wave wave-h100-20260926T172925Z (issue #80): DEVELOPMENT results, not a validation score

Owner: @Pewciu6. This was one bounded 90-minute wave on our dedicated Brev `matura-pawel` H100 (Ollama 0.34.4, `gemma4:12b-it-q4_K_M` digest `4eb23ef1…2b05c`, `think:false`, `num_ctx 32768`, temperature not sent). The launch record is [#80 comment 5848368032](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848368032) and the manifest is `wave_manifest.json`. The first scored comparison is [5848448306](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848448306) (posted 11 min after launch), and the grounding pivot is [5848518398](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848518398).

## Result

**Retrieval-grounded critic → rewrite (C3) is the only mechanism that scored higher on every item.** On 12 independent DEV topics, graded blind against the official CKE criteria A (0–12) and B (0–3):

| | A single pass | C3 grounded critic → rewrite of the A draft |
|---|---:|---:|
| mean total /15 (12 items) | 4.00 | **7.42** |
| factual errors (sum) | 34 | **14** |
| items where C3 ≥ A | | **12/12 (11 wins, 1 tie)** |
| original 8 items (round g2) | 4.25 | 7.75 |
| replication, 4 new topics (round g3) | 3.50 | 6.75 |

All families, per grading round (mean /15 and total factual errors over the items):

| family | mechanism | g1 (8 items) | g2 (8 items, re-graded) | g3 (4 new items) |
|---|---|---|---|---|
| A | dedicated long-form single pass | 4.00 / 23 | 4.25 / 23 | 3.50 / 11 |
| B | facts-first: ungrounded fact bank → argument | 3.62 / 29 | — | — |
| C | critic → rewrite of the A draft (ungrounded) | 5.75 / 19 | 5.38 / 21 | — |
| D | topic selection → A prompt (separately named experiment) | 4.50 / 23 | — | — |
| B3 | family B variant: fact bank grounded in the #6 BM25 corpus → argument | — | 6.38 / 12 | — |
| C3 | family C variant: critic checks the draft against retrieved excerpts → rewrite | — | **7.75 / 8** | **6.75 / 6** |

Median words per family were 368–434 and every essay had ≥300 words except one (B, item 001: 283 by the heuristic count, graded B=0). Per-item scores, element levels and every listed factual error (claim and correction) are in `grades.dev.jsonl`.

**Grading.** Each round used fresh blind grader subagents (Claude Opus; they never saw which family wrote an essay, and codes were shuffled per round), with the official CKE essay criteria A and B, including factual-error deductions. Six grader sessions scored 76 essays in total (72 DEV + 4 validation-check). A and C were re-graded in g2 by different graders: A 4.00 → 4.25 (mean absolute item difference 0.25) and C 5.75 → 5.38 (0.63), so the grading was stable. It is still one agent grader per essay per round, so this is **DEVELOPMENT grading**. Promotion needs independent graders, and this must not be combined into an exam score.

## What we learned

- **The content failure dominates.** Every family clears 300 words and the structure checklist, yet A scores about 4/15. The graders rated almost every element "superficial" and found invented entities (popes, organisations, treaties, battles) plus date errors. This confirms the lead's review of the pilot.
- **Grounding is the lever.** Retrieved evidence cuts errors by more than half (A 23 → C3 8 on the same items) and, because fewer false premises get through, it raises the argument levels too. An ungrounded critic helps only a little (21 errors): without evidence the model can't recognise its own inventions.
- **Critic → rewrite beats fact bank → write at the same grounding** (7.75 vs 6.38). Keeping a complete draft and correcting it seems better than regenerating from a list of facts.
- **Remaining weak spots come from corpus coverage.** Item 005 (Polish Underground State) and item 008 (identity 1864–1905) stay at 5–6/15 under C3, because retrieval returns mostly one article, or chunks from outside the topic's period (1905, Wiosna Ludów). The essays still miss organic work and the political parties. A broader corpus would help more than prompt changes.
- **Topic selection (D) is not a mechanism for this model.** It chose topic 1 in 7 of 8 items. On those items D is effectively a second A sample, and the A/D differences (up to 3 points on one item) estimate the per-sample noise.

## Pivot log

| time (UTC) | decision |
|---|---|
| 17:35 | b1 launched: A, B, C, D × 8 topics (56 calls) plus the validation dev check (7 calls) |
| 17:45 | g1 graded. **B-ungrounded PARKED**: together with the pilot's plan→write that is two probes with no gain, and the lead parked plan→write in [5848377158](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848377158). **D PARKED**: it mostly resamples A, so no mechanism effect. C is the lead to replicate. |
| 17:47 | Pivot to the lead's grounding and verification guidance: B3 and C3 (grounded variants inside families B and C, so the wave still has 4 families) on the same 8 topics (32 calls) |
| 17:56 | g2 graded: C3 is best, and C is superseded by C3. Replication of C3 vs A on 4 new topics, 009–012 (12 calls) |
| 18:00 | g3 graded: the replication holds (4/4 wins). Wave closed with 4 calls unused. |

## Validation development check (single item, never training)

`val2024-hist-z26`: the model saw only the exam task text, never keys. A grader graded it separately against the full task rubric. Only scores and error counts are published, because the grader's notes refer to restricted marking material.

| family | total /15 | errors |
|---|---:|---:|
| A (topic 1) | 2 | 6 |
| B (topic 1) | 2 | 7 |
| C (topic 1) | 3 | 4 |
| D (chose topic 3) | 3 | 4 |

All four have superficial argument and invented institutions or dates, and one item can't rank families. C3 was **not** run on this item. **Deviation:** the lead's relay described a "one/two-call" validation check, but this used 7 calls (all four families on the one item). That stayed inside the wave envelope, and it is recorded here rather than hidden.

## Envelope and ledger (enforced by `scripts/Pewciu6/essay_wave_run.py`)

- **Wall time:** the wave started at 17:35:20Z, the deadline was 19:05:20Z, and the wave closed at about 18:01Z. Per-call timeout was `min(420 s, time left)`, with a watchdog. Wall time per call was 8–13 s.
- **Calls:** 107 in the wave plus 9 prior (3 smoke + 6 pilot) = **116/120**.
- **Requested tokens:** 158,592 in the wave plus 7,168 prior = **165,760/240,000**. Actual output tokens: 77,481.
- **Families: 4/4** (A, B, C, D; B3 and C3 count under B and C).
- **0 failed, 0 unsent, 0 retries.** The only refusal came from the pre-flight check, which counted B3/C3 as new families before a fix; no call was sent.
- **Cost:** the owner's hourly rate is still pending. The estimate is about 3.28 USD/h × about 0.5 h of active wave (1.5 h reserved), which is ≤4.92 USD. Nothing was purchased.
- **Backups:** everything in the private dir (ledger, raw outputs, prompts, intermediate stages, grader files) was copied to `~/matura-backups/wave-h100-20260926T172925Z/` after each batch.

## Files

| file | content |
|---|---|
| `answers.dev.jsonl` | 60 final DEV essays: `id, item, family, topic, answer, error_type, batch` |
| `answers.valcheck.jsonl` | 4 final validation-check essays (development check only) |
| `grades.dev.jsonl` | per round and item: A, B, total, element levels, deduction, factual errors (claim/correction), grader comment |
| `grades.valcheck.jsonl` | validation check: scores and error counts only |
| `stage_provenance.jsonl` | every call: batch, family, item, stage (facts/critic/select/final), cap, prompt SHA-256, status, elapsed, eval/prompt tokens, done_reason |
| `retrieval_provenance.jsonl` | B3/C3: topic-derived queries and retrieved chunk ids/locators/scores (no source text) |
| `ledger_totals.json` | totals, per-batch status and failed/unsent lists, SHA-256 of every published file |
| `wave_manifest.json` | pre-launch manifest: host, envelope, hashes, rate |

Private, in the git-ignored `private/` dir plus the local backup: prompts, fact banks, critiques, retrieved excerpts, raw provider output and grader keys, so errors can be traced to the stage that caused them. Retrieval used the #6 index built in our issue-13 worktree (`bm25_index.json` `350800b1…0429`, `retrieval.py` `5ce9918f…51a3`, 109 pl.wikipedia CC BY-SA sources). The #13 contamination check of that corpus against VALIDATION found 0 flagged chunks. A 12-gram check found 1 shared 12-word span across the 20 grounded essays, so the answers carry facts, not copied source text.

Reproduce, from the repo root, with the tunnel open (fresh `<wave_dir>`, new batch ids; the ledger refuses duplicates):

```sh
python3 scripts/Pewciu6/essay_wave_run.py init --wave-dir agentsLog/Pewciu6/essay/private/<wave_dir>
ESSAY_RETRIEVER=<path>/agentsLog/Bukareszt/scripts/retrieval.py \
python3 scripts/Pewciu6/essay_wave_run.py run --wave-dir agentsLog/Pewciu6/essay/private/<wave_dir> --batch b1 \
  --families A,C3 --source agentsLog/Pewciu6/essay/dev_fixtures.jsonl --items dev-essay-001,...  [--check]
python3 scripts/Pewciu6/essay_wave_grade.py packet --wave-dir ... --batches b1 --source ... --out .../grading/g1
python3 scripts/Pewciu6/essay_wave_grade.py aggregate --grading .../grading/g1 --markdown
python3 scripts/Pewciu6/essay_wave_export.py --wave-dir ... --out agentsLog/Pewciu6/essay/results/<wave_dir>
```

## Limits

- Everything here is DEVELOPMENT grading by agents: one grader per essay per round, on our own original fixtures (12 topics, from medieval to 1945; independent premise checks found 15/15 premises supported for 006–008 and 32/33 for 006–012 combined, see `../../premise_check_wave.md`), with a single sample per family and item. It is not an exam score and not promotion evidence.
- Retrieval queries come from the topic text alone. The corpus is small (109 articles), and coverage limits some topics.
- C3 needs 3 calls per essay (A draft + critic + rewrite) and about 5k prompt tokens with excerpts. On the H100 that took about 30 s of wall time per essay.

## LoRA gate note (out of scope for this worker)

Data gate: **not yet satisfiable.** We have 12 original DEV prompts, which are fixtures, not training data. There are no rights-cleared, source-group-separated essay training targets (that is #97). Export gate: **not yet shown.** The desk study (`../../lora_feasibility.md`) finds training time feasible, but three export steps are unverified: the llama.cpp converter's support for the Gemma 4 layout, reproducing the registry base as a pipeline control, and Ollama `ADAPTER` support for `gemma4`. It proposes CPU / zero-adapter checks first. Given this result, grounding (C3) addresses the main failure (invented facts) more directly than an essay-only LoRA would.
