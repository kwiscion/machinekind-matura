# Matched Qwen/Gemma recovery comparison — preparation

Two executable six-item packages are prepared privately as `qwen-recovery-pair-20260927-v3/{gemma,qwen}`. No generation is authorized. Old v6 and its zero-call failed predecessor remain unchanged.

Panel is the already-declared printed IDs2,4,5.1,13,14.1,25, in source order:8points per arm,7image references/6unique pages. Every original prompt and image byte matches v6 and the central champion inputs. No keys, scores or historical hints enter either package.

The shared scheduler remains exact d99d9271…a54a521. The additive binding accepts only one hash-pinned `qwen35_9b_thinking_v1` profile; ordinary Gemma manifests retain the original payload/defaults. Qwen has one exact6,594,462,816-byte GGUF container with integrated vision, no separate projector. Its manifest is6488c96f…93ea7. Gemma remains7,556,497,632weight bytes. Each model alone fits8.8GB; their combined14,150,960,448bytes does NOT. Use separate isolated caches and sequential services, never bundle both as a submitted model set.

Read-only installed `/api/show` reports Qwen architecture `qwen35`, context262144 and vision/thinking capabilities. This supports attempting65536 but does not prove its loaded context, throughput or memory use. The first scored request must pass existing live loaded-digest/context checks; no warmup. Runtime remains pinned Ollama0.34.4/executable ad9c5344…92ff4.

Declared proposal:12initial slots/48maximum attempts,1,769,472requested output tokens total, ONE shared absolute60minute deadline and$3.28planning ceiling. Both arms retain initial32768/escalation49152,three failure retries,600s recovery reserve,420s maximum request walltime, full-source preservation and owned backend quiescence. Qwen uses fixedT1/p.95/k64; Gemma sampling remains omitted. This is a systems comparison, not an isolated model-only effect.

## Operator handoff (after independent review and root declaration)

1. Fresh-stage exactly the pinned native manifest/referenced blobs into each model-only cache. Reuse the existing inventory primitives; Qwen uses `closed_profile.wrap_guard(guard).native_inventory` plus `verify_inventory`. Do not copy the whole development cache. Keep runtime outside weights. Fresh live ownership/idleness checks remain mandatory.
2. Preserve both prepared manifests, then declare both with the SAME awareUTC start/deadline (span<=3600) and authorization reference. Preserve all other pins/controls. Use one evidence-preserving outer dispatch marker and retain actual return codes; no automatic command retry.
3. Run sequentially with each package's existing guardian; both derive their remaining time from the same deadline:

```sh
bash GEMMA_PACKAGE/operator_recovery.sh GEMMA_PACKAGE --execute
# Only after terminal cleanup, with the same absolute deadline still live:
bash QWEN_PACKAGE/operator_recovery.sh QWEN_PACKAGE --execute
```

Stop the combined dispatch on systemic/runtime/cleanup failure. Preserve all12planned slots, including unsent second-arm slots, in comparison metadata; do not silently extend time or retry. Back up exact raw/ledger/runtime and separate answer-only files. The original idle service remains untouched. No model/server operations occurred in this preparation.

CPU checks:5closed-profile tests,8binding regressions,21scheduler tests passed. Both actual six-item dry preflights pass and sources/images are byte-equal. Fresh isolated caches are NOT staged yet. The read-only metadata proves architectural allowance, not actual65536 loaded qualification.

The initial automatic-review rejection combined a shared mutation with a metadata call and cited stale source-only scope. Root explicitly reconfirmed the additive integration exception; the local patch and read-only metadata query were then separated and accepted. No frozen run/package changed.
