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

## 01:16 — #117 next step: eval16 argument comparison made launch-ready (CPU only)
- Run3 evidence merged as PR #154. Worker asked root on #117 to declare the eval16 argument-improvement run.
- Greg asked for maximum progress: the watcher told the worker to prepare the eval16 comparison fully while waiting. Arms: unchanged base export vs run3 merged candidate, optional thinking-base arm. Cap 32 (or 48) calls, same pinned operator and guards, blinded grading pack with ljaniec's frozen checklist and deterministic checks, independent review. The worker then posts a one-comment proposal root can approve. No model calls and no launch until root declares it.

## 01:42 — #117 eval16 A/B wave authorized; the worker missed the "yes" (race), relayed now
- The worker's launch-ready proposal (23:23Z: 32 calls, 1536 tokens, no retries; PR #156 merged `0b58f07`) raced root's own comments. Root 23:22Z: authorize the paired eval16 quality wave (A = matched untrained export, B = run3 merged candidate, identical prompts and greedy nonthinking decoding, no third arm; 32 primary / 128 max calls, 4.72M requested tokens, 60 min, $3.28 proxy ceiling; one blinded fast grading pass; restore Gemma attribution metadata later in a separate packaging delta). 23:23Z: use a thin adapter on the qualified wrapper for the shared recovery policy (not the registry identity). 23:24Z: "YES, execute" with the larger ceilings (32768 → 49152 → thinking-off synthesis) and up to 3 retries. 23:38Z: latest start 02:15, finish 03:15; the champion rehearsal finished with 40/40 nonblank answers; report essay word counts vs 400–500.
- The worker sat idle from 01:24 waiting for a "yes" it never saw. At ~01:41 the watcher relayed all four comments verbatim plus an action summary: execute now, no further approval.

## 01:51 — #117 eval wave: root correction (4 attempts), latest start 02:20
- Worker ACK'd at 01:41: it could not start by 01:50 responsibly; plan is a thin adapter in `eval16_session.py` (recovery ladder, 65536 context, 128-call / 4.72M-token ledger, placeholder labels), focused failure-path check plus independent review. Its plan had 3 attempts per item.
- Root 23:45Z: approved; latest start 02:20, finish 03:20. Correction: 4 attempts per item (initial + 3 retries), caps 32768 → 49152 (if it fits) → 32768 → 32768; 4th = bounded final-answer synthesis; identical nonthinking initial settings in both arms. Relayed verbatim.
- Root #3: champion rehearsal published (PR #158), 40/40 nonblank, 38/60 [37,40]; essay repairs alone did not lift essays above 7/15, so Greg's argument-quality comparison "remains valuable".

