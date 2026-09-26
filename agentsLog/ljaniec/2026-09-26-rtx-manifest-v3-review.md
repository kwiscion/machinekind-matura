# Independent RTX readiness review — issue #38

26 September 2026, 17:50 Europe/Warsaw. Reviewed merged #76 at `ec06de5`, manifest `agentsLog/semberecki/2026-09-26-rtx5090-gemma-prep.json`, SHA-256 `f16fcb16e4b0b415f67e64da26b17c413a14202821a352f9a5a70927e8387d10`. **Read-only metadata/source review, zero model calls, installs, weight downloads, SSH/GPU/namespace operations or paid spend.** Piotrek owns execution; ljaniec did not inspect or rehash his private machine files.

## What the delivered evidence supports

- Reported native `gemma4:12b-it-q4_K_M`, Ollama 0.34.4 on RTX 5090 Laptop; effective context 32768 and 100% GPU placement.
- Full native manifest/model/projector digests and model 7,381,382,048 + projector 175,115,584 = **7,556,497,632 saved weight bytes** match the retained recipe. This is consistency of reported metadata, not a new independent disk hash audit.
- Official archive SHA matches the release. Executable SHA is now recorded as `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`. Source archive and executable hashes are separate.
- Three completed synthetic smoke calls, explicit stop reasons and nonempty final responses reported; native `think:false`, num_predict1024, no per-call context override. Full generated 128×128 PNG hash is recorded. A fourth readiness call remains reserved; this review assigns no extra call.
- Reported9,184MiB llama-server memory is expressly one sample, not an attributed peak series. This does not establish full-package memory headroom.
- Local text/vision readiness is reported. Successful external-network-isolated inference and final-package completion are **not** established by these smoke calls.

## Timing audit: retain units and comparable workloads

These are completed **synthetic** calls with different prompt/output sizes, not the final exam or paired laptop tasks. Durations are rounded in the supplied JSON.

| Smoke | Prompt / generated tokens | Load s | Prefill s | Decode s | Total request s | Reported decode tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cold text |26 /14|29.32|23.08|5.28|57.7|2.7|
| Warm image |116 /17|0|2.99|0.25|3.3|67.7|
| Warm longer text |51 /233|0|0.07|4.32|4.5|54.0|

The third rate is consistent with233 / 4.32≈53.94 decode tok/s. Total-request rate is a different quantity; missing higher precision explains small rate/phase rounding differences. First-request57.7s includes29.32s load plus first-call prefill/warmup and decode: do not label57.7s as load duration.

Piotrek's Markdown claims roughly 8× faster per answer and a 40-call stage guarantee. Those compare a 233-token synthetic output with a 37.4s mean across different laptop exam tasks, token lengths, images, runtime/context and offload. **No paired speedup or full-exam deadline follows.** The lead explicitly forbids extrapolating synthetic 54 tok/s into complete-exam/stage timing. Preserve the synthetic timings; wait for actual completed runtime-transfer records and total elapsed time. No concurrency optimization is justified by this smoke comparison.

