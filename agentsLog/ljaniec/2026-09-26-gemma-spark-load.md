# Gemma 4 preparation on Spark — bounded load task

Owner: @ljaniec. Coordination: [issue #33 claim](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5845725912) and [duplicate-run coordination](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5845870039).
Scope: one native Gemma download, actual saved-weight verification, and at most two original text/vision probes. The full frozen May 2024 validation remains with #33; this task has not accessed exam inputs, keys, or sealed 2025 material.

## Current status

**Native weights verified; the load probe failed with CUDA out of memory. No usable Gemma answer or vision result is claimed.**
SSH inspection succeeded at approximately 11:07 UTC on 26 September 2026. The resumable native pull started at **11:10:27.882 UTC** and completed, including actual size/hash verification, at **11:16:28.817 UTC** in **360.9349 seconds**. SSH output delivery stalled; completion was observed after connectivity recovered at **11:33:54 UTC**. These preparation and observation times describe different events.

At 11:27 UTC, the lead independently observed that the Tailscale peer was Online/Active with a recent handshake and a roughly 72 ms ping response, while SSH attempts were timing out. This narrows the observed problem to SSH/device shell responsiveness; it does not establish that the machine is offline or that Ollama failed.

The installed weight inventory was recovered locally and independently checked by the lead. Both weight hashes were freshly checked again before the one original text probe, and the installed manifest and backend tag digest matched the captured native manifest. At **11:35:45.255 UTC**, native `/api/chat` returned **HTTP 500** after **2.391841 seconds**, reporting a CUDA out-of-memory startup failure after its own projector CPU offload retry. That duration is failed request/startup latency, **not generation latency or successful cold-load latency**. It returned no content, `done`, or finish reason. The vision request was not attempted.

Further Spark probes stopped immediately. No manual retry, second download, runtime repair/build/reinstall, service restart, model deletion, GPU-control change, or VLLM intervention occurred. The lead released the [CPU handoff on #33](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5845947062). This worker did not start or duplicate that CPU work.

## Selected native route and provenance

The installed runtime is **Ollama 0.32.14**, verified through CLI and local `/api/version`. The downloaded `/api/show` reports architecture/tokenizer `gemma4`, Q4_K_M, and completion/vision/audio/tools/thinking capabilities. Its template field is the placeholder **`{{ .Prompt }}`**; this is **not proof of the resolved backend chat renderer**. Tokenizer metadata reports BOS insertion enabled, BOS ID 2 and EOS ID 1.

The worker’s final read-only inspection recorded these runtime fingerprints; its retained transcript is reconstructed from observed tool output and has no exact inspection timestamp: `/usr/local/bin/ollama` SHA-256 `26f44ca89143f2326a3aad98b2cb5e8b5af9397aef7001cd8d022e90d6e0b55e`; `/usr/local/lib/ollama/llama-server` SHA-256 `f6e05586c5e7dd2110b2d8efadf23ff3b081dcdd53be67cfd32884af7b476163`.

Selected tag: **`gemma4:12b-it-q4_K_M`**, native Q4_K_M model with a BF16 projector. Immutable native manifest SHA-256: **`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`**. [Ollama's library listing](https://ollama.com/library/gemma4:12b) identifies the model, projector, and Apache-2.0 license. [Google's publisher model card](https://huggingface.co/google/gemma-4-12B-it) also identifies Apache-2.0. The native [registry manifest](https://registry.ollama.ai/v2/library/gemma4/manifests/12b-it-q4_K_M) and actual saved files agree:

| Weight layer | Actual saved bytes | Verified SHA-256 |
| --- | ---: | --- |
| Model | 7,381,382,048 | `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606` |
| BF16 projector | 175,115,584 | `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842` |
| **Total weights** | **7,556,497,632** | **443,502,368 B below the 8,000,000,000 B limit** |

Every downloaded layer, including config/license/parameters, matched its manifest hash and size. Config/license/parameters are retained in the inventory and are not inference weights. The saved candidate weight pair is **7,556,497,632 B** and fits the 8,000,000,000 B file limit. Successful serving remains unproven. The native manifest does not supply an upstream HF commit revision. No HF QAT bundle was downloaded or combined with this native quantization.

## Shared machine and honest memory reporting

Initial readings: 130,594,136,064 B total RAM, approximately 21,414,739,968 B available RAM, and 2,284,574,896,128 B free disk space. The device is an NVIDIA GB10 with driver 580.173.02 and CUDA 13.0. `nvidia-smi` reports global memory as **Not Supported**. This is unknown, not zero. An existing VLLM worker was listed at 93,990 MiB; that shared worker was left untouched.

Before the failed probe, shared `MemAvailable` was **21,424,705,536 B**; the minimum of five samples was **21,317,132,288 B**; after failure it was **21,405,171,712 B**. Maximum sampled combined Ollama daemon/runner RSS was **265,400,320 B**. This brief failed startup is not a measured successful or isolated model peak. Before and after `/api/ps` showed no loaded Ollama model. Final device readings remained N/A, and the worker’s final inspection listed VLLM PID 70522 with 93,990 MiB reported; this point observation has no exact inspection timestamp. CUDA allocation failed despite available shared RAM; the cause was not isolated.

The executed request passed the 14,000,000,000 B pre-POST headroom check. It did not trigger the 8,000,000,000 B client memory abort or wall abort. Those guards would close the client socket only; they do not prove server cancellation. The shared service was not changed.

## Commands and private evidence

Remote task directory: `/home/ljaniec/matura-tasks/gemma-load-20260926-1106`.
Local private directory: `agentsLog/ljaniec/private/gemma-spark-load-20260926/`.
Prepared scripts, original image, raw requests/responses, and memory samples stay private. The public [aggregate and artifact hashes](2026-09-26-gemma-spark-load-summary.json) retain actual inventory, manifest binding, failure timing, limitations, and SHA-256 identifiers for 15 retained private evidence files plus the labeled reconstructed final-inspection transcript. No exam content or keys were accessed.

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes ljaniec@dell-gb10 \
  'timeout 2450 python3 /home/ljaniec/matura-tasks/gemma-load-20260926-1106/prepare.py'
```

The script used existing local Ollama `/api/pull` and retained `registry-manifest.json`, `show.json`, `tags.json`, verified `inventory.json`, start/end metadata, and append-only `pull-progress.jsonl`. The reviewed probe command was:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes ljaniec@dell-gb10 \
  'timeout 420 python3 /home/ljaniec/matura-tasks/gemma-load-20260926-1106/probe.py'
```

It made exactly one original text request. Do not rerun this script: its exclusive evidence/lock guard rejects existing probe evidence, and this task's Spark inference step has stopped.

The saved weight pair can be verified read-only on Spark without the private script:

```bash
sha256sum \
  /usr/share/ollama/.ollama/models/blobs/sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606 \
  /usr/share/ollama/.ollama/models/blobs/sha256-675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842
stat -c '%n %s' \
  /usr/share/ollama/.ollama/models/blobs/sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606 \
  /usr/share/ollama/.ollama/models/blobs/sha256-675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842
sha256sum /usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M
```

For review, this is the exact native localhost request, with an original prompt, that produced the startup error. **Do not run it automatically or while the resource block remains.** A future owner needs a cleared resource situation, a reviewed request-specific memory/cutoff guard, a fresh manifest/backend binding, and a new private evidence path. The original worker made no new attempt after the failure.

```bash
curl --max-time 180 --no-buffer --fail-with-body \
  -H 'Content-Type: application/json' \
  --data-binary @- http://127.0.0.1:11434/api/chat <<'JSON'
{
  "model": "gemma4:12b-it-q4_K_M",
  "messages": [{"role": "user", "content": "Odpowiedz jednym krótkim zdaniem po polsku: w którym roku odbył się chrzest Polski?"}],
  "think": false,
  "stream": true,
  "keep_alive": "2m",
  "options": {"num_ctx": 2048, "num_predict": 96, "temperature": 0, "seed": 26}
}
JSON
```

The Python worker used this payload with HTTP streaming under an external 420-second process bound, an internal 180-second request wall guard, and the 12:06 UTC task cutoff. A bare cURL command is reference reproduction, not a substitute for those reviewed guards. This native startup diagnostic does not replace the portable runner/adapter or authorize a validation run.

The request used native `/api/chat`, **`think: false`**, a 2,048-token context, 96 output tokens maximum, temperature zero, and a two-minute keep-alive. **Thinking was requested disabled; actual thinking-disabled behavior is unproven because startup failed.** The original synthetic image was created privately but never sent. The script refused prior probe evidence and required fresh weight hashes and unchanged installed/backend manifest bindings before its POST; the cutoff bounded the request. An empty, truncated (`done_reason: length`), or unfinished response is unusable. The [native API documentation](https://docs.ollama.com/api/chat) specifies the `think` control.

This task establishes actual saved-weight size/hash compliance and a reproducible failed native load request. It establishes **no nonempty answer, vision/OCR result, validation score, training gain, successful cold-load latency, isolated memory peak, or offline serving success**. Exactly **one original probe request and zero exam requests** were made. The CPU handoff and any full validation remain lead/#33 work.
