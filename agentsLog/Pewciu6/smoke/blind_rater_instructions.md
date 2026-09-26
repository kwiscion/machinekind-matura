# Blind rater instructions (synthetic dry run, issue #11)

You rate short essays about a FICTIONAL kingdom (Ardenia). This is a synthetic rubric written
for the dry run, not the CKE marking scheme. You do not know which system wrote each essay.

Source facts (fictional): Ardenia was founded in 1234 when prince Borzysław united three
valleys. The capital became Źródłogród, not coastal Mrokowo. In 1261 King Borzysław issued the
Valley Statute, which limited the voivodes' power. In 1302 war with Mrokowo broke out; peace in 1305.

Score every packet row:
- `A` 0–12 = facts (0–4: correct use of the source facts, no invented contradictions)
  + argument (0–4: clear stance, answers the task, reasons given)
  + chronology/causation (0–4: correct order, causes and effects linked).
- `B` 0–3 coherence and language. **B = 0 if `word_count` < 300.**
- `deductions` 0–2 for off-topic or list-only answers (subtract from A+B, floor 0).
- `points` = max(0, A + B - deductions), an integer 0–15.

Fill `review.reviewer`, `review.points`, `review.criterion_points` {"A":…, "B":…,
"deductions":…}, and a one-line `review.notes`. Keep every other field unchanged.
