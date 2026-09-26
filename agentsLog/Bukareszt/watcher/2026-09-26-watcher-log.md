# Issue watcher log — 2026-09-26 (Europe/Warsaw)

Agent: Greg's issue watcher. Orca worktree `Watch-for-tasks`, instance `8e5e9ed0-1189-4cc2-94b1-68da72b41e32`. Scheduler: live in-session cron every 15 min (minutes 4,19,34,49), ends 08:30 Warsaw.

## 01:30 — started
- Repo had 0 issues; `@Bukareszt` had read-only access. Forked to `Bukareszt/machinekind-matura`, opened PR #1 (agentsLog scaffolding). Fixed `/usr/local/bin/orca` symlink permissions (root-owned 0700 -> 755).

## 02:05 — tick found issues #3 and #6
- Accepted the pending write invitation; push access verified (`permissions.push=true`).
- Lead's feedback in #3 on PR #1: rebase, reconcile with `AGENTS.md`/upstream `agentsLog/README.md`, no shared mutable state, duplicate-dispatch and cutoff risk, dry-run evidence.
- Claimed #6 (comment with session ID/start/ETA, `ready` -> `in-progress`, assignee `Bukareszt`).
- Dispatched Orca worktree `issue-6-Bukareszt-retrieval` (branch of same name from `origin/main` @ 9913d45, terminal `term_2f687bea-cfa1-456c-9383-4974f2702275`, Claude in bypass-permissions mode) with the full brief + issue text.

## 02:15 — PR #1 rework (this revision)
- Rebuilt on `origin/main` @ 9913d45: upstream `agentsLog/README.md` untouched; everything under `agentsLog/Bukareszt/`.
- Mutable `watcher-state.json` moved to `agentsLog/Bukareszt/private/` (gitignored by upstream `.gitignore`).
- Duplicate-dispatch guard: poll script reports `claimed` (in-progress label or existing claim comment); watcher dispatches only unclaimed issues and keeps one worker per issue.
- Cutoff: watcher prompt stops polling at 08:30 Warsaw and posts a final status on #6/#3.
- Dry-run evidence, `poll-issues.sh` at 02:08 Warsaw:
  `[{"number":6,"title":"Licensed offline historical retrieval and evidence checks","labels":["overnight","in-progress"],"claimed":true,"assignees":["Bukareszt"]},{"number":3,"title":"Overnight lead: integration, split control, and Sunday freeze","labels":["overnight","in-progress"],"claimed":true,"assignees":["kwiscion"]}]`

## Limits
- Cron is in-session only (dies with the session, 7-day expiry); a re-run on session restart is needed. Not a daemon beyond this session.
- Watcher uses no model/data/source material; no purchases.

## 02:40 — #6 delivered
- Worker (Orca worktree `issue-6-Bukareszt-retrieval`) finished at 02:31 Warsaw: PR #12 merged to `main` (merge commit `4bba768`), handoff comment posted on #6, label `in-progress` -> `needs-review`, assignee `Bukareszt`. Note: the worker's own comment/README timestamps say "04:00/04:15 Warsaw"; wall clock was 02:31 (worker time-labeling error, content unaffected).
- Delivered: 107 licensed sources (100 pl.wikipedia CC BY-SA 4.0 w/ oldid+SHA-256, 7 Wikisource PD acts), stdlib BM25 + hybrid + chrono modes, 40 TRAIN queries, two independent citation audits, rights scan, `reports/REPORT.md`. Recommended: `--mode chrono --k 5`. No purchases, no paid APIs, no exam material.
- No follow-up issue opened (nothing blocking; cheap next steps are listed in the report for the lead).
- Lesson: watcher and worker both wrote `agentsLog/Bukareszt/README.md` (add/add conflict, resolved by the worker; watcher section kept). Future workers: merge `origin/main` before opening a PR.
- Watcher branch reset onto `origin/main` @ 4bba768 to avoid re-conflicting; polling continues until 08:30.

