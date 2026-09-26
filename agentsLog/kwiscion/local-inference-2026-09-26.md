# Local inference smoke probe — 2026-09-26

## Scope

One bounded inference request against the existing WSL Ollama service; inspect a candidate small model; download it only if the transfer remained within the requested 15-minute window. No exam items, credentials, paid calls, benchmark suite, configuration changes, or training were used.

## Existing Gemma 2 tag

- Exact local tag: `gemma2:9b` (`ollama show gemma2:9b` succeeded).
- Ollama reports architecture `gemma2`, 9.2B parameters, Q4_0 quantization, and 8192-token native context. Installed size from `ollama list`: 5.4 GB.
- Submitted one neutral request to `/api/generate` with `num_ctx=512`, `num_predict=32`, and `keep_alive=0`, prompt `Odpowiedz tylko słowem: gotowe`.
- The shell/tool returned no captured response body or timing. A later `ollama ps` was empty, consistent with the requested unload, but does not prove the generated answer or GPU/CPU placement. The original API request was not repeated; a separate harness check is recorded below.

### Follow-up through the repository harness

- A separate, newly authorized request ran the one-case fixture through `infer.py` against `http://127.0.0.1:11434/v1/chat/completions`, with `max_output_tokens=64`, timeout 180 seconds, and exact model `gemma2:9b`.
- Result: `OK`; 16 prompt tokens, 2 completion tokens, latency 48.939 seconds, no error. Response model was `gemma2:9b`.
- Immediately after completion, `ollama ps` reported 7.1 GB allocation, context 4096, 20% CPU / 80% GPU. `/usr/lib/wsl/lib/nvidia-smi` reported RTX 2000 Ada Laptop GPU, 8188 MiB total, 1575 MiB free, 0% utilization at sampling time.
- Ignored artifacts: `outputs/local-smoke/gemma2.config.json` and `outputs/local-smoke/gemma2-smoke.jsonl`.

## Qwen 3.5 4B availability

- The official [Ollama Qwen 3.5 4B page](https://ollama.com/library/qwen3.5:4b) lists a 3.4 GB Q4_K_M artifact, 4.66B parameters, and vision capability. The page shows the Ollama API pattern at `/api/chat`.
- First pull attempt was cancelled near 949 MB of 3.4 GB because its ETA exceeded 22 minutes. After the updated 45-minute allowance, a second pull was started around 2026-09-26 00:47 UTC with output redirected to `outputs/local-smoke/qwen3.5-pull.log`. It completed successfully around 00:51 UTC; the log ends with `success`.
- Exact installed tag: `qwen3.5:4b`, model ID `2a654d98e6fb`, size 3.4 GB. The partial data from the first attempt were reused by Ollama.
- One neutral text request ran through the harness with `max_output_tokens=128` and a 180-second timeout. HTTP returned model `qwen3.5:4b`, `finish_reason=stop`, 17 prompt tokens, 100 completion tokens, and latency 18.847 seconds, but the `content` field was empty and text appeared only in `reasoning`. The harness correctly marked the case as an incomplete answer. These counters do not establish that the 128-token limit was exhausted. No identical retry was made.
- After the request, `ollama ps` reported Qwen 3.5 4B at 3.0 GB, context 4096, 100% GPU.
- A separate, authorized native API check queried `/api/show`; the model reported family `qwen35`, Q4_K_M and 4.7B, with no top-level `thinking` metadata. A single `/api/chat` request then used `think:false`, `stream:false`, `keep_alive:0`, `options.num_ctx=2048`, `options.num_predict=64`, and prompt `Odpowiedz jednym słowem: gotowe`.
- Native response: model `qwen3.5:4b`; content `gotowane`; empty thinking field; `done=true`, `done_reason=stop`; 23 prompt tokens, 3 generated tokens; total duration 7.610 s, load 7.460 s, eval 0.049 s, client wall time 7.713 s. `ollama ps` was empty after the call and NVIDIA reported 7678 MiB free, consistent with `keep_alive:0`.
- Current official Ollama [chat API docs](https://docs.ollama.com/api/chat) specify `think:false` as requesting no thinking output; the official [thinking guide](https://docs.ollama.com/capabilities/thinking) describes model metadata discovery and the meaning of false. The official [OpenAI compatibility docs](https://docs.ollama.com/api/openai-compatibility) list reasoning/thinking control on `/v1/chat/completions`; they say `reasoning_effort:"none"` requests false for boolean-thinking models.
- A second bounded request tested that OpenAI-compatible equivalent on the installed Ollama 0.30.7: `/v1/chat/completions`, `model=qwen3.5:4b`, `reasoning_effort="none"`, `max_tokens=64`, same neutral prompt. Response content was `Gotowy`; no reasoning field; `finish_reason=stop`; 23 prompt and 3 completion tokens; wall time 12.630 s. It produced a nonempty one-word final answer, though the inflection differed from the requested `gotowe`. The model remained 100% GPU at 3.0 GB, context 4096; NVIDIA reported 4729 MiB free after this request.
- No image probe was run. A synthetic red-square fixture was prepared under the ignored smoke folder but not sent.
- The pull output, config, fixture, and model response are under ignored `outputs/local-smoke/`. `nvidia-smi` was found at `/usr/lib/wsl/lib/nvidia-smi`; the Gemma post-call GPU sample is recorded above.

## Result

The Gemma harness smoke establishes a valid local OpenAI-compatible text inference path, with mixed CPU/GPU placement. Qwen 3.5 4B is installed; native `think:false` and OpenAI-compatible `reasoning_effort:"none"` both yielded nonempty one-word outputs, while the default harness call spent 100 completion tokens in the reasoning field and returned empty content. The two bounded outputs were close to, but not exact matches for, the requested Polish word. These are smoke checks only and say nothing about exam suitability; no vision request was made.
