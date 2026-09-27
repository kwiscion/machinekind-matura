# Manual final run

The owner selected **Qwen3.5:9b with full-Wikipedia RAG for both ordinary questions and essays**. The final worker is `matura-pawel`. All development must stop before obtaining final questions. No agent is needed to operate the frozen runner.

[Readiness evidence](../agentsLog/kwiscion/2026-09-27-manual-final-readiness.md) records the live smoke, resource verification and release limits. The final freeze declaration is on [issue3](https://github.com/kwiscion/machinekind-matura/issues/3).

## Run

From PowerShell in this repository, after the readiness record confirms the freeze and you download the organizer package:

```powershell
.\scripts\run-final.ps1 -ExamPath 'C:\path\to\final-exam.zip'
```

A directory containing `exam.json`, `answers-template.json` and linked images works too. The launcher prepares, uploads, starts once, waits, downloads and validates the answer sheet. It prints the run ID and output directory. If your local connection or terminal closes, resume the same run:

```powershell
.\scripts\run-final.ps1 -Resume '<runId>'
```

Outputs are under `agentsLog/kwiscion/private/final-runs/<runId>/`: `answers.json`, `status.json`, `terminal.tar.gz` and `run-state.json`. Resume reconnects without starting another model worker. Keep the computer awake and connected for automatic download.

Keep `matura-pawel` running and leave its staged files intact. The source and index checks deliberately stop if the frozen files, host boot or index identity change. Existing WSL/Brev SSH authentication is already configured; no new credentials are needed for the verified path.

Submit only the resulting `answers.json` through the organizer page. Keep the receipt. Do not edit model answers or change code, prompts or settings after final access.

## Timing and automatic behavior

- Clock starts when the local launcher starts. Start it immediately after downloading the final package; acquisition time is additional.
- Remote work ends by minute 55. Ten minutes inside that window are reserved for recovery and export. Download and validation target minute 60, leaving five minutes for manual submission.
- All original questions receive direct answers first. The runner saves that complete sheet, then attempts essay RAG before ordinary-question RAG while time remains.
- Essay RAG selects one topic, produces six research queries, retrieves five passages per query, independently filters each passage and writes an evidence-backed essay. Ordinary RAG generates a query, filters five passages and attempts an improved answer.
- The same model handles every stage serially. No outside model, agent, network retrieval or manual cleanup participates.
- Failed, late, evidence-free or oversized improvements preserve the direct answer. Required-answer failures receive up to three recovery retries when the hard deadline permits. The emergency string `Tadeusz Kościuszko` is reported as a placeholder, never successful recovery.
- Status distinguishes attempted/skipped RAG, recoveries and placeholders. The deadline may limit RAG coverage. It cannot guarantee external transfer or submission-site availability.

## Frozen resources and evidence

One native model cache: **6,594,475,420 bytes**, below the aggregate **8,800,000,000-byte** cap. Context: 65,536. Ollama 0.34.4. Full Polish Wikipedia: 1,587,721 articles and 2,729,746 passages. Retrieval uses SQLite search, with no additional embedding-model weights. Large resources are staged before the exam clock.

The preserved direct baseline scored **40/60**, with 40 complete answers in **27m58s** and four automatically recovered timeouts. The six-item Qwen RAG diagnostic was 4/6 versus 4/6 direct. One completed essay RAG trial scored 9/15; two parallel attempts failed operationally, so final execution is serial. These provisional grades do not establish a full-exam RAG score or an 80% result.

The readiness record must identify the exact Git revision, local/remote source hashes, resource verification, tests and live smoke results. The final package remains private. May2025 remains sealed. Use existing Brev authentication and provisioned compute only; never search other projects for credentials.
