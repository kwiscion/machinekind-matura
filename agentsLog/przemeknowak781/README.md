# przemeknowak781 — grounded training data (issue #4)

- Issue: https://github.com/kwiscion/machinekind-matura/issues/4
- Branch: `issue-4-przemeknowak781-data`
- Started: 2026-09-26 00:05 UTC (02:05 Europe/Warsaw)
- Split used: TRAIN only. No 2023/2024/2025 exam questions, keys, rubrics or source packs were opened or used.

## Artifacts
| Path | Content |
| --- | --- |
| `data/przemeknowak781/topics.txt` | 101 plwiki topics, medieval → 1989; 7 pinned to explicit oldids |
| `data/przemeknowak781/sources.jsonl` | Source manifest: pinned `oldid`, SHA-256 of extracted text, CC BY-SA 4.0, `allowed_use: [reference, train]` |
| `data/przemeknowak781/examples.jsonl` | 20 hand-grounded TRAIN examples (first slice) |
| `scripts/przemeknowak781/fetch_sources.py` | Fetches pinned revisions via MediaWiki API, splits into sections into git-ignored `cache/` |
| `scripts/przemeknowak781/validate.py` | Deterministic gate: schema, verbatim evidence in pinned revision, every year in the answer present in evidence, exact/near duplicate prompts |

## Reproduce
```bash
python scripts/przemeknowak781/fetch_sources.py
python scripts/przemeknowak781/validate.py
```
Python 3.12 standard library only. Raw article text stays in `data/przemeknowak781/cache/` and is not committed; public records contain only short evidence claims with locators.

## First slice (20 examples)
Written by `claude-opus-5-5` directly from pinned revisions (`provenance: synthetic`, `prompt_revision: manual-grounded-v1`).

| Era | n | Task type | n |
| --- | --- | --- | --- |
| medieval | 3 | short_answer | 10 |
| early_modern | 9 | chronology | 5 |
| 19th_century | 5 | essay_plan | 3 |
| 20th_century | 3 | source_analysis | 2 |

Gate result: 20/20 pass (all evidence claims occur verbatim in the pinned revision; no duplicates). Negative check: an answer with a wrong year (1411) and a fabricated quote (wrong day) are both rejected.

Status: **draft**. Every `audit.status` is `pending` until an independent semantic check runs (planned: Haiku on all items, local Qwen `qwen/qwen3.8-27b` via LM Studio on a sample, agreement reported). The gate only checks years; a wrong day or name with a correct year is left to the semantic check.

## Rights
Wikipedia text is CC BY-SA 4.0. Records store short attributed claims plus revision URLs. Before any public dataset upload, confirm with the lead whether BY-SA share-alike terms are acceptable for the derived dataset.

## Next
Generate ~250–300 examples from the 101 sources (Haiku subagents), gate them, run the semantic verification, audit a sample, report counts and failures.
