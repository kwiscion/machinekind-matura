# Łukasz runtime readiness — proxy handoff, 26 September 2026

**Two synthetic readiness calls completed and their evidence is locally backed up and hash-verified.** Root Sol acted only as temporary setup/execution proxy; Łukasz remains the logical experiment owner and now owns future execution. No real exam calls were made. Existing downloads and unrelated services were untouched.

| Check | Observed result |
| --- | --- |
| GPU/runtime | H100 PCIe; driver580.126.09; Ollama0.34.4 |
| Assets | Every manifest/config/layer blob hash and size checked; model+projector7,556,497,632bytes |
| Loaded context |32768, correct full model digest after both calls |
| Text | `ready.`; finish`stop`;21prompt/3completion tokens;105.363s including cold load |
| Synthetic red image | `Red`; finish`stop`;114prompt/2completion tokens;6.063s |
| Calls/budget |2/2,256requested output tokens each,512total; no retry; no errors |
| Request controls | OpenAI-compatible chat path, reasoning_effort`none`, temperature omitted |
| Smoke wall time |111.514s; terminal at17:38:56UTC |

Text readiness establishes a usable answer; the returned punctuation is retained exactly. The image request used an original synthetic fixture with SHA256`b4467f0dd939cb7b8af870bf39e79c2433610e765485791c8524ca7a245577b8`. No exam materials or keys were involved.

Pinned model digest:`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.

Runtime archive SHA256:`c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533`.

Runtime executable SHA256:`ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`.

Local evidence archive SHA256:`6bef26e05e24218e3b416d6bf9bbffa514f9cc2d151be7c4820a68340b940e32`.

Raw response SHA256:`5944b7e6ba8a7fc92017fa86b73c2108c741c41760bbd092b952f7198ef48ec6`.

The private manifest predates all generation and declares45minutes setup/readiness, at most2calls, no retry, pinned input/code/runtime controls and a hard deadline. Rate and billing were unverified during proxy setup; planning assumptions and detailed accounting remain private. The verified local backup includes requests, raw responses, config/input/code hashes, runtime snapshots, asset proof and private operational handoff.

## Ownership and remaining limits

The [explicit ownership handoff on #38](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5848408299) tells Łukasz to inspect the existing project runtime before starting a competing service. He may reuse it or deliberately retire only its freshly re-identified owned server, preserving unrelated processes. A saved PID alone does not prove current ownership. Root proxy has relinquished future execution; these two calls count toward the lab's wave, and no repeat readiness calls are implied.

This proves only the synthetic text/image OpenAI-compatible path. Native thinking-on/off accounting, the reasoning controller/supervisor, real experiment correctness and actual offline isolation need their own review/proof. Readiness is not a model-quality score or a throughput forecast for a full exam. Connection mapping and infrastructure identifiers are intentionally absent from this public report.
