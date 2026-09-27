# Fast auxiliary Qwen RAG diagnostic

Issue189 owns the explicit post08:00 extension. No final questions had been requested when the owner released this experiment. The frozen40/60 candidate and original Gemma V2 artifacts remain unchanged.

The exact existing six-item V2 package is copied into a fresh private directory. The reviewed closed Qwen profile changes model identity and sampling to Qwen3.5:9b, temperature1/top_p0.95/top_k64, context65536. `fast_hook.py` subclasses the unchanged V2 hook. Only auxiliary calls change: queries use thinking off and512 requested output tokens, independent passage judgments use thinking off and384; all three auxiliary recovery attempts use thinking off and1024. Direct/final requests retain their original prompts, images, reasoning and recovery budgets. Both actual payload and scheduler settings change together before durable reservation, so the ledger records actual requested caps.

Four format probes gate48 main slots. The original full index, lexical query policy, five independent judgments, exact-quote admission, source preservation, phase barriers and complete-direct export fallback remain unchanged. Maximum208 attempts, calculated maximum1,908,736 requested output tokens; the original7,667,712 outer ceiling remains a conservative bound. One hour/USD3.28 planning ceiling, with actual declared hard terminal09:05Warsaw27September2026. Actual billing is unverified.

CPU verification: `python -B -X utf8 agentsLog/kwiscion/fast-rag-prep/test_fast.py` passes six tests, including real scheduler reservation equality, retry ordering/fail-stop, image/source preservation and exact direct/final request equality. Independent review also passed the actual package preflight. Staging uses the existing reviewed Qwen-only stager: fivefiles6,594,475,420bytes, no service or model calls. The remote guardian enforces the real launch deadline, not merely descriptive metadata.

Prepared manifest SHA256: `6f8f146da995c9bc82190c17e2a7939e42fc1482e6e405095ac4575aebf87889`.

Declared manifest SHA256: `a5bd4d57fa07c1d14a01c2d8ad3d4724712651c00931890c38d16a2b3d8551e2`.

Declaration: https://github.com/kwiscion/machinekind-matura/issues/189#issuecomment-5853392962

Single dispatch08:29:49Warsaw. Four probes passed first attempt; terminal quality evidence is pending. A selected six-item diagnostic cannot establish full-exam improvement.
