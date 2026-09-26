# Saved-answer complementarity — 26 September 2026

**Perfectly selecting whole answers from the historical Gemma and Qwen runs gives40/60 centrally, still below48.** This is a retrospective oracle calculation using known validation grades, not an executable router, measured ensemble or prediction for fresh generation. It supports experiments that produce better answers, beyond selecting between these saved outputs.

Inputs are the two independently adjudicated same-v1 scorecards under `agentsLog/Pewciu6/results`: `review_gemma4-12b-val40-1024.json` and `review_qwen35-9b-val40-1024.json`. Their frozen input hash is `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`. They each contain the same40 unique IDs, matched maximum points totaling60. This comparison deliberately does not mix fresh H100, source-v2 correction, prompts or runtime settings into a causal estimate.

Calculation: sum each item's larger `reviewed_points` value. Gemma totals35, Qwen25, their whole-answer oracle40. Using the respective descriptive low/high review judgments gives31–45; these are not confidence intervals. The oracle retains the better complete essay score and does not splice sentences, subparts or rubric elements within an answer.

Qwen exceeds Gemma by one reviewed point at each of z1, z17.2, z23.2, z24 and z25. These IDs are retrospective diagnosis only and must never become an inference routing table. Ten IDs score zero in both: z3.1,z3.2,z5.1,z7,z8.1,z11.1,z12.1,z14.1,z19.1,z19.2. This is not evidence that those questions cannot be solved by either model with another input or method.

The five complementary points motivate a generic disagreement/evidence-checking hypothesis, while also showing its limit on these exact candidates. Reaching48 requires additional points from newly grounded facts, stronger essay content, better visual interpretation or another model. A heterogeneous observer may produce a new answer rather than merely select a saved one; this calculation neither proves nor rules out such gains.

Reproduction: load both JSON files, index `items` by `id`, assert40 matching unique IDs and equal `max_points` per ID, then compute `sum(max(g[id]['reviewed_points'], q[id]['reviewed_points']) for id in g)`. No new model calls, source acquisition, training data or test access were used.
