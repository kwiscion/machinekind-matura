# Independent RTX runtime review — PR #73 / #71

Reviewed PR #73 exact head `7fda45f56514f2505a1a65a313914137a8836679` and PR #71 handoff head `2efd58b26c3c88163b2c7cf6304bc2ad5c564133` via read-only `git show`, after current WINNING_PLAN. No host access, generation, checkout, downloads or teammate edits. PR artifacts attached.

**Verdict: sufficient reported readiness to schedule a bounded useful RTX run; not independent proof of stage-time compliance or final offline readiness.** Piotrek reports three successful synthetic native text/image calls, full GPU placement and ample capacity on the **24 GB Laptop** variant. Runtime archive/executable hashes and complete model/projector digests now identify a reproducible candidate. Do not spend another cycle blocking useful work on documentation wording.

| Claim | Independent assessment |
|---|---|
| Same saved model | Full manifest/model/projector digests and 7,556,497,632 combined bytes agree with the accepted recipe. Evidence says Ollama verified at pull; PR contains a summary, not raw local hash-command output. Run the existing PR71 read-only all-blob check and retain its result before the arm. |
| Runtime | Reported Ollama 0.34.4/archive SHA agrees with PR71 metadata; executable SHA is separately supplied. This differs from laptop 0.30.7. Runtime change must be recorded, not called an identical replication. |
| Driver13.2 | `serve.log driver=13.2` is not enough to label an installed NVIDIA driver release. It likely denotes the CUDA driver/API version; exact meaning remains unverified here. Record `nvidia-smi --query-gpu=driver_version --format=csv,noheader` separately. No upgrade/install is indicated by a working load. |
| Image delivery | Correct synthetic description plus116 prompt tokens supports the claim. Token count alone does not prove the actual bytes entered the request. Only a16-hex image hash prefix and prose appear in PR73; exact request JSON/hash, full PNG hash and raw response are not supplied in the reviewed files. Keep those privately with the next request. Native `done_reason` fields do not establish the core OpenAI-compatible runner path. |
| Effective context | Reported32768 from `/api/ps`, versus laptop4096. PR71's16384 example is a proposal, not the measured value. Declare the next context explicitly and record effective context after its first real load; do not silently mix these three values. |
|54 tokens/s |233 /4.32 =53.94 decode tokens/s is arithmetically consistent with the summary; total request4.5s differs from decode time. Raw timing evidence remains private/unattached. |
|“8x faster per answer”; full arm fits |Not supported: one warm synthetic233-token output is not a matched comparison to laptop37.435s mean across mixed exam prompts/images/essays. Cold call57.7s and long-image prefill are material. Neither stage allowance nor final package distribution is known. PR71's category/end-to-end measurement method is appropriate. |

The PR73 table also mentions a smoke added around17:48 despite a17:30 commit timestamp. Reconcile host timezone/clock or prose later; this does not negate successful output. No final offline namespace/model proof is included in PR73. PR71 explicitly distinguishes documented support from measured execution and correctly avoids promising a deadline.

## Practical next action

1. Piotrek retains sole ownership of his RTX endpoint. Record actual driver, version, `/api/show` parameters, installed full digest and read-only blob hashes; preserve exact private request/response and asset hashes. These are short metadata checks, not a new experiment.
2. Use the already reserved fourth synthetic smoke **only if the exact `infer.py` OpenAI-compatible text/image path has not been tested**: same1024 cap, thinking off, no retries, existing synthetic image, declared context. It closes a transport gap rather than benchmarking again. Alternatively, the first authorized full-arm request may serve as that gate, with its response preserved and no second dispatch on incompatibility.
3. Lead selects and freezes one useful40-case source-v2 arm and its hypothesis. If the purpose is delivery/throughput qualification, bare source-v2 is the measured working candidate; label this as a new-runtime portability/timing run, not a duplicate claim of score gain. Keep1024 output tokens, thinking off, serial requests, no new policy/crops/RAG unless separately selected. For comparability use explicit4096; if deliberately selecting32768, declare the context change and evaluate it as such. Cap40calls/40960 requested tokens/$0/no retries, all failures/unsent IDs retained, fixed deadline and exclusive queue. No May2025.
4. Time the entire arm, including cold load and image/essay requests; separately report decode throughput. Final offline proof and organizer acceptance remain subsequent gates. Do not hold the bounded validation run waiting for those later gates or for correction of the driver label.

No inference is authorized by this review. The lead owns the launch decision and exact frozen handoff.
