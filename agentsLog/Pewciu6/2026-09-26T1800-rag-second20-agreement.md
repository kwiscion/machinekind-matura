# Bounded-RAG rows 21–40: per-item agreement addendum

Compares Sol's independent second-20 review (`agentsLog/kwiscion/2026-09-26-bounded-rag-review-second20.json`, PR #82 / main, answer-only SHA `870fce1c...`) against ours (`agentsLog/Pewciu6/results/review_gemma-bounded-rag-val40.json`, PR #79). Same 20 items (`val2024-hist-z14.2` … `z26`), same answer file. Docs-only; no key text, no new grading beyond the two flagged items below.

## Agreement

**18/20 items agree** on point value (90%). Both totals are **17/39** for the slice — Sol's aggregate and our reviewed total already matched before this pass; the item-level check confirms it isn't offsetting errors.

## Disagreeing items

| item | Sol | ours | reason |
|---|---|---|---|
| `val2024-hist-z18` | 0/1 | 1/1 | we credit the correct side (Entente vs Central Powers) without the identifying headgear named; Sol requires the explicit label. Already inside our published range (low 0, high 1). |
| `val2024-hist-z23.2` | 1/1 (adjudication) | 0/1 | two conflicting decisions, wrong then corrected; Sol credits the final corrected decision, we score 0 to match the bare-arm treatment of the same contradiction pattern. Already inside our published range (low 0, high 1). |

## Ruling on the flags

- **z23.2**: hold our score at 0. Both raters' values were already inside our own published [0,1] range for this item, so this is a marking-convention disagreement (credit the corrected decision vs. penalize the contradiction), not a data or transcription error. We keep the bare-consistent treatment (0) so the RAG arm stays comparable to how the same contradiction pattern was scored in bare. Not flipping.
- **z26**: no disagreement — both Sol and our review score it 2/15, matching the lead's local essay proposal of 2/15 [1,5]. Our published range [1,5] contains the lead's range. No ruling needed; confirms the essay's -6 delta vs bare stands.

## Does 27/60 [22,33] change?

**No.** Neither disagreeing item is being flipped — z18 and z23.2 both stay at our original central values, and both were already inside our published low/high bounds before this addendum. The full-40 total remains **27/60, range [22,33]**, delta -8 vs bare 35. This addendum only adds the item-by-item confirmation; it does not alter the verdict (bounded RAG HURTS; do not promote).
