# Greg #117: one bounded real-base LoRA pilot

**Preparation only. Root declares launch; Greg owns the only worker.** Use the existing local pinned base/runtime; no repeat downloads or environment rebuild. The separate data-only clearance is `essay_lora_clearance_v1.json` SHA256 `9a31742306e1c37aa096ff9e16e128083b8fff8e83257658e21457f2b35921fd`. It authorizes neither training nor serving by itself.

Choose **ONE merged-model deployment candidate** for this pilot. Do not spend this wave investigating adapter switching as well. An adapter-serving pivot needs its own later bound. Preserve the pristine base and existing unmodified export as development controls; never submit both full models.

## Fixed envelope and useful stopping points

One absolute60minute window, at most$3.28 at the explicitly unverified$3.28/hour planning proxy. Start clock before the real-base probe. Maximum1 synthetic optimizer step, then **36 history optimizer steps** (90rows×3epochs, batch1/accumulation8, including each epoch's final2-row group);120 is a hard ceiling, not a target. **At most4 synthetic generation calls total**,512 output tokens each: exported-control text+image, then candidate text+image. No retries, warmups or history evaluation inside this stage. Eval16 and full-exam/all-route promotion require separate finite declarations.

| Latest stage budget | Action | Required evidence / stop behavior |
|---|---|---|
| 0–10min | Fresh real12B synthetic probe,1optimizer step | Exact88textq/v modules,5,193,728trainables, finite loss/gradient/update, nonzero parameter delta, peak allocated/reserved memory. Probe changes are discarded; no probe checkpoint enters history training. Failure stops this wave. |
| 10–20min | Load **existing unmodified export**,2synthetic calls | Same pinned converter/quantizer/template intended for candidate, one text and one original synthetic image. Record full request/response/settings/image hashes and successful stop/runtime usage. Stop if load/template/image path fails. Do not claim registry equivalence. |
| 20–45min | Fresh pristine-base history load and36steps; save adapter + BF16 merge | Independently cleared90rows only, no truncation, answer-only labels, no eval/early stopping, same candidate hyperparameters. Full state keys/shapes and multimodal tensor hashes unchanged after merge. Deadline/OOM/nonfinite failure leaves evidence but no qualified model. |
| 45–55min | Fresh candidate conversion/Q4 export,2matched synthetic calls | Fail closed on every command; never reuse stale outputs. Compare exact same text/image requests and settings to exported control. These are serving checks, not essay-quality evidence. |
| 55–60min | Aggregate inventory, backup and stop | One candidate+projector ≤8,800,000,000B. Hash all weights/configs/prompts/logs; back up locally. No automatic extra run. |

If an earlier stage uses its allowance, later stages retain the **same absolute deadline**. Never start history without enough time for its1500second cap plus export/backup reserve. If export or serving cannot finish, keep the trained adapter privately for a later declared stage; preserve the unchanged-base route. No promotion from training loss or synthetic calls.

## Existing evidence, correctly labelled

PR135 exact merge `e5a730ebe423751bfd4f632378878141c159d8a4` proves a tinyCPU synthetic optimizer/merge probe, pinned real base acquisition, and **unmodified** BF16→Q4 export7,556,499,104B including projector. It does not prove a trained merged artifact's size, real12B backward, or serving. The reported tokenizer-control90-row log is absent from that exact tree: rerun the existing `prepare.py data` below and archive its actual output. Registry quantized tensors **and template** differ from the new export; use the same new export pipeline for both control and candidate.

## Commands and frozen stage manifests

Set project-local absolute variables `REPO`, `BASE`, `RUN`, `GPU_PY`, `CONVERT_PY`, `LLAMA_SRC`, `CONTROL`, `TRAIN`, `EVAL_INPUTS`, and `CLEARANCE` to Greg's existing artifacts. Do not print credentials or host mapping. Use canonical LF training SHA `83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5` and eval SHA `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28`. Check current GPU/process ownership first.

Wrap the **whole operator script**, including serving/export, in one orchestration lock and an OS process-group deadline:

```bash
# Use a fresh RUN; no --foreground and no detached/setsid children inside the wave.
flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s 3590s bash "$RUN/operator-stages.sh"
```

`operator-stages.sh` must start with `set -euo pipefail`; propagate each failure. Keep all child workers in that process group. Clean up only servers started by this wave, after checking their captured PID/start ticks/executable. Do not stop an existing owner service or unrelated process. The stage driver additionally uses a distinct stage lock and SIGALRM, but those do not replace this external whole-process-tree bound. Record actual absolute UTC start/deadline before dispatch. Freeze `operator-stages.sh` and its manifest/code hashes for root review.

The new `run_real_pilot.py` validates without model imports by default:

```bash
"$GPU_PY" "$REPO/agentsLog/kwiscion/essay-lora-prep/run_real_pilot.py" "$RUN/probe-manifest.json"
"$GPU_PY" "$REPO/agentsLog/kwiscion/essay-lora-prep/run_real_pilot.py" "$RUN/probe-manifest.json" --execute
```

Manifest fields: `mode` (`synthetic_probe` or `history`), `status:DECLARED`, common absolute `deadline_utc`, `base`, fresh `output`, distinct `lock_file`, `base_weight_sha256`, `inference_calls:0`, exact `max_optimizer_steps`1/36 and `max_seconds`600/1500. `files` maps absolute paths to SHA256 and must pin this driver, `prepare.py`, `candidate.json`, `evidence-manifest.json`. The history manifest additionally pins `train`, `eval_inputs`, `clearance`, `synthetic_probe_report`, `control_serving_report`, with `train_records:90`. Each report file is itself hash-pinned. Probe provenance must match the same driver/base/tokenizer/candidate; history always creates a new base, LoRA and optimizer.

Before history, archive the existing full data/tokenizer gate:

```bash
"$GPU_PY" "$REPO/agentsLog/kwiscion/essay-lora-prep/prepare.py" data \
  --train "$TRAIN" --eval-inputs "$EVAL_INPUTS" --clearance "$CLEARANCE" \
  --local-base "$BASE" --output "$RUN/prepared-data"
```

The driver revalidates clearance and tokenizes the same90rows itself. It never optimizes evaluation inputs. A reviewed control-serving report must have `status:PASS`, `scope:matched_unmodified_export_text_image` and the exact control/runtime/template/quantizer/image/request/response hashes and two-call ledger; an independent owner agent verifies the predeclared criteria and freezes that evidence before history, without a new lead-approval pause inside the60minute window. Execute the history manifest with the same CLI and `--execute` only after both qualifications pass.

Use the existing pinned converter environment (Transformers96331a9f override retained), **not** PR135's non-fail-closed `export_control2.sh`:

```bash
set -euo pipefail
# Fresh paths: these commands must not reuse previous candidate output.
"$CONVERT_PY" "$LLAMA_SRC/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" \
  --outtype bf16 --outfile "$RUN/candidate-bf16.gguf"
"$CONVERT_PY" "$LLAMA_SRC/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" \
  --mmproj --outtype bf16 --outfile "$RUN/candidate-projector.gguf"
"$LLAMA_SRC/build/bin/llama-quantize" "$RUN/candidate-bf16.gguf" "$RUN/candidate-q4_k_m.gguf" Q4_K_M
"$GPU_PY" "$REPO/agentsLog/kwiscion/essay-lora-prep/prepare.py" size \
  "$RUN/candidate-q4_k_m.gguf" "$RUN/candidate-projector.gguf"
```

Freeze one original synthetic text fixture and one original synthetic image fixture **before** control calls, then reuse their exact payload/settings for candidate calls. Use the same installed serving implementation and pinned chat-template interpretation for both. Record returned text/images/model identity; no compensating prompt or template repair mid-comparison. Serving commands remain Greg's runtime-specific two-call operator script, which must receive independent review before root declares launch; this document does not invent unverified server flags.

Required terminal handoff: stage manifests/code and environment hashes; data/tokenizer proof; synthetic and history step ledgers with actual counts/loss/delta; memory; merge multimodal proof; fail-closed conversion statuses; same-pipeline control/candidate tensor/template/runtime inventory; all4call reservations/raw results; complete candidate weight inventory; actual elapsed/rate estimate; verified backup. Label the artifact **training/serving pilot**, not an independently validated essay improvement or final submission. Future16-topic evaluation and nonessay/image/full40 regression are required before any merged-model promotion.