# przemeknowak781 — grounded training data (issue #4)

- Issue: https://github.com/kwiscion/machinekind-matura/issues/4
- Branch: `issue-4-przemeknowak781-data`
- Split used: TRAIN only. No 2023/2024/2025 exam questions, keys, rubrics or source packs were opened or used.

## Export eligibility (lead repair, extended to rounds B, C and the context audit)

`data/przemeknowak781/train_strict.jsonl` is the only default training input: **211 records**, reconstructed by `strict_eligibility.py` from committed verdicts only, with no new model judgment. A record is eligible only if both lenses are explicitly true in its round and the full-article context audit has no confirmed defect. The set is provisional and not human-verified.

| Round | Input | Accepted |
| --- | --- | --- |
| r1 | 231 legacy records, committed `r1_S`/`r1_Q` | 24 (23 after context audit) |
| rB | 169 round-1 repairs + 60 essay plans, exactly as judged (`payload_rB`) | 120 (118) |
| rC | 96 round-B repairs, exactly as judged (`payload_rC`) | 74 (70) |
| rD | context audit over the 218 accepted records (`payload_rD`); 8 flagged, 7 confirmed by an independent agent | excludes 7 |

`strict_provenance.json` pins every input by SHA-256 of UTF-8/LF-normalized text: `train.jsonl`, all verdict, repair and audit files, the 10 essay files, the three judged payload snapshots, and the four rubrics. Reconstruction checks that each judged payload equals the rebuilt record text (prompt, answer, task type, era, claims and locators), so a verdict cannot be reused for altered text even when a hash is re-pinned. The original round-1 pins are unchanged, and the lead's 24-record reconstruction is still reproduced; one of those 24 is excluded by the context audit. The exporter refuses legacy, altered or missing inputs and never overwrites existing export files.

Grounded distractors are sampled only from the destination source-group partition, and exports include `context_source_group_ids`. Current split: 199 train / 12 internal holdout per variant, with 0 train rows citing a holdout group. General historical facts can appear independently in both groups; this is source-group isolation, not a promise that every fact is unique across splits.

```bash
python scripts/przemeknowak781/strict_eligibility.py --check
python -m unittest discover -s scripts/przemeknowak781 -p 'test_*.py' -v
python scripts/przemeknowak781/export_sft.py --output-dir data/przemeknowak781/cache/sft-reviewed
```

The tests are the lead's 6, with the expected counts updated from 24 to 211, plus 3 new ones: round counts and context exclusions; r1 as the lead's reconstruction minus one defect; and refusal of a repair whose text differs from the judged payload. `data/przemeknowak781/sft/` holds the export from the lead's exporter; the earlier export from commit 9b77039 leaked holdout passages into training context and was replaced. The verbatim-source gate (`validate.py`, which needs the local article cache) is inherited evidence and is not rerun in CI.

| Era | n | Task type | n |
| --- | --- | --- | --- |
| medieval | 50 | essay_plan | 57 |
| early_modern | 72 | chronology | 58 |
| 19th_century | 31 | short_answer | 49 |
| 20th_century | 58 | source_analysis | 47 |

89 of 100 source articles are cited.

## How the records were produced and judged
1. **Sources**: `fetch_sources.py` fetches 100 plwiki articles (medieval → 1989) by pinned `oldid` into git-ignored `cache/`, with SHA-256 of the extracted text. Reruns reuse oldids from `sources.jsonl` (98/98 hashes identical on re-fetch) and skip disambiguation pages.
2. **Generation**: `claude-haiku-4-5` subagents (`prompts/haiku_gen_v1.md`, `haiku_gen_v2.md`); 60 essay plans by `claude-opus-5-5` (`prompts/essay_gen_v1.md`, 2 per source over the 30 largest articles, balanced by era); 20 items written by hand.
3. **Deterministic gate** (`validate.py`): schema and enums, verbatim claims in the pinned revision after normalisation, every answer year inside a claim, no exact or near-duplicate prompts.
4. **Strict dual-lens verification** (`prompts/verify_strict_v2.md`, orchestrated with `strict_rounds.py`): two independent `claude-opus-5-5` judges per record, Lens S (evidence support) and Lens Q (exam quality), one repair per failure (`prompts/repair_v2.md`, claims fixed), then fresh judges. Calibration: the hand-written items passed Lens S 7/20 in round 1; several failures only objected that a claim fragment did not name its subject, so Amendment 2.1 lets the cited article title fix the subject, nothing else, from round B. The essays scored Lens Q 57/60 but Lens S 0/55 in round B (facts from the article outside the cited claims) and entered only after repair.
5. **Context audit** (`prompts/context_audit_v1.md`): all 218 accepted records re-read against the full article paragraphs; confirmed defects included a disputed coronation date stated as settled, AK strength figures the article calls uncertain, and a troop count attributed to the wrong force.

## Quality evidence (provisional)
| Set | Strict spot check (Opus, random) |
| --- | --- |
| Haiku-verified legacy `train.jsonl` | 12/20 ([audit_sample.md](audit_sample.md)) |
| `train_strict.jsonl` | 10/10 (seed 29) |

18 of the 20 hand-written items survived. No human review has been done.

## Legacy artifacts (preserved, not export-eligible)
`train.jsonl` (231 records; Haiku `verify_v1` labels), `generated/`, `verification.py` and the v1 prompts are kept for provenance and research. Their old `verified` labels do not make a record eligible.

## Cost
- Haiku: about 2.8M subagent tokens.
- `claude-opus-5-5` strict verification, essays and context audit: about 10.2M subagent tokens.
- No purchases and no paid API keys. A local `qwen/qwen3.8-27b` (LM Studio) was tried as a verifier and dropped: about 3 tok/s with thinking not disabled.

## Rights
Wikipedia text is CC BY-SA 4.0. Records hold short attributed claims with section locators and revision URLs; raw article text is not committed. The SFT files contain answers derived from BY-SA text, so the lead should confirm that share-alike terms are acceptable before any public upload.

## Limits
- All verifiers are Anthropic models; there is no cross-family or human check.
- Answers stay close to the source wording: good for the grounded variant, possibly an encyclopedic register for the closed-book variant.
- 211 examples teach format and grounding behaviour, not broad knowledge; facts should come from retrieval (#6).
- 19th century is the smallest era (31); 11 of 100 sources have no example.
- The deterministic gate checks years only; days, months and names rely on the judges.
