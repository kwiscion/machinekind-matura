# RTX multiscale/crops diagnostic — run record — 2026-09-26 (owner semberecki / Piotr)

Claim [#95](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5848628513);
mechanism per the frozen launch record
[2026-09-26-rtx-multiscale-diagnostic-launch.md](2026-09-26-rtx-multiscale-diagnostic-launch.md)
(source-preserving task-focused multiscale: originals at 110 DPI unchanged +
220 DPI full-page renderings of each item's own referenced sources as
additional images; explicit temperature 0.2). Frozen before dispatch.

## Result: complete — 18/18 passes, 0 errors, 0 unsent

- Stop reason `all_passes_dispatched`; wall **1 m 43.2 s**
  (start `18:43:16Z`, end `18:44:59Z`) vs the 45-minute dispatch deadline.
- Latency: sum 102.734 s, mean 5.7074 s, median 5.310 s, max 10.675 s.
- Prompt tokens: max 3,850 (`val2024-hist-z14.1:final`, 4 images) — no
  truncation at context 32768; observation passes 1,198 pt (220 DPI renders).
- Completion tokens: max 659 — **0 length-stops** at the 1024 cap.
- Single response model `gemma4:12b-it-q4_K_M` on every pass; served digest +
  context asserted by the corrected wrapper (PR #120) after first success.
- Guards: 0 trips; no retries; $0 spent.
- Copied-source check: max 7 consecutive word overlap answer-vs-own
  prompt/observation-instruction; **0 answers with ≥10-word runs** (cleaner
  than the transfer run's 7 ≥10-word instruction echoes).

## Frozen hashes (verified before render/dispatch)

- Question PDF `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`
  (exact frozen hash, re-verified immediately before rendering).
- Input v2 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`
  (exact frozen hash; enforced by the runner pre-dispatch).
- Diagnostic config `d5bebaa1c3ebe740cc33896eb5b0af931accbc71aace64254bb31af810b21eba`
  (pinned tag, loopback, reasoning none, 1024 cap, temperature 0.2, 420 s).
- Model blob `1278394b…895a606` (7,381,382,048 B) + projector `675ad6e6…9842`
  (175,115,584 B) verified pre-start; Ollama 0.34.4; CUDA0 active.
- Per-page orig110/hires220 hashes in the launch record table.

## Answer-only handoff (publication contract, 14:38Z owner authorization)

[model-answers/gemma4-12b-val6panel-multiscale-diag.jsonl](model-answers/gemma4-12b-val6panel-multiscale-diag.jsonl)
— 18 rows (six known-validation diagnostic items × control/observation/final),
sha256 `b3072b4e466904a26b8c95c1cba83d69a708c8e70a9441acdc1323ae885f4512`;
fields `id`/`pass`/`answer`/`error`/`finish_reason`/`latency_seconds`.
No source passages, keys, question packs, credentials or provider envelopes.

## Reviewability

- Public runner copy: [rtx_multiscale_run.py](rtx_multiscale_run.py) (no exam
  material embedded; item IDs explicitly labeled known-validation diagnostics).
- Private traces (immutable): per-pass raw results + manifest under the
  gitignored owner-private dir; per-page 220 DPI renderings.
- The completed RTX transfer control (34/60, 146.6 s) stays untouched.

## Limitations

- Six-item known-validation panel, DEV unavailable; automatic grades remain
  provisional pending independent review.
- No full-40 arm until diagnostic review; different exam/runtime from the
  May 2023 DEV scores discussed on #38.
