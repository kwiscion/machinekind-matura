# Consolidated validation scores: Qwen 3.5 9B vs Gemma 4 12B (issue #11)

**Provisional.** This is @Pewciu6's independent review plus item-by-item adjudication of the lead's Sol first pass (PR #52). It is agent grading against the official CKE rules, not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here. This note supersedes the Qwen total in `2026-09-26T1540-score-qwen.md` (26 → 25 after adjudication).

## Headline

| Model (v1 input, thinking off, 1024 tokens) | Automatic | Sol first pass | **Consolidated** | Range | Gap to 48 |
|---|---|---|---|---|---|
| Qwen 3.5 9B (`qwen3.5:9b` 6488c96fa5fa) | 5.0 | 24 | **25** | 16–29 | 23 |
| Gemma 4 12B Q4 (`gemma4:12b-it-q4_K_M`) | 11.0 | 35 | **35** | 28–40 | 13 |

- The consolidated score is my adjudicated point estimate. The range covers my uncertain items plus any item where Sol and I disagree.
- **Gemma is the stronger base by about 10 points.** It completed all 40 items, lost nothing to truncation, and wrote an essay of qualifying length (8/15 vs 2/15).
- Neither model is near 48. Even Gemma's high bound (40) falls short.
- Hashes (all verified):
  - Qwen answers `731c0ca3…a2418`
  - Gemma answers `39a5dbbb…aeaf3`: matches the PR #52 manifest, and the first 30 rows are identical to the partial `8da19623…`
  - Keys `f66e3877…`, frozen input `f4df6bcb…`
- The harness reproduces the lead's automatic 5.0 and 11.0 exactly.

## Adjudication against Sol (PR #52)

Qwen: 37/40 items agree. Gemma: 38/40 agree. Where Sol and I initially differed, I revised my own grade twice (Qwen z13, Gemma z6) and kept it in the cases below.

| Model | Item | Sol | Consolidated | One-line reason |
|---|---|---|---|---|
| Qwen | z6 | 0 | 1 | Identifies the three estates through the labelled groups and adds the Christ figure and hierarchy: partial, not zero |
| Qwen | z24 | 0 | 1 | Both crises correctly distinguished; a stray chronology slip in the summary doesn't change the justification |
| Qwen | z26 | 3 | 2 | Both inside the 1–3 band; underlength sets coherence to 0, errors cost 2 narrative points |
| Qwen | z13 | 0 | 0 | Agree (revised from 1): the answer invents a scene that contradicts the actual engraving |
| Gemma | z13 | 0 | 1 | The dated-inscription reference meets the accepted justification without invented scene content |
| Gemma | z23.2 | 1 | 0 | A wrong decision and a corrected one both remain; the multiple-answer rule gives a point estimate of 0 |
| Gemma | z6 | 2 | 2 | Agree (revised from 1): refers to three depicted figures and states the hierarchy |

The automatic grader was also overturned. Qwen: 5 automatic "incorrect" grades raised (parser misses). Gemma: 2 automatic "correct" grades lowered (z3.1 and z11.1: a correct answer hedged with a wrong alternative) and 1 automatic "incorrect" raised (z12.3).

## Where the points go

### Qwen 3.5 9B: loss by cause

| task_type | items | auto | reviewed | range | max | source_image | truncation | format | factual | reasoning |
|---|---|---|---|---|---|---|---|---|---|---|
| essay | 1 | 0 | 2 | 1–3 | 15 | 0 | 0 | 3 | 2 | 8 |
| multiple_choice | 5 | 2 | 4 | 2–4 | 7 | 1 | 2 | 0 | 0 | 0 |
| short_answer | 20 | 3 | 11 | 7–14 | 24 | 3 | 1 | 1 | 7 | 1 |
| source_analysis | 14 | 0 | 8 | 6–8 | 14 | 2 | 2 | 0 | 1 | 1 |
| **total** | 40 | 5 | **25** | 16–29 | 60 | 6 | 5 | 4 | 10 | 10 |

| modality | items | auto | reviewed | range | max | source_image | truncation | format | factual | reasoning |
|---|---|---|---|---|---|---|---|---|---|---|
| image | 30 | 4 | 16 | 11–19 | 34 | 6 | 5 | 1 | 4 | 2 |
| text | 10 | 1 | 9 | 5–10 | 26 | 0 | 0 | 3 | 6 | 8 |
| **total** | 40 | 5 | **25** | 16–29 | 60 | 6 | 5 | 4 | 10 | 10 |

### Gemma 4 12B: loss by cause

| task_type | items | auto | reviewed | range | max | source_image | truncation | format | factual | reasoning |
|---|---|---|---|---|---|---|---|---|---|---|
| essay | 1 | 0 | 8 | 6–10 | 15 | 0 | 0 | 1 | 1 | 5 |
| multiple_choice | 5 | 5 | 5 | 5–5 | 7 | 0 | 0 | 0 | 2 | 0 |
| short_answer | 20 | 6 | 14 | 11–16 | 24 | 3 | 0 | 2 | 5 | 0 |
| source_analysis | 14 | 0 | 8 | 6–9 | 14 | 4 | 0 | 1 | 1 | 0 |
| **total** | 40 | 11 | **35** | 28–40 | 60 | 7 | 0 | 4 | 9 | 5 |

| modality | items | auto | reviewed | range | max | source_image | truncation | format | factual | reasoning |
|---|---|---|---|---|---|---|---|---|---|---|
| image | 30 | 6 | 19 | 15–21 | 34 | 7 | 0 | 2 | 6 | 0 |
| text | 10 | 5 | 16 | 13–19 | 26 | 0 | 0 | 2 | 3 | 5 |
| **total** | 40 | 11 | **35** | 28–40 | 60 | 7 | 0 | 4 | 9 | 5 |

Causes: source/image = visual misread or omitted, truncation = incomplete at the token limit, format = conflicting or misplaced answers or an underlength essay, factual recall, reasoning = information present but used wrongly, or shallow argument.

### Side by side

| Slice | Max | Qwen | Gemma | Gemma lost |
|---|---|---|---|---|
| source_analysis | 14 | 8 | 8 | 6 |
| mod:image | 34 | 16 | 19 | 15 |
| short_answer | 24 | 11 | 14 | 10 |
| mod:text | 26 | 9 | 16 | 10 |
| multiple_choice | 7 | 4 | 5 | 2 |
| essay | 15 | 2 | 8 | 7 |

**Which item types lose the most (Gemma, the base to improve):**

1. **Image items: 15 of 34 lost.** 7 of those points are pure image misreading: z1 reliefs, z5.1/z14.1/z24 maps, z25 cartoon (all 3 points). This is the largest single cause. Qwen loses 6 here too.
2. **Factual recall: 9.** Persons, document and dynasty names, a wrong true/false set: z3.2, z7, z8.1, z12.1, z17.2, z19.1 (2), z19.2. Both models miss the same items (z3.2, z7, z8.1, z19.2). These are knowledge gaps rather than prompt issues.
3. **Essay: 7 of 15 lost.** Satisfactory rather than rich argumentation, plus terminology errors.
4. **Format: 4.** Hedged or conflicting answers (z3.1, z11.1, z23.2) and a chatty essay preamble. These are free points.

## Where improvements could come from (ranked by expected points per effort)

1. **One final answer only (+3–4, near zero cost).** A system prompt or post-processor that forbids alternatives ("lub …"), self-corrections and restated sub-questions. For Gemma this recovers z3.1, z11.1 and z23.2 plus essay coherence. For Qwen it also avoids the truncation loops.
2. **Image fidelity (up to +7 for Gemma).** Higher-resolution crops of the relevant figure instead of whole pages, and the v2 source fix for z13. Maps and cartoons are the weak spot, so a retrieval note naming the depicted event would also help if the rules allow it.
3. **Chronology and recall retrieval (+3–5).** The shared misses are classic facts: document names, generals, dynasties, dates. The chrono retrieval index is the right lever. Measure it on these item IDs first.
4. **Essay template (+2–4).** Enforce ≥300 words, an explicit stance, three labelled aspects with concrete facts and dates, and no preamble.
5. **Token budget.** It matters for Qwen (5 points), not for Gemma. There is no reason to spend Gemma runtime on a larger budget.

Realistic Gemma ceiling from items 1–4: about 45–50. Reaching 48 needs most of them to work, so the image slice matters most.

## Per-item consolidated scores

`≠` marks a disagreement with Sol. A range is given only where uncertain.

| Item | Type | Mod. | Max | Qwen auto | Qwen Sol | **Qwen** | Qwen range | Gemma auto | Gemma Sol | **Gemma** | Gemma range | Gemma note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| z1 | source_analysis | image | 1 | 0 | 1 | **1** |  | 0 | 0 | **0** |  | wrong decision; reliefs misread (image reading) |
| z2 | source_analysis | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | decision and two-source justification accepted |
| z3.1 | short_answer | text | 1 | 0 | 0 | **0** |  | 1 | 0 | **0** | 0–1 | correct name hedged with an invented alternative; multiple-answer rule gives 0 (automatic grade overturned; low confidence) |
| z3.2 | short_answer | text | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | one of two offices wrong (factual recall) |
| z4 | short_answer | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | valid argument from the image |
| z5.1 | source_analysis | image | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong decision; map misidentified (image reading) |
| z5.2 | short_answer | image | 1 | 1 | 1 | **1** | 0–1 | 1 | 1 | **1** |  | correct |
| z6 | short_answer | image | 2 | 0 | 0 | **1** ≠ | 0–2 | 0 | 2 | **2** | 1–2 | three depicted figures plus hierarchy; full credit (third estate slightly broadened) |
| z7 | source_analysis | text | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong decision; events confused (factual recall) |
| z8.1 | short_answer | image | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong document name (factual recall) |
| z8.2 | source_analysis | image | 1 | incompl. | 0 | **0** |  | 0 | 1 | **1** | 0–1 | decision and core two-source justification accepted despite misattributing the document (low confidence) |
| z9 | source_analysis | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | decision, inscription and graphic element accepted |
| z10 | multiple_choice | image | 1 | 1 | 1 | **1** |  | 1 | 1 | **1** |  | correct |
| z11.1 | short_answer | image | 1 | 0 | 0 | **0** |  | 1 | 0 | **0** | 0–1 | wrong first assignment later self-corrected, but a wrong alternative is left in; conflicting answers give 0 (automatic grade overturned) |
| z11.2 | short_answer | image | 1 | 0 | 0 | **0** |  | 0 | 1 | **1** |  | explanation accepted |
| z12.1 | short_answer | image | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong ruler (factual recall) |
| z12.2 | short_answer | image | 1 | incompl. | 0 | **0** |  | 1 | 1 | **1** |  | correct |
| z12.3 | source_analysis | image | 1 | 0 | 1 | **1** | 0–1 | 0 | 1 | **1** |  | style and visible feature accepted; the automatic parser missed the inflected decision |
| z13 | short_answer | image | 1 | 0 | 0 | **0** | 0–1 | 0 | 0 | **1** ≠ | 0–1 | event correct, justification cites the dated inscription; v1 input omitted the image (low confidence) |
| z14.1 | source_analysis | image | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong decision; map period misread (image reading) |
| z14.2 | multiple_choice | image | 1 | 0 | 0 | **0** |  | 1 | 1 | **1** |  | correct |
| z15.1 | short_answer | text | 1 | 1 | 1 | **1** |  | 1 | 1 | **1** |  | correct |
| z15.2 | source_analysis | text | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | decision and two-source justification accepted |
| z16.1 | source_analysis | image | 1 | 0 | 0 | **0** |  | 0 | 1 | **1** |  | decision and two-source justification accepted |
| z16.2 | multiple_choice | image | 1 | 1 | 1 | **1** |  | 1 | 1 | **1** |  | correct |
| z17.1 | short_answer | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | causal link with both sources accepted |
| z17.2 | short_answer | image | 1 | 1 | 1 | **1** |  | 0 | 0 | **0** |  | wrong dynasty (factual recall) |
| z18 | source_analysis | image | 1 | incompl. | 0 | **0** |  | 0 | 1 | **1** | 0–1 | decision with two graphic elements; some image detail inaccurate (low confidence) |
| z19.1 | multiple_choice | image | 2 | incompl. | 0 | **0** |  | 0 | 0 | **0** |  | one of three judgments correct = 0 (factual recall) |
| z19.2 | short_answer | image | 1 | 0 | 0 | **0** |  | 0 | 0 | **0** |  | wrong person (factual recall) |
| z20.1 | source_analysis | text | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | decision and justification accepted |
| z20.2 | multiple_choice | text | 2 | 0 | 2 | **2** | 0–2 | 2 | 2 | **2** |  | all three judgments correct |
| z21 | short_answer | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | valid argument from the image |
| z22.1 | short_answer | text | 1 | 0 | 0 | **0** |  | 1 | 1 | **1** |  | correct |
| z22.2 | short_answer | text | 2 | 0 | 2 | **2** | 1–2 | 0 | 2 | **2** | 1–2 | both similarities accepted |
| z23.1 | short_answer | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **1** |  | both methods accepted |
| z23.2 | source_analysis | image | 1 | 0 | 1 | **1** |  | 0 | 1 | **0** ≠ | 0–1 | two conflicting decisions left in the answer (a wrong one, then a correct re-try); 0 point estimate (format) |
| z24 | source_analysis | image | 1 | 0 | 0 | **1** ≠ | 0–1 | 0 | 0 | **0** |  | wrong decision; map misread (image reading) |
| z25 | short_answer | image | 3 | 0 | 1 | **1** | 0–2 | 0 | 0 | **0** |  | cartoon completely misread; message, elements and context all wrong (image reading) |
| z26 | essay | text | 15 | 0 | 3 | **2** ≠ | 1–3 | 0 | 8 | **8** | 6–10 | topic 1, stance taken, 331-word body; two aspects satisfactory, one superficial, several factual/terminology errors; chatty preamble |

## Reproduction

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # rebuilt with build_validation_2024.py
python3 $H/matura_harness.py score --outputs agentsLog/kwiscion/model-answers/gemma4-12b-val40-1024.jsonl \
  --keys $P/eval_keys.jsonl --split VALIDATION --run-id gemma4-12b-val40-1024 --scorecard $P/gemma_auto.json   # -> 11.0
```

Machine-readable output, including per-item Sol points, agreement and reasons: [`results/review_qwen35-9b-val40-1024.json`](results/review_qwen35-9b-val40-1024.json), [`results/review_gemma4-12b-val40-1024.json`](results/review_gemma4-12b-val40-1024.json). Per-item private reasoning is kept only in `agentsLog/Pewciu6/private/` (git-ignored).

**Limitations:** two agent raters (Sol and Claude), no human examiner. Essay bands are the least certain. The Gemma answers are taken from PR #52, which is open and unmerged at the time of writing. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0.
