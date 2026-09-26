# Matura: small offline exam assistant

Current handoff: [morning status and active work](agentsLog/kwiscion/2026-09-26-morning-status.md). After the Windows restart, the owner extended lead work through **10:47 Europe/Warsaw on September 26**; this supersedes the original overnight operational cutoffs.

For the installed HF CLI and project-specific account login, see [Hugging Face setup](docs/huggingface.md). Run `.\scripts\hf.ps1 auth login` from PowerShell, then confirm `kwiscion` with `auth whoami`.

Overnight hackathon working assumption: **Polish history matura**. The lead must confirm the final subject before promotion; all records carry a `subject` field so other work can proceed. The final system may use local retrieval and tools, and each saved model's weights must fit within **8 GB**. Closed models and synthetic data are allowed during development; the final inference path must run offline.

The handoff package is in [docs/overnight/PLAN.md](docs/overnight/PLAN.md). Start with [SETUP.md](docs/overnight/SETUP.md), then read [CONTRACTS.md](docs/overnight/CONTRACTS.md) and your assigned issue. Source and publication rules are in [SOURCE.md](SOURCE.md). GitHub issues are the overnight scheduling authority; live assignments are recorded in [ISSUE_LINKS.md](docs/overnight/ISSUE_LINKS.md); local issue bodies preserve the original briefs.

| Issue | Owner | Local brief | GitHub lookup |
| --- | --- | --- | --- |
| Lead, integration and freeze | @kwiscion | [Lead](docs/overnight/issues/lead.md) | [Issue](https://github.com/kwiscion/machinekind-matura/issues/3) |
| Grounded training data | @przemeknowak781 | [Data](docs/overnight/issues/data.md) | [Issue](https://github.com/kwiscion/machinekind-matura/issues/4) |
| Compact model experiments | @ljaniec | [Spark](docs/overnight/issues/spark.md) | [Issue](https://github.com/kwiscion/machinekind-matura/issues/5) |
| Historical retrieval | @Bukareszt | [Retrieval](docs/overnight/issues/retrieval.md) | [Issue](https://github.com/kwiscion/machinekind-matura/issues/6) |
| Evaluation and rubric audit | @Pewciu6 | [Evaluation](docs/overnight/issues/eval.md) | [Issue](https://github.com/kwiscion/machinekind-matura/issues/7) |

Retrieval #6 and evaluator #7 are accepted implementation handoffs; model quality has not been promoted. [Evidence selection #15](https://github.com/kwiscion/machinekind-matura/issues/15) is closed as a negative experiment; keep the original retrieval baseline. [Real-output validation #11](https://github.com/kwiscion/machinekind-matura/issues/11) remains open. Training-data [PR #18](https://github.com/kwiscion/machinekind-matura/pull/18) needs strict-export and internal split fixes, now claimed by the lead for a scoped repair. Spark issue #5 has no reported result. Original issue ownership is retained; do not duplicate active workers.

The canonical input is JSONL with `{ "id", "prompt", "images"? }`; each task supplies its own standalone script or adapter. The portable Python [inference runner](docs/inference.md) supports local Ollama and hosted OpenAI-compatible endpoints, saves raw responses, timing, usage, and model identity, and excludes answer/rubric fields from requests. Start with `python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/smoke.jsonl --dry-run`. Hosted development endpoints need explicit configuration and a project-scoped API key; keep credentials out of Git.

For the lead's 8 GB GPU, `config.qwen.local.example.json` selects the installed Qwen 3.5 4B model with thinking disabled. A text transport smoke returned a final answer with full GPU placement; this is not an exam score. See the [local inference log](agentsLog/kwiscion/local-inference-2026-09-26.md) for settings and limitations.

The lead has a coordination heartbeat through the extended 10:47 handoff. Workers still need to start their own session using [WORKER_PROMPT.md](docs/overnight/WORKER_PROMPT.md); an issue assignment alone does not execute work.

No repository-wide code or dataset license has been selected. Original code could later use MIT if the owner approves; each third-party dataset subset needs its own source/license review.
