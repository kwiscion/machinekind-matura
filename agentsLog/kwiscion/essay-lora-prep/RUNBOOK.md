# Essay-only Gemma 4 Unified LoRA: prepared path, runtime gates pending

**Verdict:** a concrete source-supported path exists: BF16 `Gemma4UnifiedForConditionalGeneration` → text-only PEFT LoRA → BF16 merge → pinned llama.cpp text/projector conversion → Q4_K_M → offline qualification. This preparation does **not** establish that attachment, backward, full-model conversion or serving works. Those are the next finite checks, independently of waiting for training data. No training/inference/weight download/GPU process was executed here.

**Authorized CPU setup result,19:51UTC:** PyTorch2.8.0+cpu installed into the new ignored `evidence-private/cpu-venv`; its CUDA build is `None`. The pinned Git clone failed with HTTP/2 earlyEOF. A same-commit archive fallback downloaded the two source archives, but dependency installation hit the original absolute15-minute setup deadline before completion. The installer was terminated at19:51:29UTC; **Transformers/PEFT remain absent and the tiny model probe was not executed**. `cpu-install-report.json`, `cpu-install-archive-report.json`, `cpu-environment-partial.json` and `cpu-dependencies-partial.txt` preserve the result. No existing environment was changed. This is a setup/network blocker, not evidence that LoRA fails on this architecture.

The exact next install command, only under a **new separately declared setup bound**, is:

```powershell
agentsLog/kwiscion/essay-lora-prep/evidence-private/cpu-venv/Scripts/python.exe -m pip install --constraint agentsLog/kwiscion/essay-lora-prep/evidence-private/constraints.txt https://codeload.github.com/huggingface/transformers/zip/96331a9f93b72697f160a958d2883d4b49a56739 https://codeload.github.com/huggingface/peft/zip/b8674c86183a5dee38d0c3ede392e189593025e5
```

After successful installation, `python agentsLog/kwiscion/essay-lora-prep/run_cpu_probe.py --execute-synthetic` checks exact VCS commit IDs or exact commit archive URLs+archive hashes, verifies four installed source-file hashes against the pinned evidence, requires torch2.8.0+cpu with no CUDA build, and enforces a120-second subprocess deadline for the tiny probe. The archived install script retains its expired deadline deliberately; do not silently extend it. Record a complete dependency freeze only after the installation actually finishes.

## What is verified

