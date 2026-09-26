# Gemma 4 baseline handoff to @semberecki — issue #33

Owner: @ljaniec, handoff only. Trigger: author comments
[5845608463](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5845608463)
and [5845609135](https://github.com/kwiscion/machinekind-matura/issues/5#issuecomment-5845609135).
Issue #5 stays closed. The new best-score instruction authorizes one proven
Gemma load or this recipe handoff if Spark SSH is still denied. It supersedes
the earlier stopped-work instruction for this targeted task only. No specialist
training, new smoke audit, purchases, HF publication, PR #23 merge or 2025 access.

## Access result and ownership

At **2026-09-26 10:51 UTC / 12:51 Europe/Warsaw**:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes ljaniec@dell-gb10 'hostname'
```

returned `Permission denied (publickey,password)` (exit 255). No environment
repair, model download or inference was attempted. The explicitly authorized
fallback is to hand this recipe to @semberecki on #33. That owner claims the
24 GB GPU run; this session does not claim their issue or start a second arm.
Coordinate with the lead before downloading: only one Gemma and one Qwen 9B
validation run across the team. Preserve interrupted files, but a partial
download is not an installed model.

## Pinned bundle — metadata, not a load result

Catalog: [`scripts/ljaniec/model_candidates.json`](../../scripts/ljaniec/model_candidates.json).
Repository: `google/gemma-4-12B-it-qat-q4_0-gguf`.
Revision: `29d097773436b69ff9feafd636ab4cf873786537`.
Quantization: QAT Q4_0. Repository-reported license: Apache-2.0.
[Pinned publisher source](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf/tree/29d097773436b69ff9feafd636ab4cf873786537).

| File | Publisher-reported bytes | Publisher-reported SHA-256 |
| --- | ---: | --- |
| `gemma-4-12b-it-qat-q4_0.gguf` | 6,975,879,296 | `93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b` |
| `mmproj-gemma-4-12b-it-qat-q4_0.gguf` | 175,115,616 | `cb018338a7538a9814d994bfe54644c71eb7ed54e31eae2f721e45fd3c260da7` |

Total **7,150,994,912 B**, including the projector; metadata headroom below
8,000,000,000 B is 849,005,088 B. Independent Sol review checked catalog
arithmetic, hash/revision lengths and the pinned publisher source. These are
not hashes of downloaded files, runtime compatibility, measured memory or a
nonempty-load result. This HF QAT bundle differs from the interrupted Ollama
quantization: do not mix its projector, hashes or byte totals with another tag.

If the team chooses this bundle, on the inference machine with an existing HF
CLI, use repository-scoped cache and the immutable revision:

```bash
HF_HOME="$PWD/.hf-home" hf download google/gemma-4-12B-it-qat-q4_0-gguf \
  gemma-4-12b-it-qat-q4_0.gguf mmproj-gemma-4-12b-it-qat-q4_0.gguf \
  --revision 29d097773436b69ff9feafd636ab4cf873786537 \
  --local-dir ./models/gemma4-12b-qat-q4_0
sha256sum ./models/gemma4-12b-qat-q4_0/*.gguf
stat -c '%n %s' ./models/gemma4-12b-qat-q4_0/*.gguf
```

Compare **both** actual hashes and sizes with the catalog before loading. Record
every served weight/projector file, total bytes, exact runtime build, tokenizer/
template, GPU offload, cold-load time, peak process/device memory and latency.
Use the matching projector and a runtime that actually supports this model's
vision architecture. No specific runtime build has been validated here.

## Nonempty load, then the single frozen validation arm

First prove a nonempty final Polish answer with thinking disabled and a simple
self-authored prompt, for example `Odpowiedz krótko po polsku: w którym roku
odbył się chrzest Polski?`. Preserve the full provider response and finish
reason; transport success or thinking tokens alone do not prove a usable
answer. Verify image support with the matching projector before the full arm.

For the author-requested run use **`infer.py`**, with the real local endpoint
and exact model ID returned by that server. A local configuration must include:

```json
{
  "name": "gemma4-12b-q4-validation",
  "base_url": "http://127.0.0.1:11434/v1",
  "model": "REPLACE_WITH_EXACT_VERIFIED_SERVER_MODEL_ID",
  "reasoning_effort": "none",
  "max_output_tokens": 1024,
  "timeout_seconds": 600
}
```

Use port 11434 only for Ollama; replace the base URL for another local server.
The config's thinking request must be supported by the actual backend/template.
The independent `run_local_smoke.py` has no thinking-control flag, so it cannot
by itself meet this task's thinking-disabled requirement. `infer.py` passes the
configured field; backend acceptance/behavior must still be verified.

The lead transfers private runner input **and its page images**, not keys.
Check input SHA-256 is exactly
`f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`.
Keep image paths relative to that input and preserve all 40 items. A differing
hash or missing assets goes back to the lead before model calls. Do not rebuild
or transmit evaluation keys through the model-facing path.

```bash
python3 infer.py --config agentsLog/semberecki/private/gemma4-config.json \
  --input agentsLog/semberecki/private/validation_2024/runner_input.jsonl \
  --output agentsLog/semberecki/private/gemma4-validation-raw.jsonl \
  --max-calls 40
python3 scripts/normalize_outputs.py \
  --input agentsLog/semberecki/private/gemma4-validation-raw.jsonl \
  --output agentsLog/semberecki/private/gemma4-validation-model.jsonl
```

These paths are the suggested owner layout; use the actual transferred files.
`--max-calls 40` is required because the runner defaults to 20. One attempt per
item, no retries, images included, output paths new, incomplete answers retained.
Give @Pewciu6 the raw/normalized paths privately for #11 scoring; publish only
rights-reviewed aggregates. Keep the 40-item/60-point denominators and failed/
incomplete/image cases. If the lead already started Qwen 9B, take Gemma rather
than repeating it. The lead selects the higher provisional score and owns the
Sunday 27 September 11:00 Warsaw freeze; May 2025 remains sealed.

This handoff contains **zero actual Gemma inference results**. No installation,
load latency, peak memory, exam score or training gain is claimed. The standing
15-minute monitor remains active; share this note and the complete standing
brief/repository rules with each subagent or new session handling the baseline.
