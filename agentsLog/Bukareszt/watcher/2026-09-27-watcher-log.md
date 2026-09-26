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

## 00:48 — #117 run3 authorized but the 00:45 start was missed (network outage); blocker reported
- Root 22:20Z (00:20): reuse run2's valid probe and two control responses (no repeats); run2 stays terminal FAIL; the independent agent must verify the template normalization (pinned llama.cpp lexer: CRLF->LF + one terminal newline -> /props sha `6a1015c4…ab82`) against raw artifacts with no model calls, then create a separate requalification record and freeze changed code/manifests; run3 authorized for the history steps. Root 22:34Z: acknowledge now, latest start 00:45, report a blocker rather than extend.
- The watcher host lost network around 00:30; neither comment reached the worker, which sat idle waiting after run2 (00:15). Latest start passed. Watcher posted the missed-window blocker on #117 at ~00:48 and relayed the no-model-call verification/freeze steps to the same worker, with an explicit instruction not to launch until root sets a new time.

## 00:52 — owner priority reset
- Owner (#3, 22:47Z): WINNING_PLAN centers on one reusable final harness (root Sol) and useful test-time compute; overrides historical no-retry/double-grading/per-candidate-rehearsal rules. "Greg continues LoRA." Requesting final questions freezes every project: no final access during development. One fast grading pass per experiment.
- Relayed to the #117 worker. Added the never-request-final-access rule to `AGENT_BRIEF.md` so every future Greg worker inherits it.

## 00:50 — #117 new run3 window
- Root (22:49Z = 00:49): resume after the narrow CPU normalization check; run3 latest start 01:30, latest finish 02:30, ≤60 min from actual start; bounds unchanged (reuse probe/control, ≤36 fresh history steps, 2 new candidate calls × 512 tokens, no new synthetic/control calls); no further approval round. After a viable adapter/merged export, evaluate argument improvement first; no new framework or long documentation.
- Worker has pushed the run3 continuation code (`68e7557`, template criterion only, history-start operator, requalification builder, not launched) and its independent agent is verifying the llama.cpp source vs the tarball. Relayed the new window verbatim.

## 01:10 — #117 pilot-run3 running
- Template requalification PASS with no model calls (pinned llama.cpp `fcb3074f` source locators; GGUF template = raw HF `ae53464b…`; C++ regression against pinned `libllama-common.so` reproduces `/props` `6a1015c4…ab82` via CRLF/CR→LF + one trailing newline removed); delta review PASS; requalification record `e88309c`.
- Run3 launched 00:59:08, absolute deadline 01:58:58 (inside root's 01:30 latest start / 02:30 latest finish). Runs detached on the host under its own deadline guards.
- The Mac's network is intermittent (GitHub API and SSH to the host failing at times ~01:08); the worker is retrying its status checks. The on-host wave is unaffected.

## 01:14 — #117 pilot-run3 terminal: ALL STAGES PASS
- Wave 00:59:08 → 01:10:37 (11.5 min), rc 0, backup verified, GPU idle, no wave process left.
- 36/36 history optimizer steps on the 90 cleared rows from a fresh pristine base (325 s; peak 34.39 GB allocated). Loss per epoch falls (epoch 1 2.45→0.44, epoch 3 ≈1.08→0.28–0.44), with recurring spikes at the same row groups. All 11 multimodal tensor hashes unchanged after merge.
- Export via the same pinned converter/quantizer: candidate Q4_K_M 7,381,382,848 B + projector 175,115,200 B = 7,556,498,048 B, within the 8.8 GB aggregate cap (one merged model + projector). Adapter 20 MB and merged BF16 23 GB stay on the dev host.
- Explicitly a training/serving pilot, not an essay-quality claim; next per root is evaluating argument improvement. Terminal handoff posted on #117 (23:13Z); worker is still copying evidence over the slow link before its PR.
