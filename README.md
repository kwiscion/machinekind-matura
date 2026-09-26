# Matura: small offline exam assistant

Start with **[WINNING_PLAN.md](WINNING_PLAN.md)** for current priorities and owners. GitHub issues are the scheduling authority; claim one task before starting.

Best complete known-validation result: **Gemma native thinking, independently reviewed 38/60**. All 40 central grades agree between reviews; three empty finals remain zero and the essay earns 8/15. This is agent evaluation, not an organizer score or final qualification. Preserved fallback: 35/60. Target: 48/60. [Score reconciliation](agentsLog/kwiscion/2026-09-26-full-thinking-review-reconciliation.md).

The organizer allows **8 GB + 10% across all submitted model weights together**. Our conservative limit is 8,800,000,000 bytes. The actual Gemma-only cache is verified at **7,556,509,301 bytes**, including vision projector and metadata. Repeated calls share those weights. Development challengers remain separate. [Rule](docs/SUBMISSION_WEIGHT_BUDGET.md) · [Package evidence](agentsLog/kwiscion/2026-09-26-final-package-stage.md).

| Active track | Owner | Task |
|---|---|---|
| Organizer integration, offline qualification, freeze | @kwiscion + Sol | [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| Argument planning versus thinking essays | @Pewciu6 | [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| Single-model essay LoRA pilot | @Bukareszt | [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| Source-grounded essay evaluation checklist | @ljaniec | [#143](https://github.com/kwiscion/machinekind-matura/issues/143) |
| Standalone Qwen native-thinking challenger | @semberecki | [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| Standby; Bielik proxy completed | @przemeknowak781 | [#97](https://github.com/kwiscion/machinekind-matura/issues/97) |

For execution, read [AGENTS.md](AGENTS.md), [source/split rules](SOURCE.md), the current issue and [Sunday operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md). Final inference is offline; May 2025 remains sealed. No fine-tuned candidate is qualified yet. Assignment alone does not start a worker; the old overnight heartbeat remains paused.

The portable [inference runner](docs/inference.md) accepts JSONL records with `id`, `prompt` and optional `images`. A CPU dry run:

```sh
python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/smoke.jsonl --dry-run
```

For project-scoped HF login, see [setup](docs/huggingface.md); on Windows run `.\scripts\hf.ps1 auth login`, then `auth whoami` and confirm `kwiscion`. There is no HF publication on the current path.

Original overnight [contracts](docs/overnight/CONTRACTS.md) and [setup](docs/overnight/SETUP.md) remain references; current issues supersede their historical assignments. Previous README chronology is preserved in [the archive](agentsLog/kwiscion/2026-09-26-readme-history.md). Logs and detailed findings belong under `agentsLog/<owner>/`, not in the strategy page.

No repository-wide code or dataset license has been selected; third-party material requires its own rights review.
