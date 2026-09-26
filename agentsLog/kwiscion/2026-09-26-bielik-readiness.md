# Bielik/Gemma text readiness

Two synthetic text requests completed successfully through the existing OpenAI-compatible runner. Both returned a nonempty final answer with `finish_reason=stop`, valid usage and the expected loaded digest/context. These are transport checks, not historical-quality evidence.

| Model | Exact final answer | Prompt/output tokens | Request seconds, including loading |
| --- | --- | --- | --- |
| Bielik 11B v3 Q5_K_M | `Ready.` | 18/3 |31.895|
| Gemma 4 12B Q4_K_M | `ready.` |21/3|88.488|

Each call requested at most256 output tokens; two calls/512 requested total, no retries. Effective context was32,768. Sampling temperature was omitted; Gemma thinking was disabled. No exam item or key was used in readiness.

## Pins and template correction

The official [Bielik GGUF](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-GGUF/tree/518fbbc2e677bf490776e4a98a300a822faca1a2) is Apache2.0, text-only,7,907,041,920 bytes. The downloaded file matched SHA256 `1a6baba952f0ebb12fa64f55feeb98271dc906954aad4cff6be234d90efccbc4`; it is below the8,000,000,000-byte model limit. The imported saved manifest is `771843b8f249eae2f2faad7d0f0aabe33e22b00c90332976f9eba1608ca1d28a`.

The embedded GGUF ChatML template explicitly begins with `<s>`, while `tokenizer.ggml.add_bos_token=false`. Ollama's automatic import selected a ChatML template that omitted that BOS. Before generation, an explicit faithful template restored `<s>`, with `<|im_start|>` / `<|im_end|>` role boundaries and stops. The pinned runtime's [documented-in-source render-only API](https://github.com/ollama/ollama/blob/v0.34.4/api/types.go) returned the exact expected synthetic prompt; it generated no completion. The older Llama-header example was not used.

Gemma model+projector totals7,556,497,632 bytes; saved manifest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`. Runtime0.34.4 executable SHA256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`. Runner SHA256 `d307356518aa8b35534525ceff39b9f3478366204ef5c3c81dd1299b3aacd782`.

The private local backup was verified against remote archive SHA256 `8268b9367a9d3bb3a6c8c16ca7546801a643102fef66142280b28610e8e34454` and raw SHA256 `de33c6752254065e4ad1bc839a4b9f026cadd02566d49320b7a64cf5d8c80d77`. It retains original requests/responses, runtime snapshots, template/render proof and reservations. No image capability or offline network-isolation qualification is claimed for Bielik.

The separately declared nine-item paired comparison follows only after independent controller review; it is a known-validation text slice, not a full exam or model promotion.
