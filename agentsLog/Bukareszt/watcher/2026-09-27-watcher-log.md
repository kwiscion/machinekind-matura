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

## 04:23 — #178 in progress; corrected source-crop package unavailable to Greg
- Root 02:13Z: claim acknowledged, H100 stays Greg's; panel changed BEFORE any calls to IDs 6, 14.1, 18, 25, 1, 23.2 (four known visual failures + two controls; a diagnostic, not a full-exam estimate); reuse the PR #176 two-stage wrapper structure; keep the strategy portable to Qwen; report any difference from central Ollama Gemma.
- Worker 02:22Z: applied the new panel; the corrected source-crop package (`e93b7488…aac6`) is on neither the Mac nor `matura-greg`, and the worker will not route it around the approval block. Building the source-independent implementation with the public tiny-package fixture plus synthetic images; asked root to place the package privately on `matura-greg` (verified on arrival, never committed).
- Root 02:06Z on #117: frozen grade unmasked; control wins both completed content pairs (8/11 vs 1/11, 12/15 vs 7/15); run3 and further automatic training parked; one-epoch NOT authorized; reports merged via #179.

## 05:17 — #178 input gate cleared; relayed to worker
- Root 02:51Z: prepared the six-item input package (IDs 6, 14.1, 18, 25, 1, 23.2; 9 points; 7 PNGs; sha `8d458388…05e8`); automatic approval first rejected the private transfer, and root requested the owner's approval. A second project session posted a collaborator-only draft GitHub release with the full package (owner approved delivery via GitHub).
- Root 03:00Z (05:00 CEST): the owner explicitly approved; root copied and remotely verified `source-six.tar.gz` on `matura-greg` at `/ephemeral/mm-lora/private-inputs/may2024-source-crops-v1/`. No source gate remains; use one verified input path. Root asks for the PREPARED code/tests/manifest for immediate review.
- The worker has been in one long turn (~1h11m) building the implementation; relayed the cleared gate, the single input path (not the draft release), the privacy rule, and the 07:20 finish / 08:00 freeze.
- Team status (#3, PR #185): corrected Gemma 39/60, Qwen 36/60; the full Polish Wikipedia (1.59M articles) is indexed by root.

## 05:35 — #178 PREPARED + independent review PASS; awaiting root "go"
- Worker posted the PREPARED recipe at 05:21 and the independent focused review PASS at 05:22 (commit `7d250fa`, not run). Host claim: sole worker on `matura-greg`, 0 GPU processes, Ollama not started. Input: root's verified `source-six.tar.gz` (`8d458388…05e8`) normalized via the standard adapter to `prepared-six.jsonl` (`b8171f4f…25fb`), kept private under `/ephemeral/mm-lora/private-inputs/`.
- Same registry Gemma4 Q4 + projector blobs (7,556,497,632 B) for every call, one owned pinned llama.cpp `fcb3074f` server, template gate `36e3a42e…`. Session `5314efaa…`, operator `da396fee…`, pins `3fa629c9…`; cap 120 attempts / 4,423,680 requested tokens enforced before dispatch; answer-only exports.
- Review note: this direct control is llama.cpp-served, not the Ollama organizer path, so compare arms within this wave only (not vs 39/60). Run ~5–8 min; latest sensible start 06:15 (finish ≤07:20). The worker will not start without root's authorization and will say so on #178 if none arrives by 06:15.

## 06:05 — #178 GO; wave launched; root grants a standing go
- Root (03:52Z = 05:52): "go! And assume go decision for every further experiment/run. Just get it done." The worker launched the #178 wave at 05:55:12 CEST (absolute deadline 06:55:02; `wave.env` `b26aee72…47f0`; reviewed session/operator/launch/pins unchanged; 30 primary / ≤120 attempts / ≤4,423,680 tokens).
- Watcher relayed the standing go to the worker, with fixed limits: nothing past the 08:00 freeze (plan to end by ~07:45), bounded runs with guards, one worker on the host, no purchases or instance changes, no final-exam access, private inputs out of git; stop and hand off if no gain.

## 06:20 — #178 terminal: v2 wave complete; answers handed to root
- Wave 1 (05:55) was stopped cleanly after item 14.1's text-transcription view looped to the 32768 cap under greedy decoding, since continuing would have starved later items of even their direct answers (rc 143, backup verified, evidence kept).
- v2 under the standing go (06:09:45, deadline 07:09:35): identical weights, template and sampling; full ladder kept for direct and final calls; only the three view calls capped at one 2048-token attempt (a truncated view kept as a labelled partial). Focused test 17/17 PASS; cap 66 attempts / 1,806,336 tokens.
- Result: terminal PASS in 2 min 20 s; 30/30 calls; direct 6/6 and perspectives 6/6 complete, 0 blanks, 0 placeholders. Decision unchanged on 14.1, 18, 1 and 23.2; changed on open items 6 and 25. Descriptions plausibly introduced false facts (item 6 swaps knights for "Christ on the cross"; spurious map dates on 14.1; "a soldier in Polish dress with a cape" on 18; transcription typos; the loop). Overhead 5× calls per image item. Answer-only exports posted on #178 for root's single grade pass; raw views stay private on the host. #178 `needs-review`. GPU idle; the worker starts nothing new before the 08:00 freeze unless a specific task arrives.

## 07:21 — #178 graded and closed; final CPU packaging audit assigned
- Root's sole masked grade of #178 (PR #187 head `14f69be6`): direct 4/9 vs three-view 3/9 (item 6 dropped 2→1; both fail the map dating and the cartoon). Not promoted; PR #187 retained as evidence; no more GPU work.
- Root's final integration dispatch (#3, 07:09): GPU experiments are terminal; freeze 08:00; Greg to provide a concise CPU-only final packaging audit on #3 (template IDs/schema, linked PNGs, complete inputs, no blank finals, no online dependency), without accessing the final package or launching inference. Measured fallback Gemma 39/60.
- Relayed to the same worker with a stop-at-07:55 instruction.

## 07:35 — final packaging audit posted on #3 (07:22)
- CPU-only audit of `origin/main` @ `461a779` (root's recovery runtime and native package path) against Greg's `matura_package.py` contract, using public fixtures only (no final package, no inference, no GPU).
- One actionable finding: `run_native_package.py:29-35` PINS hold CRLF working-tree hashes for `infer.py`, `scripts/Bukareszt/matura_package.py` and `agentsLog/kwiscion/offline_rehearsal.py`. On any LF checkout `prepare_native_package.py:52` raises "Reviewed dependency changed", so the final package can only be prepared on the Windows checkout that made the pins. Fix: prepare on that Windows checkout, or add scoped `eol=lf` attributes and switch to the LF hashes. The other checked items (template IDs/schema, linked PNGs, complete inputs, no blank finals, size limits, offline) had no blocker.
- No shared files edited; the H100 is idle. Greg's work is complete before the 08:00 freeze.

## 08:05 — development freeze passed
- 08:00 development freeze reached. No Greg workers running, no GPU work, the H100 idle. From now until 11:00 only final checks/run/submission (root-owned); Greg's side dispatches nothing new and only answers small requests addressed to him. Never request final exam access.

## 08:20 — root final freeze notice
- Root (#3, 08:10): all model/prompt/harness experiments stopped; root owns final acquisition, execution and submission; nobody else requests final questions or changes submitted projects. Selected code `afd9ccd5` (PR #188): generic coverage wrapper with Qwen3.5:9b plus the autonomous recovery runtime. No RAG, LoRA, vision ensemble or factual referee enabled. Selected full run 40/60 (32+8), 40/40 complete, 44 calls in 28 min, all 4 timeouts recovered (48/60 target not reached). Qwen-only final cache staged and verified before 08:00 (6,594,475,420 B, Ollama 0.34.4).
- Nothing for Greg to do. Watcher keeps polling for requests only.
