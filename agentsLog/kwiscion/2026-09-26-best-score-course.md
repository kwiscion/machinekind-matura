# Best-score course correction — 26 September, 12:45 Europe/Warsaw

Historical checkpoint, superseded by [WINNING_PLAN.md](../../WINNING_PLAN.md). The 14:27 owner target is 48/60 reviewed validation points by18:00. Piotrek has an RTX5090; Blackwells are unavailable. The full Qwen run is already active on the lead laptop. The earlier five-item result included completed-answer errors as well as truncation; it was not solely a truncation finding.

Owner decision: compete only for the highest Sunday matura score. Progress and smallest-model categories are out of scope. Binding rules are `hackathon_rules.txt`: Polish history matura, each saved model at most 8 GB, local RAG and tools allowed, offline at exam time. LoRA does not count toward the cap. Final freeze remains Sunday 27 September at 11:00 Europe/Warsaw.

This correction keeps the merged stack and points it at one working model. It does not replace the runner, the May 2024 evaluator, the chrono retrieval index, the strict data exporter, or the pinned GGUF recipes.

## What is already good enough to use

- `infer.py`, `scripts/prepare_rag.py`, and `scripts/normalize_outputs.py` are the exam path. Thinking stays off (`reasoning_effort: none`). Output budget for the next run is 1024 tokens, not 512. The cap in `docs/inference.md` is 4096.
- May 2024 validation is the selection set: 40 items, 60 points, 11 text and 29 image, frozen `runner_input.jsonl` hash `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`. Keys stay in `agentsLog/Pewciu6/private/`. Incomplete answers count as zero. Only 18/60 points are fully automatic; report that split.
- Retrieval stays `--mode chrono --title-weight 1.0 --k 5`, index SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`. Issue #15 stays closed.
- Training data stays the fail-closed 24-record export. PR #23 stays an unmerged draft. Nobody trains on it until a scored run shows factual misses.
- Installed local candidate: Ollama `qwen3.5:9b`, Q4_K_M, about 6.6 GB. Pinned but not yet run: Gemma 4 12B Q4 including the vision projector, reported 7.15–7.56 GB. The morning Gemma pull was interrupted and must be resumed or discarded, not treated as installed.
- The five-item 1/5 diagnostic stays a truncation finding. It is not a model rejection.

## Critical path

One full validation run of `qwen3.5:9b` with thinking off and 1024 output tokens, images included where the input has them. Then the same input on Gemma 4 12B Q4 once those weights are actually loaded. Same denominator. Paweł scores both. The lead freezes the higher scored model as the working candidate.

The 8 GB laptop already ran the 9B model on text. Image items and Gemma need the 24 GB GPU. One 9B validation run and one Gemma validation run, not parallel duplicates of the same arm.

After that scorecard, and only then:

- a second arm may add answer-format instructions for closed items and the essay, through the existing runner
- a paired RAG arm may use the existing chrono index
- a LoRA may start only for miss types the scorecard marks as factual, on the frozen base, with the alias-split repair done first

May 2025 stays sealed. No Hugging Face upload on this path. No specialist fleet.

## Owner moves

| Owner | Keep | Do next | Stop |
| --- | --- | --- | --- |
| @semberecki [#33](https://github.com/kwiscion/machinekind-matura/issues/33) | New GPU lane | Claim #33. First hour: nonempty Polish answers, thinking off, weights bytes, latency. Then the validation run the lead is not already running. Gemma is the second candidate. | A second copy of a run already started. Fine-tuning before the scorecard. |
| @Pewciu6 #11 | Harness, keys, 40-item input | Score the incoming raw outputs. Publish closed/open/essay, incomplete count, and auto vs manual. | New rubric features and new audits. |
| @Bukareszt | Chrono index and #6/#15 results | Rebuild that pinned index on the inference machine and hand the `prepare_rag.py` command to the candidate run. | A new selector or a larger corpus before the scorecard. |
| @przemeknowak781 #4 | Strict exporter and source pipeline | Finish the source-alias connected-component split on the existing 24 records so later training is safe. | Round-B judging, the 200-example chase, and any training run. |
| @ljaniec | Runner, byte catalog, Qwen3-8B text fallback | Resume or replace the interrupted Gemma 4 12B Q4 install and prove one nonempty multimodal load with bytes and latency. If Spark SSH is still denied, pass the recipe to @semberecki. | Another smoke-audit loop and specialist training. Qwen3-8B is the text fallback, not the best-score candidate. |
| @kwiscion #3 | Integration | Transfer the private validation input, not the keys, to the GPU machine. Compare the two scorecards and freeze one candidate. | HF publication, merging PR #23, opening May 2025. |
