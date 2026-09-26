# Audit sample — provisional

Auditor: `claude-opus-5-5` (different model from the generator and the verifier, both `claude-haiku-4-5`). Date: 2026-09-26. Strict standard: every fact in the answer must be stated in the cited verbatim claims, and the prompt must be answerable on its own. Human review not done.

## Verified items: 20 random (seed 11, ids in `cache/audit_sample_ids.json`, round 1+2, manual slice excluded)
Strictly supported and usable: **12/20**. Not fully supported or low quality: 8/20.

| id | Problem |
| --- | --- |
| pn781-hk-02-003 | "Siemomysł was Mieszko I's predecessor" is not in the claim (true historically, unsupported here) |
| pn781-hk-04-014 | Interpretation (centralisation, armed resistance) beyond the claims |
| pn781-hk-04-016 | Names Nicholas I; the claim does not |
| pn781-hk-06-019 | Adds a second NKN founder and "w Galicji" beyond the claim |
| pn781-hk-08-020 | "Germanisation intensified" not in the claim |
| pn781-hk-09-012 | Prompt has no question; "największy triumf" unsupported |
| pn781-hk-09-014 | Garbled prompt; "likwidacja Konstytucji" unsupported |
| pn781-hk-10-021 | Context-free prompt ("Kto dowodził wojskami polskimi?") |

No sampled item states something historically false; the failure mode is unsupported embellishment plus poorly formed prompts. The Haiku verifier accepts added context and interpretation more readily than this standard allows.

## Drafts: all 34 adjudicated
The Haiku verifier's `minor`/`unsupported` calls were correct in 33/34. Disagreement: `pn781-hk-08-011` (liberum veto) is fully supported; the verifier penalised a correct omission.

## Corrected hallucinations caught by the pipeline (examples)
- Deterministic gate: wrong year, fabricated or paraphrased quotes (38 of 293 generated records failed the gate across both rounds).
- Verifier: `pn781-hk-02-021` added deportation to Siberia to a claim about language restrictions; `pn781-hk-06-014` changed November 1790 to December; `pn781-hk-09-001` invented an order of two titles held simultaneously.

## Other defects
- 2 verified records contain stray non-Latin characters (e.g. Devanagari inside Polish text).
- 28 verified prompts are under 40 characters; several lack context (clustered in batches 09 and 10).
- Two Haiku generators misreported their own results (claimed missing cache; typo in a source id). All counts here come from `validate.py` and `verification.py`, not from agent summaries.
- Three topics resolved to disambiguation pages; `fetch_sources.py` now skips those, and no example used them.

## Estimate
With 12/20 strict precision (small sample, wide uncertainty), about 60% of the 197 Haiku-verified items would meet the strict standard (~120), versus 20/20 for the hand-grounded slice.
