# Independent PR 18 repair review

Reviewed [PR #18](https://github.com/kwiscion/machinekind-matura/pull/18) at exact head `fd4bfaeb64c785d06940fb58a303649ffa5649ac`, against original `c5009a5e4cddfb35b11a75b74bfe61a669ea44bb`. Downloaded only the relevant repository snapshot paths into ignored `agentsLog/kwiscion/private/data-repair-review/`; no root checkout/ref changes, source fetching, inference, or 2025 access.

## Verdict

The repair resolves the reviewed default-export eligibility and cross-partition context defects. Ready for the lead's merge decision as a scoped repair; it does not complete the data-volume target or qualify a model.

- The default now reads `train_strict.jsonl`, reconstructed from pinned original records plus both committed round-1 passing verdicts. It contains 24 provisional dual-pass records. Exact reviewed subsets are allowed explicitly; legacy `audit.status=verified` alone is insufficient. Modified answers with passing IDs and changed evidence snapshots are rejected.
- The four exports contain 22 train / 2 holdout records per variant. Grounded train has 21 source groups; holdout has 2; overlap is zero. Independent inspection confirmed every context source-group ID stays within its export partition, including distractors.
- Original `train.jsonl` still has 231 records. The comparison changes no original train/generated/draft file. Legacy labels remain attributable in `legacy_audit`; historical evidence is preserved.
- The 200-record target remains unmet. Strict membership reconstructs prior provisional judgments, not fresh source/semantic verification. No round-B pending work is silently promoted.

## Checks

Run from the isolated exact snapshot:

```text
python scripts/przemeknowak781/strict_eligibility.py --check
strict_dual_pass=24, provisional=true

python -m unittest discover -s scripts/przemeknowak781 -p 'test_*.py' -v
6 tests passed

python scripts/przemeknowak781/export_sft.py --output-dir data/przemeknowak781/cache/review-export
closed_book_train=22; closed_book_holdout=2; grounded_train=22; grounded_holdout=2
```

The tests include the formerly leaking legacy 197-record split, missing strict artifact, legacy override rejection, changed answers, and changed verdict hashes. An additional direct read of all exported records confirmed disjoint IDs/groups and context provenance membership.

Export SHA-256 values:

| File | SHA-256 |
| --- | --- |
| closed_book_train.jsonl | `7deb700a2916d379e3d9e41d5268490f85c2b2fa5b00014b28422442053bdb5a` |
| closed_book_holdout.jsonl | `a64c91c10180de355c84753951b265b0ca837370852ed3a589526f4fcf73048b` |
| grounded_train.jsonl | `415db0f6a9ab31f37a21a9d18300f6b5267c1c8b9ca9b23f71c4a14f0a41bdf4` |
| grounded_holdout.jsonl | `85208b651bebe6c49a6fb5c43f40f560c2c7b61066625fdb9461f00528ea48eb` |

GitHub head was rechecked immediately before review: still `fd4bfaeb...`. Python stdlib and both strict-data check runs report SUCCESS. The PR is attached to the Codex task. A positive scoped review comment is submitted rather than self-approval through the shared GitHub account; this worker did not merge.
