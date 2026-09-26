# Gemma 4 12B bounded-RAG arm, full 40 records: reviewed score vs bare Gemma (issue #11)

**Provisional.** This is @Pewciu6's independent agent review of the complete bounded-RAG arm (PR #75, head `5abf977`), on the basis of PR #53/#58/#61/#74, with an item-by-item adjudication of the lead's local Sol first pass. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt, retrieved passage or source text appears here.

## Headline

| 60 points | Automatic | **Reviewed** | Range |
|---|---|---|---|
| Bare Gemma, consolidated (#53 + source-v2 z13) | 11 | **35** | 28–40 |
| Format arm (#58) / question-policy arm (#61) | — | 35 / 32 | — |
| Sol first pass for this arm (lead, #11) | — | 26 | 23–31 |
| **Bounded RAG, full 40 (PR #75, `f3b9b65a…`)** | 10 | **27** | **22–33** |
| **Paired Δ RAG − bare** | | **−8** | ranges overlap only at 28–33 |

The split: first 20 items (21 pts) **10** vs bare 12, carried from #74. Rows 21–40 (39 pts) **17** vs bare 23. On the short items alone it is **−2** (25 vs 27 of 45); the essay is **−6** (2 vs 8 of 15).

**Verdict: HURTS.** Do not promote. Keep bare 35 as the base.

- **Recall items: net zero on points, and not reliable.** Retrieval fixed z17.2 (dynasty, 0→1) and half of z19.1 (two of three judgments correct, 0→1). It also *introduced* recall errors on z15.1 (wrong uprising, 1→0) and z17.1 (Sedan tied to the fall of Napoleon I and an invented dynasty instead of German unification, 1→0), and it lost bare's upside on z3.1. Six recall misses from bare are still wrong: z3.2, z7, z8.1, z11.1, z12.1 and z19.2 (the last also wrong in bare). Where retrieval changes a recall answer, it is about as likely to break it as to fix it.
- **Essay: the main loss (8 → 2).** The model switched to topic 3 (bare wrote topic 1). It takes a stance, but all three aspects are generic and superficial, and no key 1918 actors, institutions or diplomacy are named. It also has at least two factual/causal errors: the 1919–1920 war is presented as enabling independence in 1918, and recognition of independence is attributed to the League of Nations. That puts criterion A at about 2. The body is **297–299 words**, under the rules' 300-word minimum, so B = 0. If the "WYPRACOWANIE na temat nr 3." heading counted (302–304 words), B could reach 2. Range 1–5.
- **Justification completeness −2** (first half, from #74): z6 (2→1) and z9 (1→0).
- **Image misreads are unchanged or worse:** z1, z5.1, z14.1, z24 and z25 are still wrong, and z25 is misread in a new way. Retrieval does not help with reading images, as expected.
- **Format:** z23.2 again leaves two conflicting decisions (a wrong one, then a corrected re-try), exactly as bare did, so it gets the same 0 (0–1).

## Byte check of rows 1–20

The first 20 lines of `bounded-rag-gemma-val40-answer-only.jsonl` are **byte-identical** to the PR #70 partial (`83b752e5…`), checked by comparing raw bytes line by line and by the SHA-256 of the 20-line prefix. The #74 grades are carried unchanged. Rows 21–40 are also byte-identical to `bounded-rag-gemma-rows21-40-answer-only.jsonl` (`870fce1c…`). The full-file SHA matches the manifest: `f3b9b65abb3cd8257ca41f45e837def3622d7448cf189d73150968e7dda3621d`. There are 40 records and 40 unique ids, all `stop`, with 0 errors.

## Adjudication against Sol

The Sol first pass is **26/60 [23,31]** (lead comment on #11): 9/21 on the first 20 plus 17/39 on rows 21–40, with the essay at 2/15 [1,5].

- **First 20:** Sol's per-item grades (PR #75 `rag-review-first20.md`) agree with #74 on 19 of 20 items. The one **disagreement is z13**: Sol 0 (range 0–1), mine 1 (0–1). The event is correct and the dated inscription on the drawing is cited, and the invented detail is peripheral, the same basis as bare's source-v2 composite 1. The range is kept at 0–1.
- **Rows 21–40:** Sol's per-item grades for this half were not published at review time, only the 17/39 aggregate and two flags. My independent total is also **17/39**. Both flags agree: z23.2 is 0 because of the contradiction, and the essay is 2 [1,5], with the underlength affecting only B.
- The whole 1-point difference between Sol's 26 and my 27 is z13.

## Paired item table (items with a changed grade)

| Item | Max | Bare | RAG | Cause | Reason |
|---|---|---|---|---|---|
| z6 | 2 | 2 | 1 (1–2) | reasoning | hierarchy/religious order only implied (#74) |
| z9 | 1 | 1 | 0 (0–1) | source/image | no graphic element referenced (#74) |
| z15.1 | 1 | 1 | 0 | factual | wrong uprising named (introduced) |
| z17.1 | 1 | 1 | 0 | factual | wrong causal chain, Napoleonic-era confusion (introduced) |
| z17.2 | 1 | 0 | **1** | — | correct dynasty (recall fixed) |
| z19.1 | 2 | 0 | **1** | factual | two of three judgments correct (bare one) |
| z26 | 15 | 8 (6–10) | 2 (1–5) | reasoning/factual/length | see the essay bullet above |

The other 33 items keep bare's points. In rows 21–40, the items carried on the same substance as bare are z14.2, z16.1, z16.2, z19.2, z20.2, z21, z22.1, z23.1, z23.2 and z24. The items reviewed fresh at the same score are z15.2, z18, z20.1, z22.2 and z25. The automatic grader gives 10.0; review overturns z20.1 (the parser missed a bare numeral decision) as well as z12.3 (#74).

## Where the points go (60)

| Slice | Max | Bare | RAG |
|---|---|---|---|
| short_answer | 24 | 14 | 12 |
| source_analysis | 14 | 8 | 7 |
| multiple_choice | 7 | 5 | 6 |
| essay | 15 | 8 | 2 |
| mod:image | 33 | 18 | 17 |
| mod:text | 27 | 17 | 10 |

| Cause (points lost) | Bare | RAG |
|---|---|---|
| Factual recall | 9 | **11** |
| Source/image misread or unused | 7 | **8** |
| Reasoning / incomplete argument (mostly the essay) | 5 | **10** |
| Answer format / length (hedged, conflicting, essay under 300 words) | 4 | 4 |
| **Total lost** | 25 | **33** |

## Hashes and reproduction

- Answers `f3b9b65a…` (full), with the first-20 prefix `83b752e5…` and the rows 21–40 file `870fce1c…`. Input `60728768…`, source-v2 `6615fea2…`, model digest `4eb23ef1…`, as recorded in the PR #75 manifest. Keys `f66e3877…` are the same as #53.

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # git-ignored
cp agentsLog/kwiscion/model-answers/bounded-rag-gemma-val40-answer-only.jsonl $P/rag40_answer_only.jsonl   # sha256 f3b9b65a…
python3 -c "import json;[print(json.dumps({'id':r['id'],'raw_response':r['answer'],'error':r['error'],'finish_reason':r['finish_reason']},ensure_ascii=False)) for r in map(json.loads,open('$P/rag40_answer_only.jsonl'))]" > $P/gemma_rag40_contract.jsonl
python3 $H/matura_harness.py score --outputs $P/gemma_rag40_contract.jsonl --keys $P/eval_keys.jsonl \
  --split VALIDATION --run-id gemma4-12b-rag-full40 --scorecard $P/gemma_rag40_auto.json --items $P/gemma_rag40_auto_items.jsonl
# -> strict 0.1667 (10.0 / 60)
```

Machine-readable output (ids, points, ranges, basis, Sol adjudication, deltas and aggregates only): [`results/review_gemma-bounded-rag-val40.json`](results/review_gemma-bounded-rag-val40.json). Per-item private reasoning stays in git-ignored `private/`.

**Limitations:**
- One agent rater reviewed the fresh items. Sol's per-item grades for rows 21–40 were not available, so agreement on that half is at the aggregate level only.
- There is no human examiner.
- The ranges sum per-item uncertainty and ignore correlation.
- Sampling used provider defaults with no seed (temperature 1). A −2 on the short items is within run-to-run noise. The essay's −6 is one draw, and a single essay is high-variance: it moved from topic 1 to topic 3.
- The essay's B criterion depends on whether the heading counts toward the 300 words; B = 0 is the strict reading.
- The run was not stopped or selected on these interim grades.

Rights: CKE material is cited, not redistributed. Cost: CPU only, $0; the scorer made no model calls.
