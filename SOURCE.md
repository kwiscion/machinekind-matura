# Sources, rights, and split boundaries

The working subject is Polish history. Record the exact exam title, year, formula, issuing body, publication URL, download time, document revision or file hash, and license or permission for every exam and historical source. A public URL is not proof that its content may be redistributed. Keep acquisition scripts and manifests public where possible; publish only content whose rights permit the intended use. Do a copyright and attribution scan before any public dataset upload. Never commit secrets, private API responses, or unlicensed scans/transcriptions.

Made during the Warsaw Model Trainers hackathon, Kolektyw3, 25–27.09.2026

## Owner sharing decision — 26 September, 19:10

Our code, original prompts and fixtures, model answers, item-level grades, error analyses and negative findings may be shared publicly without a separate approval or competitive-secrecy gate. The owner explicitly prioritizes rapid collaboration. Preserve exact answers and provenance. This does not grant redistribution rights to third-party exam/source packs or official keys, and credentials remain private. The fixed evaluation/training boundaries below are unchanged. Prefer useful compact artifacts; incidental private/copyrighted material inside raw envelopes can be omitted without withholding our findings.
## Fixed evaluation split

| Split | Exam | Overnight access | Allowed use |
| --- | --- | --- | --- |
| DEV | May 2023, history, formula 2023 | Already viewed | Development diagnostics and evaluation only |
| VALIDATION | May 2024, history, formula 2023 | Any owner may use official answers in an isolated evaluator; keys stay in evaluation artifacts | Overnight selection and scoring, never training or retrieval content |
| SEALED_TEST | May 2025, history, formula 2023 | Do not read questions, answers, rubrics, or source packs until lead's morning release | One lead-controlled final check after decision freeze |

Training examples may derive from pre-2023 historical exams/informators and independently sourced reference material, subject to rights review. Exclude DEV/VALIDATION/SEALED_TEST question-derived examples, model-generated paraphrases of those items, their answer keys, rubrics, and direct copies of exam source packs from training and retrieval. Group same source pack and its paraphrases under one `source_group_id` before splitting or deduplication. Hash normalized question text and record near-duplicate checks; a hash match is a warning, not a complete contamination audit. General historical facts from independently licensed sources may be retrieved, even if relevant to an exam topic. Do not claim any exam is novel to pretrained weights.

For each acquired source, store a manifest record with `source_id`, `url`, `title`, `publisher`, `retrieved_at`, `revision_or_sha256`, `license`, `allowed_use`, and `local_path` when retained. For web pages, use a revision/date or archived link where possible. For images/OCR, retain path references and rights metadata; do not embed third-party images in public JSONL without permission. Closed-model output must be labeled as synthetic with model/provider and generation date, then checked against cited evidence by a separate audit. An assistant's claimed citation does not establish source support.

The lead owns public uploads to `kwiscion/matura` and any private model repository. Workers can prepare `candidates/<handle>/<run>/` bundles for review; local artifacts and PRs are sufficient overnight. Do not share personal credentials. No blanket MIT license applies to third-party data. A proposed MIT license for original code requires owner approval before adding a license file.
