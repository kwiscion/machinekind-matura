# Generic organizer Qwen preparation

This additive wrapper uses the existing organizer adapter, source-preserving recovery preparer and reviewed closed Qwen profile. It accepts arbitrary package IDs/counts and explicit essay IDs; it contains no benchmark selection. Preparation does not authorize execution or establish model promotion.

```powershell
python -X utf8 agentsLog/kwiscion/qwen-thinking-prep/prepare_qwen_exam.py --exam-dir PRIVATE_ORGANIZER_PACKAGE --output agentsLog/kwiscion/private/FRESH_QWEN_PACKAGE --essay-id ACTUAL_ESSAY_ID --minutes 60 --cache /owned/fresh/qwen-only-models --binary /owned/runtime/bin/ollama --lock /owned/worker.lock
python -X utf8 agentsLog/kwiscion/private/FRESH_QWEN_PACKAGE/run_recovery_package.py agentsLog/kwiscion/private/FRESH_QWEN_PACKAGE
```

Use `--no-essay` instead when the package has no essay; repeat `--essay-id` for multiple explicitly identified essays. `--minutes` accepts60 or120. The budget is four attempts and147,456 requested output tokens per item, with the existing recovery/deadline policy. No faults are injected. Input text, complete images and organizer answer order remain preserved.

The closed profile fixes Qwen3.5:9b, context65,536, temperature1/top_p0.95/top_k64 and the reviewed single-container weight digest. Stage only that model's manifest and referenced blobs using `closed_profile.wrap_guard`; never combine Gemma and Qwen weights for submission. The current cache counts6,594,475,420bytes including metadata. Runtime/cache verification and actual loaded-context checks remain mandatory at execution.

The prepared manifest remains `PREPARED`. A separately declared, independently reviewed execution envelope must freeze aware UTC timestamps, authorization and actual cache/runtime pins before the existing `operator_recovery.sh` is used. Do not access final questions before the team-wide freeze.

CPU regression: `python -X utf8 agentsLog/kwiscion/qwen-thinking-prep/test_prepare_qwen_exam.py`.

Executable Qwen-only CPU cache staging (run from the repository tree, retaining the sibling `final-package-prep` helpers):

```bash
python agentsLog/kwiscion/qwen-thinking-prep/stage_qwen_cache.py /existing/native/cache /owned/FRESH-qwen-models --report /owned/FRESH-qwen-stage.json
python agentsLog/kwiscion/qwen-thinking-prep/test_stage_qwen_cache.py
```

The wrapper pins the exact closed profile, shared staging implementation and inventory guard. It selects only the five native Qwen members, rejects an existing destination, verifies every copied byte/hash, and requires exactly6,594,475,420 bytes including metadata. Source development extras are excluded; source contents are not changed. Shared staging may hardlink immutable files on the same volume and counts each destination entry fully. Never edit either linked copy. No Ollama service or model call is made. Keep the report outside the model directory. Production pins have no CLI override; tiny synthetic fixtures mock inventory only in tests.

For the final120-minute policy, use the promoted `../coverage-prep/prepare_coverage_exam.py --model qwen --minutes 120` entry point (the bare `prepare_qwen_exam.py` deliberately omits the coverage suffix); budgets remain4N attempts and147,456N requested tokens forN actual items, with the ten-minute reserve and complete original sources. Preparation is CPU-only. The declared operator supplies the absolute deadline, exclusive ownership, no-egress namespace and exact owned cleanup; final access and inference remain separately authorized.
