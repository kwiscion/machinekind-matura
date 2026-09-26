# #80 paired native-thinking wave: K-think vs K-nothink (DEVELOPMENT), 2026-09-26 19:02–19:22Z

Authorization: https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848780385 · launch record:
https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848989193 · pre-launch cleaner fix: PR #124.
**DEVELOPMENT grading on our own original DEV fixtures. Not a VALIDATION score or promotion evidence.**

## Setup

- `gemma4:12b-it-q4_K_M` (digest `4eb23ef1…b05c`), Ollama 0.34.4, Brev `matura-pawel` H100. Sequential calls, `num_ctx` 32768 (loaded
  `context_length` checked after every call: 32768 on 24/24), temperature not sent, service config untouched.
- Six fixtures frozen before any call, all topic 1, two per era: medieval 007, 006; early modern 011, 002; 1795+ 012, 008.
  Rule: lowest sha256(`issue80-think-v1|id`) within each era.
- **T K-think**: `think:true`, 20480 total generation tokens per call. **N K-nothink**: `think:false`, 4096 per call.
- Two stages per item and arm. Stage 1 is the contract-v2 draft with no evidence. Stage 2 is ONE grounded review-and-rewrite
  over the same frozen #6 BM25 excerpts (4–5 per item, identical to C3's) and returns `{uwagi, topic_id, body}`.
  Nothing else was sent.

## Ledger (enforced; `ledger.json`)

**24/24 calls, 294,912/294,912 requested tokens, 0 retries, 0 smokes, 0 truncations** (`done_reason=stop` on all 24).
Wall time was 19:02:25–19:21:37Z against the 20:01:57Z deadline. At the unverified 3.28 USD/h planning proxy, the run took
≈20 min ≈ 1.1 USD. This is not a bill.

| arm | native eval_count per call (thinking+final, as reported) | mean s/call | thinking chars |
|---|---|---:|---|
| T draft | 16741, 5754, 12600, 5897, 8138, 6833 (max 82% of cap) | 93.5 | 17k–39k |
| T review | 5085, 6029, 10471, 4780, 12949, 4103 | 73.2 | 11k–33k |
| N draft | 834–928 | 10.1 | 0 |
| N review | 1135–1252 | 13.4 | 0 |

No thinking/final token split is derived. Thinking text stays private and is never part of an answer.

## Mechanical contract (v2)

- All 12 drafts passed the hard contract.
- T finals: 6/6. **N finals: 3/6 FAILED as invalid JSON.** Two had unescaped ASCII quotes inside `body` and one had an escaped
  closing quote. The v2 rules allow no repair, so they are failures and score 0 in the denominator.
- Three answers kept a literal `\n` escape (N-draft 002, T-draft/final 008). This is a new cleaner gap, noted below.

## Blind grading (3 fresh Opus graders, 7 shuffled essays each, CKE A/12 + B/3, every factual claim listed and checked)

All 6 items per arm are in the denominator; a failed final scores 0.

| slot | mean /15 (n=6) | mean A /12 | mean B /3 | factual errors | claims checked / incorrect |
|---|---:|---:|---:|---:|---|
| **T-draft** | **7.00** | 4.50 | 2.50 | **4** | 44 / 4 |
| **T-final** | **7.67** | 4.83 | 2.83 | 4 | 54 / 4 |
| N-draft | 4.50 | 2.00 | 2.50 | 14 | 51 / 16 |
| N-final | 3.33 (3 failed) | 2.00 | 1.33 | 5 (on 3 graded) | 26 / 6 |

Paired per topic, total /15 (factual errors in parentheses):

| item | T-draft | T-final | N-draft | N-final |
|---|---|---|---|---|
| 002 potop | 5 (3) | 5 (1) | 5 (2) | 8 (0) |
| 006 Chrobry | 10 (0) | 13 (0) | 3 (4) | fail |
| 007 Zakon 1409–66 | 6 (0) | 5 (1) | 3 (4) | 3 (4) |
| 008 zabory 1864–1905 | 5 (0) | 7 (1) | 3 (3) | fail |
| 011 upadek RON | 7 (0) | 9 (0) | 6 (0) | 9 (1) |
| 012 wojna 1920 | 9 (1) | 7 (1) | 7 (1) | fail |

## Findings

1. **Native thinking is the lever, mainly through facts.** Drafts: T wins 5/6 against N and ties 1. The mean is 7.00 vs 4.50, and
   factual errors fall from 14 to 4 (incorrect claims 16/51 → 4/44). Finals: T wins 4/6, ties 1 and loses 1. With N's 3 JSON failures
   the mean is 7.67 vs 3.33; on the 3 N finals that were graded, the paired totals are 19 (T) vs 20 (N).
2. **The review stage is not a reliable gain.** T draft→final is +0.67 mean: 3 up, 2 down, 1 flat, and the error total is unchanged
   at 4→4. It fixed errors on 002 (3→1) but ADDED a new error on 007 (0→1) and 008 (0→1). For N, it fixed 002 (2→0) and 011, left
   007's 4 errors in place, and broke the JSON on 3/6.
3. **Still prominent: length-only expansion introduced a factual error** (contract probe k1, PR #119). This wave again shows that a
   rewrite adds claims, and new claims bring new errors (007, 008). A rewrite is not a fact check.
4. The C3 7.42 vs 4.00 result remains a DEVELOPMENT result, not an established gain. Graders disagreed on its size (lead note
   2026-09-26 18:54Z).

## Limits

- n = 6 topics, one sample per arm, one grader per essay. Grader severity differed: the part means were 7.29, 6.71 and 5.29, and
  slots were randomly spread across graders.
- `format_score` is noisy: one grader docked the `Temat nr N` render line that the answer sheet requires.
- T's thinking uses up to 82% of the 20480 cap, so a smaller cap risks truncation.
- DEV fixtures only; no validation item.

## Next pivot (proposed; needs a new bounded declaration)

- **K-think as the default drafting mode** (think:true, cap 20480), with structured output via Ollama `format` (JSON schema) or a
  plain-text body and no JSON. This fixes the quote-escaping failure without an extra call. A cleaner fix for literal `\n` goes with it
  (CPU).
- Replace the rewrite-style review with a **claim-level verify-only stage**: list the claims, check them against the excerpts,
  delete or correct only the wrong ones, and add no new facts. A second independent grader per essay would give tighter comparisons.

## Files

`answers.jsonl` holds, per item and arm, the rendered draft/final answers, raw content, pre- and post-cleanup text, the review's
`uwagi`, contract triggers/advisory and native counts (no thinking text). Also `ledger.json`, `manifest.json` (frozen bundle
minus evidence text and prompts; chunk ids and hashes kept), `grades_part{1,2,3}.json`, `grading_key.json` and `aggregate.json`.
The private dir and `~/matura-backups/think-h100-20260926/` hold prompts, evidence text, raw provider output including thinking,
and the rubric.
Code: `scripts/Pewciu6/essay_think_run.py`, `essay_think_export.py`, `test_essay_think_run.py` (17 tests).
