# Independent deadline RAG review

Status: **PASS, CPU qualification only**. Reviewer: `fast_rag_review_grade_sol`. No model calls or final-package access.

Command: `python -B agentsLog/kwiscion/deadline-rag-prep/test_deadline_rag.py`

Result: **13/13 passed**, 41.530 seconds.

Direct payloads, complete sources/images and explicit essay behavior remain unchanged. The actual declaration is at most55minutes under the60minute guardian configuration. Optional work lasts at most20minutes and ends at least10minutes before the global deadline; the runtime rechecks after startup/verification and rejects late optional responses.

Cutoffs, invalid/partial optional outputs and interruption retain the saved direct export. Zero admitted evidence skips final sampling. The qualified baseline exporter handles aggregate size; oversized optional replacements are rejected. Arbitrary counts/IDs and synthetic namespace collision are tested.

Two review findings were fixed before this passing run: aggregate-size export regression and optional timeout enforcement after runtime setup. An earlier run had two transient Windows `os.replace` permission errors, without failed semantic assertions.

## Reviewed SHA-256

- `prepare_deadline_rag.py`: `348dcf1bdc08a90eef5e68c0e6260d9e36d6861481e19e738ac2445055892897`
- `deadline_runtime.py`: `bcf52932069aa6d7e836964065517a6b3bbce9217b3ee2d0039aa200c7df708f`
- `deadline_hook.py`: `aff872d338c0650f158031b4acaef8c642d6491b60a361c3f628d413a86a7305`
- `test_deadline_rag.py`: `6036f0622c9a8e05540b93efbac020ba327ec8d19e943de2eaf3583fcd763ef2`
- `verify_index.py`: `b3231bac5c6b82b2783b81a3d055e05ed4df11a6ed7e3ba6619aed5fa0165b88`

## Passing tests

- `test_preparation_exact_baseline_inputs_and_arbitrary_ids`
- `test_exact_direct_payload_and_auxiliary_caps_images`
- `test_success_uses_only_complete_optional_finals`
- `test_failed_final_preserves_exact_direct`
- `test_no_evidence_skips_final_sampling`
- `test_late_optional_final_is_rejected`
- `test_cutoff_at_every_optional_phase_preserves_unfinished_direct`
- `test_no_optional_window_does_not_issue_optional_calls`
- `test_direct_failure_gets_three_retries_then_nonblank_fallback`
- `test_partial_and_interrupted_export_preserves_saved_direct`
- `test_generic_plan_counts_and_collision_namespace`
- `test_declared_window_is_at_most_55_minutes`
- `test_large_aggregate_keeps_qualified_direct_and_rejects_oversized_rag`

## Limits

This is independent CPU qualification, not a new full rehearsal, model-quality result or promotion decision. Final deployment requires these frozen hashes, the prepared manifest and a valid full-index proof from the actual final host/boot/stat. The generic path intentionally omits the diagnostic four-probe gate and runs one optional chain per eligible item. Quality and measured throughput remain separate diagnostic gates.

A later author repeat returned 12 passes and one Windows PermissionError in the unchanged baseline atomic os.replace helper. The independent 13/13 passing run above remains valid; this recurring Windows filesystem issue is a qualification limitation. Any Linux compatibility smoke requires root release after diagnostic grading; proposed bound is a 15-minute declaration with a 600-second reserve, no later than 09:12 Warsaw, and is not another full rehearsal.
