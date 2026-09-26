# Audit procedures: citation support, independent item audit, blind essays, vision/OCR

Written 2026-09-26 02:25 Europe/Warsaw by @Pewciu6 (Claude Code) for issue #7. Everything here is **provisional**. Human review is optional at the morning review.

## 1. Citation-support audit (`matura_harness.py audit-citations`, also run inside `score`)

1. **Collect citations.** They come from two places:
   - an explicit `citations: [{source_id, locator, claim}]` field on the output record;
   - inline `[[source_id#locator]]` markers in `raw_response`. For these, the claim is the enclosing sentence.
2. **Resolve each citation against the licensed retrieval corpus.** The corpus is JSONL of `{source_id, locator, text}`, for example the corpus from #6. It must never contain exam source packs or keys.
   - An unknown `source_id` is `source_missing`.
   - An unknown locator is `locator_missing`.
3. **Run the lexical check.** A citation is `supported` only when both conditions hold:
   - at least 50% of the claim's content tokens appear in the passage (5-character prefix stems, to tolerate Polish inflection);
   - every year stated in the claim appears in the passage.

   Otherwise it is `unsupported`.
4. **Flag unsupported citations.** Any status other than `supported` adds `citation_unsupported`. When the key sets `requires_citation`, a missing citation counts too, and credit is capped at `citation_fail_max_points`.
5. **Human or independent check.** For each `supported` claim sampled for audit, open the cited passage and confirm it states the claim. Recognising a source's title is not support, and neither is a plausible paraphrase of general knowledge. Record the passage locator in `audit.evidence_checked`.
6. **Known blind spots.** Negation ("not in 1410") and paraphrase without shared tokens both slip through the lexical check. Claims made without years are only token-checked.

## 2. Independent item audit on VALIDATION (15–20 items)

The prerequisite is real model outputs. **None existed as of 02:25.** Only the synthetic fixtures and the oracle, wrapped, shotgun, and null sanity runs have been scored. No model score is claimed.

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024
python3 $H/matura_harness.py leakcheck --inputs $P/runner_input.jsonl --keys $P/eval_keys.jsonl   # must exit 0
# run the model on $P/runner_input.jsonl (images are relative to $P) -> <run>_outputs.jsonl
python3 $H/matura_harness.py score --split VALIDATION --outputs <run>_outputs.jsonl --keys $P/eval_keys.jsonl \
  --run-id <run> --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json --items-out $P/<run>_items.jsonl
python3 $H/matura_harness.py audit-sample --items $P/<run>_items.jsonl --keys $P/eval_keys.jsonl \
  --outputs <run>_outputs.jsonl --n 20 --out $P/<run>_audit_sheet.jsonl
# reviewer fills audit.{reviewer,points,agrees_with_auto,error_categories,evidence_checked,notes}
python3 $H/matura_harness.py audit-summary --sheet $P/<run>_audit_sheet.jsonl --out $P/<run>_audit_summary.json
```

**How to review**

- **Who.** The reviewer is independent of the model under test: a different model family or a human. The reviewer never sees the model name, because the sheet carries only the id and the response.
- **Grading.** The reviewer grades against the official CKE rule text (`official_rules`) and example answer (`reference_answer`). Each claim is checked against the exam sources in the sheet PDF, not against memory.
- **Disagreements.** All of them are kept; `audit-summary` lists them. Only aggregates (agreement counts, disagreement categories) go into public PRs. Item text stays in `private/`.
- **Sampling.** The sample prioritises `needs_review` items and image items, then round-robins across task type and status.

## 3. Blind essay-rubric slice (Zadanie 26, 0–15, plus any essay_plan items)

- **Automatic diagnostics.**
  - Under 300 words zeroes criterion B, following the CKE rule. This sets the upper bound to 12.
  - The stance/conclusion marker is diagnostic only.
  - Criterion A (narrative, 0–12) and criterion B (coherence, 0–3) are `manual_only`.
- **Blind pack.**
  ```
  matura_harness.py blind-pack --outputs <runA> --outputs <runB> --keys <keys> --out-dir $P/blind
  ```
  - `packet.jsonl` has no model, backend, revision, latency, or usage fields, and its order is shuffled.
  - `mapping.jsonl` is restricted.
- **Raters.** At least two raters each copy the packet and fill `review.points` (0–15) and `review.criterion_points` `{A, B, deductions}`.
- **Merge.** `blind-merge --reviewed r1.jsonl --reviewed r2.jsonl --mapping $P/blind/mapping.jsonl` reports per-model totals, exact agreement, and mean range. Items with a range of 3 or more points get a third rater.
- **Status.** Real essays are pending model outputs. The mechanism was exercised on 2 synthetic essays with 2 synthetic raters: exact agreement 0.0 and mean range 1.0, by construction.

## 4. Vision/OCR slice

- **Coverage.** 29 of 40 VALIDATION items reference visual material: maps, photographs, posters, caricatures, woodcuts, stamps, charts, a genealogy table, a film frame. The label comes from a keyword heuristic on the source captions, and the matching words are recorded per item in `modality_evidence`.
- **Images.** `runner_input.jsonl` attaches rendered pages (`pages/page-NN.png`, 110 dpi, 21 pages) for those items only.
- **Scoring breakdown.** The scorecard reports `by_modality` (image vs text). Items with `modality=image` that are not fully credited get the `possible_image_ocr` review flag.
- **Reviewer's job.** For each flagged item, the reviewer classifies the failure as perception (misread the image or text in it), knowledge, or reasoning. Only perception failures take the `image_ocr` category.
- **Text-only fallback.** A text-only model sees the caption text but not the image. Its image-item score measures caption-plus-knowledge performance and should be reported separately.

## Rubric sanity evidence (VALIDATION keys, no model)

These runs are from `sanity_validation_2024.py`. The aggregates are in `results/validation_2024_sanity.json`.

| Run | Items | Auto points | Gate+manual upper bound | Manual upper bound |
| --- | --- | --- | --- | --- |
| Oracle (official answers) | 39 (the essay is excluded; it has no example answer) | 18/18 | 14/14 | 13/13 |
| Oracle wrapped in a sentence | 39 | 18/18 | 14/14 | 13/13 |
| Shotgun (hedges every option) | 40 | 0/18 (upper bound 11, routed to review) | 0/14 | 25/28 |
| Null (empty) | 40 | 0 | 0 | 0 |

Two bugs were found and fixed before publishing:
- bracketed optional parts in the official answers (for example, a synthetic "Kazimierz [III] Wielki") did not match;
- hedged decisions ("Tak / Nie") and hedged true/false answers ("1 P F") earned credit.
