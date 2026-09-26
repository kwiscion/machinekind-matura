# Frozen wave `ljaniec-reasoning-20260926T1755Z` — terminal ledger and first paired outputs

Owner: @ljaniec · parent #38 · prepared 2026-09-26. WINNING_PLAN / AGENTS / SOURCE /
contracts govern. Accuracy scoring belongs to @Pewciu6; nothing here is an
accuracy, promotion or whole-system claim.

Controller frozen for the whole wave: `scripts/ljaniec/reasoning_lab.py` at
`6a268bb`, SHA256 `092c1b2ec3882ef3b16501c2045d78aa996dd3ab501196e579aa8ddeb6d98ae2`.
Panel SHA256 `393d4b70ec748a899605cfbc52f4cf3301fb288f0e59ec16401fd42df88063b2`
(question-only, frozen before dispatch; raw envelopes and thinking text stay private).

## Terminal counts (recomputed independently from the raw JSONL, zero discrepancies)

| Measure | Value |
| --- | ---: |
| Generation calls planned (42) | 42 |
| Calls reserved | **36** |
| Calls completed | **35** |
| Guard-stopped call | **1** |
| Calls never dispatched | **6** |
| Requested output+reasoning tokens | **73,728** of 86,016 plan |
| Answer rows (9×3 families + 2 PF) | 29 → 22 completed / 1 failed / 6 unsent |

| Family | rows | completed | failed | unsent |
| --- | ---: | ---: | ---: | ---: |
| baseline | 9 | 9 | – | – |
| pf_statementwise | 2 | 2 | – | – |
| critic | 9 | 9 | – | – |
| thinking | 9 | 2 | 1 | 6 |

Wall clock: first ledger event `17:57:13Z`, last `18:01:28Z` → 4m 15s. The
authorized wall bound (`max_wall_seconds: 5400`) was never approached; the
declared deadline was 19:00:00Z. Readiness reuse: 2 calls / 512 tokens from
comment 5848408299, **0 new readiness calls**.

## Guard that stopped the wave, and why it is the lead's #121 finding reproduced

Guard-stopped row: `val2024-hist-z7`, family `thinking`, stage 0,
`error.type = wave_guard`. Its retained raw response is the mechanism, verbatim:

```
done: true          done_reason: "length"
truncated: null     context_truncated: null
eval_count: 2048  ==  the full num_predict cap
prompt_eval_count: 644
message.thinking: 7,390 characters (non-empty)
message.content:  ""  (empty final answer)
```

The model spent the entire 2,048-token single-generation budget on reasoning and
reached the cap before emitting a final answer. The frozen controller correctly
refused to accept an empty final answer and stopped all later generation — so the
**6 unsent calls are the correct, authorized behaviour of a stopped wave, not data
loss**. This is the #121 diagnosis (2,048 total generation may prematurely cap
reasoning) reproduced on our own eligible artifact, first hand at it.

Two further observations from the completed rows:

* Both completed thinking rows consumed **far more** generation than their
  baseline twins (z1: 1,619 vs 177 tokens; z2: 1,215 vs 340 tokens) yet emitted
  *shorter* final text than the baseline twin (577 vs 622 chars; 710 vs 1,101
  chars) and the answers are not identical. Direction of any accuracy effect is
  @Pewciu6's call; this wave has no authority to score it.
* Two critic rows collapsed (`z14.2`: 17+17 tokens / 34 chars; `z20.2` second
  stage: 25 tokens, 46 chars final) — degenerate outputs worth flagging for the
  grader, not edited by me.
* Latency: the slowest single row was the z1 **baseline** call at 118.0 s; the
  PF three-stage task took 11.7 s; the two completed thinking calls cost 23.5 s
  (z1) and 13.3 s (z2), the guard-stopped thinking call 20.6 s. Median across the
  22 completed rows ≈ 5.2 s. All 36 reserved chat calls returned inside the
  300 s transport bound; zero retries were made (the controller allows none).

## How these numbers were produced

Every figure above was recomputed directly from the three retained JSONL files
(`ledger.jsonl`, `answers.jsonl`, `private-envelopes.jsonl`) plus the frozen
launch manifest, by parsing each line as JSON rather than by reading the text.
The first draft of this report disagreed with the raw bytes on three points
(which row carried the 118 s latency, the completed-thinking call latencies, and
whether thinking finals were longer or shorter than their baseline twins) and was
corrected against the data; no number here is quoted from memory. No answer text
was edited, no row was dropped or re-ordered, and the 9-item / 11-point panel
denominator is untouched. Failed and unsent items stay in their denominators.

## What is preserved

Immutable, untouched: `run-1755/ledger.jsonl`, `answers.jsonl`,
`private-envelopes.jsonl` (raw requests, responses, thinking) and the terminal
backup `terminal-backup.tar.gz` (SHA256 in the private launch record). Ready for
@Pewciu6's independent grading of the 22 completed answers, scored against the
full planned denominators.
