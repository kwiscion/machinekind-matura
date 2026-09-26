# Gemma question-policy arm — prepared, not launched

26 September 2026. This preparation does not authorize inference. The lead must resolve competing laptop-worker ownership and explicitly approve launch. The recommendation's 16:10 launch and 17:10 completion gates remain binding unless the lead explicitly redeclares them before a call.

## Prepared artifacts

- Builder: `agentsLog/kwiscion/prepare_question_policy.py`.
- Final input: `agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2-question-policy-frozen.jsonl`.
- Manifest: the final input name plus `.manifest.json`; contains policy, source/config/builder/image hashes and execution limits.
- Prepared input SHA-256: `3257dd89909ec1aeea1f85180244e962cc647e4f2b9d37cb24b1907cabfabb92`.
- Exact generic policy SHA-256: `6a5827f450b15a0709093f3d2fd7fc2827e3cf8399befde0bfdb3b0cee768122`.
- Original config SHA-256: `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`.

The builder requires pinned v2, pinned original config, the exact policy in the recommendation and every image's bootstrap-manifest hash. It adds only policy plus two newlines to the original prompt. All 40 IDs, original prompt suffixes and image lists remain exact; output is a fresh private sibling so relative images retain meaning. Earlier `runner_input.v2-question-policy.jsonl` is preserved as preparation evidence; the `-frozen` file records the final builder hash.

Reproduce to fresh sibling names only:

```powershell
python -B agentsLog/kwiscion/prepare_question_policy.py --output agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2-question-policy-frozen.jsonl
```

Independent offline assertions passed: exactly 40 policy-only changes; 30 image cases serialize through existing `infer.load_cases`; overwrite and public-output refusal. No model requests were made.

## Launch gate still unresolved

Exact rendered multimodal context fit is **unproven**. Available metadata records baseline effective context 4096 and historic token usage; neither supplies exact revised chat-template/image-token counts. No project tokenizer/counting artifact was located in the bounded local inventory. No inference, tokenizer download, or character-based fit claim was used. The required limit is 2816 input tokens including template/images, leaving 1024 output tokens and 256 reserve. All 40 must pass an exact runtime-compatible count before launch; otherwise this plan stays blocked. Never shorten sources silently.

Original sampling defaults were not fixed: the unchanged runner sends no temperature or seed. Record available server defaults before launch, without changing them. Record effective context 4096 and the pinned model digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; mismatch blocks launch.

## Execution plan for separate approval

Use the unchanged `outputs/local-smoke/gemma4-12b-val40-1024.config.json`: thinking off, output 1024, timeout 420 seconds. No retrieval, extra hints, temperature/seed change or retries. Maximum 40 sequential attempts and 40,960 requested output tokens; $0 paid API. Preserve every original artifact and failure on the fixed 40-item/60-point denominator.

Before each request, the approved dispatcher must check exclusive worker ownership, elapsed time and infrastructure state. Dispatch in the frozen input order using existing `infer.run_case`; append/flush each raw result to one fresh private JSONL. After five recorded responses, project finish from elapsed time per attempt; stop new requests if projection exceeds 17:10. Also stop after two consecutive infrastructure failures, OOM, detected context truncation or 60 elapsed minutes. An already active request may finish within its original 420-second timeout. Do not retry, resume this arm, change settings or stop based on correctness. Record unsent IDs and stop reason. Provider/HTTP/transport errors count as infrastructure failures; ordinary answer incompleteness is retained and flagged without regeneration.

This is an execution **plan**, not an implemented timed dispatcher. A bare `infer.py --max-calls 40` does not implement the required intermediate stopping checks and must not be used as a substitute. Root must approve and supply the bounded dispatcher after the context and ownership gates are resolved.

Comparison anchor is the preserved v1 answers plus the completed one-item Gemma source-v2 correction, explicitly labeled reused-results input-repaired composite. Do not attribute its source repair to policy. Grade all item deltas independently, flag essay body word count under the applicable criterion, and retain baseline if improvement or adjudication is unresolved. No scoring or candidate freeze was performed here.


## Revised lead gate and executable dispatcher

The lead subsequently replaced the exact-tokenizer prerequisite with explicitly **estimated** context fit and a per-response prompt-token ceiling of 2816. No exact multimodal fit is claimed. `agentsLog/kwiscion/run_question_policy.py` now implements the bounded dispatcher; this supersedes the earlier paragraph saying it was not implemented. Default invocation preflights only and makes no model/status requests. Launch still requires a separate lead signal.

After explicit approval, run in WSL Ubuntu from the repository root:

```sh
python3 -B agentsLog/kwiscion/run_question_policy.py --execute
```

It pins input/config, verifies images, requires resident full Gemma digest and context 4096, and records read-only Ollama version/show parameters. It checks competing Python inference workers before each request, keeps one fresh raw output, enforces the declared time/projection/infra/context stops, and records unsent IDs. Request-level timeout stays420 seconds; no retries. Sampling defaults remain unchanged/unfixed. Context truncation detection covers returned diagnostics; undiagnosed server-side truncation cannot be ruled out. No cooperative worker lock prevents another independent session starting in the interval between checks, so root ownership coordination remains required.

Offline validation: three focused stop-condition tests passed, covering deadline,60-minute cap, after-five projection, competing worker,2816 bound/missing usage,OOM/context signal,two consecutive infrastructure failures and ordinary incompleteness. Default preflight accepted all40 frozen cases without network/model calls. Qwen correction remains postponed.
