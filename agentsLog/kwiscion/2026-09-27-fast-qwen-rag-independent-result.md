# Fast Qwen RAG: independent result

**Direct4/6; filtered4/6. Do not promote RAG; preserve the measured Qwen40/60 full-exam candidate.**

Twelve arm-masked answers were graded once, then grades were frozen before the arm key was released. No grade changed after unmask.

| Item | Direct | Filtered | Admitted passages |
|---|---:|---:|---:|
| 3.2 | 1 | 1 | 0 |
| 11.2 | 0 | 0 | 0 |
| 12.1 | 0 | 1 | 0 |
| 17.2 | 1 | 1 | 0 |
| 5.2 | 1 | 1 | 3 |
| 19.2 | 1 | 0 | 0 |

The gain on12.1 and regression on19.2 both had no admitted evidence: these were stochastic reruns of the same source-only prompt. The sole evidence-bearing item,5.2, remained correct. No retrieval-backed gain was demonstrated.

| Phase | Calls | Failed | Seconds | Generated tokens |
|---|---:|---:|---:|---:|
| probes | 4 | 0 | 10.76 | 229 |
| direct | 6 | 0 | 264.37 | 35934 |
| query | 6 | 0 | 6.92 | 447 |
| judge | 32 | 2 | 24.93 | 415 |
| final | 7 | 1 | 572.93 | 77581 |

Total wall time: **907.22s (15.12min)**. All52stage slots completed in55attempts, with3failed attempts preserved; no placeholders or unknown usage. Requested output budget:460,800tokens; actual known prompt/generated tokens:93,082/114,606.

Auxiliary query/judge calls were fast, but final answer reasoning dominated runtime. This six-item result does not qualify all-question RAG under the70minute limit.

## Provenance

- Masked packet SHA-256: `46625bd85ddfe34e985b9b3c31c9f2b2799553b5831db02ac4463662c2f89802`
- Frozen blind grades SHA-256: `1355e38af172d9bd9c6e206164c1a83c48079dee04abf4091fd0b39ac65168c0`
- Declared manifest SHA-256: `a5bd4d57fa07c1d14a01c2d8ad3d4724712651c00931890c38d16a2b3d8551e2`

## Limits

One provisional grading pass on six matched items. Both recognizable office-name variants on3.2 were accepted consistently before unmask; organizers remain authoritative. The pre-score generic no-evidence-skip policy differs from the diagnostic and must not be described as a newly measured full run. Phase timings include all attempts and transport overhead. Official keys, copied source text and provider envelopes remain private.
