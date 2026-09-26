# przemeknowak781 — grounded training data (issue #4)

- Issue: https://github.com/kwiscion/machinekind-matura/issues/4
- Branch: `issue-4-przemeknowak781-data`
- Work window: 2026-09-26 00:05–03:45 UTC (02:05–05:45 Europe/Warsaw)
- Split used: TRAIN only. No 2023/2024/2025 exam questions, keys, rubrics or source packs were opened or used.

## Use this
| File | Content |
| --- | --- |
| `data/przemeknowak781/train_strict.jsonl` | **211 strictly verified TRAIN records** (canonical schema, `audit` filled) |
| `data/przemeknowak781/sft/closed_book_{train,holdout}.jsonl` | Chat format (`messages`): system, question, answer. 199 train / 12 holdout |
| `data/przemeknowak781/sft/grounded_{train,holdout}.jsonl` | Same, with the record's claims plus 2 distractor passages from other topics in the user turn (RAG-style) |

The holdout is chosen by `source_group_id`, so no topic is in both parts. It is only an overfitting check for LoRA runs, not an exam split.

`train.jsonl` (231 records, Haiku-verified) is superseded; keep it only for provenance.

| Era | n | Task type | n |
| --- | --- | --- | --- |
| medieval | 50 | essay_plan | 57 |
| early_modern | 72 | chronology | 58 |
| 19th_century | 31 | short_answer | 49 |
| 20th_century | 58 | source_analysis | 47 |

89 of 100 source articles are cited. All 211 records pass `validate.py` against the pinned revisions.

## How a record gets into train_strict.jsonl
1. **Sources**: `fetch_sources.py` fetches 100 plwiki articles (medieval → 1989) by pinned `oldid`, splits them into sections into git-ignored `cache/`, and records SHA-256 of the extracted text. Reruns reuse oldids from `sources.jsonl` (98/98 hashes identical on re-fetch) and skip disambiguation pages.
2. **Generation**: `claude-haiku-4-5` subagents (`prompts/haiku_gen_v1.md`, `haiku_gen_v2.md`) wrote short-answer, chronology, source-analysis and essay items; `claude-opus-5-5` wrote 60 essay plans (`prompts/essay_gen_v1.md`) over the 30 largest articles balanced by era; 20 items were written by hand from the pinned text.
3. **Deterministic gate** (`validate.py`): schema and enums, known source ids, every claim a verbatim substring of the pinned revision (after Unicode, dash, quote and whitespace normalisation), every year in the answer inside a claim, no exact or near-duplicate prompts.
4. **Strict dual-lens verification** (`prompts/verify_strict_v2.md`, `strict_rounds.py`). Two independent `claude-opus-5-5` judges per record: Lens S (every fact in the cited claims, no added interpretation) and Lens Q (standalone prompt, complete and fluent answer, correct task type). A failing record gets one repair (`prompts/repair_v2.md`: prompt and answer only, claims fixed), is gated again, and is judged by fresh judges.
   - Round 1, 231 Haiku-era records: 24 passed both lenses; 169 repaired; 37 dropped. Calibration: the hand-written items passed Lens S 7/20 (real catches, e.g. facts from the article but not in the cited claim, plus complaints that a claim fragment did not name its subject), so Amendment 2.1 lets the cited article title fix the subject, nothing else, from round B.
   - Round B, 229 candidates (169 repairs + 60 essays): 120 passed; 96 repaired; 13 dropped. The essays scored Lens Q 57/60 but Lens S 0/55: the generator used facts from the article that were not in its cited claims.
   - Round C, 96 repairs, no further repair: 74 passed; missing verdicts were re-requested (none were needed).
5. **Context audit** (`prompts/context_audit_v1.md`): all 218 accepted records were re-read against the full article paragraphs around each claim, since earlier judges saw only the claims. 8 flagged; an independent agent confirmed 7 and refuted 1. Confirmed defects included a disputed coronation date presented as settled, AK strength figures the article labels uncertain, and a troop count attributed to the wrong force. Those 7 were excluded, leaving 211.

Every verdict, repair, and audit finding is in `strict/` (`r1_*`, `rB_*`, `rC_*`, `rD_context_*`), and counts are in `strict/summary.json`. The earlier Haiku-only pipeline (`verification.py`, `prompts/verify_v1.md`, `repair_v1.md`) is kept for provenance.

## Quality evidence
| Set | Strict spot check (Opus, random) |
| --- | --- |
| Haiku-verified `train.jsonl` | 12/20 ([audit_sample.md](audit_sample.md)) |
| `train_strict.jsonl` | 10/10 (seed 29) |

Kept from the 20 hand-written items: 18/20. The spot checks are provisional; no human review has been done.

## Reproduce
```bash
python scripts/przemeknowak781/fetch_sources.py
python scripts/przemeknowak781/validate.py data/przemeknowak781/train_strict.jsonl
python scripts/przemeknowak781/export_sft.py
```
Python 3.12 standard library only. The LLM steps are subagent and workflow runs driven by the prompt files, so they are not bit-reproducible; raw generator outputs are in `data/przemeknowak781/generated/`.

## Cost
- Haiku generation and first verification: about 2.8M subagent tokens.
- Strict verification, essays, and context audit: about 10.2M `claude-opus-5-5` subagent tokens.
- No purchases and no paid API keys. A local `qwen/qwen3.8-27b` (LM Studio) was tried as a verifier and dropped: about 3 tok/s with thinking not disabled.

## Rights
Wikipedia text is CC BY-SA 4.0. Records hold short attributed claims with section locators and revision URLs, and raw article text is not committed. The SFT files contain answers derived from BY-SA text; before any public upload, the lead should confirm that share-alike terms are acceptable.

## Limits
- All verifiers are Anthropic models; there is no cross-family or human check.
- Answers stay close to the source wording. That suits the grounded variant; the closed-book variant may teach an encyclopedic register.
- 211 examples teach format and grounding behaviour, not broad knowledge; facts should come from retrieval (#6).
- 19th century is the smallest era (31); 11 of 100 sources have no example.
- The deterministic gate checks years only; days, months, and names rely on the judges.
