# Structured reasoning diagnostic preparation — #151

## Authority and readiness

Assigned by #151 and author comment 5850652855; claimed in 5850668925 at 22:57 UTC, preparation ETA 23:15 UTC. The author accepted the eval16 checklist and closed #143. This preparation makes zero model/GPU inference calls and does not start or replace a service, create compute, or purchase anything.

At 22:58:35 UTC, normal authenticated Brev access to the already provisioned dedicated H100 succeeded. Read-only GPU metadata reported NVIDIA H100 PCIe, 81,559 MiB total, 0 MiB used and 0% utilization. No compute application or matching inference-worker process was reported. No listener was visible on the inspected 11434/8000/8080 ports; localhost Ollama metadata requests returned no payload. This proves login and idle GPU visibility in the checked Brev environment, not readiness of the forthcoming serving runtime. Connection details and raw command output remain under the ignored project-private log directory.

The existing rate reported by the user is $3.28/hour. No new paid resource was provisioned; instance uptime billing is separate from model-call accounting. The eventual runtime estimate and hard budget must be in the lead's declaration before inference.

## Shared handoff gate

At base `f4f31f2`, the requested `agentsLog/kwiscion/essay-planning-prep` handoff path was not yet present. Root owns shared prompt/routes/panel design and the reusable larger-context/output/recovery harness. Consume and hash the published handoff; do not independently redesign the prompts or build another serving framework.

Dispatch remains gated on a concrete frozen runner/panel/runtime handoff and finite lead call/token/wall/cost declaration. The first diagnostic has four existing items: closed, open/source, image and original DEV essay. Compare strong single thinking with purpose-specific staged calls at matched per-item wall budgets; preserve complete text/images and all candidate finals. Treat the adaptively selected panel as known validation/DEV, never an unseen test. Keep a topic-selection variant separate from the fixed-topic comparison.

Mechanisms and reporting from #151: independent closed candidates plus evidence-grounded disagreement selection; required claims/evidence/coverage for open answers; image observation separated from interpretation; essay evidence/causality planning then prose. Report selected and candidate-oracle scores, selection mistakes, failure/recovery/placeholder counts, wall time and usage. One fast shuffled grading pass; a second only for material uncertainty. No duplicate workers or per-candidate full rehearsal.

## UTF-8 portability follow-up

Author PR149 comment 5850652566 requested explicit UTF-8 decoding in the eval16 verifier. Four call sites (seven reads in a normal verification run) now use `encoding="utf-8"`; the manifest updates only the verifier hash. Frozen research/input/source/readable bytes and the original research freeze timestamp are preserved.

Meaningful regression: a bounded monkeypatch made `Path.read_text` default to cp1250 whenever no encoding was passed. The original verifier failed on the UTF-8 input with `UnicodeDecodeError` at byte offset 2262. The fixed verifier passed with all seven reads explicitly UTF-8. Normal `python3 agentsLog/ljaniec/eval16/verify.py` still passes: 16 inputs, 32 alternatives, 88 evidence dimensions and 64 source records. The final diff whitespace check passes. This simulates the relevant Windows decoding condition, rather than claiming a native Windows run.

## Standing boundaries

Use only normal current-project account sessions and authorized hosts; keep source packs, official keys, reasoning/provider envelopes and connection metadata private. Publish owned original findings and exact answer-only exports with provenance. May 2025 and FINAL questions remain closed. Accessing FINAL freezes every team project: code, prompts and settings must be committed first. No held-out training/retrieval or purchases/reset credits. The 15-minute issue monitor remains active and current work/processed IDs are recorded privately to avoid duplicate dispatch.
