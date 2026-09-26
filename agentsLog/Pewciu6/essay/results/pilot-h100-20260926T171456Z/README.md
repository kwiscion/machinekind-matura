# Essay pilot pilot-h100-20260926T171456Z (issue #80). Development pilot, NOT a validation score

The inputs are our own original DEV fixtures (dev-essay-001 Kazimierz III Wielki, dev-essay-002 Potop szwedzki); no exam material was used. Run on Brev matura-pawel (H100, Ollama 0.34.4, gemma4:12b-it-q4_K_M, think:false, num_ctx 32768, temperature not sent) with the bounded launcher `essay_pilot_run.py`: 6/6 calls complete, 0 failures, no retries, well under the 1800 s deadline.

Two modes were compared. Deterministic essay_report shows (no grading):

| id | mode | words | ≥300 | thesis | 3 aspects | conclusion | distinct years | named terms |
|---|---|---|---|---|---|---|---|---|
| dev-essay-001 | single | 381 | yes | yes | 3 | yes | 4 | 14 |
| dev-essay-002 | single | 380 | yes | yes | 3 | yes | 4 | 14 |
| dev-essay-001 | plan→write | 360 | yes | yes | 3 | yes | 2 | 13 |
| dev-essay-002 | plan→write | 336 | yes | yes | 3 | yes | 3 | 8 |

**Observations (n=2, not evidence of a score gain):**
- Both routes remove the baseline failure modes we measured on VALIDATION: bare Gemma's essay was under 300 words (criterion B = 0), with weak aspects and a preamble. Here all four essays are ≥300 words, with a thesis, three labelled aspects, a conclusion and no preamble.
- Single-pass gave slightly more dates and named facts than plan→write at the same caps.
- Both still start with a literal "Temat nr 1" line, which is harmless but could be stripped.
- Caveat: the usage fields in the write-stage output mirror the single-stage values. That looks like an accounting quirk to check, and it doesn't affect answers or ledger bounds.
- Factual correctness has not been checked. Independent graders (not us) must judge quality before any promotion.

Files: `answers.{single,write}.jsonl` (checked exact final answers, public per #108), `report.*.json/md`, `run_summary.json`. Raw provider outputs, plans and prompts stay private, with a local backup.
