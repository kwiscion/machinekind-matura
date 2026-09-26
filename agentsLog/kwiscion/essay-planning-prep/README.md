# Current issue151 structured route handoff

Start with [STRUCTURED_HANDOFF.md](STRUCTURED_HANDOFF.md) and [SHARED_RUNTIME_INTEGRATION.md](SHARED_RUNTIME_INTEGRATION.md). The current proposal compares four fixed cases across strong-single and structured arms, through one shared recovery runtime. The typed stage API still requires owner integration; no execution is authorized here. Exact publication files and private source-v2 acquisition/mapping are in [PUBLICATION_INVENTORY.json](PUBLICATION_INVENTORY.json). Generic prompts and cleared synthetic DEV fixtures can be published; original exam text/images stay private.

The six-topic `prepared-v1` study below is archived, unused reference preparation. Its18-call no-retry policy does not govern the new study; preserve its pinned bytes.

---

# Argument-planning CPU preparation

**CPU pipeline ready for review; no live execution is authorized or implemented here.** Root owns #80 under comment 5850512012. The original experiment is comment 5849836497: the same six original DEV topic-1 tasks, control thinking/20480, planner thinking/8192, writer nonthinking/4096; alternating arm order; at most 18 calls, 196608 requested tokens, 45 minutes, no retries or smoke calls. Both arms retain a 90-point denominator. Previous Paweł artifacts are unchanged.

`prepared-v1/manifest.json` is PREPARED with null declaration/deadline/authorization. `inputs.json` copies only the exact full tasks and their hashes from the existing DEV edit-wave bundle, with explicit topic 1 and required aspects. Retrieval evidence is excluded. No benchmark, new corpus or model call was used. `prompts.json` freezes the generic planner, writer, control and fallible-plan framing.

`planning_wave.py` contains the transport-independent reference stage/accounting loop. It reuses exact copies of Paweł's `essay_contract`, `essay_route`, `essay_wave_run`, `essay_think_run`, and their existing normalization dependency under `deps/`; original authorship and repository licensing remain applicable. These helpers are not modified. The new final-answer contract requests plain prose, preserves exact accepted strings, and rejects outputs requiring cleanup. The existing mechanical contract enforces the task minimum (300 words here); the requested 400–500 target is advisory, not a grade or a silent hard filter.

Before each send, requests and reservations are fsynced. Every native envelope is saved before validation. A failed/empty/length/invalid plan blocks its writer, without substituting the control answer. Item-local failures continue; uncertain transport, identity, usage, context or timing failures stop further dispatch. Twelve answer slots are created before dispatch, including failed and unsent entries. Source text is complete at every stage. No control answer enters the candidate pipeline. Plans remain fallible private intermediate outputs, never external evidence.

Fourteen CPU tests pass on Windows (5.753 s) and local WSL/Linux (9.663 s), including full 18-call accounting, ordering, source preservation, exact finals, failed plan/writer behavior, raw/reservation persistence, deadline admission and post-response failure, pin tampering, duplicate plan structure, no replay and zero-dispatch guard refusal. All transport and ownership checks were mocked. This does not establish runtime cancellation or host ownership.

## Shared runtime integration

Per root's latest instruction, do not build a second guardian. `shared_routes.py` exposes `route_stage(item, stage, plan=None)` returning `{name,suffix,think,cap}`, and `stage_result` to accept a plan or exact final and gate the next stage. The shared engine must prepend the untouched original task/images, retain exact intermediates, enforce the whole-operation and request deadlines, and perform its existing owned-process cleanup. This suffix placement is an adapter proposal; freeze the actual composed prompts in the eventual shared-runtime manifest before dispatch. Preserve `prepared-v1` as the reviewed CPU reference, rather than silently replacing its prompt ordering.

The older reference loop accepts injected `transport(payload, timeout)` and `runtime_guard()` callables for CPU tests. It does not provide a live transport or process guardian; its time checks cannot cancel a blocked server themselves. The shared runtime integration and independent review are required before a fresh root declaration. Existing Paweł service state cannot serve as proof that a client timeout stops an in-flight generation.

The shared recovery ladder must not silently add calls to the original no-retry 18-call declaration. Root must either keep that study's original failure semantics or explicitly freeze a new matched-budget study with recoveries included in its finite total. `prompt-study-proposal.md` describes the separate broader route comparison; it does not authorize execution.

```powershell
python -B -X utf8 agentsLog/kwiscion/essay-planning-prep/test_planning_wave.py
python -B agentsLog/kwiscion/essay-planning-prep/planning_wave.py check agentsLog/kwiscion/essay-planning-prep/prepared-v1
```
