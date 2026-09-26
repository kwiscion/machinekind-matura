# Failure-only recovery: insufficient quality gain

The six-call paired diagnostic completed, but fresh nonthinking recovery earned **1/6** and recovery conditioned on interrupted reasoning earned **0/6**. Both independently graded arms agree with the lead's earlier provisional assessment. The lead's assessment was recorded in session context before the second assessment arrived, but was not persisted as a separately hashed grading artifact before that arrival; this document is a reconciliation, not a new blinded rater record.

| Printed item | Maximum | Fresh final A | Notes-to-final B | Failure class |
|---|---:|---:|---:|---|
| 12.1 | 1 | 0 | 0 | Wrong historical identification despite source constraints |
| 19.1 | 2 | 1 | 0 | Incorrect factual true/false selections |
| 25 | 3 | 0 | 0 | Wrong visual inscription, historical context and intended message |

The lead inspected the original source-v2 text, relevant full-page images and official evaluator rules, without reading interrupted reasoning. The separate reviewer independently inspected the text and images, verified exact answer hashes, and froze the report before receiving lead scores. Arm labels were visible; this was not a blinded model comparison.

## Decision

- Park interrupted-reasoning recovery. It consumed substantially more input without recovering credit and repeated factual/visual errors.
- Keep fresh retry as an available generic runtime-failure fallback, not a promoted quality improvement. A retry returns usable output but does not guarantee a correct answer.
- Do not report 39/60 as a measured full exam: 38+1 is posthoc arithmetic across separate runs. The measured full-thinking result remains38/60 pending second full review.
- Do not inject the correct ruler, inscription or historical context into production prompts. Such corrections belong only to evaluation. Subsequent source-grounding experiments must use generic, input-defined mechanisms and matched controls.
- Prioritize the incoming paired RTX reasoning evidence, essay argument construction and the now-ready single-base training pilot over more changes to the failed notes prompt.

## Evidence

[Terminal execution](2026-09-26-answer-recovery-result.md), [independent grading](2026-09-26-answer-recovery-second-review.md), and [per-answer hashes](2026-09-26-answer-recovery-second-review.json) retain exact outputs and source provenance. All six submitted finals were nonempty with normal stop and no returned thinking. Original full40 answers remain unchanged.

A handoff SHA256: `ad93976a5361179d209e67e4ed6573849bfaf0e6b829b1c13549727ae0e7b56c`.
B handoff SHA256: `fcc745275a65969ec04e54a0c4ed649d97c7da8c20e31ba3db7eeb96b2e31f5a`.
Second-review JSON SHA256 at handoff: `cf67bbaabb158c43ffd8391157c938c43e662c3de6b075b28e66deb6155f854b`.
