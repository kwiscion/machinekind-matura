# Native-thinking comparison bundle — frozen launch record — 2026-09-26 (owner semberecki / Piotr)

Authorized in [#95 comment 5849041941](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5849041941)
(19:09:43Z); ACK + claim posted 5849662468 (20:34:28Z). **Frozen before any
dispatch.** Public-safe: no prompt text, keys, answers or reasoning embedded —
hashes only.

## Bundle (new named bundle; not an isolated quantization or temperature claim)

**Native Gemma thinking on the SAME six source-heavy items** as the parked
multiscale diagnostic, full originals retained (110 DPI pages from the frozen
v2 input, unchanged; no crops/observer, no new images):

- **Fresh direct control**: `think:false` / **1024 total**
- **Thinking arm**: `think:true` / **10240 total**
- All other input/runtime/decoding settings matched; **explicit temperature
  1.0 / top_p 0.95 / top_k 64 in both arms** (organizer-inspired reasoning
  bundle)
- Fixed order per item: control → thinking

**Max 12 sequential calls / 67,584 requested generation tokens / 30-minute
absolute guarded deadline from actual start** (checked before each dispatch;
in-flight may finish within the 420 s timeout) **/ $0, no retries, no new
smokes, one RTX worker.**

## Failure semantics (declared before dispatch)

- **Infra/systemic failures STOP the bundle on first occurrence**: transport
  or timeout, response error field, response model changed, server identity
  change (digest/context fail-closed), thinking-evidence violations in either
  direction (think:true with no thinking; think:false with thinking).
- **Sampling outcomes are recorded as failures and NOT retried; the bundle
  continues** so all 8 points stay in each arm's denominator: truncated
  final (`truncated`/`context_truncated` flag truthy — both enforced),
  length stop (`done_reason` != "stop"), empty final.
- Native num_predict includes thinking; no invented final reserve or separate
  counts. Raw thinking is preserved privately; the published answer-only
  output excludes reasoning.

## Frozen hashes (verified before dispatch)

- Input `runner_input.v2.jsonl` SHA-256
  `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`
  (exact frozen v2 hash; enforced by the runner pre-dispatch).
- Question PDF `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`
  (exact frozen hash, re-verified this session after a private-dir restore).
- Native bundle config SHA-256
  `f06c570d6f1b09251264ebafd5c8cad4436f4a17c5a1486eb4504f8d71f9dd40`
  (pinned tag, native `127.0.0.1:11434`, context 32768, caps 1024/10240,
  temperature 1.0, top_p 0.95, top_k 64, timeout 420 s).
- Native runner SHA-256 `61da9874d2c0ebc5d36b…` (recorded in full in the
  private run manifest at dispatch).
- Model blob `1278394b…895a606` (7,381,382,048 B) + projector `675ad6e6…9842`
  (175,115,584 B) verified pre-start; Ollama 0.34.4.
- Capability check: **zero-generation metadata** `/api/show` → capabilities
  include `thinking` (levels false,true) — confirmed 20:41Z; the actual first
  case records behavior.
- Served identity asserted by the runner after first success: digest
  `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`,
  context 32768, unambiguous loaded model — fails closed.

### Frozen item hashes (6 IDs / prompt / image)

| Item | prompt SHA-256 (first 16) | image SHA-256 (first 16) |
| --- | --- | --- |
| val2024-hist-z5.1 | `ddfe8137168bc85e` | `e9c5197e0939a81d` |
| val2024-hist-z14.1 | `ae970b622ba45555` | `6438d789a043a029` `c485908ba79b3f5f` |
| val2024-hist-z25 | `edb86406a76a6e7a` | `b8188663e218a568` |
| val2024-hist-z2 | `f48729d728806fd0` | `00e24d9d33d6aa5b` |
| val2024-hist-z4 | `e5fdd036c37ce7d0` | `066aae308bbd0f52` |
| val2024-hist-z13 | `e47838eff1448ba2` | `6438d789a043a029` |

Image hashes match the parked multiscale launch record's orig110 values
exactly (full originals retained, unchanged).

## Attempt ledger (frozen format)

Per call, flushed per result: item id, arm, outcome (`ok` /
`failed_sampling` / `systemic_stop`), reason, latency, prompt_eval_count,
eval_count, real `request_started_utc` / `response_completed_utc`. Full raw
responses including thinking stay private; stop reason, unsent calls and
sampling-failure count recorded in the private manifest.

## Budget and stop

- Start/deadline: actual UTC start + 1800 s, checked before each dispatch.
- Stop conditions: first infra/systemic failure (see semantics), dispatch
  deadline, output-token budget (67,584 requested), context-reserve breach.
- Every attempt preserved; sampling failures stay in the 8-point denominator
  of their arm; no retries.

## Deliverables

- Exact final answers (public answer-only, NO reasoning/thinking), private
  raw thinking traces, call/latency/runtime evidence, failures and unsent
  calls. Root arranges independent grading; do not route by known correct
  answers (items are the frozen known-validation diagnostics from #95).
- Reuses the reviewed native request/guard work (ljaniec's native payload
  shape + answer/usage validation semantics, PR #133) with per-arm caps.
- The parked multiscale bundle and the RTX transfer control stay
  untouched/immutable.
