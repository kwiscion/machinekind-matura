# Essay-only LoRA for Gemma 4 12B: feasibility desk study (issue #80 stretch)

Owner: @Pewciu6. Written 2026-09-26, about 19:45 Europe/Warsaw. **Desk study only:** no training, weight downloads, GPU use, model calls or purchases. I fetched only public config files, without logging in. **Training success is not a score gain.** Only an independent grade of the exported, quantized artifact's answers counts. Final verdict first: **feasible on the central H100 in well under 60 minutes, but blocked by data and by three unverified export steps.** Those steps must pass on CPU or with a zero-adapter check before any training is worth running.

## 1. Exact architecture (verified from the HF repo, revision `707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7`, last modified 2026-07-20)

These values come from `google/gemma-4-12B-it`. Evidence: `config.json` sha256 `478c46e8…36bd9` and `processor_config.json` sha256 `6b938e76…545c9`, fetched with `curl` from `resolve/main`, plus the model card.

| Field | Value |
|---|---|
| Class / `model_type` | `Gemma4UnifiedForConditionalGeneration` / `gemma4_unified` (saved with transformers `5.10.0.dev0`) |
| Parameters | 11.95 B (model card). The single `model.safetensors` is **23,919,549,408 bytes** in BF16 (x-linked-etag `5a84cb31…f18d`). |
| Text tower | `gemma4_unified_text`: 48 layers. 40 are `sliding_attention` (window 1024) and 8 are `full_attention`: layers 6, 12, …, 48, a 5:1 pattern. Hidden 3840, MLP 15360 (GeLU-tanh). 16 query heads, 8 KV heads with `head_dim` 256 on sliding layers. Global layers use `global_head_dim` 512, `num_global_key_value_heads` 1 and `attention_k_eq_v: true`. Vocabulary 262,144, tied embeddings, final logit softcap 30, context 262,144. RoPE θ is 1e6 (proportional, partial 0.25) on global layers and 1e4 on sliding layers. |
| Vision | `gemma4_unified_vision` is "encoder-free": linear patch embedding into the LM (patch 16, model patch 48, pooling kernel 3, 280 soft tokens per image by default, position table 1120). The processor is `Gemma4UnifiedProcessor` / `Gemma4UnifiedImageProcessor`, with no normalisation and rescale 1/255. |
| Audio | `gemma4_unified_audio` (hidden 640). Not used here. |
| Deployed runtime | Ollama `gemma4:12b-it-q4_K_M`: model blob 7,381,382,048 B (Q4_K_M, arch `gemma4`) and projector 175,115,584 B (BF16, listed as arch `clip`). **Combined 7,556,497,632 B**, from the root readiness record. |

**Not verified:** that the Ollama registry blob was converted from this exact HF revision. The registry page names no upstream revision. Before exporting a merged model, confirm that our own convert-and-quantize of the **unmodified** base reproduces the tensor list and approximately the bytes of the registry blob (step 5.3). Otherwise adapter effects cannot be separated from pipeline drift.

## 2. PEFT/LoRA support: what is known and what is not

- **Public reports** (below) concern the April 2026 `Gemma4ForConditionalGeneration` release:
  - The vision and audio towers wrap `nn.Linear` in `Gemma4ClippableLinear`, and PEFT refuses to attach to it.
  - PEFT ≥ 0.19.0 therefore ships a default Gemma 4 target that is a regex scoped to `language_model`. A plain list such as `["q_proj","v_proj"]` still walks the towers and fails.
  - transformers ≥ 5.5.2 is required, because earlier versions break the inter-layer KV sharing under `use_cache=False`, and text-only batches need `mm_token_type_ids`.
  - vLLM and SGLang do not serve Gemma 4 LoRA at runtime, so the adapter must be merged before serving.
  - DeepSpeed ZeRO-3 can save empty adapter tensors. Use a single GPU with no ZeRO.
- **The July 2026 unified variant is different.** It is encoder-free, and `num_kv_shared_layers: 0`. I found no public report of PEFT on `gemma4_unified` specifically. Whether ClippableLinear still exists in the unified patch embedder is **unverified**. The text-tower regex below avoids those modules either way.
- **Target scope (proposed):** `target_modules = r".*language_model\..*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"`. That is text-tower only, all 7 projections. A public Gemma 4 comparison found 7 projections clearly better than PEFT's default 2 (q and v) on a classification task. That is evidence for capacity, not for essays. Vision, audio, embeddings and `lm_head` stay frozen, so image items and the short-answer base are untouched **when the adapter is not applied**.
- **Adapter size estimate:** at r = 16, summing r·(in+out) over the 7 projections gives about 1.36 M parameters per layer, or ≈ **65 M parameters** over 48 layers, about **0.13 GB in BF16**. The global layers differ by a few percent. The adapter is reported separately and does not count toward the 8 GB model limit (CONTRACTS.md).

