# Matura: small offline exam assistant

Start with **[WINNING_PLAN.md](WINNING_PLAN.md)** for current priorities and owners. GitHub issues are the scheduling authority; claim one task before starting.

The supplied **37-item organizer mock is verified** through the actual adapter and autonomous export path with synthetic responses: [commands and evidence](agentsLog/kwiscion/2026-09-27-mock2023-package-compatibility.md). May2024 validation uses **21 reviewed source crops with corrected image links**: [input package and reproduction](agentsLog/kwiscion/source-crops-prep/README.md). The downloaded mock stays local under `data/history-2023-mock-v1/`.

Current complete corrected-input result: **Gemma native thinking39/60** (31/45 nonessay +8/15 essay), all40 answers complete with zero placeholders. Runtime:41 calls in15m48s. The one-pass grade has item-based judgment sensitivity37–42, not a confidence interval or organizer grade. Legacy38/60 remains separate; changed inputs prevent a crop-only causal claim. Target48/60. [Score and point losses](agentsLog/kwiscion/2026-09-27-corrected-gemma40-grade.md) · [Runtime evidence](agentsLog/kwiscion/2026-09-27-corrected-gemma40-result.md).

The [native-thinking six-item comparison](agentsLog/kwiscion/2026-09-27-native-pair-comparison.md) scored Qwen6/8 versus Gemma4/8. Full corrected Qwen40 now runs in [#95](https://github.com/kwiscion/machinekind-matura/issues/95), due05:01 Warsaw. [Essay branching](agentsLog/kwiscion/essay-branching-prep/WAVE.md) runs on `matura-lukasz`, due05:05. Greg owns [three-view image reasoning](https://github.com/kwiscion/machinekind-matura/issues/178), with local fallback if unavailable. **Development freezes08:00 Warsaw;08:00–11:00 is final checks/execution/submission.**

The3-epoch essay LoRA is parked:2/16 complete versus16/16 control, with control winning both complete content comparisons. [Frozen unmask](agentsLog/kwiscion/2026-09-27-eval16-unmasked-comparison.md). No further training is authorized without new evidence.

The organizer allows **8 GB + 10% across all submitted model weights together**. Our conservative limit is 8,800,000,000 bytes. The actual Gemma-only cache is verified at **7,556,509,301 bytes**, including vision projector and metadata. Repeated calls share those weights. Development challengers remain separate. [Rule](docs/SUBMISSION_WEIGHT_BUDGET.md) · [Package evidence](agentsLog/kwiscion/2026-09-26-final-package-stage.md).

| Active track | Owner | Task |
|---|---|---|
| Qualified recovery harness; final integration | @kwiscion + Sol | [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| Structured prompts; one fast grading pass | Root Sol | [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| Per-topic essay drafts and same-model selection preparation | Root Sol | [#168](https://github.com/kwiscion/machinekind-matura/issues/168) |
| CPU failure-pattern/prompt hypotheses | @Pewciu6; claim pending | [#163](https://github.com/kwiscion/machinekind-matura/issues/163) |
| Three-view image descriptions and matched control | @Bukareszt; claim pending | [#178](https://github.com/kwiscion/machinekind-matura/issues/178) |
| CPU final runtime integration review | @ljaniec; claim pending | [#151](https://github.com/kwiscion/machinekind-matura/issues/151) |
| Native-thinking Qwen versus Gemma comparison | @kwiscion + Sol | [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| CPU final answer-package audit | @semberecki; claim pending | [#165](https://github.com/kwiscion/machinekind-matura/issues/165) |
| Standby; Bielik proxy completed | @przemeknowak781 | [#97](https://github.com/kwiscion/machinekind-matura/issues/97) |

The [recovery runtime guide](agentsLog/kwiscion/final-package-prep/RECOVERY_RUNTIME.md) documents larger context/output budgets, up to three recovery retries, preserved candidates, no blank answers, and a60/120-minute deadline. The [full rehearsal](agentsLog/kwiscion/2026-09-27-champion-rehearsal-result.md) completed46calls in about20minutes, recovered all3 failed attempts, and verified65,536 context, offline isolation, packaging and cleanup. Inference/recovery required no external agent intervention. The [older Sunday runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md) preserves the fallback.

For execution, read [AGENTS.md](AGENTS.md), [source/split rules](SOURCE.md) and the current issue. **Requesting final questions freezes all team projects:** commit code, prompts and settings first. Final inference is offline; May 2025 remains sealed. No fine-tuned candidate is qualified yet. Assignment alone does not start a worker; the old overnight heartbeat remains paused.

The portable [inference runner](docs/inference.md) accepts JSONL records with `id`, `prompt` and optional `images`. A CPU dry run:

```sh
python infer.py --config config.local.example.json --input fixtures/smoke.jsonl --output outputs/smoke.jsonl --dry-run
```

For project-scoped HF login, see [setup](docs/huggingface.md); on Windows run `.\scripts\hf.ps1 auth login`, then `auth whoami` and confirm `kwiscion`. There is no HF publication on the current path.

Original overnight [contracts](docs/overnight/CONTRACTS.md) and [setup](docs/overnight/SETUP.md) remain references; current issues supersede their historical assignments. Previous README chronology is preserved in [the archive](agentsLog/kwiscion/2026-09-26-readme-history.md). Logs and detailed findings belong under `agentsLog/<owner>/`, not in the strategy page.

No repository-wide code or dataset license has been selected; third-party material requires its own rights review.
