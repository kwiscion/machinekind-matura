# Independent reasoning-wave terminal audit and grades

**The old wave is terminal. Independent scores: baseline 6/11; evidence critic 5/11; statement-wise PF 4/4 [3,4] versus baseline 2/4; thinking 1/11 including failed/unsent items.** This is a selected known-May2024panel, not a full 60-point score or promotion.

## Terminal evidence

At 19:25:31UTC, read-only process inspection found no running reasoning controller, guardian or Ollama process. Actual artifacts record 36 new calls and an early stop for an incomplete native answer. First reservation 17:57:13.209UTC; last response 18:01:48.477UTC, about 275.27 seconds later. The 19:00 UTC deadline was not used as proof of termination.

The ledger reconciles 22 completed, 1 failed and 6 unsent family outputs out of 29 planned. This represents 36 of 42 planned generation calls. Including the 2 prior readiness calls gives 38 calls and 74,240 requested tokens (73,728 new). Actual new usage is 36,646 prompt and 11,906 generated tokens; the latter includes thinking. Final-only versus thinking-only counts are unavailable. No actual bill is inferred.

All four downloaded evidence files match remote SHA-256. The formerly missing last-three-response audit is closed: **all 36 responses omit both truncated and context_truncated fields**; none has a truthy explicit flag.35 responses ended stop. Thinking z7 ended length after 2048 generated tokens, with 7390 thinking characters and zero final-answer characters; its failed row correctly remains 0. Absence of explicit flags is not proof against every silent context issue.

PR127 is merged, exact fixed head1e1f6b0ebc8c96e2aa4eec4409462db426b9263b, mergeba63a3583ce92ed5a6f7cc330c93c45881a2b5fd. The frozen old wave used6a268bb19d2608af5614cf565169a2b695e16880. Nothing was changed or restarted. The current process absence and terminal evidence establish no intervention is needed for this old task; they do not identify its exact historical cleanup timestamp.

## Independent item ledger

| Item | Max | Baseline | Critic | PF | Thinking |
|---|---:|---:|---:|---:|---:|
| z1 | 1 | 0 | 0 | — | 0 |
| z2 | 1 | 1 | 1 | — | 1 |
| z7 | 1 | 0 | 0 | — | 0 |
| z10 | 1 | 1 | 0 | — | 0 |
| z14.2 | 1 | 1 | 1 | — | 0 |
| z19.1 | 2 | 0 | 0 | 2 [1,2] | 0 |
| z20.1 | 1 | 1 | 1 | — | 0 |
| z20.2 | 2 | 2 | 2 | 2 | 0 |
| z24 | 1 | 0 | 0 | — | 0 |
| Total | 11 | 6/11 | 5/11 | 4/4 [3,4] | 1/11 |

PF is assigned only two items; its other rows are outside that family, not unsent failures. Thinking completed z1/z2, failed z7 and left six subsequent items unsent. Its observed two-item result 1/2 ties baseline 1/2; this must not replace the planned 1/11 result.

## Interpretation and disputes

- Critic produces a secure one-point regression on z10 and no gain. It preserves major visual/chronological errors and sometimes adds new false historical detail.
- PF improves the same two-item panel from 2/4 to 4/4 [3,4]. On z19.1 the third stage initially gives the wrong indication, debates the choice and ends with the correct indication. Central accepts the explicit final commitment; low invalidates the conflict and awards 1/2 for the two remaining correct indications. Its supporting history remains unreliable. Thus the binary-score gain is not evidence of consistently grounded reasoning.
- z20.2 uses 0-based numbering in baseline/critic, but the three values in source order are recoverable and correct. The prompt itself includes an extracted 0–1–2 score-band artifact. No automatic exact-number parser was substituted for manual judgment. PF repeats consistent correct values.
- Baseline z14.2 includes an unsolicited wrong answer to the adjacent subtask, then clearly gives the correct requested choice. The extra prose is logged as a quality problem; it is not a competing choice for the graded item.
- Native thinking did not improve its two completed cases and exhausted the shared generation cap before any final answer on the third. This supports testing a separately declared larger budget; it does not establish a quality gain.

Every request retains its exact source-v2 prompt verbatim. I checked official May2024criteria and inspected the actual rendered request images for essential visual judgments. Public JSON contains all 29 item/family scores, reasons, uncertainties, answer hashes and the complete compact 36-response flag audit. No new exam was opened, no benchmark content entered training, and no model call, GPU operation or Git mutation was made.

Exact answer-only handoff: `private/lukasz-reasoning-review-20260926/answer-only.jsonl` (29 records). It excludes provider envelopes, thinking, source/image buffers and infrastructure metadata. It remains ignored because some model finals themselves reproduce question/source wording; this public report contains original summaries and hashes.
