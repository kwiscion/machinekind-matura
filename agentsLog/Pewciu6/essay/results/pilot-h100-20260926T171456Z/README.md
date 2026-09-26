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
- **Correction (2026-09-26, per the lead's [#80 comment 5848302160](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848302160)):** an earlier version said bare essays are under 300 words. That blanket claim was wrong: the reviewed H100 bare essay had 338 body words and still scored only 4/15 provisionally, because of weak argument and factual errors. All four pilot essays are ≥300 words with a thesis, three labelled aspects, a conclusion and no preamble, but **length and structure do not fix the content failure**. The lead's independent review ([#80 comment 5848377158](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848377158)) found a major factual error in each pilot essay's political centerpiece and no plan→write gain (17/40 vs 17/40 on a diagnostic /20 rubric).
- Single-pass gave slightly more dates and named facts than plan→write at the same caps.
- Both still start with a literal "Temat nr 1" line, which is harmless but could be stripped.
- Caveat: the usage fields in the write-stage output mirror the single-stage values. That looks like an accounting quirk to check, and it doesn't affect answers or ledger bounds.
- Factual correctness has not been checked. Independent graders (not us) must judge quality before any promotion.

Files: `answers.{single,write}.jsonl` (checked exact final answers, public per #108), `report.*.json/md`, `run_summary.json`. Raw provider outputs, plans and prompts stay private, with a local backup.
