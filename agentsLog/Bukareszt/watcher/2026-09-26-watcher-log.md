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
