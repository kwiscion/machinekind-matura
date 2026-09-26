# Gemma4 readiness and download — 2026-09-26

- Authorized public model: `gemma4:12b-it-q4_K_M`; existing WSL Ollama is `0.30.7`. No HF login/cache used.
- Started at **09:25:14 Europe/Warsaw / 07:25:14 UTC**. Hard operational cutoff **10:10 Europe/Warsaw**; curl additionally has a 2700-second request limit.
- Active tool session **87369**, WSL wrapper PID **312306**, curl PID **312308**. Initial detached launcher did not start; only the foreground tool session is active.
- Ignored progress: `outputs/gemma4/pull.log`; status/exit code: `outputs/gemma4/pull-status.txt`. Download uses `/api/pull`, not inference. Do not load Gemma until the Qwen9B diagnostic releases the GPU.
- Expected manifest SHA256: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
- Model blob `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606`: **7,381,382,048 bytes**.
- BF16 projector blob `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842`: **175,115,584 bytes**.
- Combined inference weights: **7,556,497,632 bytes**, below decimal 8GB. Full layer download ~7.5565GB. Installation/digest verification pending.
- Official registry config requires Ollama **0.30.5**. Architecture `gemma4`, Q4_K_M, Apache-2.0. Saved size does not guarantee full GPU residency; CPU offload and runtime allocations must be measured during the later diagnostic.

## Thinking control for the later fair diagnostic

The official Gemma listing documents switchable thinking: enable with `<|think|>` in the system prompt, omit it to disable; Ollama handles the template. Current Ollama API docs document native `think:false` and OpenAI-compatible `reasoning_effort:"none"` for boolean-thinking models. After installation inspect `/api/show` metadata and the versioned renderer; metadata absence is not proof of unsupported thinking. Use the same disabled-thinking policy as the Qwen comparison only after confirming the installed path supports it. Record final-answer completeness, finish reason, latency and token cap; do not grade reasoning as the answer. No inference has been requested by this download task.

Sources: [official model](https://ollama.com/library/gemma4:12b-it-q4_K_M), [registry manifest](https://registry.ollama.ai/v2/library/gemma4/manifests/12b-it-q4_K_M), [thinking API](https://docs.ollama.com/capabilities/thinking), [OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).

## 09:40 milestone

- Model blob: 1,577,025,488 / 7,381,382,048 bytes (~21.4%); projector pending. Average throughput since start ~1.76MB/s, so completion before cutoff is uncertain unless throughput improves.
- Hard-cutoff watchdog tool session **26823** will terminate only curl PID312308 at **10:10 Warsaw** if it still matches this pull request. Primary pull session remains87369.
- Exact versioned [Ollama0.30.7 Gemma renderer](https://github.com/ollama/ollama/blob/v0.30.7/model/renderers/gemma4.go) verified: `hasThink := thinkValue != nil && thinkValue.Bool()`; only true inserts `<|think|>`. Native `think:false` is supported by this renderer. OpenAI-compatible `reasoning_effort:"none"` is the documented false mapping; native path removes ambiguity. No runtime inference verification yet.
