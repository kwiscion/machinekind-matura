# agentsLog/Bukareszt — Greg's owner log

Owner: `@Bukareszt` (Greg). Issue: #6 (licensed offline historical retrieval). Branch for #6: `issue-6-Bukareszt-retrieval` (worker writes its own README/notes here when it lands).

## Watcher (this PR)
- Path: `agentsLog/Bukareszt/watcher/` — the issue watcher that dispatches Greg's issues to Orca worktrees.
- Time: started 2026-09-26 01:30 Europe/Warsaw (23:30 UTC 25 Sep); polling stops 08:30 Warsaw.
- Artifacts: `watcher/AGENT_BRIEF.md` (brief passed to every worker), `watcher/poll-issues.sh` (poll script), `watcher/2026-09-26-watcher-log.md` (timestamped log incl. dry-run evidence).
- Mutable state lives in `agentsLog/Bukareszt/private/watcher-state.json` (gitignored, never committed).
- Commands: `agentsLog/Bukareszt/watcher/poll-issues.sh` (prints candidate issues as JSON).
- Split/model/sources: none touched by the watcher.
- Failures/limits: see the watcher log. Next action: worker for #6 delivers; watcher verifies handoff by 08:30.
