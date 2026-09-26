# Heterogeneous source observer replication — completed

The mechanically selected six-case comparison completed all 18 calls with no errors, fallback, or unsent stages. Every response ended with `stop`; actual quality awaits independent grading. This selected known-validation panel is not a full-exam promotion result.

Execution order: z8.1, z9, z13, z18, z21, z23.1. Selection used the lowest SHA256 of `hetero-replication-v1|id` among 25 eligible image-bearing nonessay cases, excluding the original six. No keys/scores informed selection. Full original source text and seven image references were preserved. Existing generic observer/solver prompts and both pinned models were unchanged.

| Stage | Calls | Prompt tokens | Completion tokens |
|---|---:|---:|---:|
| Gemma bare | 6 | 5,622 | 620 |
| Qwen observation | 6 | 11,263 | 1,683 |
| Gemma final | 6 | 7,986 | 727 |

Maximum requested output: 18,432 tokens; actual completion: 3,030 tokens. Thinking off; temperature omitted; context 32,768; output cap 1,024; request timeout 420 seconds. Sampling defaults remain unfixed. Runtime 0.34.4 and full model digests/context were checked before/after calls. Returned usage and explicit truncation flags were checked; this is not a separate formal proof of the runtime's internal truncation behavior.

The first durable reservation was 2026-09-26T19:36:29.846590+00:00; completion was 19:38:32.830949+00:00. Worker wall time including preflight was 137.915 seconds. Execution-time estimate at the supplied $3.28/hour planning rate is $0.1257; actual billing is unverified. Declared maximum was 30 minutes/$1.64, deadline 20:02:34 UTC. An initial timestamp serialization failure occurred before any reservation/model call; normalizing fractional precision did not extend the deadline or change model settings. No retries or additional smokes occurred.

Local backup verified: `94a1098231204555f807fddf1a95ab9d756fe7dc4807f955144ed6c26e9e10e1`. Raw response SHA256: `ab7189ff99c368f16d4e00721a059060a708719652d4460d52d9a75e149e0630`. Manifest SHA256: `02828463f129d0341ef2a5308e6d9f379e2416dbeb7cf654a0b251b57025134d`. All dependency/input/image/request hashes match. Raw responses, original source packs, runtime snapshots and the fsynced call ledger remain private.

Exact answer-only handoffs are `model-answers/hetero-replication-bare-six.jsonl` and `model-answers/hetero-replication-final-six.jsonl`, with `model-answers/hetero-replication-six.manifest.json`. Both contain all six IDs, exact unedited answers, errors and finish reasons. Source-text overlap screening found no 15-word matches; no answers were silently changed. The observation handoff is privately retained. No score is asserted here.

Fifteen inherited CPU tests and selection/source-byte checks passed before launch. The worker is terminal and the owned runtime remains unchanged for the next authorized task.