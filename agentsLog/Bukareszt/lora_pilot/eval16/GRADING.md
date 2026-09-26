# eval16 blinded grading: one fast pass

**Input:** `blind/pack.jsonl` (sha256 posted before grading). It holds 16 prompts, each with essays under random labels X/Y. Do not open `SEALED-key.json`, `answers-*.jsonl` or the server logs until your grades are committed.

**Rubric:** @ljaniec's frozen checklist `agentsLog/ljaniec/eval16/checklist.md` (sha256 `27eb5cbe2b324039cfe61dded4563e84d0ec6f17c10325dc7d4bb015b14e8447`), grading procedure in its `README.md`. The checklist anchors are evidence aids, not gold essays.

For each essay:
1. **Topic:** identify the chosen topic. If the essay mixes both topics, record `mixed` and grade only its dominant topic.
2. **Required aspects:** score each explicitly required aspect **0 / 1 / 3 / 4** (absent / superficial / satisfactory / rich).
3. **Factual errors:** list distinct verified false claims, each with a correction. Deduct 1 for 1–2 errors, 2 for 3–5, 3 for more than 5, once, from the aspect subtotal (floor 0). Verify a claim before penalizing it; vagueness is not an error.
4. **Coherence:** 0–2, using the existing calibration. Under 300 body words gives 0.
5. **Deterministic flags:** already computed in the pack (`word_count`, `in_400_500`, `preamble_or_meta_opening`, `mentions_both_topics`, `markdown_or_list`, `truncated`). Report them; do not re-score them into the aspect points.
6. **Preference:** X, Y or tie. Say whether the preference is `argument` (thesis, causal reasoning, use of evidence) or `facts`, and give a margin of `clear` or `close`.

Output one JSON line per input to `grades-pass1.jsonl`:
`{"id", "grader", "X": {"topic", "aspects": {...}, "errors": [...], "coherence", "total"}, "Y": {...}, "preference", "basis", "margin", "notes"}`

**Second pass, only where it matters:** use a different grader, and only for inputs where the pass-1 totals differ by 1 point or less, the margin is `close`, or a factual error is disputed. Keep both passes.

**Unblinding:** after the grades are committed, open the key (its sha256 was posted in advance) and report:
- per-arm totals and wins/ties/losses;
- error counts;
- deterministic-flag counts.

There is **no promotion from this alone**: a candidate also needs the nonessay/image/full40 regression checks.
