# Finite replacement wave — widened native-thinking budget on the frozen paired slice

Owner: @ljaniec · parent #38 · 2026-09-26. Declares the **actual remaining
allowance** and one concrete, bounded wave, per the lead's 18:39Z request. No
GPU is started and no call is dispatched until the lead authorizes this
declaration. WINNING_PLAN / AGENTS / SOURCE / contracts govern; accuracy scoring
stays with @Pewciu6.

## Remaining allowance (what is already spent, and the cap it sits under)

Standing authorization for this lab: **120 calls / 240,000 requested
output+reasoning tokens / ≤4 mechanism families**, counted across all waves.

| Phase | calls | requested tokens |
| --- | ---: | ---: |
| lead-proxy readiness (reused, comment 5848408299) | 2 | 512 |
| frozen wave `run-1755` (reserved before the stop) | 36 | 73,728 |
| **consumed total** | **38** | **74,240** |
| **remaining under the cap** | **82** | **165,760** |

## The measured mechanism (why 2,048 is the wrong number)

The stopped wave gave the first causal reading on our own eligible artifact: the
thinking call for `z7` used `done_reason:"length"`, `eval_count 2048` (= the whole
cap), `prompt_eval_count 644`, produced **7,390 characters of thinking and an empty
final answer**. Two thinking calls that did finish (`z1`, `z2`) consumed 1,619 and
1,215 tokens and still emitted non-empty finals — so 2,048 is right at the
boundary, not comfortably above it. This reproduces the organizer audit #121
(2,048 total generation may prematurely cap reasoning) and matches the organizer's
own page, which requests **8,192 thinking + 2,048 final** for short tasks.

Throughput measured from the 22 completed rows: **9,858 tokens in 254.9 s = 38.7
tok/s** including one cold-start artifact (the z1 baseline call took 118.0 s for
177 tokens); excluding that cold load the rate is **70.7 tok/s**. Both rates are
quoted below.

## The single number: `thinking_num_predict = 8192`

A frozen per-arm override, already implemented on the pushed controller branch
(see PR). It widens **only** the native thinking arm; baseline, critic and PF keep
the untouched 2,048, so the paired controls stay comparable and only one variable
(thinking budget) moves.

Why 8,192 and not another value (cap-choice reasoning, conservative throughput):

| cap | per-call wall @38.7 tok/s (slow) | @70.7 tok/s (fast) | vs frozen 300 s timeout | headroom over the 2,048 failure |
| ---: | ---: | ---: | :--- | ---: |
| 2,048 | 53 s | 29 s | ok | ×1 (the point that failed) |
| 4,096 | 106 s | 58 s | ok | ×2 |
| **8,192** | **212 s** | **116 s** | **safe margin** | **×4** |
| 10,240 (organizer short-task *total*) | 265 s | 145 s | thin | ×5 |
| 16,384 (organizer essay *thinking*) | 422 s | 232 s | **exceeds → abort** | ×8 |

* **8,192 is the organizer's own named thinking budget for short tasks** — the
  most faithful number to the source, and the panel is short-answer/PF/decision
  (essays are excluded from the frozen 9-item slice).
* It keeps the worst-case single call (212 s at the conservative 38.7 tok/s)
  **safely under the frozen `timeout_seconds = 300`**, so widening the cap cannot
  itself trigger a transport timeout and abort the wave (which would waste the
  reservation). 16,384 would blow the timeout and is rejected.
* After ~2,500 tokens of thinking it still leaves ~5,700 tokens for the final
  answer — far above every final size observed here (max 515 tokens).
* 10,240 (organizer *total*) is the upper alternative if the lead prefers exact
  total-budget parity; it needs `timeout_seconds ≥ 360` to keep the same safety
  margin, at ~12 min extra wall in the worst case. 6,144 is the conservative floor.

## The wave (one wave, no duplicates, no smoke)

`scripts/ljaniec/reasoning_lab.py` `--execute`, **same** controller, same
runtime (Ollama 0.34.4, pinned executable SHA256 `ad9c…2ff4`), same served model
`gemma4:12b-it-q4_K_M` manifest `4eb23ef1…b05c`, same `context 32768`, same
canonical prompt bytes, same frozen panel SHA256 `393d4b70…88063b2` — a
byte-identical reproduction of the stopped wave **except** `think:true` now gets
`num_predict 8192`. Native `/api/chat`, `stream:false`, `truncate:false`,
`shift:false`, no sampling override, no retries (the controller allows none).

**Dispatch: 7 thinking-only calls** — exactly the items still missing from the
paired set: `z7` (the capped one, re-run) plus the six that were never sent
(`z10, z14.2, z19.1, z20.1, z20.2, z24`). `z1`/`z2` already hold thinking rows
and are **not** duplicated. This completes the 9-item × {baseline, critic,
thinking} grid. `readiness_calls = 0`: the two lead-proxy readiness calls are
reused; the server binary is restarted (same pinned SHA + manifest digest) and the
zero-generation `health()` checks (`/api/version`,`/api/tags`,`/api/show`,
`/api/ps`) run before generation.

Declared bounds for this wave: `max_calls = 7`, `max_requested_tokens = 57,344`
(7 × 8,192) — so even a controller bug cannot overshoot the plan. After it, the
standing cap still leaves **75 calls / 108,416 tokens**.

Wall and cost (labelled, honestly separated measurement from estimate):
* measured — expected ≈ cold load ~120 s + 7 × ~40 s ≈ **7–9 min** of occupancy.
* worst case, every call running to the cap: ~**27 min**; hard bound
  `max_wall_seconds = 1800`; proposed `deadline_utc` = authorization + 90 min.
* controller's declared ceiling `rate × max_wall / 3600` = 3.28 × 1800/3600 ≈
  **$1.64**; measured-rate expectation ≈ **$0.4–0.6**. The H100 is
  owner-provisioned and billed by the hour; **nothing is bought or purchased.**

## Stop / pivot rule (fixed now, before dispatch)

1. If any call returns `done_reason = "length"` **with an empty final answer even
   at 8,192**, that is itself the finding (the cap is not the sole cause).
   **Stop, report, do not silently escalate** to 16,384 — escalation needs a new
   authorization because it crosses the timeout bound.
2. Any transport/identity/context/empty-answer failure stops the wave at the first
   occurrence (unchanged behaviour); failed and unsent items stay in the 11-point
   denominator.
3. This wave makes no accuracy or promotion claim; the 22+7 completed answers go
   to @Pewciu6 for independent grading against the full denominator.

## Reproduction (CPU-only dry run, zero HTTP)

```
python3 -B scripts/ljaniec/reasoning_lab.py \
  --manifest <private manifest with thinking_num_predict: 8192> \
  --panel <frozen 393d… panel>
```
prints the frozen plan, per-arm `num_predict` and `http_requests: 0`. CPU suites:
`test_reasoning_lab.py` 31 tests, `test_reasoning_lab_supervisor.py` 20 tests,
all pass; the default (no override) payload is byte-identical to the frozen
controller at `6a268bb`.
