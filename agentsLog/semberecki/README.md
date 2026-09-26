# agentsLog/semberecki/ — Piotr (`@semberecki`)

Shared knowledge center for Piotr's work on `machinekind-matura`. Reports,
artifacts and handoffs live here; scripts and machine-local state elsewhere.

## Ownership

- GitHub: `semberecki` (Piotr). `Pewciu6` is Paweł Litwin — a different person.
- Issue #33: RTX 5090 Gemma readiness and next measured improvement (GPU
  candidate execution). Claimed 17:15 CEST 2026-09-26, session
  `01a0de3f-e03d-75ba-8a97-eb400acb36a2`, label `in-progress`.

## Files

- `2026-09-26-session-summary.md` — previous Claude Code session handoff
  (~14:49–17:05 CEST) plus the pi continuation (17:05→).
- `2026-09-26-rtx5090-gemma-prep.md` — bounded RTX 5090 readiness prep report.
- `private/` — gitignored machine-local state (watcher snapshot).

## Watcher (quarter-hour issue monitor)

`watcher/poll_issues.py` + `watcher/poll-issues.sh` (repo root) poll issues
addressed to Piotr every quarter of an hour (cron `7,22,37,52 * * * *`), log
findings to `watcher/2026-09-26-watcher-log.md`, state in
`agentsLog/semberecki/private/watcher-state.json`. Read-only: no model calls,
no purchases, no issue writes.

## Standing rules (verbatim, pass to every session)

Watch GitHub issues addressed to Piotr every quarter of an hour; on new items
dispatch a subagent task. Post results into the triggering issue; open new
issues marking Piotr for discovered follow-ups; inform other agents. Results go
to `agentsLog/` as the center of sharing knowledge with other team members. Do
not stop polling GitHub issues while running other agents. Do not wait for
owner approval to merge scoped additive PRs. NEVER buy anything. Use English
for code, commands, filenames, commit messages and technical documentation.
