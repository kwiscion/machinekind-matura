# Gemma 4 preparation on Spark — bounded load task

Owner: @ljaniec. Coordination: [issue #33 claim](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5845725912) and [duplicate-run coordination](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5845870039).
Scope: one native Gemma download, actual saved-weight verification, and at most two original text/vision probes. The full frozen May 2024 validation remains with #33; this task has not accessed exam inputs, keys, or sealed 2025 material.

## Current status

**Pending connectivity recovery. No Gemma inference result is claimed.**
SSH inspection succeeded at approximately 11:07 UTC on 26 September 2026, after an authorized sandbox network escalation. A resumable native pull began after the lead confirmed the coordination claim. At 330.5 seconds, the model download had reached **7,203,251,644 / 7,381,382,048 bytes**. Subsequent independent SSH inspections timed out before connection. The original pull session remained waiting without a new confirmed status at 11:24 UTC.

At 11:27 UTC, the lead independently observed that the Tailscale peer was Online/Active with a recent handshake and a roughly 72 ms ping response, while SSH attempts were timing out. This narrows the observed problem to SSH/device shell responsiveness; it does not establish that the machine is offline or that Ollama failed.

Installation, actual blob hashes, served template, cold load, vision support, and thinking-disabled final responses remain unverified. Partial downloads and a private progress log are preserved. The remote preparation process has a 2,450-second outer limit; the local task ends by 12:06 UTC. No second model download, runtime repair/build/reinstall, service restart, model deletion, or VLLM intervention was attempted. A separate team's CPU HF preparation was noticed and coordinated in #33; this worker did not start or duplicate it.

## Selected native route and provenance

The installed runtime is **Ollama 0.32.14**, verified through both CLI and local `/api/version`. Its installed binary contains Gemma 4, Gemma 4 Unified, and no-thinking architecture/template identifiers. This is a static support check, not a successful runtime load.

Selected tag: **`gemma4:12b-it-q4_K_M`**, native Q4_K_M model with a BF16 projector. [Ollama's library listing](https://ollama.com/library/gemma4:12b) identifies the model, projector, and Apache-2.0 license. [Google's publisher model card](https://huggingface.co/google/gemma-4-12B-it) also identifies Apache-2.0. The native [registry manifest](https://registry.ollama.ai/v2/library/gemma4/manifests/12b-it-q4_K_M) supplied these expected inventory values:

| Weight layer | Expected saved bytes | Expected SHA-256 |
| --- | ---: | --- |
| Model | 7,381,382,048 | `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606` |
| BF16 projector | 175,115,584 | `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842` |
| **Total weights** | **7,556,497,632** | **443,502,368 B below the 8,000,000,000 B limit** |

The registry also has config, license, and parameter layers; those are retained in the manifest but are not inference weights. The preparation script verifies every downloaded layer's actual size and SHA-256 and rejects a changed manifest. **These numbers are expected source metadata until that script's inventory is recovered.** No HF QAT bundle was downloaded or combined with this native quantization.

## Shared machine and honest memory reporting

Initial readings: 130,594,136,064 B total RAM, approximately 21,414,739,968 B available RAM, and 2,284,574,896,128 B free disk space. The device is an NVIDIA GB10 with driver 580.173.02 and CUDA 13.0. `nvidia-smi` reports global memory as **Not Supported**. This is unknown, not zero. An existing VLLM worker was listed at 93,990 MiB; that shared worker was left untouched.

The prepared, **unexecuted** probes require at least 14,000,000,000 B `MemAvailable` before each POST and request a client-side socket abort if sampling falls below 8,000,000,000 B or the wall time expires. That abort does not prove the server stopped generation; no shared-service cancellation or restart is attempted. They record shared `MemAvailable`, Ollama process RSS, `/api/ps`, and device memory availability; shared totals are not isolated model peaks.

## Commands and private evidence

Remote task directory: `/home/ljaniec/matura-tasks/gemma-load-20260926-1106`.
Local private directory: `agentsLog/ljaniec/private/gemma-spark-load-20260926/`.
Prepared scripts and raw requests/responses stay private. Aggregate summaries can be published after independent review.

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes ljaniec@dell-gb10 \
  'timeout 2450 python3 /home/ljaniec/matura-tasks/gemma-load-20260926-1106/prepare.py'
```

The script uses the existing local Ollama `/api/pull` with `gemma4:12b-it-q4_K_M`, preserving Ollama's partials. Successful preparation would retain `registry-manifest.json`, `show.json`, `tags.json`, `inventory.json`, start/end metadata, and append-only `pull-progress.jsonl` in the task directory. Recover and review those files before any load call; do not assume the pull finished.

The unexecuted probe script uses native `/api/chat`, `think: false`, a 2,048-token context, 96 output tokens, deterministic temperature zero, and a two-minute keep-alive. It is prepared for one original short Polish prompt and one original synthetic image of colored shapes, subject to verified inventory, fresh file hashes, adequate headroom, review, and the cutoff. It refuses prior probe evidence, opens new raw files exclusively, and retains streaming content, `done`, `done_reason`, usage/load timings, absence or presence of thinking text, and memory samples privately. An empty, truncated (`done_reason: length`), or unfinished response is unusable. The [native API documentation](https://docs.ollama.com/api/chat) specifies the `think` control; backend response evidence is still required.

No validation score, training gain, OCR quality, cold-load latency, isolated memory peak, or offline success is established by this preparation status.
