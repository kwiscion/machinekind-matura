# Matched sampling attempts — 26 September 2026

Both attempts are terminal and locally backed up. No score or promotion is claimed.

| Arm | Requested temperature | Complete / failed / unsent | Attempted calls | Prompt / output tokens | Arm wall time |
| --- | --- | --- | ---: | --- | ---: |
| A | Omitted | 40 / 0 / 0 | 40 | 43,934 / 6,357 | 112.750 s |
| B | 0.2 | 38 / 1 / 1 | 39 | 43,416 / 6,085 | 97.572 s |

Total: 79 generation calls, 80,896 requested output tokens, no retries. All 40 IDs remain in each evaluator handoff; failed and unsent answers are blank. Complete final strings are unchanged. Original provider responses, including the failed partial answer, remain private.

## Frozen controls and verification

- Input: unchanged bare source-v2, 40 IDs and 21 canonical PNG assets; SHA256 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`.
- Model digest: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
- Ollama 0.34.4, effective context 32768, thinking off, output cap 1024, timeout 420 seconds. Runtime executable SHA256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`.
- Runner revision `568ed7027329138943c6897512b10e112d42af31`; runner file SHA256 `d647172438b14fbcf56554ed418dafa264187a03b6a67574fc5e5e3843515edb`. Fourteen focused CPU checks passed before generation.
- All 39 paired request bodies compare equal after removing B's explicit temperature field, including prompts and image data URLs. A omits that field throughout. Other sampling defaults and seed were not fixed.
- Local backup archive, raw response, per-request and final handoff hashes were checked. Each handoff has exactly the frozen 40 IDs in order.
- Runtime identity/context checks passed for all complete calls; a separate read-only observation after B's failure still showed the pinned digest/context. The failure row has no post-call runtime entry because response validation stopped first.

## Stopping event

B stopped at `val2024-hist-z25`, its 39th request. Actual `finish_reason` was `length`: 759 prompt tokens and 1024 completion tokens, with 2474 nonempty final-content characters, no reasoning text and no refusal field. The generated text became repetitive and reached the output cap. It was not rescued, edited or retried. `val2024-hist-z26` was never dispatched. Recorded latency was 10.689 seconds. Numeric HTTP status was not retained; the parsed completion has no recorded transport error, so no exact HTTP status is claimed.

## Handoff integrity and limitations

A answer-only SHA256: `4f4345a65bc4658ec574f0ace411a40d35c1118ac47617b2337743bbf0d6e380`.

B answer-only SHA256: `030dc23e9f44e2f9e07cb76e484eeb6ee317b9aa7a4f93efc2dcb67ae4f8bda7`.

Private quote audit found one A overlap flag at z23.1: an echoed task label/instruction, not a historical source passage. B has no 15-word overlap flag among complete finals. This is a scoped overlap check, not a general rights guarantee; publication remains a separate lead decision.

Provider usage and truncation indicators are recorded, but do not constitute formal proof that no input truncation occurred. Sequential unseeded attempts cannot isolate temperature's causal effect. Independent evaluation must retain failed/unsent cases in the full denominator. No evaluation keys entered generation, no model settings were changed after termination, and the server was left unchanged.
