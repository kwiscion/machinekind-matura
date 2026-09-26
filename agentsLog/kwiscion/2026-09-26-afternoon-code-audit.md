# Afternoon code audit — 26 September 2026

Scope: read-only review of the dirty source-alias repair and unfinished HF bundle builder at HEAD `bcfcca6`; local CPU checks only. No implementation, commit, merge, publication, inference, training, or data rewrite. This report is the only retained audit output.

## Result

The source-alias correction is implemented and passes focused checks. The frozen 24 eligible records and their pinned review evidence remain intact. The corrected default export is **23 train / 1 internal holdout**, with no shared source IDs or source-group IDs. The repair remains uncommitted, and no corrected SFT export directory is present. No training benefit or model readiness follows from this small data check.

- `scripts/przemeknowak781/strict_eligibility.py:26` gathers both listed and evidence source IDs. The connected-component union at line 37 joins shared groups and sources transitively; its canonical key is independent of row order.
- `scripts/przemeknowak781/export_sft.py:38` uses that assignment for both export variants and restricts distractor pools to each partition. Lines 79–82 check context group/source partition membership.
- `scripts/przemeknowak781/strict_eligibility.py:105` retains the pinned hash checks and exact reviewed-record reconstruction; line 129 continues to reject changed records or legacy labels.
- The real November/January uprising alias component stays together. Only `pn781-train-0013` changes partition, from holdout to train. The one holdout is `pn781-hk-10-010` (`grp-bitwa-pod-wiedniem-1683`). There are 21 components from 23 group IDs; train/holdout contain 21/1 distinct source IDs, with zero overlap.

## Incomplete work

The local HF builder is not usable and is outside the active no-publication course:

1. `agentsLog/kwiscion/hf-release-2026-09-26/build_bundle.py:35` still asserts 22/2 and now raises `AssertionError` before writing anything. Its summary at lines 67–74 and 82 also describes the old split and overlap.
2. At line 47 it passes `sources.jsonl` to `strict.read_rows`, which requires `id`; source records have `source_id`. Isolated reproduction returns `KeyError: 'id'`.
3. At line 62 it reads `DATASET_CARD.md`, which is absent. No `bundle` directory exists.
4. `README.md:20` still describes 22/2 and a correction in progress. This accurately signals unfinished integration but does not describe the tested dirty code's 23/1 behavior.

For later integration, retain the frozen input and commit/review the narrow repair with its updated split evidence. Treat the single-record internal holdout as an overfitting smoke check only. Component assignment is computed from the supplied rows, so separately exporting different subsets is not guaranteed to preserve the full-set partition; use one frozen full-set export for any later comparison.

## Verification

- `python -B -m unittest discover -s scripts/przemeknowak781 -p test_export_sft.py -v`: **7 passed** (0.368 s), covering the real strict set, adversarial/transitive aliases, old 197-record leakage regression, mutated records/verdicts, and refusal before writes.
- `python -B scripts/przemeknowak781/strict_eligibility.py --check`: **24 strict dual-pass, provisional**, successful.
- 50 independent input-order shuffles preserve all component keys.
- In-memory export: closed-book and grounded each 23/1; source overlap empty. Source manifest contains no duplicate exact URLs.
- Strict input SHA-256 after the repository's LF text normalization: `8b56ed72061e183fd8dd3839841f701ad6fc1b9fcfbd2193678669cf79282186`.
- `git diff --check`: passed (only a line-ending warning for AGENTS.md). No dirty tracked data, review snapshots, or prompt evidence files.
- HF builder run fails at the expected stale assertion; confirmed no bundle was created.

These checks establish export isolation and preserved eligibility, not a new semantic/source audit. The active model decision still requires the full May 2024 validation scorecard.
