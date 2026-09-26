# Hugging Face setup

The repository keeps `uv` for reproducible dependencies. `pyproject.toml` and `uv.lock` install the Hugging Face library/CLI in the ignored `.venv`; Python 3.11 matches CI. The unused `uv init` greeting script was removed. Core inference and evaluation can still run with standard-library Python without HF installed.

From PowerShell in this repository:

```powershell
uv sync --frozen
.\scripts\hf.ps1 auth login
.\scripts\hf.ps1 auth whoami
```

Choose browser login, open the displayed device URL, and approve while signed into **kwiscion**. `whoami` should confirm that account before uploads to `kwiscion/matura`. The CLI also supports an access token created in your Hugging Face account settings; enter it only into the local CLI prompt, not Git or chat. Dataset uploads require write permission.

The wrapper sets `HF_HOME` to this repository's ignored `.hf-home` for the process, then restores the prior environment. It does not reuse the unrelated account found in the default WSL cache. Use the wrapper for project commands. For a WSL process, explicitly set `HF_HOME` to the same project's `.hf-home` path rather than the global cache; use `.venv-wsl` if creating a Linux environment, because a Windows virtual environment cannot be shared with Linux.

Examples after login:

```powershell
.\scripts\hf.ps1 upload --help
```

Only upload a reviewed candidate folder. Do not upload the repository root, `.hf-home`, private evaluation keys, exam PDFs, or raw responses. The accepted strict training records are separate from legacy/draft data; see `agentsLog/przemeknowak781/README.md` before preparing an export.

Official references: [installation](https://huggingface.co/docs/huggingface_hub/main/en/installation) and [CLI authentication](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#hf-auth-login).