## 03:10 — #6 closed by lead; #15 claimed and dispatched
- Lead accepted and closed #6 (00:58Z) after Sol review; integration is on `main` (`985aaf0`, see `docs/inference.md`).
- New optional follow-up #15 (context selection for complete answer support) assigned to `@Bukareszt`, `ready`, unclaimed. Precondition (no active #6 worker) met.
- Claimed #15 (comment with session/start/ETA, `ready` -> `in-progress`) and dispatched Orca worktree `issue-15-Bukareszt-context` (branch of same name from `origin/main` @ 985aaf0, terminal `term_72a1c7ff-55c5-4c7f-a1f6-087ba4e694ce`). Timebox 90 min; first slice due 04:10; handoff by ~04:45.
- Workers so far: 2 (#6 done, #15 running). Cap 3 before 08:00.

## 03:36 — #15 delivered
- Worker (Orca worktree `issue-15-Bukareszt-context`) finished 03:22 Warsaw: PR #17 merged (`68fdc55`, CI `stdlib-tests` green), handoff comment on #15, label `in-progress` -> `needs-review`. Result: no measurable gain in complete-answer support over the frozen #6 baseline; reported as a negative result with blind audit, commands, hashes, examples, limits (report under `agentsLog/Bukareszt/`).
- No follow-up issue (no blocker). Workers used: 2 of 3 (#6, #15 both done). Polling continues until 08:30.

## 08:36 — cutoff, polling stopped
- Final tick: no new issues for `@Bukareszt`; #15 still `needs-review` (lead); #6 closed. No running workers.
- Final status posted on #3. Scheduler (in-session cron, 15 min) deleted. Ticks ran 01:30–08:36 Warsaw; 2 workers dispatched (#6, #15), both delivered and merged; 0 purchases; 0 follow-up issues.
- Restart the watcher (new cron) if the lead assigns more work after the 09:00 review.

## 11:01 — watcher restarted by Greg
- Polling resumed (in-session cron, every 15 min, no fixed stop; final freeze 2026-09-27 11:00 Warsaw respected).
- Since cutoff: #15 closed by lead at 08:47 as an accepted negative experiment (chrono k=5 baseline kept). Lead's morning status on #3 (08:50) assigns no new work to `@Bukareszt`. Open PR #23 (lead draft) does not mention Greg. No running workers.

## 13:00 — lead course correction (best score only)
- Lead's 12:45 comment on #3: retrieval directive for `@Bukareszt` = keep chrono k=5, index `350800b1…0429`, rebuild on the inference machine when the RAG arm starts, no new retriever before the scorecard; #6/#15 stay closed. New issue #33 (best-score baseline) is owned by `@semberecki`, not Greg.
- Watcher replied on #3 with the exact rebuild recipe (fetch/index/graph/query commands, expected 107 sources / 3481 chunks / index hash) for the GPU owner. No worker dispatched (no task for Greg; rebuild happens on a machine we don't control).

## 14:45 — #37 claimed and dispatched
- Lead opened #37 "Organizer package to offline answers.json — Greg" (assigned `@Bukareszt`, `ready`, lead comment: start now, 45-min slice, 90-min PR, team target 48/60 by 18:00). #38 (Lukasz, RTX 5090 runtime handoff) references Greg's adapter contract but is not Greg's.
- Claimed #37 (comment with session/start/ETA, `ready` -> `in-progress`) and dispatched Orca worktree `issue-37-Bukareszt-submission-adapter` (branch of same name from `origin/main` @ edd6e01, terminal `term_2a83ab04-1524-4aa7-8fd5-4be51f9c8392`). Scope: `scripts/Bukareszt/` + `agentsLog/Bukareszt/`; mock contents gitignored; no GPU, no purchases.
- Note: poll script's `claimed` heuristic flagged #37 as claimed because the lead's comment contains the word "claim"; the watcher checked labels/comments manually. Heuristic to tighten later (match "claiming" by a non-lead author or `in-progress` label only).

## 14:57 — #37 first slice accepted with one P2; relayed to worker
- Worker pushed first slice `b59eaad` at 14:46 (6 min after claim): stdlib CLI `scripts/Bukareszt/matura_package.py` (fetch-mock/check/prepare/finalize/validate/run/synthetic-outputs), real-mock aggregates confirmed (37 items / 60 points / 19 PNGs, hashes pinned), 29+ tests. Progress comment posted on #37.
- Lead's Sol review (12:54Z): core integration passes; P2 = `finalize --report` may collide with `--output` and overwrite answers.json while exiting 0. Fix + regression required before acceptance. Essay budget warning accepted, no 512-token limit.
- Watcher relayed the P2 and the WINNING_PLAN.md pointer to the worker terminal (`orca terminal send`). Worker still active (40 tests passing, rerunning real-mock evidence).
- Lead's #3 checkpoint 14:51: WINNING_PLAN.md merged (#40), 48/60 target by 18:00, Greg's #37 noted as started; next gate 15:15 (not Greg's).

## 15:10 — #37 delivered
- Worker finished 14:58 Warsaw (18 min after claim): lead's P2 (report/output path collision + input/template overwrite guard) fixed in `7944429` with regression tests; PR #42 merged (CI: 2/2 green); handoff comment posted on #37; label `in-progress` -> `needs-review`.
- Delivered: `scripts/Bukareszt/matura_package.py` (stdlib; fetch-mock/check/prepare/finalize/validate/run/synthetic-outputs), pinned mock hashes + aggregate acquisition manifest under `agentsLog/Bukareszt/submission/`, tests on invented fixtures, report. No model run, no score claimed, mock contents gitignored.
- Workers today: #6, #15, #37 all done; none running.

## 15:30 — #37 closed by lead; #44 and #45 claimed and dispatched
- Lead closed #37 (15:15) after acceptance. Two new items for Greg:
  - #44 "stage the pinned chrono index for offline GPU inference" (lead, assigned `@Bukareszt`, `ready`; precondition #37/#42 met). Claimed; Orca worktree `issue-44-Bukareszt-stage-index` (from `origin/main` @ e0daf40, terminal `term_f9064351-fc62-453c-b88b-dee91d43d50d`). First artifact due 30 min, handoff PR 60 min, then short notes on #33/#38.
  - #45 "Submission adapter: reject unverified completion and missing source fields" (filed by `@ljaniec` from #38 review; implementation is Greg's adapter). Claimed implementation (in-progress, `Bukareszt` added as assignee, ljaniec keeps acceptance); Orca worktree `issue-45-Bukareszt-adapter-fix` (terminal `term_062c5e7f-b72c-45ee-a5e7-88af5a3075c8`). Fix + tests due 30 min, PR 45 min.
- Both workers told about each other (disjoint files) and to re-merge `origin/main` before PR. Concurrent workers: 2 of 3.

## 15:40 — #45 delivered; #44 PR open
- #45 worker finished 15:31 (about 6 min after dispatch): PR #48 merged (`b64081b`), explicit completion set required, any non-null error = failure, absent `instructions`/`source_text` rejected, regression tests added; handoff posted for `@ljaniec` acceptance; `needs-review`; issue closed 15:31.
- #44 worker: first artifact `1cf19ad` pushed (`scripts/Bukareszt/stage_index.py`, one-command staging with offline identity proof), progress comment posted, PR #50 open at 15:37 (inside the 30-min target); worker's reviewer subagent is checking `verify_staged` before merge. Still running.

## 15:58 — #44 merged, lead hold arrived a minute late; follow-up dispatched
- #44 worker finished 15:47: PR #50 merged (`dcdd047`, CI 2/2 green), handoff on #44, `needs-review`; lead closed #44. Lead's hold request (15:48:06) arrived ~1 min after the self-merge (15:46:58); watcher acknowledged the timing on #44.
- Lead's portability review found: Windows CRLF checkout changes `sources.jsonl` hash (`701ad15…` vs pinned `8b77a63a…`, no .gitattributes), and a retriever hash mismatch at `stage_index.py:531` is recorded, not rejected. Requested a narrow fix.
- Dispatched Orca worktree `issue-44-Bukareszt-identity-fix` (from `origin/main` @ a8f4c79, terminal `term_6014ec99-9ba5-48af-b432-c756b314987c`): LF-normalized identity hashing + CRLF regression tests, fail-closed hash mismatch, no root .gitattributes (recommendation only). Worker told NOT to self-merge; wait for lead review. PR due 30 min.
- Lead's #3 note 15:40 (Gemma baseline done, format run ownership conflict) assigns nothing to Greg.

## 16:12 — #54 (formal #44 follow-up) claimed for the running worker
- Lead opened #54 "finish staging portability and destination guards" (assigned Greg, 30-min target) with three blockers: normal CRLF checkout identity (scoped .gitattributes now authorized), validate `--root`/destinations before recursive replacement, validate retriever hash before import in `load_retrieval()`.
- The follow-up worker had already opened PR #55 (held, not self-merged) covering LF-normalized hashing + fail-closed mismatch. Watcher claimed #54 for that same worker (no second worker), relayed the three blockers into its terminal, asked for an updated PR #55 + `needs-review` on #54.
- Lead's 16:08 checkpoint (#3): Gemma 35/60 is the working baseline (PR #53); "Greg handles #54/#55". Nothing else for Greg.

## 16:26 — #54 awaiting root review; #57 queued
- #54 worker folded all three blockers into PR #55 (CRLF-safe identity + scoped .gitattributes, destination/root guards, hash-before-import), addressed root's follow-up review (report-path symlink escape) at `715b56a`; #54 set `needs-review`; PR held for root's review; worker polls until ~17:00.
- New #57 "prepare bounded offline retrieval input for next measured arm" (assigned Greg, target 16:45) has precondition "start after #54 is accepted". Not met yet; watcher posted a queued note on #57 and offered a parallel start if root wants it. Will dispatch on the tick after acceptance (or on root's go-ahead).

## 16:42 — #54 accepted; #57 claimed and dispatched
- Root approved and merged PR #55 at 16:27 (CRLF identity, verified-byte imports, destination and report write-path guards); #54 closed and accepted. Root: "proceed to queued #57; no inference".
- Claimed #57 (bounded offline retrieval input for the next measured arm; assigned Greg) and dispatched Orca worktree `issue-57-Bukareszt-bounded-rag-input` (from `origin/main` @ 9ff6277, terminal `term_ff10a9f2-a522-4a93-9303-944c181b2bf9`). Constraints: separate owned script, query = original prompt only, chrono k=3 / tw 1.0 / 1600-char budget incl. headers, identity validation + socket guard, private outputs, zero model calls. First slice 25 min, PR 45 min; 16:45 target will slip ~30 min (acceptance landed 16:27) — stated on #57.
- Workers today: #6, #15, #37, #45, #44, #54 done; #57 running (1 of 3).

## 16:55 — #57 delivered
- Worker finished ~16:47 (about 8 min after dispatch): `scripts/Bukareszt/prepare_bounded_rag.py` + tests, report, synthetic fixture, real-index aggregate; PR #60 merged (CI green, scoped); handoff posted on #57; the PR's "Closes" keyword auto-closed #57, worker reopened it with `needs-review` for root's acceptance and settings decision. Zero model calls.
- Workers today: #6, #15, #37, #45, #44, #54, #57 all done; none running.

## 17:12 — #57 accepted; #62 claimed and dispatched
- Root accepted #57 at 17:00 after independent review of PR #60 (18 tests + wrong-pin sentinel + 1,301 budget checks); root's laptop worker now runs the frozen 40-case bare source-v2 RAG attempt (k3/1600, no policy). #57 closed.
- New #62 "opt-in bounded retrieval for organizer-package runner" (assigned Greg; precondition #57 accepted). Claimed; Orca worktree `issue-62-Bukareszt-optin-rag-runner` dispatched (terminal in private state). Targets: slice ~17:25, PR + handoff ~17:35; PR held for lead integration review (changes accepted submission flow). Zero model calls.

## 17:25 — #62 PR open and held for lead review
- Worker pushed `a286b8b` and opened PR #68 at 17:14 (ahead of root's 17:30 target): `matura_package.py run --bounded-rag` (opt-in, k=3 / 1600 chars, no policy), original input+manifest preserved, fresh RAG input + trace, pins validated before any call, finalize on original manifest, default path unchanged; tests incl. dry-run of both paths. Handoff posted on #62, `needs-review`; PR NOT self-merged (integration review is root's). Worker polls PR/issue until ~18:15 to address review comments.

## 17:40 — #62 accepted
- Root approved and merged PR #68 at 17:24 (84 tests at exact head); #62 closed, RAG stays opt-in pending score-based selection. Root: stand by for concrete final-package issues from #66 / offline rehearsal, no new retrieval work.
- Workers today: #6, #15, #37, #45, #44, #54, #57, #62 all done.

## 17:43 — #72 claimed and dispatched
- New #72 "optional explicit temperature for a measured single-pass candidate" (assigned Greg; lead-authorized scope exception for one optional `temperature` field in shared `infer.py`; DO NOT MERGE, root reviews after the active run). Claimed; Orca worktree `issue-72-Bukareszt-explicit-temperature` dispatched (terminal in private state). Root's 17:40 target missed by construction (issue filed 17:27, #62 accepted 17:24); ETA stated on #72: slice ~18:00, PR ~18:15.

## 17:55 — #72 delivered and merged by root
- Worker opened PR #77 at 17:43 (optional `temperature` in `infer.py`: finite 0–2, forwarded only when supplied, omitted payload byte-identical; pinned Ollama 0.30.7 conversion cited from primary source; experimental non-promoted Gemma temp-0.2 candidate config under owned paths; tests), handoff on #72, `needs-review`, held per instruction. Root's review asked for one narrow fix (bounds check before `isfinite` for huge ints) -> `568ed70`; root merged #77 at 17:52 (`1f25930`). #72 stays open `needs-review` for root's closure.
- Workers today: #6, #15, #37, #45, #44, #54, #57, #62, #72 all delivered; none running.

## 18:12 — #83 claimed and dispatched
- New #83 "make qualified offline launcher portable to central H100" (assigned Greg; integration exception to refactor root's #82 launcher/helper via an explicit frozen runtime profile; hold PR for lead review; slice 18:30 / PR 18:45). Claimed; Orca worktree `issue-83-Bukareszt-portable-launcher` dispatched (terminal in private state). ETA stated on #83: slice ~18:35, PR ~18:50, not merged.
- #38 lead note (16:02Z) to Lukasz mentions H100 readiness under #81; nothing else for Greg. #88 (RTX handoff repair) is not Greg's.

## 18:25 — #83 PR open and held for lead review
- Worker opened PR #93 at 18:17 (ahead of root's 18:45 target): `--runtime-profile PATH` on the #82 launcher (omitted = built-in laptop WSL 0.30.7 / ctx 4096 profile, behavior unchanged), native-Linux H100 profile template with placeholders the launcher refuses, every manifest blob verified, hard mismatch failures, profile hash in provenance, tests; profile doc + README note under owned paths. Handoff on #83, `needs-review`, NOT merged; worker polls for root's review until ~19:15.

## 18:45 — #83 accepted and merged by root; #96 claimed and dispatched
- Root's independent review accepted PR #93 at `9ad8b14` (30 CPU tests + 7 fail-closed checks) and merged it 18:39; H100 qualification stays root-owned (#81). Root asked for the two nonblocking provenance wording nits as a scoped follow-up: relayed to the #83 worker (tiny held PR on `issue-83-Bukareszt-provenance-wording`).
- Root's evening plan (#3, 18:39): Greg's active track is #96 (query decontamination ablations, question-only evidence router, relevance gate, selective RAG; CPU now, H100 offered but not ready; first-wave review 19:30, selection 20:30, target 22:00).
- Claimed #96; Orca worktree `issue-96-Bukareszt-selective-rag` dispatched (terminal in private state). ETA on #96: ranking table ~19:15, held PR + GPU proposal ~19:45.

## 18:55 — #83 nits merged; #96 first findings posted
- #83 provenance-wording follow-up PR #98 merged by root (no behavior change). #83 worker finished.
- #96 worker pushed `a527894` (CPU rank ablations for query decontamination on synthetic + TRAIN fixtures, 28 fixture cases, pinned index staged from the #44 bundle, socket-guarded) and posted first findings on #96 at 18:53, ahead of the 19:15 ETA. Continuing with the evidence router / relevance gate and the held PR.

## 19:10 — #96 PR open and held for root
- Worker opened PR #104 at 18:57 (ahead of the 19:45 ETA): opt-in `scripts/Bukareszt/selective_rag.py` (query decontamination, question-only evidence router, zero-hit relevance gate, one compact passage, opt-in prepare with paired cases), tests, report with ablation ranking tables, 12-pair GPU proposal; handoff on #96, `needs-review`, NOT merged (root owns launch/merge). Worker polls for review until ~19:57.

## 19:27 — #96 becomes the factual-evidence lab; dedicated H100 assigned
- Root's review of PR #104 found three routing/relevance defects; worker fixed them (`66cd33a`, `6b3c519`), 68 tests; built May 2024 question-only source-v2 locally (hash identical to root's, no keys): corrected router changes only 5/40 prompts, so the paired proposal shrinks to 5 pairs / 10 calls. PR still held pending root's independent correctness review.
- Owner/root confirmed a dedicated H100 for Greg (instance `matura-greg`, Brev `sx8ihq0wx`, org `kwiscion-ff7442-omfi`, hyperstack H100, running/idle, no Ollama/weights yet). Worker installed the Brev CLI, inspected read-only, provisioned nothing, posted the claim on #96 with an unknown hourly rate flagged; instance is billing while idle (owner's instance, owner's call).
- Root's envelope for Greg's wave: 12 pairs/24 calls after review, then one recorded 90-min wave, ≤120 calls, ≤240k requested tokens, ≤4 mechanism families, ledger with hashes/rate/cost; public findings; independent grading on #11; no purchases.
- Watcher relayed to the #96 worker: keep the session alive, do host readiness now (Ollama 0.34.4, pinned Gemma, profile fill, launcher qualification, 2 synthetic calls), never buy/provision/resize/stop instances, no paired calls before root's review, then run the wave inside the envelope. Greg's "never buy" rule holds: the H100 is owner-provisioned, not purchased by us.

## 19:40 — PR #104 merged; H100 ready; 5-pair diagnostic authorized
- Root: start runtime/weight setup now on the owner-provisioned GPU; record `rate_unverified: true`, actual elapsed time, and a labeled planning estimate using the central rate as proxy; hard controls stay 90 min / 120 calls / 240k tokens.
- Worker posted READY at 19:33: Ollama 0.34.4 (exec hash identical to the central H100), `gemma4:12b-it-q4_K_M` pulled into project-owned paths, every manifest blob verified (7,556,497,632 B), single worker on host, launcher qualification passed. No purchase; owner-provisioned instance.
- Root merged PR #104 at reviewed head `6b3c519` (35 Linux tests + reproduced ablations) at 19:32 and authorized the declared 5-pair / 10-call diagnostic within the standing wave, baseline control kept, exact outputs published for independent grading. Worker is running it now.

## 19:55 — #96 H100 wave 1 complete, ungraded; root's W1 grade: no gain
- Worker ran wave 1 on `matura-greg` 19:36–19:42: 70 calls (W1 5 pairs = 10, W2 fixed subset S10 = 60), 0 errors/retries, 71,680 requested tokens, 4 families, isolated namespace, ≈$1.0 at the central-rate proxy (`rate_unverified: true`); exact answers + ledger pushed (`2701ba0`, `agentsLog/Bukareszt/issue96/wave/`). Not graded by us.
- Root's independent W1 grading: bare 1/5 vs corrected selective 1/5, no observed gain; specific misses listed. Root: do not expand corrected-selective on fixture gains; W2's 40 finals go to a separate Sol reviewer; wait for W2 scores before spending the remaining ~50 calls. Worker is waiting accordingly.

## 20:10 — #96 wave closed (no gain); network outage on the watcher host
- W2 independent grading recorded: no gain for any of the 4 mechanisms (corrected selective RAG 1/5 vs bare 1/5 earlier; retrieve+relevance-check 2/4, model-written query 4/4 vs 4/4 control, fact cards 2/4). Worker closed the wave without replication (nothing promising; 4-family limit used), 72/120 calls and 73,728/240,000 tokens used, 48 calls unspent; 9-item disjoint subset prepared but unused. Results + stop recorded in `agentsLog/Bukareszt/issue96/wave/README.md` (`286398d`), closing handoff posted on #96 at ~20:06. Takeaway: with the 107-article corpus, added encyclopedia context does not help and sometimes hurts; reviewer points to reading the exam's own sources/images better (Piotrek's track).
- `matura-greg` H100 is idle but still running/billing (owner-provisioned); nothing running on it; runtime + model kept in `~/mm` for reuse. Worker left the stop decision to Greg/root (correct: not ours to stop without instruction). Session stopped.
- GitHub unreachable from the watcher host at 20:09 ("network is unreachable" / DNS); verification of the pushed handoff and this log's push deferred to the next tick.

## 20:45 — network restored; #96 closed; #117 claimed and dispatched
- Watcher host network back ~20:43. #96 closed by root 20:22 (independent review: no secure gain; negative artifacts preserved; no more RAG variants).
- New #117 (grounded essay SFT corpus + format-repair pairs) was assigned to Greg at ~20:20 during the outage; root pinged twice and started temporary coverage (Astra seed 4+4, Sol worker up to 8+8). Claimed at 20:45 with root's narrowed scope: canonical source grouping/dedup + train/eval leakage check, separate original 16-topic eval set, expansion only on undeclared topics, all drafts until independently reviewed.
- Dispatched Orca worktree `issue-117-Bukareszt-essay-corpus` (from `origin/main` @ 1794f5b, terminal `term_7c59be6e-6610-4b5a-8c7c-f6d0ee29b326`). No training/GPU/HF/purchases.
- H100 `matura-greg` remains idle and billing (owner-provisioned); not part of #117; stop decision left to Greg/root.
