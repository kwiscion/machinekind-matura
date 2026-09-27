# Corrected-input Qwen40 challenger: CPU preparation

**PREPARED, unstaged and not authorized for execution.** Full40 CPU payload and dry-preflight checks pass. This reuses the closed Qwen profile and successful sequential-pair mechanism with the current reviewed PR172 essay diagnostics. No shared runtime code, active Gemma package, remote host, cache or service was changed. No model calls occurred.

Private package: `agentsLog/kwiscion/private/corrected-qwen40-20260927/package-v1/`. Prepared manifest SHA **`b00f756ca143f48489373b6e6bcd274636dccf214d2e1cf13de9262a5f74c2c4`**. The complete copied-file pins and per-item initial-request hashes are in [the public preparation receipt](2026-09-27-corrected-qwen40-preparation.json); it contains no copied questions, sources or answers.

- Exact approved cropped May2024 exam `e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6`, template `aa4451a853063e3f67d1b9d281ac063ee48c112e01c3cb8712ded433253b865f`: 40 items / 60 points, 21 PNGs / 32 image references. Original input, routed input, routes, exam and template match the corrected Gemma40 package byte-for-byte. Every emitted request preserves the complete original text and images.
- One model: `qwen3.5:9b`, native digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. One integrated model/vision container: 6,594,462,816 bytes. Expected fresh eligible cache including metadata: **6,594,475,420 bytes**, to be staged and fully verified later; this preparation does not certify any remote cache.
- Initial requests: thinking on, context65,536, output cap32,768, temperature1, top-p0.95, top-k64, truncation/context shift disabled. Essay item26 uses the same normal essay suffix/diagnostics as Gemma; no special Qwen essay prompt or alternate topic choice. The recovery ladder remains at most four attempts per item, with the final two thinking-off and fixed Qwen sampling retained.
- Bounds: **160 maximum attempts / 5,898,240 requested output tokens / 60 minutes / $3.28 planning ceiling**, no injected faults. Request limit420s, recovery reserve600s, finalization reserve30s. All declaration, deadline and authorization fields remain null.
- All40 initial payloads checked, plus synthetic-history essay retry settings; five closed-profile regressions passed and the actual portable dry CLI reports PASS. Synthetic prompt-usage metadata checks only ladder configuration; real prompt-token fit, loaded model identity/context, wall time and quality remain live runtime checks.

| Copied implementation | SHA-256 |
|---|---|
| Scheduler | `628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0` |
| Native runner | `60393fc61705efb8bdeaf8348ac6fd754bc8a4c0ad1efe142b7c6c39846cda6f` |
| Recovery binding | `54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392` |
| Closed Qwen profile | `953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d` |
| New preparation-only script | `85ff0b39a2df0c6e68d91d415d1b7f0113fde0c351c0fa962f705bc7ce175160` |

## CLI handoff

The CPU-only reproduction command requires a fresh private destination. The runtime-root value names a **future** separate directory; it creates nothing remotely.

```powershell
python -B -X utf8 agentsLog/kwiscion/qwen-thinking-prep/prepare_corrected_full40.py --output agentsLog/kwiscion/private/corrected-qwen40-reproduction/package-v1 --runtime-root /home/shadeform/machinekind-matura-h100-readiness-20260926/corrected-qwen40-20260927
python -B -X utf8 agentsLog/kwiscion/private/corrected-qwen40-20260927/package-v1/run_recovery_package.py agentsLog/kwiscion/private/corrected-qwen40-20260927/package-v1
```

After Gemma terminal evidence and verified cleanup, root must assign the sole worker, stage a fresh exact Qwen-only cache with the reviewed inventory helper, freeze its evidence, and provide a fresh aware-UTC declaration/deadline/authorization. Format future launch timestamps with exactly six fractional digits (for example, `2026-09-27T01:00:00.123456+00:00`), because the deployed Python 3.10 parser rejected a seven-digit timestamp in a separate zero-call attempt. Preserve any originally declared deadline when correcting representation; do not extend it. Only after those steps does the existing Linux guardian command apply:

```sh
bash /ABS/DECLARED_QWEN_PACKAGE/operator_recovery.sh /ABS/DECLARED_QWEN_PACKAGE --execute
```

This handoff supplies no execution permission. Keep model caches separate; the development comparison does not authorize submitting Gemma and Qwen together. Inputs are now source crops, so old full-page scores are not an identical-input comparison. Publication scope: this note, its metadata-only JSON, and `qwen-thinking-prep/prepare_corrected_full40.py`; original exam payloads stay private.
