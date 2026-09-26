# Source v2 correction calls — blocked preflight

2026-09-26T15:34:22.690465+02:00

No correction calls were started (0/2 calls, 0/2048 requested output tokens, $0). Mandatory WSL concurrency check found active PID 794, a `python3 infer.py` Gemma format arm with `--max-calls 40`, writing `gemma4-12b-val40-format-raw.jsonl`. No process was stopped or changed. Calls remain blocked until the lead reconciles this worker; no substitute experiment or retry was attempted.

Affected-only input hash and page-16 hash agree with the frozen plan and local bootstrap/repair manifests. Both planned correction output paths are absent. Configs were read without modification. No prompts, keys, scores, or candidate decisions were inspected or changed. Runtime/context was not queried because the concurrency gate failed.

## Preflight SHA-256

| File | SHA-256 |
| --- | --- |
| `infer.py` | `b702857347fd0fa99b9aba9a844afca1a4a8634b22eaa826199d27986dca1f0a` |
| `agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.jsonl` | `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7` |
| `agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2.jsonl` | `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4` |
| `agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2-affected.jsonl` | `85bce5d99ed077d873ee6b5ca9b8d60bfd232002c5c0a44e19be518c4adbe66e` |
| `agentsLog/kwiscion/private/validation_2024_keyfree/pages/page-16.png` | `9bda8c79c19a1433b11fda0cb32d615258954c3b1632255ac58178f240a4d23e` |
| `outputs/local-smoke/gemma4-12b-val40-1024.config.json` | `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa` |
| `outputs/local-smoke/qwen35-9b-val40-1024.config.json` | `6e670e24ef960d2b94510d0380ea0ed7f0b017c9bfa372a50d46417208a9fb61` |


## Resumed Gemma correction and second concurrency block

Fresh worker check was clear before dispatch. One Gemma call ran 2026-09-26T15:37:36.790172+02:00 to 2026-09-26T15:38:01.700301+02:00; normal stop, no error, 24.702 seconds, 539 prompt / 136 completion tokens. Budget used: 1/2 calls, 1024/2048 requested output tokens, $0. No retry. Original config unchanged.

Served model: `gemma4:12b-it-q4_K_M`; installed digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; Ollama 0.30.7. Before/after status reports context length 4096, resident size 8,908,324,205 bytes and VRAM 5,925,356,174 bytes. These resident-size counters are not saved-model artifact sizes. Context stayed unchanged across this call; no independent comparison against the v1 runtime is claimed here.

The next worker check found unexpected PID 29130 running the Gemma format-rest input/output arm. Qwen was not dispatched, and that process was not touched. Possible overlap makes latency comparisons uncertain. Lead notified immediately.

Raw answer and full local status metadata remain private under `agentsLog/kwiscion/private/source-corrections-20260926/`. No answer release or scoring occurred. V1 artifacts preserved.

| Artifact | SHA-256 / revision |
| --- | --- |
| input_sha256 | `85bce5d99ed077d873ee6b5ca9b8d60bfd232002c5c0a44e19be518c4adbe66e` |
| config_sha256 | `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa` |
| script_sha256 | `b702857347fd0fa99b9aba9a844afca1a4a8634b22eaa826199d27986dca1f0a` |
| git_revision | `bb388b861ea727f6b02b7fdd37834a27d4501692` |
| output_sha256 | `8e3d6e64869e9c149afacf86e8ac2979420d1c020cc2fe47bb6b4bab28f4d0a9` |
