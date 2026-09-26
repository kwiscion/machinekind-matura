# RTX multiscale/crops diagnostic — frozen launch record — 2026-09-26 (owner semberecki / Piotr)

Claim [#95](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5848628513)
(start claim 20:11:50 CEST); envelope per the #95 body + lead's 17:18:02Z
reassignment comment (different visual mechanism; route-lab structure).
**Frozen before any dispatch.** This file is public-safe: item IDs are
explicitly labeled known-validation diagnostics (DEV unavailable); no prompt
text, keys, answers or envelopes are embedded — prompt hashes only.

## Mechanism (different from #110's per-source observation arm)

Source-preserving **task-focused multiscale input**: each item's own referenced
page(s) (from the input's `images` field — question/source structure, never
keys or validation IDs for routing) are re-rendered at **220 DPI full pages**
(`pdftoppm` Poppler 24.02.0) as ADDITIONAL images. Originals at 110 DPI are
never replaced or cropped. Differentiated from PR65's source-group crops
(single scale, no effect) and #110's text-observation mechanism; not an
alternative model (Przemek owns the factual/text alternative track).

## Six diagnostic items (frozen from existing prior reviews, before new answers)

Failed source interpretations (0 points in the bare baseline):
- `val2024-hist-z5.1` — map era misread, 0 (range 0–1); #110's secure-repair target
- `val2024-hist-z14.1` — map era misread, 0 (range 0–1)
- `val2024-hist-z25` — cartoon misread, 0/3

Previously correct source-dependent controls (1 point in the bare baseline):
- `val2024-hist-z2` — 1, both-source comparison
- `val2024-hist-z4` — 1, source-dependent architecture item
- `val2024-hist-z13` — 1, rycina event identification

Per item three passes, fixed order: **control** (bare, original input, cap
1024) → **observation** (higher-res routed source(s), generic source-observation
instruction, cap 1024, private trace) → **final** (original prompt + original
images + 220 DPI rendering(s) + observation text, cap 1024).
**Max 18 sequential calls, 18,432 requested output tokens, 45-minute dispatch
deadline from actual start (checked per dispatch; in-flight may finish within
420 s), $0, no retries, one RTX worker.** Incomplete items are reported rather
than exceeding cap; first declared failure stops (corrected wrapper guards,
PR #120).

## Frozen configuration and hashes (verified before render/dispatch)

- Question PDF `MHIP-R0-100-A-2405-arkusz.pdf` SHA-256
  `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21` — exact
  frozen hash, re-verified immediately before rendering.
- Input `runner_input.v2.jsonl` SHA-256
  `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4` (exact
  frozen v2 hash).
- Diagnostic config (private copy): pinned tag `gemma4:12b-it-q4_K_M`,
  loopback `127.0.0.1:11434/v1`, reasoning none, **max_output_tokens 1024,
  explicit temperature 0.2** (per the #95 envelope; reduces the default-sampling
  noise Pewciu6 identified in the transfer review), timeout 420 s.
  Config SHA-256: `d5bebaa1c3ebe740cc33896eb5b0af931accbc71aace64254bb31af810b21eba`.
- Model/runtime: served digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`
  + context 32768 **asserted** by the corrected wrapper after first success
  (fails closed per PR #120); blobs `1278394b…895a606` + `675ad6e6…9842`
  verified pre-start; Ollama 0.34.4.
- Renderer: `pdftoppm` (Poppler 24.02.0), 110 DPI originals (frozen input) +
  220 DPI additions (this diagnostic).

### Page hashes (routed sources; orig110 = frozen input, hires220 = this diagnostic)

| Page | orig110 SHA-256 (first 16) | size | hires220 SHA-256 (first 16) | size |
| --- | --- | --- | --- | --- |
| page-05 | `00e24d9d33d6aa5b` | 812,925 B | `8bd77da496b94d49` | 2,652,831 B |
| page-07 | `066aae308bbd0f52` | 432,992 B | `17054e24f96e5dda` | 1,486,520 B |
| page-08 | `e9c5197e0939a81d` | 695,052 B | `bb62167936c6bebd` | 2,168,143 B |
| page-16 | `6438d789a043a029` | 534,876 B | `0438c14228a3d080` | 1,643,054 B |
| page-17 | `c485908ba79b3f5f` | 624,497 B | `6cda918d24ddee07` | 1,915,328 B |
| page-28 | `b8188663e218a568` | 218,612 B | `1d8dbd06b80022d9` | 1,327,881 B |

## Budget and stop

- Start/stop budget recorded at dispatch in the private run manifest
  (`multiscale-manifest.json`): actual UTC start, dispatch deadline
  (start + 2700 s), per-call request timestamps, stop reason, unsent passes.
- Stop conditions: first declared failure (any result error — infrastructure,
  provider HTTP 4xx/5xx, incomplete/other), served digest/context mismatch or
  missing context (fail closed), context-overflow risk, dispatch deadline,
  output-token budget. Every attempt preserved; no retries.
- Failures, unsent passes and regressions stay in the 60-point denominator
  narrative; incomplete items are reported rather than exceeding cap.

## Deliverables

- Exact final answers (public answer-only under the publication contract, no
  source/key/envelope copies), private intermediate traces (control +
  observation), call/latency/runtime evidence, failures and regressions.
- Root assigns independent grading; no full-40 arm until diagnostic review.
- The completed RTX transfer control (34/60, 146.6 s) stays untouched/immutable.
