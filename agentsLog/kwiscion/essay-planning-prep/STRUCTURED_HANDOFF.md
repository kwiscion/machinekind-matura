# Structured stage protocol handoff

This is a thin CPU implementation for the one shared harness, not a second runtime. No network, service lifecycle, token ledger, deadline scheduler, retries or final schema exporter are introduced. Root owns the eventual declaration and host. Original `prepared-v1` and its six-topic1 no-fallback experiment remain unchanged.

## Interface

`structured_routes.orchestrate(case, route, invoke, emit)` schedules only the declared semantic slots. Routes are `closed`, `open`, `image`, `essay`, or `control`. It sends a deep copy of the original case to every invocation; the shared runtime prepends its untouched complete text/images to the stage suffix.

`invoke(case, stage)` receives `{name, output_kind, suffix, profile, validation, validation_context?}`. The profile is `thinking` or `direct`; **the shared policy supplies all caps, context, stage deadlines and up to three retries**, not this module. Stage names must be part of ledger identity beneath the arm-specific case ID. The callback returns `{ok, final, error, attempt_records}`, optionally `partial_final` and `fatal`. It must have proved owned compute quiescent before returning. Exceptions or `fatal:true` stop subsequent semantic dispatch; already retained final candidates survive.

Output kinds are explicit: `intermediate`, `final_answer`, `selection`, `image_interpretation`. Intermediate `final` means a completed stage response, not a submitted exam answer. Only explicit final stages or a validated nested image `answer` can enter retained final candidates. Neither a selector envelope nor a plan is exported. Partial plan envelopes returned by an essay writer are also rejected; short clean prose can remain a labelled incomplete candidate.

`validate_stage_text(case, stage, text)` is a pure hook for the shared engine's recovery loop. It checks plan/schema/essay format without dispatching another call. The orchestrator repeats that check defensively, but malformed-output retries must happen inside the shared invocation budget. Selector stages bind retained candidate strings in validation_context, so the shared validation hook rejects missing candidates and changed strings inside its recovery ladder. Candidate-exactness is checked again after selection; invalid selection uses the first usable complete candidate, then the first usable partial, without another model call.

`emit(event)` is the host's durable sink. Every route event carries arm-specific case_id, source_case_id, study_arm and route. Stage scheduling/results, exact retained candidates, skipped stages, semantic validation, fallback and final outcome are emitted. The shared runtime separately retains every native attempt, cap, duration and reservation. The orchestrator must not be used with a no-op emitter for a live run. Its optional no-op exists only for pure CPU experimentation.

## Fixed stage behavior

- Closed: three independent candidates, no cross-candidate notes; source-contradiction selector sees all exact candidates in a deterministic rotation. `{choice:c1/c2/c3}` copies that exact candidate; optional supplied answer must match exactly. `{choice:NEW,answer:...}` is labelled new. Every candidate remains available for oracle grading. If all candidates fail, the already-declared fourth slot performs direct source-only synthesis.
- Open: claims/evidence matrix, draft, coverage. A failed matrix does not eliminate the defined draft/coverage stages. Notes are explicitly fallible, incomplete when relevant, and capped at12000characters with a visible truncation label; full original source and stored responses remain intact. Failed coverage retains a usable draft.
- Images: observations, structured interpretation, then targeted revisit only if a concrete question exists. Invalid interpretation can use the already-defined revisit slot for source-only recovery. If revisit fails, retain the complete interpreted answer. Observations and interpretation JSON are never final-answer fallbacks.
- Essay: plan then writer. Under this **new shared-runtime policy**, a failed/invalid plan uses the defined direct writer with the original task, without assuming the failed notes or the control answer. This deliberately differs from the preserved old six-topic1 study. Topic selection remains a separate future variant.

The pure `study_driver.load_cases(repo)` assembles the frozen four-case panel and verifies exact source and full-image hashes. `run_study(cases,invoke,emit)` freezes all eight answer slots before dispatch, alternates arm order by panel index and makes arm-specific case IDs. A fatal stop preserves unsent slots and previously retained candidates rather than shrinking the grading denominator. Its command line is **check only**, not a model launcher. The shared runtime must enforce the current `prompt-study-budget-v2.json` and its qualified65536context/32768thinking baseline; no smaller reasoning cap is inferred from final-answer brevity. Controls may consume their full matched item wall budget.

## CPU evidence and remaining gate

Twenty-two route tests and two driver tests pass on Windows and local WSL/Linux. They cover independent candidates, exact selection and NEW labels, invalid selection, all-failed fourth-slot fallback, complete-versus-partial retention, intermediate failure continuations, conditional image revisit, planner/selector envelope exclusion, short prose retention, fatal stop, source/image immutability, and no extra semantic calls. These mocks do not qualify live runtime ownership or semantic recovery integration. The earlier14pipeline and4suffix-hook tests remain intact.

The shared runtime currently supports final-answer recovery. Its author has confirmed that this stage protocol is a separate explicit integration step. Do not point its organizer final exporter at intermediate stage responses. Before launch: wire the typed callback/validator/durable sink, bind stage IDs and profiles in its ledger, run combined CPU checks, qualify the owned runtime, freeze actual composed prompts, and obtain root's fresh bounded declaration. This is a concrete implementation handoff, not permission to execute.

```powershell
python -B -X utf8 agentsLog/kwiscion/essay-planning-prep/test_structured_routes.py
python -B -X utf8 agentsLog/kwiscion/essay-planning-prep/study_driver.py --repo .
```
