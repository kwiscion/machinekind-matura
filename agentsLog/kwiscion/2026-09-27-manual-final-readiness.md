# Manual final readiness

The owner selected Qwen3.5:9b with full-Wikipedia RAG for ordinary questions and essays. The manual entry point is `scripts/run-final.ps1`; [the runbook](../../docs/FINAL_RUN.md) contains start and resume commands. Final questions have not been accessed.

## Verified live path

The exact PowerShell entry point processed two original May2023 DEV items: one question with an image and the essay, preserving all offered topics. This was a compatibility smoke, not a scored final exam.

- Run: `20260927T075706-fbdc2cd3`, starting 09:57:06 Warsaw.
- Validated answers reached the laptop at 10:02:39.987 Warsaw: **333.578 seconds (5m34s)** from local launch, including preparation and transfer.
- Two nonblank answers, zero placeholders. Automatic direct essay-format recovery ran before RAG.
- Essay RAG completed and its writer output was selected. Ordinary RAG completed its relevance checks; no evidence was admitted, so the exact direct answer was retained.
- Ledger: 49 reservations and 49 completed events. The finite declaration allowed 164 attempts and 611,712 requested output tokens, with a 20-minute hard remote bound for this smoke. Actual usage is preserved in the private ledger.
- Operator exit code 0; sentinel stopped successfully; post-run GPU process list empty. No external agent wrote or cleaned the answers.
- Answer SHA256: `8d4b630757873e18236b61b83d4350afb993344a46dd6da4eca1a3618eb22bd7` (4,206 bytes).
- Backup SHA256: `c2400571845803598f28186d30185798ee6449123fa56133735e32ea20da4d64` (13,725,928 bytes).
- Smoke source inventory: `e28d56c9aa07c3b1b30655c8664d80f6bd98427b3f6fa9b36ba0a4d2be50360a`; manifest: `f7bbdeef24816e2e052a76dcae9efb1d04ca2d01e5eb704e0f40676abb9615a8`.

## Bounds and resources

Production starts its clock locally: remote work ends at minute 55, optional RAG stops before the ten-minute recovery/export reserve, and local answer retrieval targets minute 60. Manual submission has five further minutes within the owner's 65-minute budget. The final question package's actual item count and essay IDs are used. This hard inference policy does not guarantee external network or submission-site availability.

The dedicated Pawel H100 stage contains a clean five-file Qwen cache totaling 6,594,475,420 bytes and a read-only 10,464,555,008-byte full Wikipedia index. Index SHA256: `5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36`. Native model manifest: `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. No additional retrieval-model weights are used.

## Verification and limits

All 14 deadline-RAG regression tests passed. Independent tests covered both successful routes, invalid essay plans, failed evidence checks, essay cutoffs followed by ordinary work, late-output rejection, full inputs, archive handling, duplicate-dispatch protection and cleanup of owned processes. Eight manual-delivery tests passed, including answer retrieval while the backup is still being built and an explicit late resume. Both standard GitHub checks passed on the initial implementation head.

The final 40-file source inventory is `60d9eb9450fca56d57b5ce83eeb894ef62645b83958ec04f21bfe8ed2b58c493`. The only execution-source delta after the live smoke permits an explicitly requested resume to retrieve its completed backup after the original local time target; inference and dispatch are unchanged. The actual PowerShell resume returned identical answers without increasing the 49-call ledger. The original first-ready timing is retained in `first-validation.json`. Three inherited Python files have explicit CRLF checkout attributes to reproduce their qualified working-tree hashes.

The direct full-exam baseline remains 40/60 in 27m58s. This two-item live smoke verifies integration, not a new full-exam score or a measured 65-minute full RAG run. Final-question access freezes all team development. The final source inventory, resume check and exact reviewed release revision are recorded with the final freeze declaration on issue3.
