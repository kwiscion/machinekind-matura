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
