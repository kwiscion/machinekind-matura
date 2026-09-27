# Native Qwen/Gemma pair — terminal execution evidence

**Twelve of twelve complete answers; fourteen calls; both operators and cleanup passed.** This is the frozen **legacy full-page source-v2** panel, not the later corrected source crops. Items2,4,5.1,13,14.1,25:8available points per arm. Quality grading is separate; no promotion is claimed.

| Arm | Calls | Failed attempts | Complete answers | Known prompt / generated tokens | Unknown usage calls | Wall seconds |
|---|---:|---:|---:|---:|---:|---:|
| Gemma |8|2|6|8,680 /44,080|1|1093.080|
| Qwen |6|0|6|11,882 /27,183|0|301.863|

Gemma item25 first reached32,768generated tokens, then its higher-cap attempt timed out at420seconds. The owned backend was stopped before the thinking-off attempt completed; no earlier valid answer was erased. Qwen completed all six initial attempts. No injected faults, warmups, extra calls or external answer selection occurred.

Both models verified exact pinned digests and actual65,536context. Complete text and images remained frozen. Each used its own single-model cache and isolated loopback-only namespace; external IPv4/IPv6 probes returned errno101. Owned cleanup receipts passed; GPU was empty afterward and the original service remained unchanged/idle. Gemma cache7,556,509,301bytes; Qwen cache6,594,475,420bytes. Each fits8.8GB separately; combining them exceeds the submission limit.

Same declaration2026-09-27T00:17:59.751934+00:00, deadline2026-09-27T01:17:59.751934+00:00; pair start2026-09-27T00:18:14.063815+00:00, terminal2026-09-27T00:41:29.163386+00:00. Actual operator wall1395.100s; declaration-to-terminal1409.411s; deadline margin2190.589s. Actual requested output475,136tokens of1,769,472;14calls of48. Known usage20,562prompt +71,263generated, plus one timeout with unknown usage. Time-based estimate$1.284 at planning$3.28/h; actual billing unverified, staging/idle time excluded.

Gemma sampling was omitted; Qwen usedT1/top_p.95/top_k64. Sequential shared-deadline allocations differ. Treat this as a declared systems comparison on six known items, not a model-only causal effect or full-exam score.

The shuffled12-row grading packet matches every terminal final exactly. Raw responses/thinking remain private. Maximum contiguous source/question overlap was14words; no final was edited. [Exact answer-only export](model-answers/native-pair-twelve-answer-only.jsonl) and [metrics/pins](2026-09-27-native-pair-result.json).

Verified local/remote full archive SHA256: `3e924723a081810135372472a1cb455f1999e3f73b1a79e692838e49fb728f6c`. No further inference is authorized by this report.