## 3. Training memory estimate (single GPU, no DeepSpeed)

| Component | BF16 LoRA | QLoRA (4-bit base) |
|---|---:|---:|
| Frozen base weights | ≈ 23.9 GB | ≈ 7–8 GB |
| Adapter + AdamW states (65 M × (2 + 4 + 4 + 4) B) | ≈ 0.9 GB | ≈ 0.9 GB |
| Activations, seq 2048, batch 1, gradient checkpointing | ≈ 2–5 GB | ≈ 2–5 GB |
| Logits over a 262 k vocab (2048 × 262,144 × 4 B, plus gradient) | ≈ 2–4 GB (fused or chunked cross-entropy reduces this) | same |
| **Total (rough)** | **≈ 30–35 GB → fits an 80 GB H100 comfortably** | **≈ 13–18 GB → would fit a 24 GB RTX 5090 Laptop, tightly** |

These are arithmetic estimates, not measurements. The first action on hardware is a 5-step smoke run that records peak `torch.cuda.max_memory_allocated`. **Throughput:** 150 examples × about 1,500 tokens × 3 epochs ≈ 0.7 M tokens. At a conservative 1–3 k tokens/s for BF16 LoRA of a 12 B model on an H100, that is about 4–12 minutes. The declared 60-minute cap is generous. Data preparation and review take longer than training.

## 4. Proposed single configuration (one run, for the lead to declare)

| Setting | Value |
|---|---|
| Base | `google/gemma-4-12B-it` @ `707f0a3b…` in BF16 (not QLoRA on H100, to avoid a 4-bit to BF16 merge mismatch) |
| Software | transformers version that loads `gemma4_unified` (≥ 5.5.2 and ≥ the saving version; pin the exact version during the smoke run), peft ≥ 0.19 (torch ≥ 2.7), trl pinned, no DeepSpeed |
| LoRA | r 16, α 32, dropout 0.05, the text-tower regex above, no bias, no `modules_to_save` |
| Optimisation | AdamW, lr 1e-4 with cosine decay, warmup 10 steps, effective batch 8 (1 × grad-accumulation 8), BF16, gradient checkpointing, seed 42, max seq 2048, loss on the assistant completion only |
| Schedule | `max_steps = ceil(3 · N_train / 8)`, **hard stop by `max_steps` plus a `timeout 3600` wrapper**, no automatic resume or extension |
| Checkpoints | Save the adapter every 25 % of steps. After each save, `rsync` the adapter, trainer state and logs to a local backup (laptop) and record their sha256. |
| Evaluation during training | Loss on the held-out dev group only. **No validation (2024) item** is used for selection, early stopping or any decision during training. |
| Output | The adapter safetensors with bytes and hash, a training log and the exact data hash, all under `candidates/Pewciu6/essay-lora-v1/` |

## 5. Export path to the offline runtime (each step is a gate; stop on the first failure)

1. **Adapter:** PEFT `adapter_model.safetensors`, reported separately with bytes and sha256.
2. **Merge:** `PeftModel.from_pretrained(base, adapter).merge_and_unload()` gives a BF16 model. Assert that the merged state-dict keys and shapes equal the base's. Public Gemma 4 reports needed a remap from `.weight` to `.linear.weight` after unwrapping the ClippableLinear towers. Scoping the regex to the text tower should make that remap unnecessary, but check it.
3. **Pipeline control (required):** convert and quantize the **unmerged base** with the same llama.cpp revision: `convert_hf_to_gguf.py` → BF16 GGUF plus `--mmproj` projector → `llama-quantize … Q4_K_M`. Then serve it through Ollama with the base's `ollama show --modelfile gemma4:12b-it-q4_K_M` template and parameters. Run the DEV essay fixtures on this control against the registry model. **Unverified:** whether the current llama.cpp converter supports the `gemma4_unified` HF layout. Public reports cover `gemma4` conversion issues only. If the converter fails, the merged-model path is blocked and step 6 is the only option.
4. **Merged export:** repeat step 3 on the merged model. The size gate is model GGUF + projector ≤ **8,000,000,000 bytes**. The same architecture and quantization should land near the base's 7.56 GB, about 0.44 GB of headroom. Record the exact bytes; do not assume them.
5. **Serving:** the essay route sends only essay-structured items to the merged model (the router in `scripts/Pewciu6/essay_route.py`). Every other item stays on the unchanged base. That means two saved models, each ≤ 8 GB. The lead decides whether that is acceptable under the event rule and in memory on the final machine, which would need two models resident or a swap with its latency.
6. **Alternative, no second model:** `convert_lora_to_gguf.py --base <base>` gives a GGUF LoRA, served with an Ollama Modelfile `ADAPTER` line or llama.cpp `--lora`. The base stays byte-identical, and the adapter is reported separately. **Unverified:** Ollama `ADAPTER` support for the `gemma4` architecture. First test a **zero-initialised adapter** (B = 0) on CPU and check that its outputs are token-identical to the base at temperature 0.
7. **Offline qualification:** load the exported artifact in the isolated offline launcher (root runbook) with text and image synthetic checks. Also run a 2-item DEV essay check, network disconnected.

