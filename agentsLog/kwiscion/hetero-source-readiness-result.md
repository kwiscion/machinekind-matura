# Qwen heterogeneous-observer readiness — 26 September 2026

**Passed exactly two synthetic Qwen calls.** The text instruction returned `gotowe`; the image probe correctly returned `czerwony`. No Gemma warmup, generation retry or real question was included in readiness.

The existing central H100 had no competing inference worker. Native Qwen `qwen3.5:9b` was absent, so the authorized setup downloaded only its pinned native manifest and blobs into the owned model store. All bytes and SHA-256 values were verified on disk. Its combined vision/model weight layer is **6,594,462,816 bytes**, with no separate projector; all declared blobs total6,594,474,711 bytes. Gemma's manifest remained unchanged. Both models independently meet the8,000,000,000-byte ceiling.

Pinned native Qwen manifest: `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`; weight layer: `dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c`. Artifact references and original controller proposal are in [hetero-source-plan.md](hetero-source-plan.md).

Runtime remained Ollama0.34.4 with context32768, one parallel request and one loaded model. Server defaults were not changed. Read-only resident-model snapshots show the existing Gemma before the first call and pinned Qwen at context32768 after each Qwen call. Requests used thinking off, temperature omitted,256-token caps and full synthetic input. The recorded model metadata/template and every request/response are retained in the private backup. This is successful transport/text/image readiness, not an accuracy benchmark or a full offline-network qualification.

| Measurement | Result |
| --- | --- |
| Calls / requested output budget |2 /512 tokens|
| Actual prompt / completion tokens |76 /7|
| Wrapper elapsed, including preflight disk verification |57.444seconds|
| Envelope declared / model install finished UTC |17:44:00 /17:45:47|
| Readiness finished UTC |17:52:58|
| Authorized setup/readiness bound |45minutes; estimated maximumUSD2.46 atUSD3.28/hour|

The elapsed setup-to-readiness interval was about8minutes58seconds, a rate-based estimate ofUSD0.49. This excludes subsequent idle time and the separately declared wave; it is not a provider bill. A shell CRLF packaging error occurred before any remote package or generation reservation; only the shell line endings were corrected. The two generation requests themselves had no retry.

## Runnable wrapper and review

`hetero-source-run.py PACKAGE --mode smoke|wave` is now standalone for a frozen package. It requires an explicit mode declaration, full pinned dependencies and images, exact native manifests/full blob verification, owned process group and worker lock, unchanged server settings, per-stage model checks, request-body equality, durable reservations/raw records, and a process-level deadline. Before each HTTP dispatch it rechecks the remaining UTC and monotonic window. Both explicit context-truncation flags fail closed; errors keep blank exported answers while preserving the provider error and raw diagnostic.

Independent review accepted the final hashes after15 supplied CPU tests and two additional adversarial probes:

- Runner `52be22debdd1710e488484ba94e9af07ae84d6280a52ff47f0d4964bdac27e79`.
- Controller `b911087c9ef5167e23c65ab055f89e359ac9e73b5a06b26872f0d8944c77e266`.
- Frozen synthetic launch `773603720c692f3d368130be6a85baa05bdc1f1cd73aa33d0c63a5f01269c0a5`.
- Verified local evidence archive `87a585dada4ffd72da5bfe292e388a353560d63300f28b971b30a2b3a705112f`.

Root separately authorized the unchanged six-case18-call heterogeneous experiment after this readiness result. [Its public declaration](https://github.com/kwiscion/machinekind-matura/issues/110#issuecomment-5848505237) freezes18,432 requested output tokens, no retries, and a20:30Warsaw deadline. Readiness does not predict whether the heterogeneous observer improves source reasoning.
