# Data and evaluation contracts

These are additive interchange formats. A local `infer.py` prototype is not yet published; every task must supply standalone scripts or a reproducible adapter. The intended model input is JSONL `id`, `prompt`, optional local `images` paths; output should retain `id`, backend/model revision, raw response, usage, latency, and error. Keep canonical records and raw outputs separate. Paths are relative to the JSONL file; public records reference assets rather than embedding third-party images.

## Source manifest (`sources.jsonl`)

One JSON object per source: `source_id`, `url`, `title`, `publisher`, `retrieved_at` (ISO 8601), `revision_or_sha256`, `license`, `allowed_use` (array such as `reference`, `train`, `redistribute`), optional `local_path`, `source_group_id`, `notes`. If rights are unknown, record `license: "unknown"` and omit restricted content from public artifacts. Preserve source revision and SHA-256 of acquired bytes when feasible.

## Canonical examples (`examples.jsonl`)

Required: `id` (stable), `subject`, `split` (`TRAIN`, `DEV`, `VALIDATION`, `SEALED_TEST`), `task_type` (e.g. `short_answer`, `chronology`, `source_analysis`, `essay_plan`, `vision_ocr`), `source_ids` (array), `source_group_id`, `prompt`, `answer`, `evidence` (array of `{source_id, locator, claim}`), `provenance` (`human`, `synthetic`, or `exam`), `rights_status` (`clear`, `restricted`, `unknown`). Optional: `images` (local paths), `era`, `topic`, `rubric_id`, `generator` (`provider`, `model`, `date`, `prompt_revision`), `audit` (`reviewer`, `status`, `notes`). A synthetic example is verified only after an independent evidence check; count drafts and verified items separately. For public distribution, keep only rights-clear content and short permitted evidence locators/claims, not copyrighted passages.

Example *training* record (illustrative, not an historical claim):

```json
{"id":"train-demo-001","subject":"history","split":"TRAIN","task_type":"chronology","source_ids":["ref-001"],"source_group_id":"group-001","prompt":"Example prompt to be replaced with a sourced question","answer":"Example answer","evidence":[{"source_id":"ref-001","locator":"section 2","claim":"Answer supported by this section"}],"provenance":"synthetic","rights_status":"clear","generator":{"provider":"local","model":"example","date":"2026-09-26","prompt_revision":"v1"},"audit":{"reviewer":"human-or-independent-model","status":"pending","notes":"Illustration only"}}
```

## Evaluation input and outputs

Build runner input as `{ "id": "...", "prompt": "...", "images": ["relative/path.png"] }`; retain split, source IDs, rubric, and expected answers in a separate restricted `eval_keys.jsonl`. Any owner may load official 2024 keys in an isolated evaluation process to score independently; keys must not enter training, generation, retrieval, model input, or a public PR. Nobody opens `SEALED_TEST` questions/answers/source packs before the lead's morning release. Do not put answer keys in model-facing input or public outputs.

Raw inference outputs stay append-only and are linked by `id` to a scorecard with `run_id`, model revision, exact saved weight bytes, quantization/template, data/index hash, split, command, timestamp, machine, latency, errors, and per-category counts. Report both denominator and exclusions. Label automatic grades and independent Sol evidence audits provisional; human review is optional at the morning decision. Keep disagreements. Citation support requires checking the cited source, not merely recognizing its title. Group source packs and paraphrases by `source_group_id` and audit near duplicates before any split-derived comparison. No claim that a fixed exam is unseen by pretrained models.

## Model and candidate manifest

Each model candidate records exact repository/revision, license, file SHA-256 and total **final served saved inference-weight bytes** (including vision/projector weights; ≤8,000,000,000 bytes unless lead clarifies units), tokenizer/chat template, quantization, adapter/base relationship, runtime, peak memory, and offline load command. List LoRA adapter bytes separately; the adapter does **not** count toward the 8 GB model-weight limit under the hackathon rule. Training precision and hardware memory may exceed 8 GB. Store review bundles under `candidates/<handle>/<run>/` locally or as a PR; public or private HF promotion is lead-owned.