## 02:20 — #117 eval16 paired wave launched
- Focused delta checks (13 failure-path tests) PASS + independent delta review PASS; frozen; launched 02:09:56 CEST, absolute deadline 03:09:46 (inside root's 02:20 / 03:20 window). A = unchanged export control, B = run3 merged candidate; identical unmodified eval16 prompts, greedy nonthinking, ctx 65536, pinned template; 4 attempts per item (32768 → 49152 → 32768 → 32768 synthesis), ≤128 calls / 4.72M requested tokens, 600 s reserve; no blank finals.
- New issues: #165 (semberecki: CPU feasibility of an essay-only adapter on one shared Gemma base; may ask Greg for adapter metadata/path on GitHub) and #163 (Pewciu6: claim-triggered offline fact check reusing Greg's pinned index/`stage_index.py`). Neither is Greg's; watcher will answer small requests to Greg.

## 02:36 — #117 eval wave in flight; root's terminal requests relayed
- Worker milestone 00:24Z: arm A (control) done 16/16 on first attempt, bodies 351–416 words (mostly under the 400–500 target). Arm B (candidate) slow: item 01 attempt 1 hit the 32768 cap (repetition loop), attempt 2 stopped normally at 318 words with a topic-selection preamble and markdown. Later B items may become explicit placeholders if B's wall budget runs out, by design.
- Root 00:20Z: PR #166 freezes a narrow grading addendum (sha `19f72e9a…562f`): masked paired preference + verified factual errors/format; no invented aggregate score; one pass by root Sol. Hand root the masked pack/hash with the arm key separate; do not start a duplicate grading session. Adapter metadata would help #165 (semberecki).
- Root 00:32Z: CPU audit (commit `6e7ad73`) finds no proven terminator/mask/template/export bug; the training data repeated 34 distinct essays for 3 epochs in fixed order (risk, not proof). At terminal preserve answer-free attempt metadata and the actual EOG config; a one-epoch checkpoint comparison happens only if quality fails and root declares it.
- Relayed both comments with a terminal action list (no own grading, masked pack to root, metadata preservation, #165 adapter-metadata pointer).

## 03:05 — #117 eval16 paired wave terminal: infrastructure PASS, candidate FAILS
- Window 02:09:56 → 02:55:46 (46 min), rc 0, 840 s left, backup verified, GPU idle. 25/128 calls, 868,352/4,718,592 requested tokens, ≈$2.5 at the unverified proxy.
- A (unchanged export): 16/16 complete on first attempt, bodies 346–412 words (median 383; only 3 meet the advisory 400–500), all with a preamble/meta opening.
- B (run3 3-epoch merged candidate): 2 complete (331, 352 words), 2 partial (runaway repetition, 18k and 15k words), 12 placeholders never attempted (arm wall budget exhausted by runaway attempts, as declared). 5 `length` finishes. EOG/stop config and served template are identical in both arms, so there is no candidate-specific EOG/template difference.
- Conclusion posted on #117: the 3-epoch candidate is not usable for essays under greedy nonthinking decoding; no quality/promotion claim. Masked pack `90211d54…c7ff` in git for root Sol's single PR #166 pass; sealed arm key off-git (`b568c54c…3d00`), available on request. Evidence PR #175 merged. The worker ran no own grading and will do no new training/inference without a root declaration (a one-epoch checkpoint comparison would need a new training run).

## 03:21 — #117 candidate rejected; next task: one-epoch plan (CPU only)
- Root (01:06Z): PR #175 accepted; the 3-epoch candidate is rejected for deployment (2/16 complete, 2 runaways, 12 placeholders vs 16/16 control). Root Sol does the single PR #166 grading pass; the sealed arm key is to be handed over via the project host handoff only after that grade is frozen.
- Next bounded task (CPU only): check whether a one-epoch / 12-step checkpoint exists; otherwise prepare the smallest exact one-epoch rerun/export plan (only epoch count changed from the audited 36-step run), with time/cost and files. No training or inference yet; the decision depends on whether the two completed trained essays show an argument benefit. If not, the adapter is parked and base-model test-time composition takes priority.
- Relayed verbatim with an action list.

## 03:35 — #117 one-epoch proposal posted (CPU only, not run)
- No 12-step checkpoint exists (the driver saves only the final adapter), so a rerun is required. Worker posted a frozen, independently checked (PASS) proposal on #117 at 03:25: a 2-line driver diff (history step bound 36→12, `epochs=1`, driver sha `a64f5d70…044a`); everything else identical to run3; epoch 1 equals run3's first 12 groups. Awaiting root's declaration, which depends on the PR #166 grade of the two complete 3-epoch essays.

## 04:06 — #117 closed out; #178 (image perspectives) claimed before the 04:15 cutoff
- Root (#178 body, 04:02): the frozen unmask shows the control wins both complete content pairs; candidate 2/16 complete vs 16/16. Do NOT start the one-epoch LoRA run. #117 is effectively finished (PRs #145/#147/#154/#156/#175/#177 merged).
- New #178, "same-model three-perspective image reasoning before the 08:00 freeze" (assigned Greg, highest priority; claim by 04:15 or root reassigns). User set a strict 08:00 development freeze; 08:00–11:00 is final checks and submission.
- Claimed at 04:05. Reused the same single H100 worker (sole worker on `matura-greg`, knows the qualified scheduler). Task: opt-in text/detail/composition descriptions plus a final answer on the same Gemma weights, direct control separate, 6 visual IDs, 30 primary / 120 max calls, exact token cap from the retry ladder, prepared manifest by ~05:15, run only after root's exact authorization, finish ≤07:20.
