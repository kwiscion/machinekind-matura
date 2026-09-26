# Frozen validation source-completeness audit

26 September 2026. Read-only, question-only review supporting the winning plan. No model calls, official keys, May 2025 access, input changes or publication of exam content.

Visual inspection of all 11 text-labelled items found **one required visual omitted from its image array**, exposing one available point to missing-input risk. The correct page asset already exists. This is not a proven lost point or a promised gain. The remaining ten items retain required source material; one has a minor loss of printed statement numbering while preserving all ordered statements. The 29 image-labelled items were outside this bounded visual review.

The lexical image heuristic caused the omission. A successful check that all referenced images exist does not establish that all required images were referenced. Input v1 therefore has a known source-completeness limitation that must accompany its score; it does not meet the winning plan's complete-source condition without qualification.

The full Qwen snapshot contains 40 results: **36 complete and four output-length failures**, all exactly at the 1,024-token ceiling. No recorded context or transport error was found. The config does not set context explicitly; earlier observations recorded 4,096. Maximum prompt usage was 3,208 and maximum actual prompt-plus-completion usage was 3,840. Two requests had insufficient theoretical room for the full requested output budget at that context, but both completed normally. Input truncation is unproven; the four length stops are direct evidence of the output ceiling.

**Proposed next action, not executed:** preserve v1 and declare a separately hashed source-completeness v2 containing only the missing image reference. Keep IDs, order, prompt strings and all prior outputs intact. The resulting distribution would be 30 image-labelled and ten text-labelled rows, still 40 items and 60 available points. Any v2 run is a new named arm; do not silently patch or mix baseline answers. Choose separate budget/context interventions from the independent loss table. The missing visual alone cannot explain a broad gap to 48/60.

Private item evidence, asset references, page review table, exact failure IDs and reproducible metadata are in `agentsLog/kwiscion/private/source-completeness-20260926/audit.md` and `metadata.json`. These files and page renders are Git-ignored.

Evidence hashes:

- Frozen input v1: `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`.
- Full raw results: `e9e47bb59f154e1b5ec6cbb861dd865f5817284bbb4ca694314bb9aaab15bf0f`.
- Question PDF: `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`.
