# Brief for every agent working on behalf of Greg (`@Bukareszt`)

Pass this verbatim to every subagent / Orca / Claude Code session you start. Repo instructions in `AGENTS.md`, `SOURCE.md`, `docs/overnight/CONTRACTS.md` take precedence where they are stricter.

- Read `agentsLog/` first (`agentsLog/README.md`, `agentsLog/kwiscion/`, `agentsLog/Bukareszt/`): other agents' entries say what was already found/done.
- Write reports and artifacts only under `agentsLog/Bukareszt/` plus separate additive script/data paths you own. Never edit another owner's files, `agentsLog/README.md`, shared contracts, benchmark manifests, core runner/config. No shared mutable log: mutable state goes to `agentsLog/Bukareszt/private/` (gitignored).
- Post results as clean comments on the GitHub issue that triggered you: milestones, discoveries other owners should know, final handoff with commands, hashes, measurements, failures, limitations.
- Before claiming an issue, check its comments and labels: one active worker per issue; do not duplicate a claim already posted. Claim with session ID, start time, ETA; switch `ready` -> `in-progress`; finish with `needs-review`.
- If you discover follow-up work, open at most two deduplicated issues mentioning `@Bukareszt`; keep speculative ideas in the report.
- Don't wait for Greg's approval: a scoped additive PR confined to owned paths may be self-merged after its checks pass and provenance review. Never force-push, never admin-bypass.
- NEVER request final exam questions or access the organizer submission page: doing so records whole-team readiness and freezes every project (owner rule, 2026-09-27 00:45). Only root/owner does that, after everything is committed.
- NEVER buy anything: no paid services, credits, subscriptions, separately-billed APIs, purchases. Free PyPI packages and public downloads are fine.
- Cutoffs (Europe/Warsaw, 2026-09-26): no new expensive work after 08:00; reports and `needs-review` by 08:30; polling stops 08:30. Final freeze 2026-09-27 11:00.
- Work only inside your own git worktree. Branch `issue-<n>-Bukareszt-<slug>`.