The field `driver: NVIDIA driver 13.2 (serve.log driver=13.2)` does not identify the installed NVIDIA driver release. Pinned [device display](https://github.com/ollama/ollama/blob/b2da9e468af2479058ae18c6d908ed29de410684/ml/device.go) uses major/minor CUDA API fields from [cuDriverGetVersion discovery](https://github.com/ollama/ollama/blob/b2da9e468af2479058ae18c6d908ed29de410684/discover/native_probe_linux.go), or [bundled-runtime filename fallback](https://github.com/ollama/ollama/blob/b2da9e468af2479058ae18c6d908ed29de410684/discover/llama_server.go) when native probing is unavailable. This field is CUDA API/runtime-version information, not a verified NVIDIA kernel-driver release. A normal `nvidia-smi --query-gpu=driver_version --format=csv,noheader` supplies that release without a model call or install. [Findings posted immediately to #33](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847605958).

## Current full-runtime measurement contract

[Author declaration5847581958](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847581958) supersedes readiness-only for **Piotrek's one runtime/context transfer control**:

- Exact key-free source-v2 input SHA `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`,40 items /60 points and all original images; no keys.
- Same native model/digests, Ollama 0.34.4, actual context 32768, thinkingnone,1024 output,420s request timeout; no RAG/policy/crops/sampling override.
- Maximum40 sequential calls /40,960 requested output tokens /$0, no retry/warmup. Stop dispatch after2400s or18:40 Warsaw; in-flight bounded by420s. Stop for required-asset/model/context/runtime/transport failure or truncation; preserve all failures/unsent IDs and60-point denominator.
- Full local hashes and served digest/context before launch; retain renderer/config/input/image hashes. Answer-only public handoff follows copied-source audit; raw provider/reasoning/source/keys remain private.

The measured comparison changes runtime/context relative to the laptop 4096 arm; do not call it identical configuration or infer accuracy gains. Report actual UTC start/end, attempted/completed/failed/unsent counts, finite completed per-item wall latency and token counts, load/prefill/decode separation, effective context and whole-arm elapsed time. Then derive the stage budget using the existing runbook without counting cold load twice. Final package item/task distribution and actual stage allowance remain unknown; even a completed40-item validation timing is not a guaranteed final deadline.

## Image controls and remaining proof

Independent source tracing establishes an environment-control path beyond flag presence:

1. Ollama's pinned [LLAMA_CPP_VERSION](https://github.com/ollama/ollama/blob/b2da9e468af2479058ae18c6d908ed29de410684/LLAMA_CPP_VERSION) is b11081, resolving to llama.cpp `161755f29e415e2c33efe906e91843c068efd664`. This is the release source pin; Piotrek has not independently delivered a backend executable/version hash.
2. Its [launcher](https://github.com/ollama/ollama/blob/b2da9e468af2479058ae18c6d908ed29de410684/llm/llama_server.go) copies the parent environment. The Gemma branch adds no image-token CLI override; the Qwen-specific override is a different path.
3. Pinned llama [argument parsing](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/common/arg.cpp) actually reads integer `LLAMA_ARG_IMAGE_MIN_TOKENS` / `LLAMA_ARG_IMAGE_MAX_TOKENS` handlers before CLI parsing. Explicit CLI values take precedence over environment values.
4. [Server context](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/tools/server/server-context.cpp) passes the values through [mtmd](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/tools/mtmd/mtmd.cpp) to clip parameters. [Clip initialization](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/tools/mtmd/clip.cpp) and its [limit helper](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/tools/mtmd/clip-model.h) substitute positive custom values.

Thus a future separately authorized task-owned startup can convey those environment controls in the pinned source lineage. This is **not evidence that Piotrek set a value, that his actual child consumed it, or that image inputs used a measured budget**. His direct backend-env capture remains pending. No environment/service/flag changed in this review; the current transfer keeps its declared settings.

The newer pinned Gemma4V/UV source default is **70–1120 image tokens**, whereas the [older laptop b9509 review](../kwiscion/2026-09-26-vision-resolution-readiness.md) records 40–280. These are source defaults/ceilings, not actual per-image token counts. A future 560 maximum is below this newer ceiling, so do not assume it doubles Piotrek's default or has the same effect as on the older laptop. Backend image preprocessing is an additional runtime-transfer difference to retain in provenance; full source images/bytes staying identical does not make tensors/visual-token demand identical across versions. The later 560-token pilot still needs a separate declaration, explicit context/accounting and measured behavior; it is not part of the current control.

Rendered complete-source delivery and counterfactual image sensitivity are not independently established by a token count plus one correct aggregate description. Preserve available request/input evidence rather than launching an unassigned repeat. The lead's isolated rehearsal remains a separate two-call declaration with both server and runner in the same namespace; localhost/`--offline` model assets alone are insufficient offline proof.

The 15-minute issue monitor and durable deduplication continue. Both Blackwells remain unavailable; no purchases, reset credits, new worker or Spark/CPU fallback. #38 stays open for actual transfer/rehearsal evidence.
