# Component review at morning cutoff

Reviewed main `ee0b8a7` on 2026-09-26 after the 08:00 Europe/Warsaw expensive-run cutoff. Scope: merged PRs [16](https://github.com/kwiscion/machinekind-matura/pull/16), [17](https://github.com/kwiscion/machinekind-matura/pull/17), [19](https://github.com/kwiscion/machinekind-matura/pull/19), [20](https://github.com/kwiscion/machinekind-matura/pull/20), and [21](https://github.com/kwiscion/machinekind-matura/pull/21). PR 18 data review belongs to the separate reviewer. No inference, training, downloads, purchases, or restricted exam/key reads were performed here.

## Decision

- Accept #15 as a completed, useful negative experiment. The paired provisional whole-context audit gives complete support on 13/40 candidate contexts versus 14/40 chrono top-3 baselines, with one win and one regression. Keep the existing core `chrono`, k=5 retrieval configuration; do not promote the candidate or any model. Candidate compression/threshold variants are not independently audited. These are TRAIN retrieval diagnostics, not exam gains.
- Keep #11 open: real exam outputs and a VALIDATION result remain missing. Correct the handoff's overbroad statement that no model outputs exist anywhere. Committed synthetic LM Studio outputs exist under `agentsLog/Pewciu6/smoke/`; local Gemma/Qwen smoke results also exist. None establish an actual exam score.
- PRs #19/#20 provide snapshot-specific lexical contamination checks, not proof of absence. Their reports cover PR #18 heads `64d69815` and `c5009a5e`; the later report records zero flagged records and three review-band records. No hidden keys were read or audit rerun in this review.

## Verification

```text
python -m unittest -v test_infer.py scripts.test_adapters
12 tests passed

python -m unittest discover -s agentsLog/Pewciu6/harness -v
28 tests passed
```

The evaluator tests cover the adversarial fixtures, raw/normalized adapter compatibility, citation marker resolution, contamination JSONL conversion, and sealed-split guard using synthetic inputs. One non-fatal ResourceWarning reports an unclosed temporary corpus file in `contamination_check.py:122`.

A separate in-memory synthetic selector check confirmed baseline5 returns five chunks and the candidate retains the leading anchor and stays within its 3000-character budget for that fixture. No full corpus benchmark was rerun.

`git diff --name-only 985aaf0..ee0b8a7 -- infer.py scripts docs/overnight/CONTRACTS.md SOURCE.md` is empty: no core runner, adapter, or shared contract drift. The owner-local evaluator schema was widened to accept the existing raw backend object, and tests verify compatibility with the core normalizer.

## Remaining evaluator finding

`agentsLog/Pewciu6/harness/matura_harness.py:894` computes the mean for every number of raters, while the summary at line 928 advertises a median after a third rater. The escalation flag at line 913 also remains true once three reviews exist. A synthetic three-rater check with points `[0, 6, 6]` returned `mean_points: 4.0` and `needs_third_rater: true`; the advertised median would be 6. This does not invalidate the reported two-rater dry run, but must be resolved before treating three-rater adjudication as implemented. No owner file was changed during review.

Acceptance criteria: test three distinct reviewers with `[0, 6, 6]`, use median 6 for the adjudicated aggregate, clear `needs_third_rater`, retain all reviews, and preserve the two-rater mean/escalation behavior. Only the three-rater adjudication path is blocked.

Posted the [#15 acceptance](https://github.com/kwiscion/machinekind-matura/issues/15#issuecomment-5844022616) and closed #15 as completed. Posted one [#11 factual review and defect note](https://github.com/kwiscion/machinekind-matura/issues/11#issuecomment-5844023940); #11 remains open. Attached all five reviewed PRs to the Codex task.

All grades remain provisional. Only 18/60 VALIDATION points are fully automatic, and no model is promoted from infrastructure tests or contamination diagnostics.
