# Gemma question-policy full validation review

Provisional first-pass review: **30/60 points** (range **24–34/60**), with **40/40** complete responses and **0** errors. Pawel adjudication is pending.

Two Sol first-pass reviewers covered disjoint halves; this is not two independent full-exam ratings.

| Half | Reviewer | Points | Range | Denominator | Adjudication flags |
|---|---|---:|---:|---:|---:|
| Rows 1–20 | GPT-6 Sol | 10 | 7–11 | 21 | 4 items / 5 points |
| Rows 21–40 | harness_sol | 20 | 17–23 | 39 | 3 items / 18 points |
| **Combined** | **Disjoint first passes** | **30** | **24–34** | **60** | **7 items** |

The policy arm is provisionally 5 points below the preserved bare-v1 composite of 35/60 (review range 27–40). The ranges overlap, so this comparison does not establish a causal effect and does not promote or freeze a candidate. The policy run is a source-v2 arm, distinct from the exploratory blanket-format arm and the separate one-item source-correction call.

Provenance:

- Frozen input SHA-256: `3257dd89909ec1aeea1f85180244e962cc647e4f2b9d37cb24b1907cabfabb92`
- Source-v2 SHA-256: `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`
- Full answer handoff SHA-256: `a625b2e70834867d2d726c0181e89ccf0f694fecf0e454ab70dcc930c93c8739`
- Model digest: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`
- First-half review SHA-256: `c44beaef065323b9467feabfc3bece8687b792fce2f33be96bc9bdea939a8d3b`
- Second-half review SHA-256: `9ac947d463cd9cec46aba1aed21132316e0888fab35c9520e801035c1c75e89d`

Adjudication flags preserved in the item-level JSON:

- `val2024-hist-z2`: needs adjudication (0–1/1)
- `val2024-hist-z3.1`: needs adjudication (0–1/1)
- `val2024-hist-z6`: needs adjudication (0–1/2)
- `val2024-hist-z9`: needs adjudication (0–1/1)
- `val2024-hist-z14.2`: wrong_subtask (0–0/1)
- `val2024-hist-z17.1`: substantive_error, adjudication (0–1/1)
- `val2024-hist-z18`: invented_visual_detail (0–0/1)
- `val2024-hist-z19.1`: unrequested_false_rationale (1–1/2)
- `val2024-hist-z19.2`: wrong_identity (0–0/1)
- `val2024-hist-z20.2`: shifted_statement_labels, adjudication (0–2/2)
- `val2024-hist-z23.2`: source_misidentification (0–0/1)
- `val2024-hist-z24`: visual_misidentification (0–0/1)
- `val2024-hist-z25`: visual_and_context_misidentification (0–0/3)
- `val2024-hist-z26`: essay, adjudication (5–8/15)

All scores are provisional agent judgments. Bounds are summed item ranges, not statistical confidence intervals. No answer text, question text, official keys, detailed official rubric, source packs, or provider envelopes are included.
