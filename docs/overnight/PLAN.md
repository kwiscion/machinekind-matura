# Overnight plan — 26–27 September 2026

Working subject: Polish history matura, pending lead confirmation. Goal: a source-grounded, offline-capable answerer with each saved model's weights at or below 8 GB. Local RAG and tools are permitted in the final path; synthetic data and closed models may be used in development. The four worker issues are independent and have a first deliverable before stretch work. The lead owns integration and publication.

| Time (Europe/Warsaw) | Decision or deliverable |
| --- | --- |
| Before 02:30 Sat 26 Sep | Owners claim issue, create branch, begin independent vertical slice |
| Within 60 minutes of claim | First useful commit and PR or local handoff link |
| 08:00 Sat | Stop starting expensive runs; finish or terminate within declared caps |
| 08:30 Sat | Each owner posts commands, artifacts, hashes, source/license check, results and limitations |
| 09:00 Sat | Lead reviews candidates and chooses bounded next experiments |
| 11:00 Sun 27 Sep | Final freeze: reproducible offline artifact and honest scorecard |

The lead has an RTX 2000 Ada 8 GB tonight and two Blackwell 96 GB GPUs tomorrow. Przemek has CPU and a large Sol/Luna token budget; Łukasz has DGX Spark and a large token budget; Bukareszt and Pewciu6 have CPU, with token appetite unknown. Compute availability informs stretch scope, not the required first deliverable. No worker relies on a lead baseline or another worker's artifact. Łukasz provides an independent model baseline and a no-training fallback recipe for tomorrow if training stalls.

Use [CONTRACTS.md](CONTRACTS.md), [SOURCE.md](../../SOURCE.md), and the assigned [issue body](issues/manifest.json). GitHub issues are the overnight scheduling authority. One owner/active task per issue by default; claim with ETA, change `ready` to `in-progress`, branch `issue-<number>-<owner>-<slug>`, commit vertical slice, then PR. An owner may self-merge a scoped additive PR confined to owned paths after useful checks and provenance review. Shared schema, benchmark manifests, core runner/configs, and promoted models remain lead decisions. Mark evidence `needs-review`; do not auto-close a pending experiment decision. Open at most two follow-up issues, only for concrete, required, nonduplicate work; keep optional ideas in the current PR/backlog notes.

A 15-minute coordination poll needs a configured scheduler or a persistent dispatcher. The issue text alone does not keep an agent running. Poll only until 08:30 or an explicit stop, and do not start duplicate tasks. At the cutoff, stop and hand off instead of generating endless follow-up work. Missing credentials, blocked access, unclear rights, or unexpected cost block only the affected action; report and continue a local fallback. Teammates may never purchase compute or data.
