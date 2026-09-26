# Final overnight handoff: @Pewciu6 evaluation work

Written 2026-09-26 07:45 Europe/Warsaw (05:45 UTC) by @Pewciu6 (Claude Code, Orca worker). Docs-only handoff; no new experiments. Full index: [`README.md`](README.md).

**Status: everything shipped is provisional infrastructure + audits. No model has been scored yet.**

## What exists

- **CPU eval harness** ([#8](https://github.com/kwiscion/machinekind-matura/pull/8), [#10](https://github.com/kwiscion/machinekind-matura/pull/10)): stdlib-only `matura_harness.py` — scoring, citation audit, blind essay review, leak checking. 40-item / 60-point May 2024 VALIDATION set built and hashed (`f66e3877…` keys, `f4df6bcb…` prompts), rebuildable from CKE PDFs. Only 18/60 points are fully automatic; 29/40 items are image-dependent.
- **Hardening** ([#16](https://github.com/kwiscion/machinekind-matura/pull/16), issue [#11](https://github.com/kwiscion/machinekind-matura/issues/11)): 67-case adversarial suite found and fixed 16 harness bugs (0 remain); real `infer.py`/normalizer adapter shape is ingested and drift-tested; blind two-rater mechanism validated (κ up to 0.99 weighted) on synthetic essays.
- **Contamination audits** (issue [#13](https://github.com/kwiscion/machinekind-matura/issues/13), closed via [#14](https://github.com/kwiscion/machinekind-matura/pull/14); training-data extension in [#19](https://github.com/kwiscion/machinekind-matura/pull/19)/[#20](https://github.com/kwiscion/machinekind-matura/pull/20)): the #6 retrieval corpus and PR #18's training data (@przemeknowak781) are both **clean** — 0 flagged units at any point, positive controls fully discriminative. A handful of single-fact overlaps (names/dates) are noted as optional exclusions, never required.

## What's blocking

**Issue #11 stays open.** The harness and the 40-item VALIDATION runner input are ready, but **no model outputs exist yet anywhere in the repo.** Nothing here is a model score — only rubric sanity (oracle/shotgun/null) and contamination checks.

## Exact command for when outputs arrive

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024
python3 $H/matura_harness.py leakcheck --inputs $P/runner_input.jsonl --keys $P/eval_keys.jsonl
python3 $H/matura_harness.py score --split VALIDATION --outputs <run>_outputs.jsonl --keys $P/eval_keys.jsonl \
  --run-id <run> --scorecard agentsLog/Pewciu6/results/<run>_scorecard.json --items-out $P/<run>_items.jsonl
python3 $H/matura_harness.py audit-sample --items $P/<run>_items.jsonl --keys $P/eval_keys.jsonl \
  --outputs <run>_outputs.jsonl --n 20 --out $P/<run>_audit_sheet.jsonl
python3 $H/matura_harness.py audit-summary --sheet $P/<run>_audit_sheet.jsonl --out $P/<run>_audit_summary.json
```

## Rights and limits (short version)

CKE PDFs are `unknown`-licensed, reference-only, kept in git-ignored `private/`; keys never leave that isolation. All contamination signals are lexical only — a warning signal, not proof of absence. SEALED_TEST (May 2025) was never opened. No purchases, no paid API calls; the LM Studio smoke test used a free local model on synthetic prompts only.

## Full detail

See [`README.md`](README.md) for the artifact inventory, exact commands, hashes, denominators/measurements, and bug list; see the five timestamped notes in this directory for method-level detail on each audit.
