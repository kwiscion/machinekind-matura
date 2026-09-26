# Gemma 4 12B bounded-RAG arm, first 20 records: reviewed slice vs bare Gemma (issue #11)

**PARTIAL SLICE, provisional.** This covers the first 20 of 40 records (z1–z14.1), worth **21 of the 60 points**. It is not a 60-point score and must not be compared with the full-arm totals (35/32/35). It is @Pewciu6's independent agent review on the basis of PR #53/#58/#61. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt, retrieved passage or source text appears here.

## Headline

| Items z1–z14.1 (21 pts) | Automatic | **Reviewed** | Range |
|---|---|---|---|
| Bare Gemma, consolidated (#53 + source-v2 z13) | — | **12** | 9–14 |
| Question-policy arm (#61), same items | — | 11 | — |
| **Bounded RAG, first 20 (PR #70, `83b752e5…`)** | 3.0 | **10** | 8–12 |
| **Paired Δ RAG − bare** | | **−2** | ranges overlap |

- **Retrieval fixed none of the factual-recall misses on this slice.** z3.2, z7, z8.1, z11.1 and z12.1 are all still wrong. On z7, z8.1 and z12.1 the model now gives a *different* wrong answer, so retrieval changed the output without correcting it.
- **Retrieval introduced one error.** On z3.1 the model now identifies the text as describing a much later ruler. Bare had the correct name, hedged with an invented alternative, so it scored 0 with an upside of 1. The RAG answer scores 0 with no upside, and the same misidentification carries into z3.2.
- **It lost two points on justification completeness, not on facts.** z6 (2→1) states the three figure groups correctly but only implies the hierarchy or religious order. z9 (1→0) uses the inscription but references no graphic element of the woodcut, which the rule requires.
- **Image misreads are unchanged**: z1, z5.1 and z14.1 carry the same wrong decisions as bare. Retrieval does not help with reading images, as expected.
- The only apparent format gain is that the hedged/conflicting answers on z3.1 and z11.1 are gone. Both are now cleanly wrong, so it earns no points.
- **Reading:** on this half, bounded RAG is neutral to slightly harmful (−2 of 21, within noise for one unseeded draw). It shows no sign of being the recall lever toward 48. Keep bare 35 as the base and wait for the last 20, which hold the essay and most of the recall-heavy short items, before drawing any conclusion.

## Sol first pass

**None published** for this arm at review time (PR #70 contains no Sol grades, and #11 says "Local Sol grades this half separately"). The item-by-item adjudication against Sol is pending and will be appended when the lead posts it. Until then this is a single-rater review. On the 11 carried items it inherits #53's two-rater basis.

## Paired item table (items with a changed grade)

| Item | Max | Bare | RAG | Cause | Reason |
|---|---|---|---|---|---|
| z6 | 2 | 2 | 1 (1–2) | reasoning | three figure groups correctly placed; the hierarchy/religious order is only implied |
| z9 | 1 | 1 | 0 (0–1) | source/image | inscription used, but no graphic element referenced; the group's confession mislabelled |

The other 18 items keep bare's points. **11 are carried** (same substance as bare, so #53's grade is reused): z1, z2, z4, z5.1, z5.2, z8.2, z10, z11.2, z12.2, z12.3, z14.1. **7 were reviewed fresh** at the same score:

| Item | Bare | RAG | Note |
|---|---|---|---|
| z3.1 | 0 (0–1) | 0 | introduced misidentification (see above); upside lost |
| z3.2 | 0 | 0 | one office right, second wrong, plus hedges; same misidentification |
| z7 | 0 | 0 | same wrong decision, different invented actors |
| z8.1 | 0 | 0 | a different wrong (garbled) document name; prompt echoed |
| z11.1 | 0 (0–1) | 0 | conflict gone, but both assignments are now wrong |
| z12.1 | 0 | 0 | a different wrong ruler |
| z13 | 1 (0–1) | 1 (0–1) | event correct, dated inscription cited; invented heads on pikes |

The automatic grader marked 5 items incorrect. Review overturns one of them (z12.3: the parser missed the inflected decision) and upholds the other four. The automatic total is 3.0.

## Where the points go (21-point slice)

| Slice | Max | Bare | RAG |
|---|---|---|---|
| source_analysis | 8 | 4 | 3 |
| short_answer | 12 | 7 | 6 |
| multiple_choice | 1 | 1 | 1 |
| mod:image | 17 | 11 | 9 |
| mod:text | 4 | 1 | 1 |

| Cause (points lost) | Bare | RAG |
|---|---|---|
| Factual recall | 4 | **6** |
| Source/image misread or unused | 3 | **4** |
| Reasoning / incomplete justification | 0 | **1** |
| Answer format (hedged/conflicting) | 2 | **0** |
| **Total lost** | 9 | 11 |

Bare's two format losses (z3.1, z11.1) became factual losses under RAG, so retrieval turned hedged answers into cleanly wrong ones. Recall loss grew from 4 to 6.

## Hashes and reproduction

- Answers `83b752e5f22110e1e0531b3ad70d63fbbd4a52a92019fa3658b2dd9d4809885f`: verified on `origin/main` (PR #70 merged), matches the manifest. 20 records, 20 unique ids, all `stop`, 0 errors.
- Input `60728768…`, source-v2 `6615fea2…`, model digest `4eb23ef1…`, as recorded in the PR #70 manifest. Keys `f66e3877…` are the same as #53.

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # git-ignored
cp agentsLog/kwiscion/model-answers/bounded-rag-gemma-partial20-answer-only.jsonl $P/rag20_answer_only.jsonl   # sha256 83b752e5…
python3 -c "import json;[print(json.dumps({'id':r['id'],'raw_response':r['answer'],'error':r['error'],'finish_reason':r['finish_reason']},ensure_ascii=False)) for r in map(json.loads,open('$P/rag20_answer_only.jsonl'))]" > $P/gemma_rag20_contract.jsonl
python3 $H/matura_harness.py score --outputs $P/gemma_rag20_contract.jsonl --keys $P/eval_keys.jsonl \
  --split VALIDATION --run-id gemma4-12b-rag-first20 --scorecard $P/gemma_rag20_auto.json --items $P/gemma_rag20_auto_items.jsonl
# -> 3.0 / 21 on 20 scored (3 correct, 5 incorrect, 12 needs_review); 20 keys excluded as missing (not yet delivered)
```

Machine-readable output (ids, points, ranges, carried/fresh basis, deltas and aggregates only): [`results/review_gemma-bounded-rag-first20.json`](results/review_gemma-bounded-rag-first20.json). Per-item private reasoning stays in git-ignored `private/`. I graded z6 and z9 against the page renders (p. 9, 12).

**Limitations:** this is a partial slice of 21/60 points, without the essay (15 pts) or the second half's short items. One agent rater reviewed the 8 fresh and 2 changed items, with no Sol first pass yet and no human examiner. The ranges sum per-item uncertainty and ignore correlation. Sampling used provider defaults with no seed, so −2 on one draw is within run-to-run noise. The run was not stopped or selected on these interim grades. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0; no model calls by the scorer.
