# Source-completeness v2 decision

26 September 2026, 15:00 Europe/Warsaw. Owner: @kwiscion, issue #3.

Preserve the original May 2024 v1 input and every original output. The question-only source audit proved that one one-point item lacks its required image, which already exists in the rendered pages. Adopt an explicitly versioned v2 input with only that image reference added. No question, prompt, answer key, output policy or denominator changes.

- V1 input SHA-256: `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`.
- V2 input SHA-256: `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`.
- Affected-only SHA-256: `85bce5d99ed077d873ee6b5ca9b8d60bfd232002c5c0a44e19be518c4adbe66e`.
- All 40 IDs and prompts preserved; the other 39 row bytes are unchanged. V2 has 30 image items and ten text items, still 60 available points.

Reproduction: run the key-free bootstrap, then `python3 -B agentsLog/kwiscion/validation-2024-keyfree/repair-v2.py --input agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.jsonl`. The repair refuses wrong input, wrong/missing image, output collisions and paths outside the private owner boundary; renderer-specific image hashes are tied to the bootstrap manifest.

The lead predeclares at most **one Qwen local request**, using the same installed `qwen3.5:9b` revision `6488c96fa5fa`, thinking off, 1024 output tokens, 420-second timeout and original config. Input is the affected-only v2 file, not a new full exam. No retries, $0 paid API cost. Record served identity, actual context, completion, latency and hashes; if runtime differs, report that limitation. Do not start while another GPU worker is running. This request is currently pending because an unexpected local Gemma worker was discovered during the concurrency check.

The resulting Qwen v2 score would reuse 39 unchanged v1 outputs and replace exactly the repaired-input item's output, regardless of whether its score rises or falls. Preserve and report v1 alongside it. Label this an **input-repaired composite**, not a fresh independent full run. Failed correction remains zero; no cherry-picked retry. It cannot by itself explain or close a broad gap to 48/60. Paweł may score v1 immediately.

15:25 extension, declared before either correction: after the full local Gemma v1 worker ends, make **one affected-item Gemma request first**, while that model is resident, with its original config (`gemma4:12b-it-q4_K_M`, thinking off, 1024 output tokens, 420-second timeout). Then make the one Qwen correction above. Total correction envelope is **two local calls / 2,048 requested output tokens / $0 paid API**, no retries or concurrent worker. Gemma uses the same affected-only v2 input and the same explicitly labeled 39-plus-one composite rule; preserve both v1 full runs. Verify served model identity and actual context before recording comparability. The final whole-candidate quality comparison must retain uncertainty and these input/runtime qualifications.

New full candidate runs use v2. A separate local Gemma v1 run started at 14:53. The 14:58 audit confirmed 13/40 nonempty final responses, all normal stops, exact model tag/response identity and actual image transport. Preserve its artifacts and do not start another local GPU worker. Piotrek's preparation can continue, but its existence supersedes the duplicate RTX baseline dispatch; #33 now waits for the next declared improvement. Output-budget, context, prompt and retrieval interventions stay separate and must be declared from the scorecard.
