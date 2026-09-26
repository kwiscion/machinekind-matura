# Portable inference runner

`infer.py` is a standard-library Python 3.10+ runner for OpenAI-compatible `/chat/completions` endpoints. It accepts JSONL `{ "id", "prompt", "images"? }` and writes one JSONL result per case. Only `prompt` and optional local images enter the model request. Fields such as `answer`, `rubric`, `split`, and `source_ids` are ignored; keep evaluation keys in a separate restricted file as required by [CONTRACTS.md](overnight/CONTRACTS.md).

## Local run

The default example points to Ollama on `127.0.0.1:11434/v1` with the installed `gemma2:9b` tag. This text-only fallback passed one local smoke prompt through the harness; see the [local inference log](../agentsLog/kwiscion/local-inference-2026-09-26.md) for the measured run. The installed `qwen3.5:4b` has a separate [local config](../config.qwen.local.example.json) with `reasoning_effort: "none"`. Luna verified a nonempty final answer with thinking disabled through both Ollama's native API and its OpenAI-compatible chat endpoint; the OpenAI transport probe took 12.630 seconds and used 3.0 GB GPU memory. The probe answer differed from the requested word, so this verifies transport and final-answer output only, not answer accuracy. Neither smoke run is an exam result. The script installs or downloads nothing.

```powershell
python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/smoke.jsonl --dry-run
python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/smoke.jsonl
python -m unittest -v test_infer.py
```

In WSL use `python3`. The `127.0.0.1` address must be reachable from the process running Python.

An input with an image looks like this. Paths are relative to the JSONL file; PNG, JPEG, GIF, and WebP are recognized from file bytes and sent as data URLs. The selected model and server must actually support vision. Each image is limited to 20 MiB.

```json
{"id":"example-1","prompt":"Describe the figure.","images":["figures/example.png"]}
```

## Hosted development

Copy `config.hosted.example.json`, set the provider's real HTTPS base URL and exact model ID, and set the named API key environment variable in this process. Confirm provider API compatibility and image support separately. The `--allow-remote` flag is required for any non-loopback host, including in dry runs.

```powershell
$env:HOSTED_MODEL_API_KEY = "your-key"
python infer.py --config config.hosted.example.json --input fixtures/smoke.jsonl --output outputs/hosted.jsonl --allow-remote --dry-run
python infer.py --config config.hosted.example.json --input fixtures/smoke.jsonl --output outputs/hosted.jsonl --allow-remote
```

`api_key_env` names the variable; no key is stored in config or output. Do not reuse credentials from another project. Remote HTTP and redirects are refused.
`reasoning_effort` is optional (`none`, `low`, `medium`, or `high`) and is passed through only when set; endpoint support varies.

## Result and limits

Each result includes `id`, configured backend name/base URL/model and optional `model_revision`, model/ID/fingerprint returned by the endpoint when available, `raw_response`, `usage` when provided, `latency_seconds`, and `error`. `raw_response` holds the parsed JSON or the original text if JSON parsing fails. Provider error objects, missing or malformed choices, empty final answers, and output cut off by the length limit are errors; the raw response remains available for diagnosis. The configured `model_revision` is user supplied metadata, not a verified weight hash; if the server omits its revision, record exact served weights and template separately in the candidate manifest. Output can include private responses or provider error text, so do not commit it without rights and privacy review.

The script validates all cases before calling the model. `--max-calls` defaults to 20 and may be set from 1 to 100; `max_output_tokens` defaults to 512 and is capped at 4096. Cases are sent once, sequentially, without retries or tools. A failed case still gets an output line. The output path must be new: existing results are never overwritten. Exit code is 0 for all successes, 1 if a case failed, and 2 for invalid configuration, input, or output path.

## Retrieval and evaluator adapters

Use the same original input and model config for a base run and a retrieval-augmented run. `prepare_rag.py` reads Bukareszt's **local** index and graph; these files are ignored by Git and must already exist. Its default `chrono` mode retrieves five passages with bounded excerpts. It writes model input, a trace with the index SHA-256 and retrieved chunk IDs, and a passage corpus for Pewciu6's citation audit. Keep these generated files under `outputs/` and review rights before sharing them.

```powershell
python scripts/prepare_rag.py --input fixtures/smoke.jsonl --output outputs/rag-input.jsonl --trace outputs/rag-trace.jsonl --corpus outputs/rag-corpus.jsonl
python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/base-raw.jsonl
python infer.py --config config.local.example.json --input outputs/rag-input.jsonl --output outputs/rag-raw.jsonl
python scripts/normalize_outputs.py --input outputs/base-raw.jsonl --output outputs/base-model.jsonl
python scripts/normalize_outputs.py --input outputs/rag-raw.jsonl --trace outputs/rag-trace.jsonl --output outputs/rag-model.jsonl
python agentsLog/Pewciu6/harness/matura_harness.py validate outputs outputs/rag-model.jsonl
```

The adapter copies the final answer into the evaluator's `raw_response` string and retains the complete provider JSON in `provider_raw_response`. Retrieved passage IDs stay in `retrieval_evidence`; they are **not** credited as model citations. The model must emit `[[source_id#chunk_id]]` markers for citation auditing against `outputs/rag-corpus.jsonl`. Original keys and rubrics are never read by these adapters. Use restricted evaluator keys only in the separate scoring process. The retrieval owner's independent audit found full support in 16 of 40 top-ranked chunks, so multiple passages are offered but their support must still be checked. The evaluator can fully decide only 18 of 60 validation points automatically; report its grades as provisional and do not infer exam gains from retrieval diagnostics.
