# Independent bounded Gemma dispatcher review

**PASS for the reviewed code; no blocking defects found. This is not launch authorization or validation of a future arm manifest.**

Reviewer: GPT-6 Sol. Time: 2026-09-26T16:47:32.001193+02:00.

- Eight supplied tests passed: four generic-dispatcher tests and four shared policy-dispatcher tests.
- Six additional synthetic checks passed: an alternate deadline, a mocked process scan, and four mocked executions.
- The declared 17:20 synthetic deadline permits 17:15 execution; the historical 17:10 constant does not govern the generic arm.
- Process scanning detects run_bounded_gemma.py, run_gemma_source_crops.py, infer.py and other run_gemma/run_qwen Python workers; it excludes its own PID.
- A mocked full run made exactly 40 unique calls, with no retries. Two consecutive infrastructure errors stopped after two calls; a returned prompt count over 2816 stopped after one; bad post-first context stopped after one.
- All mocked executions retained recorded responses, actual prompt/completion usage fields and the exact unsent-ID suffix. No status endpoint or model was contacted.
- Private input/output/manifest paths, exactly 40 ordered unique IDs, exact image-reference/hash coverage, fixed original config hash and fresh exclusive output/metadata creation are checked.
- Cold-load handling permits the pinned installed model to be initially absent from resident models, then requires the correct digest and context 4096 after the first preserved real answer.
- Bounds stay fixed at 40 calls, 40960 requested output tokens, 1024 output tokens per call, 420-second request timeout, at most 3600 elapsed seconds, and zero paid API budget.

## Scope and limits

No complete new arm manifest or launch existed for this review. Before launch, the lead must still approve the concrete frozen manifest and run its dry preflight. The manifest hash is recorded in run metadata; input/config/image bytes are rechecked against manifest/pinned values.

Worker detection is a Linux /proc snapshot of known Python script names, not an atomic reservation; a competing controller can still appear between checks. The deadline stops new dispatch; an in-flight call may complete within its original timeout. Actual context is verified after first load; exact multimodal pre-counting and absence of silent server truncation are not proven. These are the existing accepted operational limits.

Minor cosmetic issue only: the deadline stop text becomes "declared deadline deadline" after the string replacement. It does not affect stopping behavior.

No model/API/network calls, core edits, Git writes or GPU interference were performed. Synthetic temporary artifacts were confined to the owner-private directory and cleaned up.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| agentsLog/kwiscion/run_bounded_gemma.py | `34965ede0e7a5dee3b2d9d968e702df529d05dd2e30335860420ad3d42af7f47` |
| agentsLog/kwiscion/test_bounded_gemma.py | `e8415a1fa6501f44f5e387d359af5ef1888fab0c34187965637db5a8599ef72c` |
| agentsLog/kwiscion/run_question_policy.py | `39a6a27763c34934bb3083ac46992dc2f8f85ae15739c79ea1295330ccff33df` |
| agentsLog/kwiscion/test_question_policy_dispatch.py | `189583c02a174c51c77f009201ff059d7713088637098d16aa2f31e60db09331` |
| infer.py | `b702857347fd0fa99b9aba9a844afca1a4a8634b22eaa826199d27986dca1f0a` |
| outputs/local-smoke/gemma4-12b-val40-1024.config.json | `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa` |
