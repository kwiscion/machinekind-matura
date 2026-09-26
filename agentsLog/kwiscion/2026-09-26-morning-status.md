# Morning status — 26 September 2026

## Final handoff — 11:10 Europe/Warsaw

The resumed window has ended and the lead heartbeat is paused. No new inference or training was started at this final checkpoint. Agents are interrupted, no project inference/download process is running, and no reset credit was consumed.

- **Ready:** local inference/RAG/evaluation tooling, adjudication correction, reproducible 107-source retrieval index, 24 strictly eligible provisional examples, installed HF CLI and verified project account `kwiscion`.
- **Actual model evidence:** unchanged: Qwen 3.5 4B, 4B+RAG and 9B each scored a provisional 1/5 on five text questions. No full-exam score, competitive model, or fine-tuned weights exist.
- **Interrupted work:** the 1024-token follow-up has a zero-byte raw-output file and no saved results. Gemma is absent from `ollama list`; the last complete progress record is 1,956,968,848 of 7,381,382,048 model bytes, with projector pending. Its pull process is stopped. Preserve partial files; do not infer a successful installation.
- **Training/HF:** the canonical-source alias split defect remains unresolved. The interrupted packaging worker left only a draft builder, no reviewed bundle. Do not upload or use the current internal holdout for model selection. No HF data publication occurred.
- **Spark update:** the team's independent audit supersedes the earlier blocked/20-success claims. Preserved Qwen3-8B synthetic outputs have 20/20 nonempty CPU answers but only 4/20 nonempty Spark answers; 16 are empty. Completion and Spark served-file provenance remain unverified. PRs #26/#28/#29/#31 provide runner and audit corrections; this is not an exam score or a valid successful-answer speed comparison. Issue #5 is closed; #3/#4/#11 remain open.

Next session: finish the source-alias split repair before HF publication; complete Gemma installation and a predeclared adequate-output diagnostic; assess vision inputs and broader validation before selecting training. The 2025 test stays sealed until a candidate is frozen. Confirm competition subject and the Saturday-noon roster separately.

The earlier checkpoint below is historical and is superseded by this handoff.

Checkpoint: 09:44 Europe/Warsaw. The owner resumed work after the Windows restart through10:47; new model calls stop10:30 and handoffs are due10:40. About1% of the Codex weekly allowance remains, resetting around10:45. No reset credit has been used. Keep the existing heartbeat; do not duplicate workers.

| Area | Verified state | Remaining work |
| --- | --- | --- |
| Models | Qwen3.5 4B, 4B+RAG, and9B each provisionally scored1/5 on the same five text questions; completion5/5,4/5,3/5 with512outputtokens | Investigate truncation using a separately bounded whole-arm1024-token run; Gemma4 12B downloading, completion uncertain |
| Core | Runner, RAG preparation, output adapter, adjudication fix merged;51tests pass | No new infrastructure needed before model evidence |
| Retrieval |107 licensed sources,3481chunks; rebuilt frozen index hash matches original | No measured accuracy benefit on tiny diagnostic; optional context selector not promoted |
| Evaluation |2024 isolated40-item/60-point evaluator; selected5keys visually verified; public aggregate reports, private raw answers | Full key byte hash differs from prior build; do not claim full reproduction.29/40items require images.2025 remains sealed |
| Training data | PR18 merged: strict24 eligible records; legacy drafts excluded, fail-closed export | Follow-up found canonical source_id shared across differently named train/holdout groups. Sol repairing partition before HF release; do not treat current22/2split as independent at article level |
| Spark | ljaniec claimed#5 and is preparing10:00harness/recipe PR | GPU authentication blocked all real inference/training; no fine-tuned model exists |
| Hugging Face | PR24 merged; uv and huggingface-hub2.0.0 installed; project-scoped whoami verifieskwiscion | Strict candidate release is deferred until split/rights review; dataset still empty |

These five-item diagnostics are provisional, not full-exam scores or evidence that a model is competitive. RAG did not improve the aggregate. No fine-tuned model or specialist is promoted. The current priority is a stronger baseline with complete answers, then vision coverage and only evidence-backed training.

A larger-output local diagnostic was initially blocked by automatic approval review interpreting512 as a global cap. The lead checked docs/inference.md, which permits configurable output budgets up to4096; Luna has one evidence-backed retry, then must stop that step if rejected again. Earlier results remain unchanged.

Active work: local_probe_luna owns all laptop inference; harness_sol owns the source-alias split correction; ljaniec owns the independent Spark harness PR. Gemma pull tool session87369, watchdog26823, stops10:10. Preserve partial download if it cannot finish. No other-project credentials, paid calls, or reset credits were used. The user requested continuing on the laptop; Blackwell access is not assumed.

Logistics still need confirmation: final competition subject (history remains the working assumption), team roster before Saturday noon. Final freeze: Sunday27September11:00 Europe/Warsaw.
