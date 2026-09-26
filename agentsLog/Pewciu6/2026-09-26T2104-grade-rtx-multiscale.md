# RTX multiscale/crops diagnostic (6 items × 3 passes): blind first-pass grading (issue #11)

**This is a 6-item known-validation DIAGNOSTIC, not a score.** It is @Pewciu6's provisional first-pass agent grading of semberecki's #95 run, done at the request on [#11](https://github.com/kwiscion/machinekind-matura/issues/11#issuecomment-5848891589). It is not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here.

## Headline

| 6 items, 8 points | Control (bare, temp 0.2) | **Final (multiscale + observation)** |
|---|---|---|
| All 6 items | 4 (2–6) | **4** (3–5) |
| Failed source interpretations: z5.1, z14.1, z25 (max 5) | 1 | **1** |
| Correct controls: z2, z4, z13 (max 3) | 3 | **3** |
| **Paired Δ final − control** | | **0**, range −3 to +3 |

On the same items, bare Gemma #53 scored **3/8** (0 / 3), and the RTX transfer control #89 also scored **3/8**.

**Verdict: no effect shown.** The final pass fixes z5.1 (+1) and loses z25 (−1), and it breaks none of the controls. With one draw per pass, the uncertainty (±3) is much larger than the effect (0).

## Per item and pass (graded blind, then unmasked)

| Item | Max | #53 bare | Control | Observation* | Final | Δ (range) | One-line reason for the final pass |
|---|---|---|---|---|---|---|---|
| z5.1 | 1 | 0 | 0 (0–1) | 0 | **1** (1–1) | **+1** (0 to +1) | correct decision; the call is tied to crusades and the map is now correctly identified, so both sources are used |
| z14.1 | 1 | 0 | 0 (0–0) | 0 | **0** (0–1) | 0 (0 to +1) | the decision is now correct and the order is correctly identified, but the map is placed in a different war |
| z25 | 3 | 0 | 1 (0–2) | 0 | **0** | **−1** (−2 to 0) | wrong era and wrong subject; the lettering is misread, so the message and context are wrong |
| z2 | 1 | 1 | 1 | 0 | **1** | 0 | correct decision; both sources are correctly dated against each other |
| z4 | 1 | 1 | 1 | 0 | **1** | 0 | a valid argument from the image |
| z13 | 1 | 1 | 1 (0–1) | 0 | **1** (0–1) | 0 (−1 to +1) | correct event; justified by the date and symbolism in the print, with a partly invented description of the scene |

\*The observation passes are intermediate source descriptions, not answers to the question. They score 0 by construction and are excluded from the totals.

Control-pass notes: z5.1 decision correct, but the map is misread as an earlier migration era (the same failure as #89). z14.1 wrong decision (the gate fails). z25 **1** (0–2): the message and one element are roughly right, but the context is hedged across two decades, the figure is unidentified and part of the scene is misread. z13 correct event, but it invents scene details.

## Did multiscale fix the failed source interpretations?

- **z5.1: yes, on this draw.** The 220 DPI observation read the map legend correctly and the final pass used it. This is the one place where the mechanism is visibly doing its job.
- **z14.1: partly, but not for points.** The final pass flips to the correct decision but places the map in the wrong war. The observation pass described the **wrong page** as source 1: page 16 carries z13's print, so it described that print. It also read only day–month dates off the map, with no year, so the final pass had nothing to anchor the campaign's year.
- **z25: no, and it regressed.** The observation misread the lettering, gave no identification of the figure and missed a key graphic element. The final pass then invented a post-1956 reading. The control pass at temperature 0.2 had found a roughly right message (1 point), so this regression is −1 relative to control. Relative to #53 bare (0) it is unchanged.
- **Controls z2, z4, z13 were not broken.** All three stay at 1 in the final pass.

## Consistency with our earlier grades

- Control vs #53 bare: 5/6 items get the same points. The difference is z25, 1 vs 0. #53, #89 and every earlier arm read that cartoon wrongly, so this temperature-0.2 control draw is the first to get a roughly right message. That points to sampling variance, not to the input.
- The z5.1 control failure is the same "different migration" misread that #89 had, and the z14.1 control repeats the #53 wrong-decision failure. The controls reproduce the known baseline behaviour.
- z13 is uncertain (0–1) on every pass, as it was in #53 and #89, because the answers lean on the given date and add invented scene details.

## Blinding, hashes and checks

- **Blinding:** the pass labels were hidden and answers were shuffled per item with `random.SystemRandom`. Grades were written to a file before unmasking. The observation passes were identifiable by their format (descriptions, not answers), so the blinding was only effective between control and final.
- Answers `b3072b4e…4f512` (verified, 18 rows, 18 unique id×pass, all `stop`, 0 errors). Keys `f66e3877…` (same as #53). Run record: `agentsLog/semberecki/2026-09-26-rtx-multiscale-diag-manifest.md`.
- Grader evidence: the official CKE 2024 rules and 110 DPI page renders (p. 5, 7, 8, 16, 17, 28). I did not see the 220 DPI renders, which are private on the RTX host.
- The keyscan leakcheck (6-gram plus short-key) and the answer-string scan both found 0 hits on this note and the JSON.

Machine-readable output (ids, passes, points, ranges and one-line notes only): [`results/review_gemma-rtx-multiscale-diag6.json`](results/review_gemma-rtx-multiscale-diag6.json).

**Limitations:** there was one agent rater and no human examiner. There is one stochastic draw per pass at temperature 0.2. The 6 items were selected, not random, and n=6 is not evidence of a general effect in either direction. Do not extrapolate this to the 60-point scale. A full-40 arm, if wanted, should be judged on the image-item slice with repeated draws on z5.1/z14.1/z25-type items. Two mechanism issues are worth fixing first: the observation page-routing picked up z13's page for z14.1, and year-bearing map text was not extracted. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0, and the grader made no model calls.
