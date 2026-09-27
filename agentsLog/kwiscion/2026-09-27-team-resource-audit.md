# Read-only team resource snapshot

Observed 27 September 2026, 00:53:57–00:55:15 UTC (02:53:57–02:55:15 Europe/Warsaw), through the existing authorized project login. No service/model calls, downloads, remote writes, ownership changes, worker interruption, credentials, environment values, model answers or grading-key access.

| Owner | Observed state | Coordination consequence |
|---|---|---|
| Greg | Declared evaluation worker, model server and guardian are live; GPU compute active. Project ledger has 49 lines, last modification 00:47:45 UTC. Line count is not a completed-call/item count. | Preserve the original evaluation deadline **01:09:46 UTC** and sole-worker ownership. Not terminal. |
| Łukasz | GPU compute list empty, 0% utilization and no project inference worker observed at 00:54:26 UTC. No new study ledger found within established project paths. | This snapshot does not disprove off-host preparation or revoke the claim. Preserve owner claim through the latest-start cutoff **03:00 Europe/Warsaw**; root coordinates any later handoff. |
| Przemek | GPU occupied at 99% utilization by workloads outside the established matura project scope at 00:54:28 UTC. Their details/files were not investigated. | Host is **not available** for a new matura worker. Preserve all existing processes. |

Known project runtime binaries/cache filenames and sizes were inspected read-only. Cache counts alone establish neither hash integrity nor final eligibility: some contain mixed development weights or generated metadata. Any future execution still needs the exact reviewed model inventory, fresh owner claim and bounded declaration. No inference or ownership is authorized by this note.

Access: ordinary sandbox WSL invocation returned `E_ACCESSDENIED`; the same read-only audit succeeded with approved normal tool escalation. No project-host access failure remained. This is a timestamped snapshot, not continuous monitoring.

Follow-up at **01:00:49.124224 UTC / 03:00:49 Europe/Warsaw**: Łukasz's GPU remained at 0% / 0 MiB, with an empty compute-process list and no project worker. Established project paths still showed only the older readiness summary, last modified 26 September 17:38:56 UTC; no new study ledger was observed. The latest-start cutoff has now passed, but reassignment/suspension remains a root coordination action. No service or worker was changed.
