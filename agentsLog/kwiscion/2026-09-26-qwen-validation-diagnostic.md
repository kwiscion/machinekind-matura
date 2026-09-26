# Local Qwen VALIDATION smoke and paired retrieval diagnostic

Date: 2026-09-26 (Europe/Warsaw)  
Owner: @kwiscion  
Scope: May 2024 History extended, formula 2023 VALIDATION subset only. These five items are not a full-exam evaluation.

## Source and input gates

- The official exam sheet and marking PDF match the pinned source-manifest SHA-256 values: `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21` and `95c275b9546611c1f8cd45b7973c436625fd0ee5643b778dcc8bb566db56cd4c`.
- The full model-facing input remains byte-identical to the frozen `runner_input.jsonl` hash `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`.
- Five no-image rows were selected: `val2024-hist-z3.1`, `z3.2`, `z7`, `z15.1`, `z15.2`. Their private subset hash is `bf699fb7a8b575ac9297d5378d21771d0b1a3b6da3ac4b73718127fcb98e1acd`. The builder also labels z13 text-only, but visual source-page inspection showed a required woodcut; it was excluded. The five selected prompts include their printed source text. Leakcheck returned 0 errors.
- The rebuilt full private key hash is `279abe703dc1af4119a35624d6db893e310fc7afaffbef2a00e678f423706486`, differing from tracked `f66e387793c5dfad2bac8723a73716e434a9d6ecab40c544f8b529723f512123`. For the five rows, extracted max-points, reference answers, and official rules matched a fresh parse of the pinned official marking PDF; current and tracked key-only sanity aggregates are identical. This supports a byte-level extraction difference, but the prior private key bytes are unavailable, so full-key byte equivalence is not claimed. An independent reviewer audited these selected rows and provisionally graded the baseline 1/5 points; z3.2 was marked borderline for human review.

## Text-only Qwen baseline

Configuration: local Ollama `qwen3.5:4b`, OpenAI-compatible `/v1/chat/completions`, `reasoning_effort=none`, `max_tokens=512`, request timeout 180 seconds. Ollama reported 3.0 GB loaded, 100% GPU, context 4096. The runner does not set context size; 4096 is the server-reported default. Five requests completed without transport errors in 52.583 seconds total; latencies were 18.752, 4.807, 11.170, 7.029, and 10.825 seconds. API usage totaled 4,762 tokens (3,280 prompt; 1,482 completion).

The private evaluator scored all five rows: 1 correct, 2 incorrect, and 2 requiring review; 1/5 points with 3/5 points as the provisional upper bound. This is a tiny diagnostic, not an exam score.

## Paired RAG arm

Retrieval used the existing frozen local index in `chrono` mode, k=5, max 400 characters per passage. Index SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429` matches index metadata and the audited contamination report. The 107-source manifest contains pinned Wikipedia CC BY-SA 4.0 and Wikisource public-domain / CC BY-SA transcription records, with no exam-source URLs. The audit used the exact frozen 40-prompt hash plus 59 retrieved excerpts and reported zero exact, substring, or threshold flags; six short-stock phrase overlaps were separately documented.

The same five rows and unchanged Qwen settings were run once. Private RAG input SHA-256: `a222edad3d8e9413be730454b2c40d146b02571cd6c0efd19efcf477e56d0e3d`. Five attempts took 63.295 seconds total; one row (z3.2) returned no complete final answer at exactly 512 completion tokens and was not retried. Total API usage was 9,702 tokens (7,644 prompt; 2,058 completion). The other four attempts had complete outputs. Ollama again reported 100% GPU and 3.0 GB loaded.

The private evaluator scored 4/5 rows; the incomplete output was excluded from its lenient score. Those four scoreable rows received 1.0/4 points, with 4.0/4 as the maximum pending review; one citation locator was missing. For the planned end-to-end five-item comparison, the incomplete response counts as zero: RAG is 1.0/5 points (strict points rate 0.20), matching the baseline 1.0/5. Three complete RAG answers remain for review; completion was 4/5, and the one incomplete z3.2 output is not retried. This is a tiny diagnostic, not a model-selection result. The private leakcheck reported one warning: a gold-answer string for z15.1 appears in a retrieved general-history passage and was absent from the original prompt. This is a permitted historical-fact overlap from the pre-frozen, provenance-checked corpus, not exam-derived material; the warning and retrieval source IDs remain in the private audit trace.

## Reproduction pointers

Private inputs, raw outputs, traces, corpus excerpts, normalized outputs, subset keys, and scorecards are under `agentsLog/Pewciu6/private/validation_2024/`; no key text, exam prompts, source excerpts, or model answers are included in this report. Local config: ignored `outputs/local-smoke/qwen-validation.config.json`.

Baseline command:

```sh
python3 infer.py --config outputs/local-smoke/qwen-validation.config.json \
  --input agentsLog/Pewciu6/private/validation_2024/runner_input.diagnostic5.jsonl \
  --output agentsLog/Pewciu6/private/validation_2024/qwen-diagnostic5-raw.jsonl --max-calls 5
```

RAG preparation and inference used `scripts/prepare_rag.py` with the pinned index/graph, `--mode chrono --k 5 --max-chars-per-hit 400`, followed once by the same `infer.py` settings on `runner_input.diagnostic5-rag.jsonl`. No downloads, training, paid calls, SEALED_TEST material, or model retries were used.


## Second candidate: Qwen 3.5 9B (same no-RAG subset)

The installed tag `qwen3.5:9b` was verified as 9.7B parameters, Q4_K_M, Ollama model ID `6488c96fa5fa`. Its local manifest and all 3 layers + config blobs are present (6,594,474,711 bytes total); no download occurred. The prior 4B model was unloaded before this run. Inference used the identical five rows and settings (reasoning effort none, max 512 output tokens, 180-second per-request timeout). The model used 6.3 GB according to `ollama ps`, with 20% CPU / 80% GPU and context 4096.

Five attempts completed in 177.142 seconds, with API-reported usage of 4,667 tokens (3,280 prompt; 1,387 completion). Three outputs were complete; z3.2 and z15.2 reached exactly 512 completion tokens without a complete final answer. Neither was retried. Independent review graded the fixed five-item denominator at 1/5, with three complete responses and two incomplete responses counted as zero (complete-answer subtotal 1/3). Item outcomes were z3.1=0, z3.2=incomplete, z7=0, z15.1=1, z15.2=incomplete; two operational failures need review. No exam-wide conclusion follows from this sample.

Raw and normalized outputs are private at `agentsLog/Pewciu6/private/validation_2024/qwen35-9b-diagnostic5-raw.jsonl` and `qwen35-9b-diagnostic5-normalized.jsonl`. Local run config is ignored at `outputs/local-smoke/qwen35-9b-validation.config.json`.


## Independent RAG review and output-channel check

An independent reviewer assigned the RAG arm 1/5 points on the fixed denominator, with 4/5 complete (z3.2 incomplete counted zero). See [the public aggregate audit](2026-09-26-rag-validation-audit.md); per-item rationale stays private. The RAG arm did not improve the aggregate score in this five-item sample.

For Qwen 3.5 9B, all five raw responses exposed only `message.content` and `message.role`; none had separate `reasoning`/`thinking` fields, explicit think markers, or reasoning-token usage metadata. The two incomplete responses had `finish_reason=length`, exactly 512 completion tokens, and 1,747/1,509 content characters. The runner sent `reasoning_effort=none`; the local Ollama OpenAI-compatible adapter documents this as thinking disabled. These records show truncation of returned final-channel text, not a distinct surfaced reasoning channel; they do not establish whether the longer final content was unnecessarily verbose.
