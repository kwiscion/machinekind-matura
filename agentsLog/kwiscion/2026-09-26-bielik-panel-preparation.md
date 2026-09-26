# Bielik paired text panel — preparation only

The panel contains all nine source-v2 non-essay rows whose original image list is empty. Selection used no answer key or score. IDs, original source text and questions remain unchanged; no image was removed. The panel is known-validation development, not an unseen test or a full-exam result.

IDs: z3.1, z3.2, z7, z15.1, z15.2, z20.1, z20.2, z22.1, z22.2.

Parent SHA256: `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`.
Panel SHA256: `213197cc40570123d52d90e3c5609675f4d2f36f050704a042475bba418614d0`.

Source-only inspection found prose, poem versions, economic accounts and commentary with their questions preserved. The largest prompt has 3,780 characters; this is not a tokenizer/context proof. No evaluation key was opened. Correct-control membership can be reported after selection, without changing membership.

Proposed paired execution: original question/source unchanged on official Bielik 11B v3 Q5 and pinned Gemma 4 12B Q4; 9 calls/model, 1,024 output tokens/call, temperature omitted, Gemma thinking off, 32,768 effective context. At most 18 calls/18,432 requested output tokens, sequential model blocks, no retries. Frozen code/config/deadline, durable reservations, runtime/usage checks and independent controller review are required before dispatch. This document authorizes no real calls.
