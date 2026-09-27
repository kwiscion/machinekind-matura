# Matura: small offline exam assistant

Start with [WINNING_PLAN.md](WINNING_PLAN.md) for the compact strategy and [the manual final runbook](docs/FINAL_RUN.md) for execution. GitHub issue [#3](https://github.com/kwiscion/machinekind-matura/issues/3) owns final integration and the freeze declaration.

**Selected by the owner: one Qwen3.5:9b model with full-Wikipedia RAG for ordinary questions and essays.** The manual launcher uses the Pawel H100 and returns validated `answers.json` locally. Remote work is bounded to 55 minutes from local start; download/validation target 60 minutes, leaving 5 minutes for manual submission. Final-question access freezes every team's development.

```powershell
.\scripts\run-final.ps1 -ExamPath 'C:\path\to\final-exam.zip'
```

Use this only after the readiness record confirms the freeze. It accepts an extracted directory too. Resume a disconnected local session with `-Resume '<runId>'`, without starting another worker. No external agent participates in inference, recovery or cleanup.

The preserved direct baseline scored **40/60** (32 nonessay + 8 essay), completing 40 answers in 27m58s and recovering four initial timeouts. Gemma scored 39/60. The Qwen full-Wikipedia six-item diagnostic scored 4/6 both with and without RAG. One completed essay RAG trial scored 9/15; two concurrent attempts failed operationally, so the final runtime is serial. RAG is the owner's selected policy, not a measured full-exam improvement. The 48/60 target has not been demonstrated.

The selected native Qwen cache is **6,594,475,420 bytes**, below the aggregate **8,800,000,000-byte** limit. Wikipedia contains 1,587,721 articles and 2,729,746 passages; SQLite retrieval needs no additional model weights. See [weight rules](docs/SUBMISSION_WEIGHT_BUDGET.md). LoRA, image-description ensembles and separate models are not enabled.

Current work: root/Sol implementation, operations and independent review prepare and qualify the final manual workflow. Other experiments are parked. The coordination heartbeat is paused. Follow [AGENTS.md](AGENTS.md) and [SOURCE.md](SOURCE.md); May2025 remains sealed, and final questions must not be accessed during preparation.

The organizer's 37-item mock and corrected May2024 source crops remain local development evidence. The runner follows the received template's actual IDs and count. [Mock compatibility](agentsLog/kwiscion/2026-09-27-mock2023-package-compatibility.md) · [Source crops](agentsLog/kwiscion/source-crops-prep/README.md) · [Qualified recovery](agentsLog/kwiscion/final-package-prep/RECOVERY_RUNTIME.md).

Project-scoped HF setup is documented [here](docs/huggingface.md); no HF publication is part of the final path. Previous work remains in [the archive](agentsLog/kwiscion/2026-09-26-readme-history.md) and `agentsLog/`. No repository-wide code or dataset license has been selected; third-party rights remain separate.