- Pinned Google revision `707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7`: `gemma4_unified`, class `Gemma4UnifiedForConditionalGeneration`, 48 text layers (40 sliding, 8 full), hidden 3840, vocab 262144, BF16, tied embeddings; unified direct image/audio embedding modules. This is **not** the earlier Gemma4 architecture. [Config](https://huggingface.co/google/gemma-4-12B-it/blob/707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7/config.json).
- Transformers commit `96331a9f93b72697f160a958d2883d4b49a56739` implements the text attention projections as ordinary `nn.Linear`; text modules live under `model.language_model.layers`. Full-attention layers have shared K/V and no separate `v_proj`. [Implementation](https://github.com/huggingface/transformers/blob/96331a9f93b72697f160a958d2883d4b49a56739/src/transformers/models/gemma4_unified/modeling_gemma4_unified.py).
- PEFT commit `b8674c86183a5dee38d0c3ede392e189593025e5` supports generic linear LoRA. Its defaults list `gemma4`, not an independently confirmed `gemma4_unified` default. Use the **explicit text-only regex** in `candidate.json`; never `all-linear`. This avoids modifying patch/audio embeddings or relying on old ClippableLinear workarounds. [Linear implementation](https://github.com/huggingface/peft/blob/b8674c86183a5dee38d0c3ede392e189593025e5/src/peft/tuners/lora/layer.py).
- llama.cpp commit `fcb3074f2bc06943a564d7f293f9e66d4bece02a` explicitly registers **both** `Gemma4UnifiedModel` and `Gemma4UnifiedVisionAudioModel` for the pinned architecture. Thus architecture registration is no longer an unknown; actual conversion of full tensors remains untested. [Converter](https://github.com/ggml-org/llama.cpp/blob/fcb3074f2bc06943a564d7f293f9e66d4bece02a/conversion/gemma.py).
- The exact Google Jinja template was rendered with synthetic messages using isolated Jinja2 3.1.6 / MarkupSafe 3.0.3. Nonthinking inference ends its prefix with `model\n<|channel>thought\n<channel|>`, while ordinary complete-chat rendering omits that empty thought channel. `prepare.py` uses **the actual generation prefix + original answer + `<turn|>`**, with no duplicated BOS/EOS; loss covers only the answer and terminator. It requires exact token-prefix equality with the actual local tokenizer before output. [Template](https://huggingface.co/google/gemma-4-12B-it/blob/707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7/chat_template.jinja).
- 21 synthetic CPU tests passed: exact acceptance/file binding, draft rejection, aliases, multitopic dependencies, shared sources/targets, control-token rejection, assistant loss mask, boundary changes, no truncation, file-size limit and input-only evaluation gates. Static source/hash checks pass. `template-check.json` and `source-check.json` record their narrower claims.

## Candidate and data contract

`candidate.json` proposes a small **behavior pilot**, not a proven best configuration: BF16 frozen base, r8/alpha16/dropout0.05 on text q/v projections, batch1 × accumulation8, LR1e-4, 3 epochs, at most120 optimizer steps, 4096-token cap, no packing, no truncation, one declared job of at most3600 seconds. Arithmetic from the pinned architecture gives88 targeted modules and5,193,728 trainable parameters (~10.4MB of BF16 adapter tensors before metadata). Exact attachment counts must be checked on the loaded model.

BF16 base weights are approximately24GB; batch1 plus checkpointing makes an H10080GB a plausible target, **not measured memory evidence**. A full4096×262144 FP32 logits buffer alone is about4.3GB before gradients and other activations. No throughput or completion-time guarantee is made. Stop on OOM instead of silently changing sequence length or quantization. There is no arbitrary100-example minimum: a small cleared pilot can test behavior, with limited generalization claims.

Greg owns #117 canonical export and grouping. `prepare.py data` accepts JSONL with `id`, `task_type` (`essay`/`essay_repair`), `source_group_id`, nonempty `source_ids`, optional `additional_source_group_dependencies`/`context_source_group_ids`, and either `prompt`+`response`/`answer` or one user/assistant message pair (optional system). Target must be400–500 words of clean prose. Explicit DRAFT status is rejected; records cannot contradict their train/holdout file split. Preserve parent/repair/source-connected components, including Augsburg–Vienna and League–Marshall. The holdout is independently authored curriculum material, never fixed2023/2024/2025 benchmark content.

The **proposed adapter contract**, not an already issued clearance, is `essay_lora_clearance_v1`:

```json
{
  "schema": "essay_lora_clearance_v1",
  "checks": {
    "independent_content_review": true,
    "rights_export_review": true,
    "source_group_alias_dedup": true,
    "benchmark_exclusion_audit": true
  },
  "files": {"train": {"sha256": "EXACT_FILE_BYTES"}, "holdout": {"sha256": "EXACT_FILE_BYTES"}},
  "canonical_group_map": {"SOURCE_GROUP_OR_DEPENDENCY": "CONNECTED_COMPONENT"},
  "accepted_records": {
    "RECORD_ID": {
      "status": "accepted",
      "record_sha256": "SHA256_OF_SORTED_COMPACT_UTF8_JSON",
      "independent_review_reference": "REVIEW_PATH_AND_CONTENT_HASH"
    }
  }
}
```

`prepare.canonical()` defines exact record hashing. The canonical exporter/reviewer supplies this sidecar; this script does not mark drafts accepted, perform benchmark comparison, or invent review evidence. If Greg's canonical schema differs, adapt this bridge after inspecting his actual accepted manifest; do not weaken gates or hand-mark booleans. All train/holdout records must be bound exactly, and every source group/dependency mapped. Alias deduplication is trusted only after Greg's content-bound audit; raw hashes alone cannot prove no paraphrase contamination.

```powershell
python agentsLog/kwiscion/essay-lora-prep/test_prepare.py
python agentsLog/kwiscion/essay-lora-prep/check_sources.py
python agentsLog/kwiscion/essay-lora-prep/check_template.py
python agentsLog/kwiscion/essay-lora-prep/prepare.py environment
# With Greg's cleared export; local base must already exist:
python agentsLog/kwiscion/essay-lora-prep/prepare.py data --train TRAIN.jsonl --holdout HOLDOUT.jsonl --clearance CLEARANCE.json --local-base BASE_DIR --output FRESH_PREPARED_DIR
```

The canonical PR130 export was inspected read-only at Git401e1bc: **90training rows (34essays,56repairs),16independent evaluation inputs**, targets409–457words, user/assistant chat pairs without a system message. Exact blob hashes and the component map are in `canonical-export-inspection.json`; this is not training clearance. Known#80DEV overlaps are Casimir/Lublin/January, so external quality evaluation uses the separate eval16. No gold400-word evaluation targets are required.

For this actual export replace `--holdout HOLDOUT.jsonl` with `--eval-inputs eval16_input.jsonl`. The sidecar then binds `files.eval_inputs.sha256` and must additionally set `checks.evaluation_inputs_group_audit: true` after the independent audit. Accepted-record bindings cover only training rows; input-only eval rows are checked for disjoint canonical components and cannot contain answer fields. This mode has **no evaluation loss or early stopping**; run the frozen3epochs with a cap of `min(120,3*ceil(N/8))` optimizer steps (36for90rows), plus the wall cap. All stopping rules are frozen before training. Internal target holdout mode remains optional; it does not replace external eval16.

Without `--local-base`, only data gates run. Tokenization uses `local_files_only=True`, checks pinned config/template/processor metadata, rejects boundary retokenization and oversized records, and saves labels with prompt positions at-100. Actual tokenizer files and all base weight hashes must also be tied to the pinned HF snapshot in the host acquisition manifest; metadata equality alone is not weight identity.

## Next finite compatibility checks (no training data needed)

1. **Environment:** on an owner-assigned isolated environment, retain/verify a working H100 PyTorch build and install the two pinned upstream source revisions, then record `pip freeze`, Python, CUDA, driver, package source commit IDs and installation logs. These are verified source commits, **not a tested dependency lock**. No blanket version inequality guarantees compatibility. Local default Python here lacks torch/transformers/peft/tokenizers; the project `.venv` points at a missing interpreter. The Jinja test uses a separate owned ignored dependency directory.
2. **Tiny CPU probe:** after explicit next-stage authorization, run `timeout --signal=TERM --kill-after=10s 180 python runtime_probe.py --execute-synthetic --output FRESH_PROBE.json`. It constructs a random six-layer unified model, targets11 q/v modules, takes one finite synthetic optimizer step, verifies nonzero finite gradients, frozen multimodal tensors, preserved merge keys/shapes and close logits after safe merge. CPU only, no download. This script is syntax-checked but **not executed**. Numerical tolerance is recorded; temperature0 does not guarantee token-identical generation across kernels.
3. **Local snapshot/tokenizer:** acquire the pinned full HF base only in a separately authorized readiness step using project credentials if needed. Record all file hashes and disk usage. Run actual tokenizer preparation on tiny synthetic400-word records with synthetic clearance; do not mislabel them real accepted history data. Check the tokenized prefix and turn terminator before proceeding.
4. **Unmodified-base export control:** use the pinned converter before training. Budget disk explicitly: base≈24GB + BF16 text GGUF≈24GB + quantized≈7.4GB + projector; later merged copies add≈24GB each. Allow approximately100–130GB free for a non-destructive full control/candidate workflow, verify actual sizes, and retain base fallback. No weights were downloaded here.

```bash
# Future commands, paths assigned in the launch record; not executed here.
python "$LLAMA_CPP/convert_hf_to_gguf.py" "$BASE" --outtype bf16 --outfile "$CONTROL/base-bf16.gguf"
python "$LLAMA_CPP/convert_hf_to_gguf.py" "$BASE" --mmproj --outtype bf16 --outfile "$CONTROL/projector.gguf"
# Converter documents an automatic mmproj- filename prefix: inspect the emitted name.
"$LLAMA_CPP/build/bin/llama-quantize" "$CONTROL/base-bf16.gguf" "$CONTROL/base-q4_k_m.gguf" Q4_K_M
python prepare.py size "$CONTROL/base-q4_k_m.gguf" "$CONTROL/ACTUAL_EMITTED_PROJECTOR_NAME.gguf"
```

The size check lists **all served files**, hashes their bytes and enforces combined≤8,000,000,000; checking GGUF magic is not a tensor/load check. Verify matching-projector tensors, tokenizer/template metadata and a real offline load with text/image synthetic inputs. Compare this control against the current Ollama registry baseline. The known registry pair is7,556,497,632bytes, but it is **not proven derived from this HF revision**. Pipeline drift must be measured separately from adapter effects. A QAT artifact is a distinct base, not an interchangeable export of this BF16 model.

## Future declared training and export

Only after compatibility/control checks and canonical data clearance, assign one host worker and a fresh manifest with absolute start/deadline, actual host/rate (or explicitly unverified rate),3600-second hard cap, maximum optimizer steps, data/config/base hashes and backup destination. Use a single-GPU `transformers.Trainer` with PEFT, not TRL/DeepSpeed/bitsandbytes for this first path. Load the full local unified conditional-generation base in BF16 with `trust_remote_code=False`, `local_files_only=True`; disable cache, enable gradient checkpointing with nonreentrant checkpointing, attach the explicit regex, assert88 modules and only LoRA tensors trainable. Use a simple tensor collator preserving prepared `labels` and zero `mm_token_type_ids`, padding input/attention/labels with0/0/-100. Do not rerender prepared data inside a trainer or allow automatic truncation/packing.

First run one declared real-model synthetic backward step, measure peak GPU allocated/reserved memory and finite loss/gradient; this belongs to runtime qualification, not a claimed history gain. Then train with the finite candidate step count and external `timeout --signal=TERM --kill-after=20s 3600 ...` plus internal monotonic deadline callback and bounded checkpoint frequency. Timeout may interrupt saving: keep earlier complete checkpoints, never promote a partial directory. Set `report_to=[]`; no external telemetry integrations. Record actual optimizer steps and elapsed time. This preparation provides no unreviewed automatic training launcher.

Save the adapter, reload the pristine BF16 base, attach the adapter and `merge_and_unload(safe_merge=True)`. Preserve full architecture/config and copy the exact tokenizer, processor, template, generation config and auxiliary metadata. Verify state-key/shape equality and unchanged non-text tensors; do not drop the multimodal components simply because training used text. Export merged text with the same pinned pipeline and its matching frozen projector; do not reuse the registry projector based only on matching dimensions. Repeat the byte gate and real offline load.

Evaluate the **deployed quantized artifact** on independent heldout topics with factual and structural grading. Required comparisons are BOTH (a) unchanged base versus candidate with the identical nonthinking essay prompt and (b) candidate versus the strongest current unchanged-base native-thinking20k route. Root reports an independently reviewed improvement for that thinking route; this is evaluation context only, never training content. Beating the weaker nonthinking/bare control alone is not promotion. The candidate is trained on nonthinking prefixes: candidate thinking-on behavior is untrained/unverified and may only be tested in a separate declared comparison, never assumed equivalent.

Route only essays to the candidate if it wins those comparisons; the base remains for other routes. Two saved copies/residency and switching latency require final runtime verification under the event rules. Dynamic GGUF LoRA/Ollama ADAPTER support is **not** a fallback claimed working here. Training loss improvement alone is not evidence of essay score gain.

## Explicit remaining blockers

- Exact H100 dependency environment, full12B attach/backward and measured memory/throughput are unqualified.
- Actual tokenizer execution, full base tensor provenance and unmodified-base export/load control remain unexecuted.
- Greg's90-row canonical export is present, but root's independent data/rights clearance remains pending; no automatic acceptance is issued by this preparation.
- Full merged Q4_K_M+projector bytes, final offline load and independent quality comparison remain required.

These blockers are finite readiness work, not a claim that Gemma Unified lacks upstream support. The old desk study's guaranteed timing,100–200-example minimum and heading-heavy target format are not adopted. Current targets are one-topic400–500-word clean prose.
