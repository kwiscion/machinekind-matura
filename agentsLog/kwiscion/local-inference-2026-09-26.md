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
- First pull attempt was cancelled near 949 MB of 3.4 GB because its ETA exceeded 22 minutes. After the updated 45-minute allowance, a second pull was started around 2026-09-26 00:47 UTC with output redirected to `outputs/local-smoke/qwen3.5-pull.log`.
- Handoff state at 2026-09-26 00:50:53 UTC: session ID `45782`; WSL PIDs `131927` (bash wrapper) and `131936` (`ollama pull qwen3.5:4b`); log at `outputs/local-smoke/qwen3.5-pull.log`; last observed 60%, 2.0 GB/3.4 GB, 13 MB/s, ETA 1m37s. The requested 45-minute observation cutoff is 2026-09-26 01:32 UTC. Do not restart the pull while this process is active.
- The tag was absent from `ollama list` at 00:50:28 UTC; completion must be checked after this handoff. Whether Ollama retained partial blobs from the first attempt was not inspected.
- No Qwen inference, image probe, or Qwen GPU placement measurement has been completed. `nvidia-smi` was found at `/usr/lib/wsl/lib/nvidia-smi`; the Gemma post-call GPU sample is recorded above.

## Result

The Gemma harness smoke establishes that the local OpenAI-compatible text inference path works, with mixed CPU/GPU placement. This is only a smoke check and says nothing about exam suitability. Qwen 3.5 4B download and any vision check remain pending.
