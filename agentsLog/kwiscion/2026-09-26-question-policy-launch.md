# Question-policy experiment: launch decision

Lead decision at 16:08 Europe/Warsaw, 26 September 2026. Execute the independently reviewed `run_question_policy.py` once on the laptop. The matching model is installed but unloaded; the first real request loads it naturally, and its answer is preserved before checking the resident full digest and context4096. No extra warmup call.

Input SHA256: `3257dd89909ec1aeea1f85180244e962cc647e4f2b9d37cb24b1907cabfabb92`. Config SHA256: `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`. Policy SHA256: `6a5827f450b15a0709093f3d2fd7fc2827e3cf8399befde0bfdb3b0cee768122`. Full model digest: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.

One generic policy is prepended to all40 source-v2 cases. No historical facts, answers, examples or evaluator annotations are supplied. Original source text and images are preserved. Same Gemma, thinking off,1024 output tokens,420-second timeout, original unspecified sampling defaults, no retrieval. Maximum40 sequential requests and40,960 requested output tokens; paid API budget$0. No retries, regeneration or continuation.

Four offline stop/gate tests, dry input preflight and independent Sol review passed. Exact multimodal token counting before launch is unavailable. This explicitly replaces the earlier prepared plan's exact-count requirement with estimated fit and runtime monitoring: stop after a returned prompt count above2816 or missing success usage; stop on reported context truncation/OOM, two consecutive infrastructure failures, competing inference,60minutes elapsed or17:10. After five attempts, stop if measured latency projects completion beyond17:10. Preserve all attempted results and unsent IDs regardless of correctness. These controls do not prove absence of undisclosed server truncation.

Compare against the original35/60 v1 baseline and the separately reviewed39+1 source-v2 composite. Attribute the image repair separately from policy. Independent full scoring is required before promotion; failures and unsent items remain on the40-item/60-point denominator. Neither80% nor a gain is claimed at launch.

Command from project root in WSL:

```sh
python3 -B agentsLog/kwiscion/run_question_policy.py --execute
```

Actual usage, script/config/input hashes, server version and parameters, runtime verification, stop reason and unsent IDs are recorded in the private `question-policy-20260926/raw.jsonl.run.json`. The lead will release exact answer-only outputs for scoring after completion. Qwen's unused source-correction request is canceled; the completed Gemma correction remains preserved.
