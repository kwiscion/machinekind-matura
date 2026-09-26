# przemeknowak781 — grounded training data (issue #4)

- Issue: https://github.com/kwiscion/machinekind-matura/issues/4
- Branch: `issue-4-przemeknowak781-data`
- Work window: 2026-09-26 00:05–01:45 UTC (02:05–03:45 Europe/Warsaw)
- Split used: TRAIN only. No 2023/2024/2025 exam questions, keys, rubrics or source packs were opened or used.

## Result
`data/przemeknowak781/train.jsonl`: 231 TRAIN records, all passing the deterministic gate against pinned revisions.

| audit.status | n | Meaning |
| --- | --- | --- |
| verified | 197 | Gate passed and a fresh-context Haiku verifier judged the answer `supported` (rubric `verify_v1`) |
| draft | 34 | Verifier found an unsupported fragment; kept for review, not for training |
| (rejected, excluded) | 38 | Verifier judged `unsupported` |

Verified by era: medieval 40, early_modern 74, 19th_century 28, 20th_century 55. By task: short_answer 62, chronology 62, source_analysis 59, essay_plan 14.

**Read the audit before training on this set.** In a strict provisional audit ([audit_sample.md](audit_sample.md)), 12/20 random Haiku-verified items met the strict standard; the rest add context or interpretation beyond the cited claims, or have poorly formed prompts. The 20 hand-grounded items (`pn781-train-*`) passed 20/20. Recommended next step: a stricter second verification (e.g. Sonnet) before any training use.

## Strict re-verification (in progress, 2026-09-26 ~02:00–03:00 UTC)
Rubric `prompts/verify_strict_v2.md`: two independent judges per record (`claude-opus-5-5`), Lens S (every fact in the claims, no added interpretation) and Lens Q (standalone prompt, complete fluent answer, correct task type). Failures go to one repair pass (`prompts/repair_v2.md`, prompt and answer only, claims fixed), are re-gated with `validate.py`, and are re-judged by fresh judges. Orchestrated with `strict_rounds.py`; raw verdicts and repairs are in `strict/`.

- Round 1, all 231 records: 24 passed both lenses (Lens S 63/230, Lens Q 65/231). 169 were repaired and passed the gate, 1 repair failed the gate, 37 were dropped. Calibration: the 20 hand-grounded items passed Lens S 7/20 and Lens Q 18/20. Several Lens S failures were real (facts from the article but not in the cited claim); others only objected that a claim fragment did not name its subject. Amendment 2.1 therefore lets the cited article title establish the subject, and nothing else, from round B on.
- New: 60 essay plans (`prompts/essay_gen_v1.md`, 2 per source over the 30 largest articles balanced by era), all passing the gate; raw output is in `generated/essay-*.jsonl`.
- Round B: 229 candidates (169 repaired + 60 essays) are being judged.
- `export_sft.py` writes chat-format LoRA files (closed-book and grounded with distractor passages, topic-disjoint holdout); it runs after the strict set is final.

## Pipeline
1. `fetch_sources.py` — 100 plwiki articles (medieval → 1989) fetched by pinned `oldid` through the MediaWiki API, split into sections into git-ignored `cache/`. Reruns reuse oldids from `sources.jsonl` (checked: 98/98 re-extracted texts had identical SHA-256). Disambiguation pages are skipped.
2. `make_batches.py` — per-agent batches of trimmed sections (lead first, ≤6,000 chars per source).
3. Generation: `claude-haiku-4-5` subagents following `prompts/haiku_gen_v1.md` (round 1, 10 batches) and `haiku_gen_v2.md` (round 2, the 20 sources with no verified item). Each `claim` must be a verbatim substring of the pinned revision.
4. `validate.py` — deterministic gate: schema/enums, source ids, verbatim claims after Unicode/dash/quote/whitespace normalisation, every year in the answer present in a claim, exact and near-duplicate prompts. Negative test: a wrong year and a fabricated quote are rejected.
5. `verification.py` — fresh-context Haiku verifiers apply `prompts/verify_v1.md`; `minor` items get one repair pass (`prompts/repair_v1.md`) by a different Haiku agent, then re-gating and re-verification; `apply` writes `train.jsonl` with `audit` fields.

## Reproduce
```bash
python scripts/przemeknowak781/fetch_sources.py
python scripts/przemeknowak781/validate.py data/przemeknowak781/train.jsonl
```
Python 3.12 standard library only. The LLM steps are subagent runs driven by the prompt files, so they are not bit-reproducible; `data/przemeknowak781/generated/` keeps the raw generator outputs (including items that failed the gate).

## Cost
About 2.8M Haiku subagent tokens in total (generation ~2.0M, verification and repair ~0.8M), plus the orchestrating session. No purchases and no paid API keys. A local `qwen/qwen3.8-27b` (LM Studio) was tried as a verifier and dropped: about 3 tok/s with thinking not disabled.

## Rights
Wikipedia text is CC BY-SA 4.0. Records hold short attributed claims with section locators and revision URLs; raw article text is not committed. Before any public dataset upload, the lead should confirm that BY-SA share-alike terms are acceptable for the derived dataset.

## Limits
- Haiku verifying Haiku output is weaker than cross-family verification; see the audit estimate above.
- `essay_plan` is under-represented (14 verified).
- Source coverage is uneven; one round-1 agent concentrated examples on a few sources.
- The deterministic gate checks years only; wrong days, months or names with a correct year rely on the verifier.
