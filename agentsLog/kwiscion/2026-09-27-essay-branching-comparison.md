# Essay branching: frozen masked-grade join

| Output | Chosen topic | Points /15 | Scoring range | Body words |
|---|---:|---:|---:|---:|
| direct_control | 3 | 8 | [7, 8] | 425 |
| topic_draft 1 | 1 | 11 | [11, 12] | 401 |
| topic_draft 2 | 2 | 6 | [6, 8] | 379 |
| topic_draft 3 | 3 | 6 | [6, 7] | 399 |
| selector_final | 3 | 6 | [6, 7] | 407 |

The unchanged direct control scored 8/15; same-model selection/revision scored 6/15, losing 2 points. The best saved candidate scored 11/15, so selection left 5 retrospective oracle points unused.

Forcing independent topic drafts exposed a stronger candidate, but this selector did not exploit it. A selector-only candidate-ID experiment could separate choice from rewriting; it must use generic factual-support/coverage criteria and export the chosen saved answer unchanged, without rubric hints or a preferred topic.

This is arithmetic over one frozen masked scoring pass, with exact answer hashes verified against both packet and key. No answer was regraded or promoted after observing scores. Seven actual calls reserved262,144 output tokens. Scoring ranges are judgment sensitivity, not confidence intervals; the single known task cannot establish generalization.

Grade JSON SHA256: `2069ff25522e6d87a0b76ad20aae8308f947d60ec106c8ec68acde69709d3f81`. Comparison JSON SHA256: `d97786b1a83e6f79a420d769295dca71f3e0a8dc3e18523e85e90858daa25843`.
