# Issue #5: Spark compact-model baseline

Branch: `issue-5-ljaniec-smoke-harness`. Started 2026-09-26 01:56 Europe/Warsaw (2026-09-25 23:56 UTC). Owner: @ljaniec.

## Current state

This is the independent API runner supplement to [PR #25](https://github.com/kwiscion/machinekind-matura/pull/25). Its merged [README](README.md) and baseline scripts are preserved. PR #25 reports Qwen3-8B CPU/Spark runs on 20 synthetic history prompts; these are synthetic load diagnostics, not the official May 2023 DEV exam or May 2024 VALIDATION. This session performed zero real inference calls. The lead's [latest instruction](https://github.com/kwiscion/machinekind-matura/issues/5#issuecomment-5844345822) says to stop Spark environment repair, preserve this runner/recipe, and avoid duplicate downloads or specialist training.

At 09:39 Warsaw, the user authorized the GitHub CLI as `ljaniec`; authenticated CLI writes now work. [Issue #5 is claimed](https://github.com/kwiscion/machinekind-matura/issues/5#issuecomment-5844334212) and marked `in-progress`, with ETA 10:00 for the reviewed code/handoff publication. Spark SSH still rejects authentication. The GitHub integration's earlier 403 responses are historical access evidence; the CLI now provides the working publication route.

The [overnight handoff](2026-09-26-overnight-handoff.md) records the 08:00 Warsaw cutoff, delivered local files, missing measurements, and access failures. No real inference or training ran.

At the 09:00 check, the lead's [morning status](../kwiscion/2026-09-26-morning-status.md) and AGENTS.md extended operational work through 10:47 Warsaw, model calls through 10:30, and handoffs through 10:40. This supersedes the earlier operational cutoffs; source/split boundaries and the 60-minute Spark environment cap still apply. The lead keeps Spark unpromoted. SSH and GitHub writes remain blocked, so no new run began; the prepared report is still awaiting publication.

This is an initial reproducible vertical slice, **not a completed model benchmark**. The repo was cloned and the standalone `scripts/ljaniec/run_local_smoke.py` runner was added. It validates every served GGUF weight/projector file by local SHA-256 and size, optionally enforces exact equality with a pinned candidate in `model_candidates.json`, rejects a saved served weight total above 8,000,000,000 bytes, ingests `{id,prompt}` JSONL without answer keys, sends zero-temperature, fixed-seed chat requests to a localhost server, and saves append-only raw outputs plus a run manifest. The manifest records exact model revision/license/template/quantization provided by the operator, input/output hashes, latency, errors, sampled server CPU RSS, and total GPU memory use. GPU samples are device totals and may include other processes; sampling may miss brief peaks or the model-load peak.

At 03:02 Europe/Warsaw, the issue's 60-minute ARM/CUDA environment limit had elapsed without SSH authentication. In accordance with #5, Spark setup and training are stopped pending access; this report and the commands below are the CPU/repro/no-training fallback. Lead comment [5841674437](https://github.com/kwiscion/machinekind-matura/issues/5#issuecomment-5841674437) requested a claim and the first slice or concrete blocker. A claim with ETA and blocker was attempted at 03:01, but the GitHub integration still returned HTTP 403. Local branch work exists, but no remote claim or label transition should be inferred.

The script passed Python compilation, a manifest-only fixture check, a pinned-file match/mismatch check, and localhost mock chat-completions round trips for text and image requests. Text-only image skipping and image sending both produced raw JSONL accepted by `python3 agentsLog/Pewciu6/harness/matura_harness.py validate outputs <raw.jsonl>`. These verify the harness plumbing only; they are not model measurements.

Independent Sol review identified a crash on malformed JSON response shapes and missing partial-run manifests. The fixes preserve the raw body, emit per-item errors, retain an initial manifest, and finalize actual output counts after interruption. Empty/truncated responses are errors; localhost requests disable proxies and refuse redirects. Four targeted tests pass with `python3 -m unittest discover -s scripts/ljaniec -p 'test_*.py' -v`, including a real temporary localhost redirect check. They use invented prompts and fake weight bytes only. Localhost binding requires execution outside this host's network sandbox.

Candidate metadata is in `scripts/ljaniec/model_candidates.json`. Hugging Face LFS pointers and model pages report 7,150,994,912 bytes for Google's Gemma 4 12B QAT Q4_0 plus projector and 6,602,227,488 bytes for Unsloth's Qwen 3.5 9B Q4_K_M plus projector. These counts and SHA-256 values are **source-reported, not verified against downloaded files**. Both are below the cap on metadata alone. The [Google candidate](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf/tree/main), [Qwen quantization](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main), and [Qwen base](https://huggingface.co/Qwen/Qwen3.5-9B) report Apache-2.0. Runtime compatibility and multimodal quality are untested.

## Blockers and honest limits

- `ssh -o BatchMode=yes ljaniec@dell-gb10 ...` reached the Spark address but returned `Permission denied (publickey,password)`. No GPU load, runtime, latency, memory, or DEV result can be claimed yet.
- During the overnight window, the GitHub integration returned HTTP 403 `Resource not accessible by integration` for comment/label writes; the browser was signed out and `gh` unauthenticated. At 09:39, CLI authentication recovered and the issue claim/label transition succeeded. Code and full handoff publication are being completed through that route.
- No official answer keys, May 2024 validation keys, or May 2025 sealed material were pulled into this checkout. No training or DEV inference has run. Source and split rules in `SOURCE.md` remain in force.
- After this first commit, I fetched the [official OKE Warsaw May 2023 Formula 2023 history paper](https://www.oke.waw.pl/wp-content/uploads/OKE_WARSZAWA/EM/EM_2023/Arkusze/Arkusze_2023/Historia/MHIP-R0-100-2305.pdf) to ignored `agentsLog/ljaniec/private/` for DEV preparation only. Acquired PDF SHA-256: `2961b4ed5403663041fc030b1378aa7a9e61a03070914bb8da89775038d36b03`. The source is publicly accessible, but redistribution rights are not established; no exam text or image is committed. No model has consumed it yet.
- A private, text-only 11-item DEV smoke input now exists at `agentsLog/ljaniec/private/dev-2023-text-smoke.jsonl` (SHA-256 `e5c36d25e4235a6d2361da842f5bea036f708d899e6b24f62f25164f50949bac`). It was manually selected from the official PDF's extracted text. It omits images and is for load/failure diagnostics, not a complete or fair exam score; item 5.1 depends on a caption where the original also shows an image. The input has no answer keys and remains Git-ignored. No inference has run.
- No purchases or paid API calls were made.

## No-training fallback for the lead's Blackwell machine

Pin and download **one** candidate and its matching projector using the immutable revisions in `model_candidates.json`; do not download several quantizations for one served model. Example for the Qwen candidate, assuming the official Hugging Face CLI is already available:

```bash
hf download unsloth/Qwen3.5-9B-GGUF Qwen3.5-9B-Q4_K_M.gguf mmproj-BF16.gguf --revision 3885219b6810b007914f3a7950a8d1b469d598a5 --local-dir ./models/qwen35
sha256sum ./models/qwen35/*.gguf
stat -c '%n %s' ./models/qwen35/*.gguf
```

Compare the actual hashes and total bytes to the pinned manifest before loading. Record the exact `llama.cpp` commit and inspect GGUF tokenizer/chat-template metadata in the server log. Build `llama-server` from a pinned `llama.cpp` revision with the relevant CUDA backend; [upstream server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) describes its local OpenAI-compatible chat API. Start it bound to localhost with the matching model and projector, for example:

```bash
./build/bin/llama-server -m ./models/qwen35/Qwen3.5-9B-Q4_K_M.gguf --mmproj ./models/qwen35/mmproj-BF16.gguf --host 127.0.0.1 --port 8080 -c 4096 -ngl 99
```

Use `run_local_smoke.py --help` for required run metadata, and `--candidate-name Qwen3.5-9B-Q4_K_M-GGUF` to require exact local file hashes and revision against the pinned catalog. Give it a private May 2023 DEV input JSONL containing only IDs and prompts, with no answer keys; keep question texts and raw outputs in ignored/private storage if publication rights are unclear. The script rejects existing output paths to preserve each run. Run 10–20 fixed DEV items and report per-item failures, denominator, latency, peak memory, hashes, exact server command, and tokenizer/template. The source-reported bytes alone are insufficient to call either candidate a working final model. If multimodal loading fails, document that failure and continue with text-only diagnostics; do not silently claim image support.

The `llama.cpp` [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) documents localhost serving and `/v1/chat/completions`; projector support must be checked against the chosen pinned build. A no-training system can pair the verified offline model with permitted local historical reference retrieval, keeping held-out exam content out of the index. The lead owns final integration, model promotion, and sealed testing.

## Evaluator handoff for issue #11

The merged evaluator under `agentsLog/Pewciu6/` expects `id`, `backend`, `model`, `model_revision`, `raw_response`, `usage`, `latency_s`, and `error`. The smoke runner writes those fields; its mock output passed `matura_harness.py validate outputs`. It accepts `--split VALIDATION` for selection-only inference and never reads answer keys. Its default `--image-mode text-only` emits a clear error for each image item and reports `image_items_skipped`, so text-only and vision results cannot be conflated. `--image-mode send` embeds local PNG/JPEG/WebP files from paths beneath the input JSONL directory in requests to the localhost multimodal server. No image-capable runtime has yet been tested.

For issue #11, the runner input and resulting raw output must stay in ignored private storage, as the responses may quote exam content. Share a private artifact path with @Pewciu6 once the model run exists; publish only aggregates after the independent audit. The 2024 VALIDATION material is never training or retrieval material, and the 2025 SEALED_TEST remains unopened.

## Next actions

1. Publish this independently reviewed additive supplement and handoff through the authenticated GitHub CLI; link it in #5 and #11. Issue #5 was closed after the parallel PR #25 delivery; this supplement does not reopen it or promote a model.
2. The lead may use this runner with already available verified weights for official DEV/VALIDATION diagnostics, preserving raw private outputs and exact denominators. Do not duplicate its model downloads or restart Spark environment repair.
3. Keep synthetic PR #25 smoke evidence, this session's mock checks, and future exam outputs separate. No specialist training is planned; new model calls stop 10:30 and handoffs are due 10:40 Warsaw under the extension.

The standing 15-minute issue monitor is active in the Codex task; it will continue checking new assignments while this work proceeds. Pass the issue, AGENTS.md, SOURCE.md, contracts, no-purchases rule, and this log to each new subagent/Orka/Claude Code session.
