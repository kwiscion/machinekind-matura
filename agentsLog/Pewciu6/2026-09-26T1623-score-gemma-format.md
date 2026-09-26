# Gemma 4 12B format arm: reviewed score vs bare Gemma (issue #11)

**Provisional.** This is @Pewciu6's independent agent review against the official CKE rules, on the same basis as the consolidated scores in PR #53. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here.

## Headline

| Gemma 4 12B Q4, v1 input, thinking off, 1024 tokens | Automatic | **Reviewed** | Range |
|---|---|---|---|
| Bare (PR #52/#53, `39a5dbbb…`) | 11.0 | **35** | 28–40 |
| Format prefix (PR #56, `c8a1bacc…`) | 10.0 | **35** | 28–39 |
| **Δ format − bare** | −1.0 | **0** | |

- **After review, the format prefix is neutral: 35 vs 35.** Ten items change score: five gains and five losses. The automatic −1 is a parser and decision artefact, not a real loss.
- **Hedged and conflicting answers decreased.** Items with "lub …" alternatives went from 11 to 4, and the remaining four are synonyms or same-value restatements. Items where a conflicting answer actually costs points dropped from 3 to 1 (z23.2 in both arms). The format recovered all of z3.1 and z11.1 but not z23.2.
- **One new failure mode:** four format records (z6, z12.2, z19.2, z23.2) also contain answers to *other* sub-items, and some of those contradict the proper record (for example, a different 19.1 set sits inside z19.2). Each record is graded only for its own item, so these cost no points here. On a single answer sheet, an examiner could treat them as conflicting answers.
- The format gains came from answer shape and recall. The losses are mostly source reading, and they cancel the gains. The format shortened answers (median 76 → 65 words) without fixing image fidelity.
- Neither arm is near 48.

## Item deltas vs bare Gemma (consolidated 35)

| Item | Bare | Format | Cause | One-line reason |
|---|---|---|---|---|
| z3.1 | 0 | 1 | format fixed | single clean name; bare hedged it with an invented alternative |
| z8.1 | 0 | 1 | recall fixed | correct document name (bare wrong) |
| z11.1 | 0 | 1 | format fixed | both assignments correct with no self-correction (bare left conflicting answers) |
| z17.2 | 0 | 1 | recall fixed | correct dynasty (bare wrong) |
| z19.1 | 0 | 1 | recall | two of three judgments correct = 1 point (bare got one of three) |
| z10 | 1 | 0 | new error | wrong letter with no reasoning (bare correct) |
| z13 | 1 | 0 | source/image | event and date correct, but it describes a scene the drawing does not contain (v1 input omitted the image; the #53 standard gives 0 for invented scene content) |
| z15.2 | 1 | 0 | source misread | wrong version chosen; the tone of source 1 is read backwards |
| z17.1 | 1 | 0 | reasoning | self-contradictory war outcome and a wrong causal chain to the ceremony |
| z18 | 1 | 0 | source/image | wrong side; the uniforms and the monster are misread |

Net 0. The other 30 items keep the same points: 24 are **carried** (the same substance as bare, so the #53 grade is reused) and 6 were reviewed **fresh** at the same score (z6, z8.2, z12.1, z20.2, z25, z26). Three fresh same-score items are worth noting:

- **z8.2:** now attributes the document correctly, so the point is firm (bare was 0–1).
- **z20.2:** the values are correct and in order, but the statement numbering is garbled. I give 2, with a range of 0–2.
- **z26:** the essay has the same topic, stance and three-aspect structure. The body is about 320 words, the chatty preamble is still there, and the socio-economic part is still superficial with errors. It stays at 8 (6–10), the same band as bare.

## Where the points go

| Slice | Max | Bare | Format |
|---|---|---|---|
| source_analysis | 14 | 8 | 6 |
| short_answer | 24 | 14 | 16 |
| multiple_choice | 7 | 5 | 5 |
| essay | 15 | 8 | 8 |
| mod:image | 34 | 19 | 19 |
| mod:text | 26 | 16 | 16 |

| Cause (points lost) | Bare | Format |
|---|---|---|
| Source/image misread or omitted | 7 | **10** |
| Factual recall | 9 | **7** |
| Reasoning / shallow argument | 5 | 6 |
| Answer format (hedged/conflicting, essay preamble) | 4 | **2** |
| Truncation | 0 | 0 |
| **Total lost** | 25 | 25 |

**Reading:** the prefix did what it was meant to do on answer shape (format loss 4 → 2). Source-analysis items (−2) and image or source misreads (+3 lost) offset that gain. Image fidelity is still the deciding slice, and a prompt prefix does not fix it.

## v2 source correction, z13 only (kept out of the baseline totals)

| z13 | Points | Range |
|---|---|---|
| v1 bare (#53) | 1 | 0–1 |
| v1 format arm | 0 | 0–1 |
| **v2 correction** (`64aa625c…`) | **1** | 0–1 |

The v2 answer names the correct event and cites the date on the engraving, which is an accepted justification. Its "beheading scene" is a loose, symbolic reading of the felled trunk, not invented figures. It does contain a factual slip about the place of execution, so the grade stays low-confidence. The composite of the 39 unchanged bare items plus v2 z13 is **35/60**, the same as v1: the correction does not move the baseline.

## Hashes and reproduction

- Format answers `c8a1baccb82c36a1636a1d4844a5d38b2ae8fa0a8b7d0b8cd0c4a829e5b6d555`: verified, matches the manifest (40 records, 40 unique ids, all `stop`, no errors).
- v2 answer `64aa625c7ce924096b047ef9fb3d6559ec82804df1b271f4999b9282dec8872c`: verified.
- Keys `f66e3877…`, frozen input `f4df6bcb…`: verified, the same as #53.
- For the harness, the answer-only `answer` field was renamed to `raw_response` (text byte-identical) in a private copy.

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # git-ignored
python3 -c "import json;[print(json.dumps({'id':r['id'],'raw_response':r['answer'],'error':r['error'],'finish_reason':r['finish_reason']},ensure_ascii=False)) for r in map(json.loads,open('agentsLog/kwiscion/model-answers/gemma4-12b-val40-format-answer-only.jsonl'))]" > $P/gemma_format_contract.jsonl
python3 $H/matura_harness.py score --outputs $P/gemma_format_contract.jsonl --keys $P/eval_keys.jsonl \
  --split VALIDATION --run-id gemma4-12b-val40-format --scorecard $P/gemma_format_auto.json --items $P/gemma_format_auto_items.jsonl   # -> 10.0 (9 correct, 1 partial, 12 incorrect, 18 needs_review)
```

Machine-readable output (aggregates, item ids, points, ranges, carried/fresh basis, v2 z13): [`results/review_gemma4-12b-val40-format.json`](results/review_gemma4-12b-val40-format.json). Per-item private reasoning is kept only in git-ignored `private/`.

**Limitations:** one agent rater for the 16 fresh items, with no second rater or human examiner. The carried items inherit #53's two-rater adjudication. The essay band is the least certain. This arm was interrupted and resumed under a competing controller and may have shared the backend with the v2 call, so it is exploratory, not a clean baseline. The range 28–39 sums per-item uncertainty and does not account for correlation between items. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0.
