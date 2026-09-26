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
