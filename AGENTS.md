# Agent instructions

Read [WINNING_PLAN.md](WINNING_PLAN.md) before dispatch, scope changes, accepting results or reporting progress. It is the compact current strategy; GitHub issues and their latest explicit claims/declarations own scheduling. Historical instructions and checkpoints are preserved in [the archive](agentsLog/kwiscion/2026-09-26-agent-instructions-history.md), not repeated here.

## Objective and submission

- Maximize the Sunday Polish history matura score; target48/60 on known May2024 validation. Final freeze:27September2026,11:00Europe/Warsaw. The former Saturday morning/18:00 cutoffs are historical.
- ALL submitted model weights together must fit8GB+10%. Use the conservative aggregate cap8,800,000,000bytes, counting projectors, adapters and any OCR/router/retrieval-model weights. [Budget and consequences](docs/SUBMISSION_WEIGHT_BUDGET.md). Development models may be separate; keep their caches out of the final package.
- The leading architecture is one shared multimodal Gemma. Same-model repeated calls and question-specific prompts are allowed. A LoRA route needs proven shared-base adapter serving or one merged model with all-route regression; two full essay/base copies are ineligible together.
- Final inference is offline. Promotion requires a complete organizer-path exam result, exact answers.json, provenance, independent scoring and actual final-package/runtime qualification. Follow the received package's real item count;40items/60points describes our current validation exam, not an assumed universal organizer schema.
- The current leading full40 result is independently reviewed38/60; fallback35/60 is preserved. Neither the target nor final submission readiness is achieved. Current evidence and owner status belong in WINNING_PLAN/issues, not growing this file into a log.

## Work ownership and delivery

- Use English for code, commands, identifiers, filenames, commits and technical documentation. Reply in Polish when the user writes in Polish unless they request otherwise. Be concise and distinguish observed results from assumptions.
- Claim the assigned issue with start/ETA, change ready to in-progress, and keep one active task per owner/issue and one worker per host. Assignment or an old lock file is not evidence of a running worker. Inspect live processes/handles before restarting or reassigning work. Hand off terminal/partial evidence instead of silently retrying.
- Use Sol/Luna subagents for bounded implementation, research, data and review; root keeps coordination concise. Each experiment freezes inputs, model/runtime/prompt revisions, requested call/token limits, absolute deadline and cost estimate before dispatch. Preserve failed calls in denominators and retain raw evidence privately.
- Default experiment ceilings remain90minutes,120calls and240,000requested output tokens; training pilots remain60minutes with independent data and export checks. A worker cannot enlarge these limits by writing its own manifest. Follow the exact latest lead-authorized declaration, including any explicitly approved exception or tighter bound.
- Use owned agentsLog/<owner>/ paths; do not overwrite another owner's work, shared contracts, frozen inputs or promoted artifacts. Lead owns integration. Use issue-<number>-<owner>-<slug> branches for assigned numbered work; root integration branches use codex/.
- Open scoped PRs with commands, useful tests, provenance/licenses, revisions/hashes, actual runtime/results and limits. An owner may self-merge scoped additive owned-path work after checks and provenance review; lead handles shared integration. Merge only passing changes at the exact reviewed head, with no admin merge or force push. Preserve dirty work attributable to others.
- The active Codex goal drives lead continuation. The old matura-overnight-coordination heartbeat remains paused. Do not invent monitoring from an issue prompt or create a duplicate dispatcher. No automatic stop/pause based on historical morning instructions.

## Evaluation, sources and publication

- [SOURCE.md](SOURCE.md) governs rights and fixed splits: May2023 DEV, May2024 VALIDATION, May2025 SEALED_TEST. Keep May2025 closed until the lead explicitly releases it after a frozen candidate decision. Never read it merely because it is morning.
- Never put held-out questions, answers, rubrics, source packs or their direct paraphrases into training or retrieval. Independently licensed general historical facts are permitted. Preserve source-group/alias separation, provenance and accepted data hashes; do not claim pretrained models never saw an exam.
- Automatic/agent grades remain provisional relative to organizers. Follow the official applicable rubric and project calibration, retain independent first passes and resolve material disagreements. Do not promote from training loss, a selected subset, synthetic smoke success, or posthoc answer composition.
- The owner authorizes public sharing of our original prompts, model answers, grades, code, findings and negative results. Keep credentials, copied unlicensed exam/source text, official keys and raw reasoning/provider envelopes private. Use exact answer-only exports with provenance; do not silently clean completed outputs.
- No HF publication on the current path; lead owns any later release decision within the owner's authorization. Preparation/PRs do not imply a dataset/model release. HF auth is project-scoped: scripts/hf.ps1 on Windows, or HF_HOME explicitly set to this repository's .hf-home in WSL. Confirm kwiscion through normal CLI before any authorized publication; do not inspect token values or use the unrelated default WSL identity.

## Authority and resources

- The user authorizes project Git/GitHub, HF and bounded paid inference without repeated permission. Use only normal existing account sessions/current project credentials or credentials supplied for this project. Never search unrelated projects for keys, configurations, tokens or approvals.
- No teammate may purchase compute/credits/data or redeem account reset credits. Use already provisioned resources. Record provider/rate assumptions, estimated and actual usage and hard run bounds. Missing credentials or runtime support blocks only that step; continue independent work.
- GPU ownership and resource names are tracked by current issue claims and private project evidence. Blackwells are unavailable; Piotrek has RTX5090, and the owner has provisioned H100 workers. Do not duplicate workers or change another owner's service. Preserve original models, completed runs and local evidence backups.
