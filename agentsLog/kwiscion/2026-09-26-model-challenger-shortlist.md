# Compact Polish model challenger — 26 September 2026

Recommendation for #97: try **Bielik-11B-v3.0-Instruct Q5_K_M** first on the owned H100. It changes the model family and Polish specialization while using an official, ungated, Apache-2.0 quantization. Polish specialization is a hypothesis, not evidence of higher history-exam points. No held-out questions, answers or keys were read to select these candidates. This review made no generation calls or weight downloads.

## Verified shortlist

Anonymous Hugging Face API metadata and publisher cards were checked on 26 September 2026. Sizes below are exact LFS artifact bytes, using the strict decimal **8,000,000,000-byte** ceiling. All three are text-only causal language models: no image input or projector. Do not silently discard images to make an item eligible. Metadata establishes an available artifact, not a successful H100 load or downloaded-file integrity.

| Candidate / primary documentation | Architecture and configured context | Eligible quantized artifact | License / access |
| --- | --- | --- | --- |
| [SpeakLeash Bielik-11B-v3.0-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct), [official GGUF](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-GGUF) | Llama architecture, 11B; GGUF metadata context 32,768; Polish-focused multilingual instruction model, ChatML | `Bielik-11B-v3.0-Instruct.Q5_K_M.gguf`: **7,907,041,920** bytes; headroom 92,958,080 | Apache-2.0; official GGUF ungated. Original full-precision repository has automatic gating; do not request it. |
| [CYFRAGOVPL PLLuM-12B-instruct-2512](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-instruct-2512), [quant uploader](https://huggingface.co/mradermacher/PLLuM-12B-instruct-2512-GGUF) | `MistralForCausalLM`; config maximum 131,072; Polish instruction model | `PLLuM-12B-instruct-2512.Q4_K_M.gguf`: **7,477,205,184** bytes | Apache-2.0; both repositories ungated. Third-party conversion, not publisher-certified quantization. Q5_K_M is 8,727,632,064 bytes and fails the ceiling. |
| [CYFRAGOVPL Llama-PLLuM-8B-instruct-2512](https://huggingface.co/CYFRAGOVPL/Llama-PLLuM-8B-instruct-2512), [quant uploader](https://huggingface.co/Jerzman/Llama-PLLuM-8B-instruct-2512-Q4_K_M-GGUF) | `LlamaForCausalLM`; config maximum 131,072 with Llama3 RoPE scaling; Polish instruction model | `llama-pllum-8b-instruct-2512-q4_k_m.gguf`: **4,920,752,608** bytes | Llama 3.1 community license, not Apache; ungated. Preserve its license/attribution and applicable use conditions. Third-party conversion. |

Configured context is not a measured reliable long-context capability. Start at 8,192 tokens; explicitly reject overlength input rather than truncating sources. PLLuM cards describe Polish QA/extraction use and warn of possible hallucinations; those are task descriptions, not validation results. Bielik and Llama-PLLuM share a broad Llama architecture, but are different from the existing Gemma/Qwen families. PLLuM-12B offers a separate Mistral architecture fallback.

## Immutable artifact pins

| Repository | Revision | File SHA-256 |
| --- | --- | --- |
| `speakleash/Bielik-11B-v3.0-Instruct-GGUF` | `518fbbc2e677bf490776e4a98a300a822faca1a2` | Q5_K_M: `1a6baba952f0ebb12fa64f55feeb98271dc906954aad4cff6be234d90efccbc4` |
| `mradermacher/PLLuM-12B-instruct-2512-GGUF` | `2c84d04f11b84c6f250c30344667879c904cb9fe` | `489bdd48db2a3cf0a918decd7170a4c9ecc22fcf835507e6a605df20e0be9d65` |
| `Jerzman/Llama-PLLuM-8B-instruct-2512-Q4_K_M-GGUF` | `8ca2da0363d6970f35116e200aa16555758cf803` | `4d09b3095df1ea9a0aba932dd8a73f08d01a4ed5c4b0f77f4c2198ac0b9fcd25` |

Original publisher revisions: Bielik `735bfee1125fe8b497ac2769de94822a11f77167`; PLLuM-12B `2982a0b979c23af81a37cc47fa40007e2bd47e2a`; Llama-PLLuM-8B `35d90290f98abe7d2750796b5cd88096aa2219eb`. Third-party cards name their source repositories, but do not establish conversion from these exact source revisions; this provenance gap remains explicit. Source configs: [12B](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-instruct-2512/blob/2982a0b979c23af81a37cc47fa40007e2bd47e2a/config.json), [8B](https://huggingface.co/CYFRAGOVPL/Llama-PLLuM-8B-instruct-2512/blob/35d90290f98abe7d2750796b5cd88096aa2219eb/config.json). Exact sizes/hashes came from each repository's anonymous `/api/models/{repo}?blobs=true` metadata.

## First runnable path and smoke

Commands below are a proposed Linux path for Przemek's owned host, not execution evidence. They require its already approved CUDA llama.cpp build and Hugging Face CLI. Record `llama-server --version`, binary hash, CUDA/device identity and actual flags before calls; verify supported flags with that binary's help. The [primary server documentation](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) documents quantized CUDA serving, context limits and chat endpoints.

```bash
hf download speakleash/Bielik-11B-v3.0-Instruct-GGUF \
  Bielik-11B-v3.0-Instruct.Q5_K_M.gguf \
  --revision 518fbbc2e677bf490776e4a98a300a822faca1a2 \
  --local-dir models/bielik-v3-q5
sha256sum models/bielik-v3-q5/Bielik-11B-v3.0-Instruct.Q5_K_M.gguf
stat -c %s models/bielik-v3-q5/Bielik-11B-v3.0-Instruct.Q5_K_M.gguf
./build/bin/llama-server \
  -m models/bielik-v3-q5/Bielik-11B-v3.0-Instruct.Q5_K_M.gguf \
  -ngl 99 -c 8192 -n 1024 --host 127.0.0.1 --port 11437
```

Use the embedded template only after confirming the startup template matches the upstream ChatML format and stops at `<|im_end|>`. HF GGUF metadata exposes a ChatML template including BOS. The GGUF card also contains an older Ollama example using Llama-style header tokens, inconsistent with upstream ChatML; do not copy that example blindly. This makes template verification a concrete smoke requirement. Do not substitute this model into the Gemma-pinned launcher without adapting and reviewing its model/runtime pins.

Spend at most two readiness calls, counted inside #97's existing envelope: one original Polish instruction with an exact short output constraint; one original synthetic source paragraph asking for a decision plus source-grounded justification. Cap each at256 output tokens, disable network for inference, record exact prompt/template/output/usage/finish reason/latency, and require nonempty Polish output, clean stopping and no source truncation. These establish execution only. If the host already has suitable runtime qualification, do not repeat it unnecessarily.

Then freeze one 6–12-item text/factual slice selected by question/evidence structure, including correct controls, before viewing challenger outputs. Generate fresh paired Gemma/Bielik answers with identical question/source content and1024-token caps, explicitly recorded sampling, no RAG and no hidden retries. Grade the changed slice independently, retaining errors/unsent items in its denominator. Keep mixed/image-dependent questions outside this text-only route. Publish gains and regressions; do not extrapolate a slice result to a full60-point score. If Bielik yields no useful gain/diagnosis, test PLLuM-12B as the next family rather than tuning quantization repeatedly.

Outstanding: actual host/runtime support and throughput; full saved package size after license/config files are included; semantic template correctness; quantization fidelity; actual history accuracy and regression rate; whole-system offline integration. Q5 has ample room for ordinary small license/config files but the final package must still be measured. An eligible quantized artifact is not a promoted candidate.
