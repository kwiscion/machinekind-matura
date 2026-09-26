# Paired baseline scores: hypothetical oracle ceiling

26 September 2026. Source: PR #53's consolidated, agent-reviewed May 2024 scores for the preserved Gemma and Qwen v1 baselines. These remain provisional estimates, not organizer grades. The separately versioned source correction and active policy arm are excluded.

**Even perfect per-item routing of these existing answers reaches only 40/60 (66.7%), eight points short of 48/60.** Gemma alone has 35/60; Qwen has 25/60. An oracle adds five points over Gemma. Selecting each item's higher reported uncertainty bound gives at most 45/60, still three short. This arithmetic range is 31-45, obtained from per-item low/high bounds; it is not a statistical confidence interval or a measured system score.

The oracle is `sum(max(Gemma reviewed_points, Qwen reviewed_points))`, joining all 40 unique IDs with matching item maxima totaling 60. It assumes advance access to the grades. No deployed selector, answer synthesis or measured ensemble is demonstrated. Score ties do not establish identical answers, and shared zero scores do not establish identical mistakes.

## Paired outcome matrix

Cells count items. Full means all available points; partial means strictly between zero and the item maximum.

| Gemma \ Qwen | Zero | Partial | Full | Total |
| --- | ---: | ---: | ---: | ---: |
| Zero | 10 | 1 | 4 | 15 |
| Partial | 0 | 1 | 0 | 1 |
| Full | 8 | 1 | 15 | 24 |
| Total | 18 | 3 | 19 | 40 |

Gemma scores higher on ten items, with a 15-point advantage across those items. Qwen scores higher on five items, with a five-point advantage. The other 25 items tie in points: 15 both-full and ten both-zero. Both models earn some points on 17 items; Gemma alone earns points on eight, Qwen alone on five, neither on ten.

## Where complementarity exists

IDs below are the numeric suffixes of `val2024-hist-z<ID>`. Grouped IDs share the displayed per-item scores.

| Item IDs | Gemma per item | Qwen per item | Maximum per item | Oracle gain over Gemma |
| --- | ---: | ---: | ---: | ---: |
| 1, 17.2, 23.2, 24 | 0 | 1 | 1 | +4 total |
| 25 | 0 | 1 | 3 | +1 |
| 8.2, 11.2, 12.2, 13, 14.2, 16.1, 18, 22.1 | 1 | 0 | 1 | 0 |
| 6 | 2 | 1 | 2 | 0 |
| 26 | 8 | 2 | 15 | 0 |

The shared zero-point set is **3.1, 3.2, 5.1, 7, 8.1, 11.1, 12.1, 14.1, 19.1, 19.2**, totaling **11 available points** (19.1 is worth two; the others one each). Neither existing answer supplies those points under the consolidated scores. The oracle also leaves seven points on item 26 and two on item 25: **11 + 7 + 2 = 20 missing points**. The both-full set is 2, 4, 5.2, 9, 10, 12.3, 15.1, 15.2, 16.2, 17.1, 20.1, 20.2, 21, 22.2, 23.1; it contributes 17 points.

**Decision implication:** routing between the two preserved baselines cannot meet 48/60 under either the consolidated scores or their supplied high bounds. The target requires improved answers or revised grading beyond those bounds. These item-level evaluation findings must not become training/retrieval examples or an exam-specific deployed routing rule.

## Reproducible source identity

Only score fields, numeric IDs and maxima were inspected for this calculation; no official keys, questions, source text or answer content were needed. No inference, network access or changes to the active arm occurred.

- `agentsLog/Pewciu6/results/review_gemma4-12b-val40-1024.json`: SHA-256 `397453ec35b56696d5216ebcf9754a5ce27f5fc2450d826d103a59c3d4ed3a36`.
- `agentsLog/Pewciu6/results/review_qwen35-9b-val40-1024.json`: SHA-256 `46308b65eeeaf6e58ab8e712075ad079f1d6bc705034a58d3ec3c0073ebb87c5`.

Checks: unique and identical 40-ID sets; matching per-item maxima; summed maxima 60; reviewed sums 35/25; low sums 28/16; high sums 40/29; oracle reviewed/low/high 40/31/45; matrix sum 40; shared point overlap `sum(min(G,Q)) = 20`, hence `35 + 25 - 20 = 40`.
