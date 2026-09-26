# Thinking-completion wave `ljaniec-thinking-completion-20260926T224256Z` — RESULT: 7/7 complete, paired matrix closed

Owner: @ljaniec · parent #38 · authorized by @kwiscion 2026-09-26 ("Fire 8192").
WINNING_PLAN / AGENTS / SOURCE / contracts govern. **Accuracy scoring belongs to @Pewciu6 (#11);
this file makes no accuracy, promotion or whole-exam claim.** It records measured runtime facts.

## Headline

The single authorized wave ran **7/7 completed, 0 failed, 0 unsent, `stop_reason = null`.**
Every one of the seven native-thinking calls closed with `done=true`, `done_reason="stop"`,
`eval_count ≤ 8192`, **non-empty thinking AND a non-empty final answer**, and zero
truncation/context-truncation flags. The #121 failure mode is **eliminated** on our eligible
`gemma4:12b-it-q4_K_M` artifact: the very call that length-capped empty at the 2,048 budget
(`val2024-hist-z7`) now closes at `stop` with **8,292 characters of thinking and a 297-character
final answer**.

This completes the **27/27** frozen paired slice: 9 items × {baseline, critic, thinking}.

## Frozen inputs (re-verified byte-for-byte before dispatch)

| artifact | SHA256 |
| --- | --- |
| controller `scripts/ljaniec/reasoning_lab.py` (feature `thinking_num_predict`) | `858fa4e10025a3f30df5a90e9c4ea1308375fbae965c58e63464a76282092056` |
| supervisor `scripts/ljaniec/reasoning_lab_supervisor.py` | `2e7ff194bf902d17c9ba5c573f52b2877903b32d878436898dc9461bb9ddf766` |
| 7-row thinking-only sub-panel (carved from `393d…88063b2`) | `4e9bb4268f3febbd7b0c8e395d2e9e81bb723e195a2a618732522bdc8d581bdd` |
| launch manifest (final, corrected) | `84155a23…` |

Controller change is PR #133 (merged `bd1fb46`): the optional manifest field
`thinking_num_predict` widens the single-generation cap for the **thinking family only**.
The frozen payload plan is the single source of the per-call number across request options,
ledger accounting and post-response validation, so requested, accounted and enforced counts
cannot diverge. Baseline, critic and PF keep the untouched uniform `num_predict`.
**Only one variable moved: the thinking budget.**

## Declared bounds and what was actually spent

| bound | declared | observed |
| --- | ---: | ---: |
| `max_calls` | 7 | 7 reserved, 7 completed |
| `max_requested_tokens` | 57,344 (= 7 × 8,192) | 57,344 reserved; **19,809 actually generated (34.5%)** |
| per-call reservation | uniform 8,192 | distinct reserved value = {8192} only |
| `readiness_calls` | 0 | 0 (two lead-proxy readiness calls reused, 2/512) |
| `max_wall_seconds` | 3,300 | dispatch-span **188.1 s** (~3.1 min) |
| `timeout_seconds` | 300 | max per-call latency **73.9 s** (z19.1) |
| `deadline_utc` | 2026-09-27T00:02:56Z | not approached |
| cost ceiling (`rate 3.28 × max_wall/3600`) | **$3.01** | owner-side hourly occupancy ≈ 4–5 min → **≈ $0.27** |

`actual_cost_usd` is `null` in the summary: billing is owner-side and hourly, no invoice was
read. **Nothing was purchased.** Standing authorization after this wave: **75 calls / 108,416
tokens** remain under the 120 / 240,000 cap.

## Measured per-call table (public-safe; thinking character counts are private-evidence)

| item | final chars | generated tokens | latency s | `done_reason` |
| --- | ---: | ---: | ---: | --- |
| val2024-hist-z7 | 297 | 2,333 | 28.2 | stop |
| val2024-hist-z10 | 629 | 1,939 | 20.1 | stop |
| val2024-hist-z14.2 | 641 | 2,596 | 27.7 | stop |
| val2024-hist-z19.1 | 1,134 | **7,368** | 73.9 | stop |
| val2024-hist-z20.1 | 363 | 864 | 9.2 | stop |
| val2024-hist-z20.2 | **14** | 2,949 | 29.1 | stop |
| val2024-hist-z24 | 574 | 1,760 | 18.5 | stop |

Throughput: 19,809 generated tokens over the sum of per-call latencies (206.6 s) = **95.9 tok/s**
(105 tok/s over the 188.1 s dispatch span). Both exceed the first wave's 38.7/70.7 tok/s, which
is expected: longer generations amortize the per-call startup better.

## Why 8,192 and not a smaller number — decided by the run's own data

The hardest item needed **7,368** tokens (`z19.1`, 89.9% of the ceiling). Therefore:

* a **4,096** cap would have re-tripped #121 on `z19.1`;
* the previously proposed **conservative floor 6,144 would also have re-tripped #121 on `z19.1`**
  (7,368 > 6,144);
* **8,192 is the smallest authorized cap that fits the observed demand distribution**, and it keeps
  the worst-case call (73.9 s observed; ~212 s projected at the conservative 38.7 tok/s) safely
  under the frozen `timeout_seconds = 300`.
* 16,384 stays rejected: its worst case exceeds the transport timeout and would need re-authorization.

This is directly relevant to the Sunday exam run in WINNING_PLAN: a 2,048-token generation budget
is **not** sufficient for decision/justification items on this artifact; ~8 K is the working figure,
and the essay-scale variant (16,384) requires a raised transport timeout.

## Honest limitations and flags for the grader (@Pewciu6)

1. **`z20.2` final answer is only 14 characters / 6 words.** It carries a P/F-style verdict token
   but no justification, although 11,311 characters of reasoning were produced in the thinking
   channel. The controller's gate (non-empty final) is satisfied, so the row is *valid*, but its
   usable answer is thin. This is the one residual gap in "reliable final extraction".
2. Two **critic** rows from the frozen `run-1755` are degenerate and must be scored as they are,
   not repaired: `z14.2` (34 tokens / 34 chars) and `z20.2` (second stage 25 tokens / 46 chars).
3. On several items the thinking arm's **final text is shorter** than its baseline twin while
   consuming far more generation (e.g. `z19.1`: 7,368 tok → 1,134 chars vs baseline 497 tok →
   1,444 chars). Direction of any accuracy effect is the grader's call, not mine.
4. Answer rows carry no chain-of-thought field; all thinking character counts above come from the
   private envelopes and are not reproducible from the public artifacts alone.

## Pitfall recorded for all agents (dispatcher / new orca / claude-code sessions)

**The first dispatch of this wave aborted with `Supervisor deadline elapsed` (RC=2) and spent
ZERO tokens.** Root cause was operator error, not hardware, runtime or model: the manifest was
built by copying the audited `wave-launch.json` and overriding only the wave-delta fields, and
`deadline_utc` was **not** in that delta — so it kept the previous wave's `2026-09-26T19:00:00Z`,
already ~3.5 h in the past at dispatch time. Two durable lessons:

* `deadline_utc` must be recomputed at build time, never inherited from a prior wave's launch
  record; assert `deadline_utc > now + ≥60 min` in the builder, not only in the controller.
* `reasoning_lab.py --manifest … --panel …` (check mode) does **not** test deadline freshness —
  freshness is only enforced on the `--execute` path via the supervisor. A green check mode is
  therefore **not** evidence that a wave is dispatchable.
* That fail-closed behaviour is correct and desirable: no run-dir was created, no server started,
  no lock held, no tokens requested, GPU stayed at 0 MiB. Also note `brev cp` accepts only the
  `instance:/abs/path` form; a `user@instance:/path` form can silently no-op, so every pushed
  input must be re-hashed on the instance before dispatch.

## Reproduction (CPU-only, zero HTTP)

```
python3 -B scripts/ljaniec/reasoning_lab.py \
  --manifest agentsLog/ljaniec/private/reasoning-lab-20260926/completion-manifest.json \
  --panel   agentsLog/ljaniec/private/reasoning-lab-20260926/completion-panel.jsonl
```
prints `planned_calls: 7`, `requested_tokens_including_thinking: 57344`, `http_requests: 0`,
`num_predict: {baseline: 2048, pf_statementwise: 2048, critic: 2048, thinking: 8192}`.
CPU suites on the merged `main`: `test_reasoning_lab.py` 31 OK,
`test_reasoning_lab_supervisor.py` 20 OK. Immutable predecessors preserved: `run-1755/*` untouched.
