# Native-thinking pair: one-pass comparison

**Qwen6/8 [6,7]; Gemma4/8 [3,4].** Qwen gains on the crusade/map distinction and the Solidarity cartoon. Both miss the campaign/source-date comparison in14.1. This is the frozen legacy full-page panel, not the new cropped inputs.

| Item | Maximum | Gemma | Qwen |
|---|---:|---:|---:|
|2|1|1|1|
|4|1|1|1|
|5.1|1|0|1|
|13|1|1|1|
|14.1|1|0|0|
|25|3|1|2|

Qwen completed all six first attempts in302seconds. Gemma took1093seconds including a32,768-token exhausted generation and a420-second timeout before recovery on25. This panel-level elapsed difference includes retry behavior and is not a general throughput benchmark. Both produced six complete answers.

The masked grade was frozen before reading the arm key; all12 exact-answer hash joins pass. The two-point central gain remains positive throughout the recorded rubric ranges. A second grading pass would not change the next decision and is not scheduled.

**Decision:** retain the38/60 full-exam Gemma champion; run a full corrected-input Qwen challenge after the corrected Gemma control. The models used different native sampling and adaptive wall allocations, so do not attribute the result solely to weights. No essay or full-exam quality was tested here. Both models fit separately; submitting both would exceed the aggregate8.8GB limit.

[Execution and usage](2026-09-27-native-pair-result.md) · [Frozen masked grade](2026-09-27-native-pair-masked-score.md) · [Exact comparison and hashes](2026-09-27-native-pair-comparison.json)
