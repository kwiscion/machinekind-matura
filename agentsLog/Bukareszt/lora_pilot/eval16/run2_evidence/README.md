# #117 eval16 paired wave (eval16-run2): terminal, ALL STAGES PASS, with a candidate serving failure

**Wave:** start 00:09:56Z, deadline 01:09:46Z. Terminal at 00:55:46Z, rc 0, backup verified (15 files).

**Usage:** 25 of 128 calls, and 868,352 of 4,718,592 requested tokens. Both arms used identical greedy nonthinking requests and the pinned template (normalized `6a1015c4…`).

| Arm | Artifact | complete / partial / placeholder | calls | `length` finishes | completion tokens | generation s | final body words |
|---|---|---|---|---|---|---|---|
| A control | `a192fac4…` + `9ff3ded7…` | **16 / 0 / 0** | 16 | 0 | 13,649 | 128 | 346–412 (median 383); 16 ≥ 300; 3 in 400–500 |
| B candidate | `d2c7b67a…` + `24322307…` | **2 / 2 / 12** | 9 | 5 | 165,354 | 2,563 | complete: 331 and 352; partial: 18,030 and 14,818 (repetition runs) |

**Arm B, per item:**
- **01:** attempt 1 hit the 32768-token cap, attempt 2 was complete (331 words).
- **02:** 4 attempts, 3 of them runaway (32908, 49292 and 32908 tokens). Partial.
- **03:** complete on attempt 1 (352 words).
- **04:** partial after 2 attempts.
- **05–16:** placeholders. They were **never attempted** because no attempt could fit the arm wall budget. This is the declared behaviour: no extension.

**EOG/stop configuration:** identical for both arms. llama-server logs `special_eog_ids contains '<|tool_response>', removing '</s>' token from EOG list` for both models, so there is no candidate-specific EOG difference. The runaway generations are the candidate's own repetition under greedy decoding.

**Blinding caveat:** placeholders and runaway partials identify arm B in 14 of 16 items, so only items 01 and 03 allow a meaningful masked argument comparison.

**Grading:** root/Sol does one pass under the PR166 addendum.
- Masked pack: `blind/pack.jsonl`, sha256 `90211d5487fbb499bd64373a8f40f919d907eba6a9fa01a50ba5661ccb7dc7ff`.
- Sealed key (NOT in git; on the host at `eval16-run2/blind/SEALED-key.json` and in the verified backup): sha256 `b568c54c72d823b1af03981687029131e5631a5744803b7ae137c3016de53d00`.
- The unblinded answers stay on the host until grading: `answers-A.jsonl` `17fd46e2…`, `answers-B.jsonl` `a66e025c…`.

**Answer-free metadata:** `attempt-metadata.json` (`f61aa6da…`) and `call-ledger.jsonl` (`11bdb9b5…`). Per-attempt request/response hashes, finish reasons, tokens and timing are in the ledger.

**No quality claim.** Root's CPU audit (commit 6e7ad73) found no terminator, mask or template export bug. Candidate causes it lists: 34 distinct targets repeated over 3 epochs, and an overweighted final batch. A one-epoch checkpoint comparison needs a separate declaration.
