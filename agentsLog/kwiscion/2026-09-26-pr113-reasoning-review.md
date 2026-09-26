# Independent PR113 reasoning-lab review — 26 September 2026

**One narrow change requested** at exact head `6a268bb19d2608af5614cf565169a2b695e16880`: reject an explicit `context_truncated:true` response before accepting/scoring its final answer. No GPU/model/server calls or Git mutations were made in this review.

## Concrete finding

`answer_and_usage()` in `scripts/ljaniec/reasoning_lab.py:335` rejects `truncated:true` but ignores `context_truncated:true`. A synthetic response with the pinned model, `done:true`, `done_reason:stop`, nonempty final, empty thinking, valid usage and `context_truncated:true` returns a successful answer. The independent network-free reproduction printed `accepted:true`. This is the same explicit context-integrity failure class already covered by the shared launcher's repaired guard.

Expected: `StopWave`, blank failed family, no later dispatch. Add the alias check and a focused regression, including otherwise valid response fields. This is a small correctness fix; it does not require a new framework or another readiness/model call.

## Verified evidence

- Read exact public PR snapshot in isolated `outputs/reviews/pr113-6a268bb`; shared checkout and owner files unchanged.
- `python3 -B -m unittest discover -s scripts/ljaniec -p 'test_reasoning_lab*.py' -q`: **44 tests PASS** under WSL, including synthetic real-process cleanup/guardian checks. These tests start only their synthetic CPU processes, not Ollama or GPU inference.
- Inspected source/image caching: input bytes/hash, normalized text and ordered decoded image hashes are cross-checked; native payload keeps complete original text/images and appends family instructions only. PF preparation is explicitly a fixed development panel, not a deployment router.
- Native request controls explicitly include thinking off/on, context32768 and bounded total-generation tokens; raw thinking is kept private and separate token counts are honestly unavailable.
- Reservations are fsynced before HTTP; failed/unsent families/stages remain explicit. Client exchange is process-bounded and the owned-server guardian independently enforces deadline/parent-death cleanup. Fresh listener, owned groups, process start identities and inherited pipe proof prevent adopting/killing unrelated daemons through this code.
- Model/projector and native manifest references are hash/size pinned. Actual locally backed-up readiness `/show` has the expected two FROM asset references and thinking capability, matching this controller's health check.

Operational boundary: the existing proxy server must be freshly identified and deliberately retired or otherwise reconciled before this fresh-server supervisor runs; no extra smoke calls are needed. The review did not operate that service. After the narrow context-flag fix and its regression, no other launch blocker was identified in this bounded pass. Real quality, native thinking behavior and experiment output remain unproven until the separately authorized run.
