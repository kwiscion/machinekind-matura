# Organizer package to offline answers.json — Greg

Owner: @Bukareszt. Parent: #3. Integration review: @kwiscion. Scoring contract review: @Pewciu6 on #11. This is the next active task for Greg; #6/#15 stay closed and their retrieval artifacts remain unchanged.

The evaluator exists. The lead's full May 2024 Qwen run is active but has no full score yet. Your highest-value independent contribution now is the organizer submission adapter, not another retriever or grading framework.

Authoritative guide, read before implementation: https://matura-json-guide.ania-olchowik.chatgpt.site/ . It describes a mock **May 2023** package (37 items, 60 points, 19 PNGs). This is DEV/format compatibility, separate from the frozen May 2024 selection set. The final exam is not released and will have its own ID/template. Do not access May 2025.

## Claim and owned scope

Claim once with session/start/ETA and change ready to in-progress. Use `issue-<number>-Bukareszt-submission-adapter`, scripts under `scripts/Bukareszt/`, reports under `agentsLog/Bukareszt/`. First vertical slice within 45 minutes; PR within 90 minutes. Sol implementation/review and Luna bounded fixture/schema checks are appropriate. Do not change shared infer.py, evaluator, source splits, existing retrieval or promoted configuration; wrap them through their public interfaces. No GPU inference is needed for this task.

## Required vertical slice

Provide a small Python CLI and one documented command sequence that:

1. Reads a local unpacked `exam.json`, `answers-template.json`, and referenced images. Retains `exam_id` and every string item ID exactly. Validates template/input ID agreement, duplicate IDs, required fields, PNG existence and published image SHA-256. Resolve image paths relative to the exam folder. Do not fetch URLs during inference.
2. Writes our canonical `{id,prompt,images}` JSONL, supplying exam-wide `instructions`, each complete `question`, `source_text`, and `answer_format`. Format examples are syntax, not solutions. Include actual image paths for infer.py to load, not just filenames in text. Do not reorder/omit source material to fit a guessed context window.
3. Invokes or documents the existing `infer.py` path with a supplied verified model config; keep its full raw records separately. A convenience wrapper may compose these steps, but must not introduce a second inference implementation or another model worker.
4. Converts final model answers into the included template, producing UTF-8 `answers.json`. Top-level fields must be exactly `exam_id` and `answers`; each entry exactly `id` and `answer`. Every answer is a string. IDs appear exactly once; the complete template is retained. Missing, failed, empty, malformed or incomplete model output becomes an empty answer with a separate local failure report. Unknown/duplicate output IDs or mismatched exam IDs are errors. Do not put reasoning channels, logs, usage, scores, provenance or extra metadata into the submission JSON. Preserve complete essay text; do not truncate silently.
5. Validates the final encoded file: at most **1 MiB**, at most **100,000 characters per answer**, valid JSON, string fields, exact template IDs and no extra fields. Return a nonzero status on invalid output; keep diagnostics outside the answer file. The official mock essay is item26 with chosen topic number and at least300words, but do not hardcode those identifiers/requirements into a generic final-exam schema: retain the actual question's instructions.

The final command must run against a local package and local/self-hosted allowed model without internet knowledge or external AI APIs. Downloads are a separate preparation step. Use the organizer's template for each package; do not hardcode the mock ID, item count or points into production behavior.

## Public mock acquisition and checks

The guide's app.js publishes these real endpoints:

- `https://matura-json-guide.ania-olchowik.chatgpt.site/exam/exam.json`
- `https://matura-json-guide.ania-olchowik.chatgpt.site/exam/answers-template.json`
- Images at `/exam/` plus each image's relative `path`.
- The ZIP download concatenates `exam-pack-1.bin` then `exam-pack-2.bin` into `history-2023-mock-v1.zip`; preserve binary bytes and order if using this path.

Store real mock questions/images/templates/output only in ignored `private/` or `outputs/`, not public commits. Publish a downloader plus URLs/hashes and an aggregate acquisition manifest, not exam contents. Follow normal access and verify checksums; no access bypasses. Use your own tiny invented text/image fixtures in public tests.

Acceptance evidence: prepare/dry-run the real mock and confirm37items,60points,19uniqueimagefiles and template agreement; finalize an explicitly synthetic mock-output fixture without claiming a model score. Useful regression tests cover missing/duplicate/unknown IDs, non-string answers, Unicode, malformed/truncated responses, bad image hashes and byte/character limits. Confirm all required source text/images survive preparation. No fake accuracy claims from fixture output.

Deliver CLI help, exact offline commands, tests/results, package/schema hash, runtime, preserved failure examples and limitations in the PR. @Pewciu6 reviews format/scoring boundary only; the existing evaluator is not replaced.

Submission is a later lead step: organizers will provide a separate submission link; it takes team code, solution name and ONLY answers.json, then returns a receipt. This issue does not submit, register a team or expose a team code. Expected LLM grading cadence is approximately30minutes, not guaranteed. Format acceptance is not a correctness score.

No purchases, paid inference, training, HF publication, private-key handling, or changes to #33 model ownership. Final freeze remains Sunday27September11:00Warsaw.
