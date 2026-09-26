# Heterogeneous source-observer wave — 26 September 2026

**Completed18/18 calls with all18 outputs valid, zero fallbacks, zero retries and no systemic failures.** Independent accuracy grading gives assisted5/6 [3,5] versus fresh direct3/6 [1,3], with one secure gain and one disputed gain. See [second review](2026-09-26-hetero-source-second-review.md). This is a selected six-case known-validation diagnostic, not a full-exam score or a promotion.

Pinned Qwen3.5 9B observed the complete original sources/images; pinned Gemma4 12B produced fresh direct and observation-assisted answers. Every stage had a1024-token cap, thinking off and temperature omitted. The six cases and every source/image hash match the preceding #110 panel. The observation instructions and cap changed alongside the observer model; this measures the declared bundle, not an isolated model-family effect.

| Stage | Complete | Prompt tokens | Completion tokens |
| --- | ---: | ---: | ---: |
| Gemma direct |6/6|6,386|969|
| Qwen observation |6/6|11,443|2,243|
| Gemma final |6/6|9,292|1,082|
| Total |18/18|27,121|4,294|

Requested output budget18,432 tokens; wrapper elapsed140.452seconds including disk verification and sequential model switching. Finished17:59:43UTC, before the declared18:30UTC deadline. AtUSD3.28/hour, that measured interval corresponds to aboutUSD0.13; setup, transfer and idle billing are separate. No server defaults or Gemma weights changed. Runtime snapshots verify the expected stage model/context32768 after each call; full native weights were hash-checked before execution, then file signatures/manifests and runtime/code pins were guarded throughout.

Exact six-ID handoffs, preserving original final strings:

- [Direct answers](model-answers/hetero-source-bare-six.jsonl): `91696a8e646c376563615af23b6a5285577f4b2f582348b70f16268ab5341729`.
- [Assisted final answers](model-answers/hetero-source-final-six.jsonl): `9bd2bc0fa6678524d6efe46fe5ee455f82270e1efefcd4591ec1e00b5c3a791f`.
- Exact observation handoff retained locally: `676cd25037860a7993ad92564530de9636f342c5042333f58bb25cc97590d4d1`.
- [Public provenance manifest](model-answers/hetero-source-six.manifest.json).

All three handoffs had zero contiguous15-word overlap flags against the original prompt/source strings; the scan is a mechanical copying diagnostic, not a historical-factual assessment. The full private archive includes original inputs/images, raw provider responses, captured requests, reservation ledger, runtime snapshots and frozen code. Local backup hash `828f4ece818d0fcc6c120f26c9783e7cb97628ced66689671ea23a236b99b3b5`; raw stages hash `c04241a8238893c1cce9f32732a6a3f4afdd0666b5d53ac7ec79abed94872d2e`; launch hash `550bcdad4c96df1722f049c8d7f9ec9a533c0b3f148742008e6e92c7a14c3575`.

An oversized initial transfer failed before creating a remote wave package or reserving any call. A lean transfer copied the already-present source images and checked every byte against the unchanged frozen manifest. No real generation was redispatched. The previous experiment's artifacts remain unchanged.

Next interpretation must compare fresh direct versus assisted answers item by item, including regressions, and keep this separate from the previous same-model observer result. Successful observations establish completion, not truthful visual grounding.
