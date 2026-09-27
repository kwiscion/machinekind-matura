# Qwen brainstorming diagnostic: do not promote

**A7/12, structured B5/12, exported final7/12, A/B oracle8/12.** B improved one item, worsened three and tied six. All20 independent finals were complete.

**0/10 referee outputs satisfied the strict-ID contract.** Nine returned ordinary answers and one returned an unknown ID plus an extra answer field. The frozen exporter correctly retained A on all ten. This is a failed selection mechanism with preserved baseline, not a demonstrated referee gain. No posthoc parser repair or rewriting is counted.

| Item | A | B | Exported | Oracle |
|---|---:|---:|---:|---:|
| 3.1 | 1 | 0 | 1 | 1 |
| 3.2 | 0 | 1 | 0 | 1 |
| 7 | 0 | 0 | 0 | 0 |
| 11.1 | 0 | 0 | 0 | 0 |
| 11.2 | 0 | 0 | 0 | 0 |
| 12.1 | 1 | 0 | 1 | 1 |
| 17.1 | 1 | 1 | 1 | 1 |
| 17.2 | 1 | 1 | 1 | 1 |
| 19.1 | 1 | 0 | 1 | 1 |
| 20.2 | 2 | 2 | 2 | 2 |

Judgment sensitivity (not confidence intervals): A6–9, B4–5, exported6–9. Ambiguities remain in the frozen masked report; no grades were revised after key joins.

All ten reconstructed initial referee payloads match the durable request hashes and contain the selection instruction, both opaque IDs and the complete candidate finals. The failure is not missing candidate delivery. The shared ordinary-answer validator accepted nonblank replies; strict-ID failure was discovered at export and used recorded fallback. A future fix would need a separately qualified structured stage contract and semantic ID validation within the existing recovery budget. No rerun is authorized by this finding.

Execution:31 calls,1032192 requested output tokens,237128 generated-token count,37951 prompt-token count; no unknown usage. One empty/malformed draft final recovered on11.2--B. Runtime33m45.93s,operator exit0,proxy cost≈$1.8459 (not an invoice), versus120calls/4423680tokens/60minutes/$3.28 ceiling. Cleanup at03:57:55UTC confirmed an empty GPU, no workers, absent recorded owned servers and unchanged original service.

Known-validation fixed10-item subset, one stochastic pair per item, single agent grading. Ranges are judgment sensitivity, not confidence intervals. No new numeric grading of unsubmitted referee rewrites. Model/prompt authorship and prior validation exposure disclosed. After masked freeze, an accounting inspection accidentally printed a truncated embedded provider object in private tool output; raw reasoning is not published and no grade was changed. The first-pass failure was initially called timeout in a progress message; durable evidence establishes empty/malformed final, corrected here.

Frozen masked grade `b7980ac53f2248afc7bf6c0ba8eb0855a81b85be7143dce10e8fa8e05ee75de6`; exact private archive `e4e6d7796aebfc2363ad58254504561d7eaff3c375cd56d0554e5054987f1256`; exported answer artifact `95f00fe00d7d8b0ec31753eac3f1e8011960269fe962442f7db5fe39b99255c2`. All167 archived file hashes and20 masked answer joins verified; selector exports joined exactly to frozen candidate hashes.