## 6. Data requirements (the actual blocker)

- **Volume:** at least 100–200 training essays plus a held-out dev group of about 20. Przemek's #97 plans 12 in the first wave. That is enough to test the pipeline, not to change essay behaviour measurably.
- **Content:** source-verified, multi-era, varied stances and aspect structures, 350–450 words, in the same output shape the route prompt asks for (topic line, `Teza:`, three `Aspekt` sections, `Zakończenie:`). Each fact should link to evidence (`evidence[]` with source_id and locator) and be independently fact-checked before it counts as verified (CONTRACTS.md).
- **Splits:** split by `source_group_id`, so no source group appears in both train and dev. My 5 DEV fixtures in `dev_fixtures.jsonl` use distinct groups (`grp-essay-dev-essay-00N`) and stay **evaluation-only** for base-versus-adapter comparison. They must not be used for training.
- **Exclusions (SOURCE.md):** no DEV 2023, VALIDATION 2024 or SEALED 2025 prompts, keys, rubrics or paraphrases. Run a near-duplicate check against the validation essay topic before training. Label synthetic essays with generator provenance, and never count them as verified until an independent check passes.

## 7. Risks and decision

- **Bad synthetic facts get learned confidently.** This is the dominant risk, and review capacity, not GPU time, limits it.
- **Topic memorisation** and loss of instruction-following on the exact matura phrasing.
- **Quantization drift** after merge and re-quantize. Step 5.3 is the control.
- **Two-model memory and latency** on the final machine.
- **Deadline:** the Sunday 11:00 freeze leaves one attempt at most. The prompt route (PR #102) is the faster first intervention and gives the comparison baseline. The LoRA arm should be compared against **the route prompt on the base**, not against the bare prompt.

**Recommendation:**
1. On CPU now: pin library versions, check that `gemma4_unified` loads in transformers and whether the llama.cpp converter recognises it, and do the zero-adapter identity check.
2. If those pass and #97 reaches at least 100 reviewed essays, the lead declares the single 60-minute H100 job above.
3. Otherwise record LoRA as not feasible before the freeze and put the essay effort into the prompt route.

## Sources

- HF `google/gemma-4-12B-it`: [model card](https://huggingface.co/google/gemma-4-12B-it); `config.json` and `processor_config.json` fetched from `resolve/main` @ `707f0a3b…`.
- Ollama registry: [gemma4:12b-it-q4_K_M](https://ollama.com/library/gemma4:12b-it-q4_K_M).
- Gemma 4 LoRA pitfalls (ClippableLinear, PEFT 0.19 regex default, transformers ≥ 5.5.2, no runtime LoRA in vLLM/SGLang, ZeRO-3 empty tensors): [Oxen.ai write-up](https://ghost.oxen.ai/writing-a-fine-tuning-and-deployment-pipeline-isnt-as-easy-as-it-looks-gemma-4-version/).
- Text-tower regex and the 7-versus-2 projection comparison: [DenisovAV/litetune PR #48](https://github.com/DenisovAV/litetune/pull/48).
- llama.cpp LoRA conversion: [convert_lora_to_gguf.py](https://github.com/ggml-org/llama.cpp/blob/master/convert_lora_to_gguf.py); Gemma 4 converter issue [#21403](https://github.com/ggml-org/llama.cpp/issues/21403).
- Local: `agentsLog/kwiscion/2026-09-26-gemma4-readiness.md` (projector bytes), WINNING_PLAN.md (combined bytes), CONTRACTS.md (adapter reported separately).
