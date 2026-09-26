# Hugging Face readiness check — 2026-09-26

**Current state, 09:41 Europe/Warsaw:** the owner completed browser login, and the lead verified `user=kwiscion` through `scripts/hf.ps1 auth whoami`. The project uses `huggingface-hub==2.0.0` from its frozen uv lock, Python 3.11, and ignored `.hf-home` credentials. PR #24 is merged. A strict-data release bundle is being reviewed; no upload has occurred yet. The earlier observations below are retained as history, not current setup instructions.

Read-only check for the current project environment. No token contents were read or printed; no login, settings, upload, or repository changes were made.

## Public dataset

An unauthenticated GET of `https://huggingface.co/api/datasets/kwiscion/matura` returned HTTP 200. Metadata says `private=false`, `gated=false`, and `lastModified=2026-09-25T22:58:30Z`. The only repository sibling is `.gitattributes`, so the public dataset is still empty of README/data files.

## Current CLI/library/auth state

- Windows: neither `hf` nor `huggingface-cli` is on PATH.
- WSL: neither CLI is available, and the active `python3` environment does not have `huggingface_hub` installed.
- The normal WSL Hugging Face cache token file exists. No `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN` environment-variable names are present. Token contents were not accessed, and account identity/token validity could not be confirmed without the missing CLI/library.
- WSL has `uvx`. The official [Hugging Face CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli) documents `uvx hf` as an isolated CLI invocation, and says the CLI supports auth, repo creation, upload and download. It was not run during this read-only check.
- WSL Git is 2.34.1. `git lfs version` fails because its Git subcommand executable is unavailable/broken.

## Readiness

The public repository is reachable and empty. A normal account credential cache is present, but current-account authentication is unverified and no HF CLI/library is installed. `uvx` is available as a later nonpersistent way to invoke the official CLI; validate identity with its normal `whoami` command before any upload. No upload was attempted.

## Lead follow-up, 09:01 Europe/Warsaw

The official CLI ran successfully through `uvx hf auth whoami`. The cached account authenticated, but its identity differs from the project dataset owner `kwiscion`. No upload or credential change was attempted, and this account will not be used for project publication without establishing the intended identity. Prepare reviewed candidate artifacts locally; publishing remains deferred pending a project-appropriate login. No token value was read or printed.
