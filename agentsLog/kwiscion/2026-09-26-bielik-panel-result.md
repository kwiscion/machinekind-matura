# Bielik/Gemma paired text comparison — terminal handoff

All18 reserved calls completed their transport/validation path in68.706 seconds. **Bielik produced7 complete finals and2 length failures; Gemma produced9 complete finals.** No systemic failures or unsent items. Independent grading is pending; this selected known-validation text panel is not a full-exam score or model-promotion result.

| Arm | Complete / attempted | Failed IDs | Prompt / completion tokens | Summed request seconds |
| --- | --- | --- | --- | --- |
| Bielik11B v3 Q5_K_M |7/9|z3.2,z15.1 (length,1,024 tokens each)|9,544 /4,512|42.704|
| Matched Gemma4 12B Q4_K_M |9/9|none|7,174 /1,511|23.727|

The two readiness calls are separate:20 total generation calls across readiness and comparison, no retries or additional smokes. The comparison requested at most18,432 output tokens. Both arms used identical original prompts/source text,1,024 output cap,420-second timeout,32,768 effective context and omitted temperature. Gemma thinking was disabled; Bielik has no thinking capability. All model identity/context snapshots passed. Source-only selection froze every zero-image non-essay row before any grading; no image was dropped and no key entered generation.

The two failed partial finals remain private and are exported as blank answers with explicit errors. Every one of the nine IDs remains in each arm's denominator. Completed answers are exact model strings, without edits. No normalized contiguous source overlap of15 or more words was found; this is a quotation-screen result, not a quality score.

Answer-only handoffs: `model-answers/bielik-panel9-answer-only.jsonl` and `model-answers/gemma-matched-bielik-panel9-answer-only.jsonl`. Provenance, failed IDs, usage and exact hashes are in `model-answers/bielik-gemma-panel9.manifest.json`.

Private backup archive SHA256: `30c3a861d48061065a1386e8348d6979c2fdb70fa8eaa7a1cf0aea2e6d6e9d64`; raw SHA256: `2bdf49086ea14b707ae7c6c55e3b7999b7b874c6c7f2729956150a6d31b84760`. The archive was copied locally and both hashes independently checked. It retains all original requests/responses, runtime snapshots, fsynced call reservations, frozen code/input/launch files and terminal summary.

Controller SHA256: `cc11da3b70c8f3da6f6905b2878d227d90bc5bb54a308d3ee5cad7a5663b1278`. Five network-free tests passed; the lead independently reran them and verified all nine source rows before launch. Exact launch SHA256: `b387d3ac21e9da2a1db9c982655dcb6756bc3e96d822ff5b6a7dcbb2cccf1513`. The worker is terminal; no further experiment was started.
