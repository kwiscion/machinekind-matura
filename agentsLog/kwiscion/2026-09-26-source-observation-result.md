# Source-observation diagnostic — 26 September 2026

Completed **18/18 calls** in **76.530 seconds**. Six bare answers and six final answers completed. Three of six observation passes reached their 768-token cap; their reserved final slots used the unchanged bare input, exactly as declared. No retries, extra calls or systemic failures. [Independent root review](2026-09-26-source-observation-grade.md) gives **bare3/6 versus final3/6**, with the successfully assisted paths tied2/3. No promotion; this selected six-case diagnostic is not a full exam score.

Panel, in original source-v2 order: z1, z2, z4, z5.1, z14.1, z15.2. All original text and image content was preserved. Requested output budget:16,896 tokens. Actual usage:22,246 prompt +5,992 completion tokens. Runtime:Ollama0.34.4, pinned Gemma4 12B Q4, context32768, thinking off, temperature omitted and other sampling defaults unchanged.

| Stage | Complete | Prompt tokens | Completion tokens |
| --- | ---: | ---: | ---: |
| Bare |6/6|6,386|941|
| Observation |3/6|7,282|4,164|
| Final |6/6|8,578|887|

The observation passes for z5.1, z14.1 and z15.2 all ended with `finish_reason=length` at768 completion tokens. Each contained nonempty partial text, which was retained privately and **never injected into the final input**. Those final calls received byte-identical bare content. Any change versus their first bare answer is an unseeded second draw, not evidence of an observation benefit. Only z1, z2 and z4 completed the observation-assisted path.

The recorded generation interval was17:23:17.912–17:24:34.442 UTC. The declared deadline was18:06:53.127 UTC. All18 per-request runtime checks passed. Request-body checks confirm unchanged original content/image parts, temperature omission, stage caps and thinking-off controls. Each request has one reservation and a private immutable request/response record. The local archive, raw response and request hashes were verified after transfer; no server or model settings were changed at completion.

## Exact handoffs

- [Bare answers](model-answers/source-observation-bare-six.jsonl): `ca1c8a96a0c37f36766f3044336171eb77aef4b2ad13cd38f0b7ed3e2caaeff2`.
- [Final answers](model-answers/source-observation-final-six.jsonl): `552967ed5d164ff3cfbb0efb786e580483514b2a4048e2928141fc2f2dc5c6f5`.
- [Completed observations; failures blank](model-answers/source-observation-observation-six.jsonl): `04f911090e7085489ce71d273e0f57cb2db594c45edb3725a37cf8666615ec38`.
- [Handoff manifest](model-answers/source-observation-six.manifest.json), [frozen launch and original generic prompts](2026-09-26-source-observation-launch.json).

Every stage handoff retains the same six IDs. Complete final strings are copied exactly; failed observations remain blank/error, with original partial responses private. Bare/final outputs had no contiguous15-word source-overlap flags. The observation z4 flag was an echoed22-word task instruction, not a historical source passage. No official source pages, evaluation keys, provider envelopes or reasoning fields are published.

Backup archive SHA256:`a6ebf71f1bd912a76eb1316c118df974643efbfec2aa1f9b4da2597744c8e464`. Raw stages SHA256:`860f13014c742df3cd423c99683c06c269d0a5f0a4d0a080e33db392c8a084e2`.

## Reproducibility and limits

Owned worker:[run_source_observation.py](run_source_observation.py). CPU tests:[test_source_observation.py](test_source_observation.py); `python -m unittest discover -s agentsLog/kwiscion -p test_source_observation.py -q` passes4 synthetic tests, locally and before remote dispatch. They check stage/token totals, original source preservation, observation-failure fallback, and strict usage/context/runtime/systemic failures. The worker uses the reviewed case-error classifier from PR105 head5854984 and retains both explicit context-truncation stop flags.

This run exposes a concrete completion limitation: half the observation passes failed within the matched768-token allowance. Grading must separate successful observation paths from fallback paths and inspect factual errors/regressions. No longer prompt, larger cap, repeat, crop or other mechanism has been dispatched automatically. Reported usage/runtime checks are not formal proof of absence of silent input truncation.
