# Issue watcher log — 2026-09-27 (Europe/Warsaw)

Continuation of 2026-09-26-watcher-log.md. Same watcher instance 8e5e9ed0-1189-4cc2-94b1-68da72b41e32; in-session cron every 15 min.

## 00:06 — #117 pilot run1 blocked by root driver bug; run2 authorized and relayed
- Run1 (started 23:53:25) stopped fail-closed at 44 s at stage 1 (probe): `run_real_pilot.py` line 88 `apply_chat_template(..., tokenize=True)` returns a `BatchEncoding` under pinned transformers 5.18.0.dev0, not a list. 0 optimizer steps, 0 generation calls, model never loaded, backup verified, GPU idle. ~0.31 h ≈ $1.0 proxy incl. prep. Evidence in PR #145 (merged `ec6e0aa`, CI green); report on #117, `needs-review`.
- Root (00:04): one-line fix PR #146 (`return_dict=False`, new driver sha `586acd0b…e0229`). Rerun the CPU comparison, independent review of only that change + pins, post PASS/hashes/start/deadline, then ONE fresh pilot-run2 under the same bounds; latest start still 00:30, finish 01:30; no automatic further retry; preserve run1/run2 separately with cumulative usage. Relayed verbatim to the same worker.

## 00:20 — #117 pilot-run2: real 12B backward PASS; stopped at control serving on a template false negative
- Run2 started 00:11:20 (review PASS posted first; driver PR #146 `586acd0b…e0229`; CPU tokenizer check list/30 ids/answer-only labels OK).
- Stage 1 PASS (00:12:06): real 12B synthetic backward, 88 q/v modules, 5,193,728 trainable params, 1 optimizer step, loss 0.0536, nonzero delta, peak 24.19 GB allocated. Probe adapter discarded.
- Stage 2: both control calls on the unmodified export succeeded (HTTP 200, stop; text on topic; image correctly described), clean server exit. The only failing criterion was `served_template_is_pinned_hf`: `/props` template sha `6a1015c4…` vs raw pinned HF `chat_template.jinja` `ae53464b…` (server-side normalization; worker calls it a false negative). Stopped fail-closed at 00:14:53, no retry. Totals: 1 optimizer step, 2 generation calls. Evidence PR #147 merged (`04f1b27`, CI green); terminal report on #117, `needs-review`.
- Worker is waiting for root's decision (redo control calls or reuse run2's verified control evidence) and will not start anything without a new declaration. Pilot latest finish 01:30.
