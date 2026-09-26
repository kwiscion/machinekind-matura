# PR #60 independent review

Verdict: **PASS for CPU preparation of bare source-v2 with no policy**, using `--top-k 3 --budget-chars 1600` and the existing pinned manifest. This does not authorize inference or establish context fit or score gains.

Reviewed exact head `f6c636ce66a187c00098527e906596873dd0b4db`. The working-tree preparer and focused test file have no diff against that head. Read the implementation, dependency pin/import checks, tests, and issue57 report. No teammate files changed.

- `python -m unittest discover -s scripts/Bukareszt -p test_prepare_bounded_rag.py -v`: **18 passed**, 7.309 s. Synthetic fixtures only; no network or model calls. Existing retriever emitted nonfatal unclosed-file ResourceWarnings.
- Additional independent executable-sentinel check: a retriever with an incorrect expected hash was rejected before its top-level code could write a marker. Verified-byte import compiles the same bytes it hashes.
- Additional budget sweep: all 1,301 integer budgets from 300 through 1,600 kept the complete evidence block within the declared bound.
- Original prompt is appended unchanged; query uses only that prompt. IDs and other fields are copied. Image paths resolve to the original files and image hashes are recorded; sibling output keeps path strings unchanged.
- Index bytes, source manifest, graph content and retriever hashes are checked before retriever execution. Missing/tampered assets and answer/key fields fail closed. Output/trace collisions and existing files are refused; repository outputs must be private or ignored outputs. Socket guard blocks network during preparation.

Launch-manifest conditions: pin the actual input/config/assets and preparation trace; use bare source-v2, omit `--policy-file` and `--allow-unpinned`, and explicitly freeze the 1,600-character budget. The CLI permits other budgets, and graph/retriever expected hashes come from the trusted manifest, so preserve that manifest's hash too. Top-k 3 means three retrieved candidates, not three guaranteed included excerpts: the greedy budget can include fewer, with skipped/truncated IDs recorded. Character count is not tokenizer or multimodal context proof; retain the separate runtime usage/context stop checks. No new blockers found for this declared preparation.
