# Manual final-run operations

The owner runs one command from the repository:

```powershell
.\scripts\run-final.ps1 -ExamPath 'C:\path\organizer-exam.zip'
```

A directory containing the organizer package is also accepted. A ZIP may have one enclosing directory. Unsafe ZIP paths and ambiguous multiple packages are rejected. Essay routing is discovered by the reviewed preparer. No final questions were used while creating this workflow.

The script uses the qualified Python3.11 installation, verifies `frozen-sources.json`, preserves required original files, prepares on Windows, declares the deadline from local command start, and uploads a frozen package. The actual model deadline isT0+55minutes. Local answer retrieval targetsT0+60, reserving five minutes for the owner to submit within65. The script never submits answers. Network/provider failures can defeat the retrieval target, but do not extend the remote model deadline.

The run ID prints immediately. For a dropped connection or later backup retrieval:

```powershell
.\scripts\run-final.ps1 -Resume 'PRINTED_RUN_ID'
```

Resume uses the same package and remote dispatch marker. It does not create another inference worker. A failed or missing supervisor is reported for diagnosis, never automatically redispatched. Original service11434 remains untouched; each run owns its temporary sentinel and isolated model runtime.

Local output: `agentsLog/kwiscion/private/final-runs/<runId>/answers.json`, `validation.json`, `status.json`, `run-state.json`, and the full private `terminal.tar.gz` when available. The small answer file is downloaded and validated before the larger trace backup. Terminal status distinguishes complete direct answers, RAG answers, direct fallbacks and placeholders. The model export is never edited. Review the status and manually submit the exact validated file.

Pawel was staged before acquisition: a dedicated immutable full Wikipedia DB and a clean five-file Qwen cache base. Each run gets its own five-member hardlink view, so served-cache metadata never contaminates the clean base or another run. No index/model download occurs during final preparation. Full index and weight receipts are in `index-proof.json` and `weights-proof.json`.

Qualification-only invocation, using the same path and shorter actual deadline:

```powershell
.\scripts\run-final.ps1 -ExamPath 'DEV_ONLY.zip' -Smoke -RemoteMinutes20
```

The20-minute mixed DEV smoke retains the production600-second recovery reserve. It is bounded by164 attempts and611,712 requested output tokens for its exact two-item/one-essay package. Final runs do not accept a changed remote duration. `freeze.py` is a preparation tool; do not run it or edit any code after final acquisition.
