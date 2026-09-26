# RTX 5090: Gemma load and full May 2024 validation

Owner: @semberecki. Parent: #3. Scoring: @Pewciu6 on #11. This is the active scope for #33 and supersedes its earlier hardware/ownership instructions.

The owner confirms Piotrek's local **RTX 5090** is available and his GitHub watcher is active. **The two Blackwells are unavailable** and must not be used or disturbed. Record the actual GPU/VRAM from the machine rather than assuming a capacity. Start this task now; no additional owner approval is needed within these limits.

## Claim and first milestone

Claim #33 once with your session, start time and ETA; switch ready to in-progress. Branch: `issue-33-semberecki-gemma-5090`. Use Sol for implementation/review and Luna for bounded checks. One active inference worker only. Logs/configs/scripts belong under your owner paths. Aim for a working text + image load within 45 minutes of claim and the whole validation output within two hours. Report a precise blocker after 30 minutes of unsuccessful environment work instead of spending the afternoon on setup.

**Piotrek now owns both Gemma preparation and its one full validation arm.** @ljaniec: hand over your pinned recipe and existing evidence; stop further Spark/CPU Gemma preparation, downloads and probes for this assignment, preserving files. The lead's Qwen 3.5 9B 40-item run is already active with images. Do not repeat any part of it.

## 1. Load one compliant Gemma candidate

Use one route supported by the installed runtime:

- Existing compatible Ollama: native `gemma4:12b-it-q4_K_M`, model plus BF16 projector **7,556,497,632 bytes**, as verified in PR #36. Runtime and exact hashes are in `agentsLog/ljaniec/2026-09-26-gemma-spark-load.md`.
- Otherwise use the pinned Google QAT Q4_0 GGUF plus its matching projector from `scripts/ljaniec/model_candidates.json` and the PR #34 handoff. Reported combined size **7,150,994,912 bytes**; verify actual bytes/hashes after download.

Declare the chosen route in the claim. Do not combine quantizations, projectors or hashes, or download both routes speculatively. Check installed runtime compatibility and actual served model identity. Each model must stay below 8,000,000,000 saved inference-weight bytes including the projector.

Run at most four self-authored smoke calls, covering Polish text and an actual simple image. Thinking must be disabled, final content nonempty, and finish reason complete. Verify the image affects the answer. Record GPU placement, effective context size, memory and latency. Use sufficient context for prompt + image tokens + output; do not silently truncate inputs. Prefer 16k context when supported and it fits; record differences from the laptop's 4k configuration honestly.

## 2. Run the frozen validation once

Use existing `infer.py`, `reasoning_effort: none`, `max_output_tokens: 1024`, and `--max-calls 40`. Maximum per-request timeout: 600 seconds. Freeze settings before running; no prompt tuning based on answers, automatic retries, RAG, training or second baseline copy.

Model input is the existing May 2024 history set: **40 items / 60 points**, SHA-256 `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`, with its referenced page PNGs. The lead is preparing a key-free reproduction script so you can fetch only the public question PDF and regenerate this exact input without receiving answer keys. Start model setup immediately; use that script when linked. Do not run the key-dependent builder in your model process or substitute a new question set. Missing assets/hash mismatch stop only the validation step and must be reported here.

Initial envelope: **44 local calls total**, at most 1024 output tokens each, no retries; **45,056 maximum requested output tokens, $0 paid API budget**. Keep failed/truncated records and the fixed denominator. No purchases or external inference APIs. Record actual token/runtime usage.

```bash
python3 infer.py --config agentsLog/semberecki/private/gemma4-config.json --input agentsLog/semberecki/private/validation_2024/runner_input.jsonl --output agentsLog/semberecki/private/gemma4-validation-raw.jsonl --max-calls 40
python3 scripts/normalize_outputs.py --input agentsLog/semberecki/private/gemma4-validation-raw.jsonl --output agentsLog/semberecki/private/gemma4-validation-model.jsonl
```

Adjust only paths and the real local endpoint/model ID. Outputs must be new files. Preserve all input/image hashes and exact model/template configuration. Raw exam questions, answers, PDFs and keys remain in ignored private directories, never in public issues or commits. Coordinate a private raw-output handoff with @Pewciu6; publish only safe aggregates, hashes and a delivery status. A path on your own machine is not itself a completed transfer.

## 3. Deliver a candidate, then stop at the scorecard

PR your owned scripts/configs, model manifest, commands and aggregate completion/runtime report. Success requires actual text and image responses plus the full output file, not download progress or transport success alone. The lead and Paweł select from full scored results. The organizer submission adapter is a separate task; do not build a second harness.

No fine-tuning or expert models until the scorecard identifies a useful intervention and the lead assigns it. No HF publication, May 2025 access, unrelated-project credentials, service termination, or reset credits. Final freeze: Sunday 27 September at 11:00 Europe/Warsaw.
