# Strict saved-candidate selector (prepared, not executed)

This follow-up isolates selection from rewriting. Reuse the four exact terminal drafts from the completed branching wave; retain the full original question, sources/images, and every complete candidate. Generic coverage and factual-reliability criteria ask for one candidate ID. The deterministic exporter writes that saved answer byte-for-byte into the original template. No model-generated rewritten essay can enter the final.

CPU commands:

```powershell
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/essay-branching-prep -p test_selector_id.py -v
python -B -X utf8 agentsLog/kwiscion/essay-branching-prep/selector_id.py prepare --stage1 PRIVATE_COMPLETED_STAGE1 --answers EXACT_SAVED_ANSWERS --answer-sha256 EXACT_SHA --output FRESH_PRIVATE_SOURCE
python -B -X utf8 agentsLog/kwiscion/final-package-prep/prepare_recovery_package.py --exam-dir FRESH_PRIVATE_SOURCE/exam --output FRESH_PRIVATE_RUNTIME --no-essay --cache FRESH_OWNED_CACHE --binary PINNED_BINARY --lock SHARED_HOST_LOCK --minutes 60
python -B -X utf8 agentsLog/kwiscion/essay-branching-prep/selector_id.py export --source FRESH_PRIVATE_SOURCE --selected-answers EXACT_TERMINAL_SELECTOR_JSON --answer-sha256 EXACT_SHA --output FRESH_FINAL_JSON
```

Four focused CPU tests pass: complete question/source/image/candidate preservation and exact selected export; malformed, unknown, extra-key and duplicate-key decisions retain exact direct control. Complete candidates over6,000 characters fail preparation; they are never silently excerpted. A received selector intermediate is not a submitted essay.

Proposal: one primary slot, up to4 attempts /147,456 requested-output tokens, existing60-minute recovery profile, absolute deadline no later than07:40Warsaw. No new draft generation, weights, grader hints, preferred topic or key facts. It must run after the current coverage pair has quiesced, under a fresh declaration and shared lock. This document does not authorize execution.

The unmodified recovery CLI handles transport/length failures. It does not know this candidate-ID schema: malformed final choices are rejected by the deterministic exporter and fall back to the preserved control, rather than falsely claiming a semantic recovery. All raw choice attempts and exact saved candidates remain private evidence. Retrospective oracle comparison uses already frozen draft grades; only a new rewritten answer would require grading, which this route forbids.

Parser revision: one optionalJSON code fence around exactly one strict object is accepted. The original strict-parser run and fallback remain frozen; its same-response CPU replay is separately labelled in2026-09-27-essay-selector-id-result.md. No inference or grading was repeated. Generic future integration must carry candidate statuses and exclude partial/placeholder candidates; this experiment verified all four complete.
