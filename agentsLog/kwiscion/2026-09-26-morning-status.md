# Morning status — 26 September 2026

Checkpoint: 08:50 Europe/Warsaw. Windows restarted during the night; the owner has now resumed work for two hours, through 10:47. This extends the original operational cutoffs. The heartbeat is updated for this window; new model calls stop by 10:30, handoffs by 10:40. No account reset credits or other-project credentials may be used.

| Area | Verified state | Next action |
| --- | --- | --- |
| Local inference | Qwen 3.5 4B installed, fully on the 8 GB GPU; nonempty text response verified with `reasoning_effort: none` | Luna runs a bounded, source-complete May 2024 text-only diagnostic under lead issue #3; results feed #11 |
| Core integration | Portable runner, RAG preparation, output adapter, CI; 12 core/adapter and 28 evaluator tests pass | Fix the independently reproduced third-rater median/adjudication defect, then regression-check |
| Retrieval | 107 sources and a reproducible 3481-chunk index; original chrono baseline retained | #15 accepted as a negative experiment: no evidence to promote its context selector |
| Evaluation | May 2024 acquisition, isolated keys, 40-item/60-point evaluator, adversarial tests and lexical contamination audits | No actual exam score yet; 29/40 items need images and only 18/60 points are fully automatic |
| Training data | PR #18 is open at reviewed head `c5009a5e`; source manifests are structurally complete | Changes requested: 197 legacy records are exported despite only 24 passing both strict lenses; global distractors expose 6/7 internal holdout groups in 18 training prompts. Sol is repairing these exact defects |
| Spark / training | No results reported in issue #5 | Keep unpromoted; do not claim a fine-tuned model or successful GPU training |
| Hugging Face | Public dataset is still empty; normal cached account authentication is unverified, CLI/library unavailable | Prepare a reviewed candidate first; upload is not a dependency for local work |

The implemented evaluator and retrieval components are accepted handoffs, not evidence of model accuracy. Synthetic smoke outputs exist, but they are not exam results. Lexical contamination scans cover specific text snapshots and cannot prove absence of semantic or visual overlap. May 2025 remains sealed because no candidate decision is frozen.

Lead work allocation: Sol repairs data/export gates in an isolated PR checkout; a second Sol fixes evaluator adjudication; Luna performs the bounded local diagnostic. The lead coordinates and reviews exact revisions. New work is recorded in issue #3, with #4 and #11 holding their respective acceptance criteria. No duplicate teammate workers are started.

Logistical checks still outstanding: confirm the final competition subject (history is the working assumption) and complete the team roster by Saturday noon. Final artifact freeze remains Sunday 27 September at 11:00 Europe/Warsaw.
