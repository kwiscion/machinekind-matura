# Heterogeneous source observer — CPU preparation, 26 September 2026

Recommendation: one **Qwen3.5 9B observer → pinned Gemma4 12B solver** diagnostic, with a fresh Gemma direct control. This changes the observer family, shortens its requested output structure and raises its cap from768 to1024. It is a named mechanism bundle, not an isolated estimate of model-family effect. The preceding same-model #110 run provided no measured gain and half its observations hit the cap. Qwen's weaker whole-exam score does not establish whether it supplies complementary observations.

**Status: CPU preparation only, not a launch.** No downloads, generation, GPU operations or remote server changes were made. No evaluator keys were read. The controller requires reviewed transport/host-guard wiring before root declares execution. [CPU claim on #110](https://github.com/kwiscion/machinekind-matura/issues/110#issuecomment-5848351625). Piotrek retains crops/multiscale or his independently claimed model experiment.

## Actual native Qwen artifact

The [Ollama publisher page](https://ollama.com/library/qwen3.5:9b) lists vision capability, Q4_K_M and Apache-2.0. The [Qwen publisher card](https://huggingface.co/Qwen/Qwen3.5-9B) documents the multimodal model. Anonymous retrieval of the [native registry manifest](https://registry.ollama.ai/v2/library/qwen3.5/manifests/9b) on26September verified:

| Component | Bytes | SHA-256 |
| --- | ---: | --- |
| Native manifest | — | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| Combined native model/vision weight layer | **6,594,462,816** | `dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c` |
| Config |475|`be595b49fe22012bd1f5605ec14c7ffa58331783a88a4fd8c22e5fc8ec42cf9f`|
| License |11,355|`7339fa418c9ad3e8e12e74ad0fd26a9cc4be8703f9c110728a992b193be85cb2`|
| Parameters |65|`9371364b27a52acac9d87f88bd93c9db1174d8d6ec57f6888925cdc1788871ff`|

There is **no separate projector layer** in this native artifact. All declared blob bytes total6,594,474,711, comfortably below8,000,000,000. This is metadata verification, not a fresh disk hash audit. The manifest matches the prior native Qwen validation's `6488c96fa5fa` identity. Do not add a foreign projector or mix pins with the different Unsloth split GGUF recipe (5,680,522,464 model +921,705,024 projector =6,602,227,488 bytes).

Gemma remains native `gemma4:12b-it-q4_K_M`, manifest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; its model/projector total7,556,497,632 bytes and individual pins are in the manifest template. Each model separately satisfies the cap; repository rules explicitly permit several individually eligible models.

## Six-case panel and exact budget

Retain the prior source-observation panel to avoid selecting cases after seeing heterogeneous outputs. The key-free source-v2 input was inspected only to confirm structure and complete image attachment lists. This is selected known-validation development, not an unseen test.

| ID suffix | Structural role, without answer hints | Original image count |
| --- | --- | ---: |
| z1 | Text plus alternative relief images; decision with cross-source justification |1|
| z2 | Text plus political map; cross-source consistency decision |1|
| z4 | Single building photograph; visual evidence argument |1|
| z5.1 | Text plus route map; cross-source relationship decision |1|
| z14.1 | Text plus military map; cross-source consistency decision |2|
| z15.2 | Multiple written source variants; text-only comparison control |0|

For each case, sequentially generate fresh Gemma bare1024, Qwen observation1024, Gemma final1024: **18 calls /18,432 requested output tokens**, zero retries, maximum45minutes,420seconds/request, stop dispatch unless425seconds remain. Both models use thinking off (`reasoning_effort=none`), temperature and other sampling overrides omitted, context32768 verified. Omitted sampling does not make defaults identical between models: native Qwen parameters differ, so record them as part of the bundle.

All original normalized text/image parts remain byte-identical and in order. Observer and successful final only append original generic instructions; final also receives the observation as an escaped JSON string labeled as unreliable evidence. No cropping, OCR replacement, source shortening, header removal, selected answer or source-specific clue is introduced. Observer requests at most180 words, three observations/source, explicit uncertainty and at most two relations; this is a soft concision instruction, not enforced structured-output parsing or a correctness check.

If observer output is empty or length-capped, **only after** the existing conservative classifier plus valid usage/context/runtime checks classify it as case-local, its answer is blank/error and final receives the unchanged original input in its already reserved slot. Partial observation text never propagates. This fallback is another unseeded Gemma draw and cannot count as evidence that observations helped. Transport, parser, provider, tool/refusal, unknown finish, context truncation, invalid usage, pin or ownership failures stop the wave. Errors/unsent slots stay explicit. Bare/final case-local failures stay blank; they do not create another call.

## Deliverables and integration boundary

- `hetero-source-controller.py`: executable controller API with injected backend/guard/durable writer; reuses `run_source_observation.validate` and source-preserving augmentation. Two-model snapshot verifier allows zero/one/two pinned residents before a call, requires the requested model after it, rejects unknown models, duplicates and context drift.
- `hetero-source-test.py`: ten original synthetic tests covering full text/multiple-image retention,18 reservations and exact caps, stage-model switching, empty/length fallback, HTTP/parser/provider/tool/truncation stops, invalid usage, pin failure, deadline, duplicate IDs and two-model context checks.
- `hetero-source-prepare.py`: metadata-only preparation CLI; rejects duplicate/missing panel IDs, hashes original prompts/images and controller dependencies without copying exam content into public files.
- `hetero-source-manifest-template.json`: pins, exact prompt text, source hashes, caps and explicit unresolved launch fields. **It is intentionally not a launch manifest.**

CPU verification: `python agentsLog/kwiscion/hetero-source-test.py` →10 tests pass; `python agentsLog/kwiscion/hetero-source-prepare.py` → template generated. Tests use the real `infer.response_error`, adapter extraction and reviewed `run_gemma_package.case_local_generation_error`, with synthetic responses and no network.

The launch wrapper must inject `infer.run_case` with captured requests, the reviewed classifier, a durable fsync reservation/raw writer, and the existing root host lock/GPU-process/file/runtime/deadline guard. Hash the controller **and imported dependencies**. Compare the actual outgoing model/cap/thinking/temperature/content against each reserved request. Use `check_runtime` for both tag pins and permissible resident models; the old single-resident assertion must not be reused unchanged. The pure controller cannot prove host ownership or file integrity without that wiring and must not be described as a ready standalone inference CLI. Root can adapt its already proven #110 transport rather than invent a second server.

## Installation/runtime feasibility

Native Ollama0.34.4 is the preferred path: the existing endpoint supports model selection per request, so no server-default change is intrinsically required. A later authorized install can use the owned runtime/store to pull `qwen3.5:9b`, then require the exact native manifest and **every** local blob size/hash above before execution. Never infer installed identity from the mutable tag alone. Do not download now or add a speculative second runtime.

H100 capacity appears plausible for both compact models, but simultaneous residency, available memory, installed Qwen support, first-load latency and image behavior on this actual host are **unverified**. Default single-model residency can unload/reload automatically; the controller accepts that and the real wall clock includes switching cost. It does not alter `OLLAMA_MAX_LOADED_MODELS`, context, templates or sampling defaults. If new text/image readiness is required, declare its at-most-two calls separately inside the parent lab envelope; they are not hidden inside18. Stop and report if installation, image support or fixed context fails.

Root must independently review the controller and wrapper, fill runtime executable/file pins, actual deadline, owned host/rate and archive paths, verify no competing worker, and declare the wave. Afterward publish exact answer-only handoffs and independent changed-slice grades; separate successful observation paths from fallbacks and compare with the new direct controls. No promotion or full60-point claim follows from preparation or a six-case result.
