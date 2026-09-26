# Fresh organizer-path control — 26 September 2026

**Completed40/40 real model calls, with40 nonempty validated answers, no case errors, no unsent items and no retries.** Accuracy grading is pending. The denominator remains40items/60points.

This uses the actual generic organizer launcher at reviewed commit `775353b0e4844d33061828426ffba6f8a2a0b505`, including the verified-context budget correction. The input is the frozen **locally constructed source-v2 package in organizer schema**, not an organizer-issued May2024 transcription. It preserves40items,60points,43 image references and21 original PNGs. This measures the submission code path and its changed prompt construction; it is not prompt parity with the earlier runner baseline.

Gemma4 12B native Q4 remained pinned, with its projector, at7,556,497,632 weight bytes. The native-Linux H100 profile pins Ollama0.34.4 and its binary hash, context32768 and all manifest blobs. Each request retained the1024-token cap, thinking off, temperature omitted and no new sampling override. `--continue-case-errors` was enabled only for the reviewed failure classifier; no case needed it. No warmup calls were added.

| Evidence | Result |
| --- | --- |
| Generation calls / requested output tokens |40 /40,960|
| Actual prompt / completion tokens |54,600 /3,972|
| Supervised execution elapsed |222.977seconds|
| Finished UTC |18:17:58|
| Declared hard deadline UTC |18:38:54|
| Maximum declared envelope |30minutes; estimatedUSD1.64 atUSD3.28/hour|
| Measured execution-only rate estimate |aboutUSD0.20; excludes setup/waiting/idle billing|

The first cold request was slower; later requests progressed normally. A stale outer connection display was resolved through read-only remote status checks, without redispatching the control.

## Offline execution and cleanup

The zero-generation `unshare -rn` preflight passed. The actual runner and its transient server then ran in a different network namespace from the host, with **only loopback** and failed external IPv4/IPv6 connection probes (`ENETUNREACH`). Per-response runtime checks validated pinned Gemma/context32768. This is actual namespace-isolated inference evidence, not merely a loopback endpoint claim.

Only the freshly identified original root-owned server/process group was retired to free the GPU. Its model files/configuration and previous experiment artifacts were preserved. The launcher recorded cleanup of its own isolated server group; no host firewall changes were made. The launcher cleanup field `host_daemon_stopped:false` describes its isolated cleanup routine, not the outer supervisor's separately recorded prior-server retirement. No other host was modified.

The reviewed launcher was used **without instrumentation**. Exact prepared inputs, configuration and infer code are retained; request payloads were reconstructed afterward and explicitly labeled `reconstructed_not_captured`. No actual HTTP-request capture is claimed for this run.

## Grading handoff and provenance

- [Mapped40-item answer-only handoff](model-answers/organizer-control-gemma-val40.jsonl): `0286692a89f2fdbfca2d87364c3e6eb0d827eafbb6f2a6d7a939fd17d79f0536`.
- [Public provenance manifest](model-answers/organizer-control-gemma-val40.manifest.json).
- Original `answers.json`: `b52e8981f967d3e1310ca8c53a11f7c80185ac724a81790708671145b02d97d9`.
- Verified local archive: `7060b2b6d3a67693807efc6d76071eab09c585a77c872695d974ad91341ba7bb`.
- Raw responses: `139b8b87efbf144f442f093df56f5a8b27e765624673f935409cc2b50c0614ea`.
- Actual prepared input: `9600f00a473c0647de87030980425519b529b42df0ab6721b45c4da8f2b0c00f`.
- Actual launcher record: `775f0ca95fdaf2844035f4233ec350988426bf6a58f57542c94a87d38bf7d22b`.

The private archive contains the exact package, printed-ID-to-validation-ID mapping, verified source/image map, prepared input, raw responses, answer JSON, namespace proof, runtime checks, cleanup, configuration and launcher code. All40 IDs were joined bijectively in original order; maxima sum to60. No15-word source-overlap flags were found in the handoff. The published launch-declaration hash refers to the local CRLF serialization; the remote declaration uses LF with the same JSON values, and both byte identities are retained.

Private grading input root: `agentsLog/kwiscion/private/organizer-control-run-20260926/recovered/job/`. Existing evaluation keys and official marking materials remain under `agentsLog/Pewciu6/private/validation_2024/`; they were not read to construct or execute this control. Independent grading should use the mapped exact answers, preserve every item and assess the essay normally. No score, improvement or final-candidate promotion is inferred from successful execution.

Root wave accounting after this control: **78 generation calls /76,800 requested output tokens**, including the earlier18-call source wave, two Qwen synthetic calls and18-call heterogeneous wave. No further GPU calls were made by this task.
