# #83 frozen runtime profile for the offline organizer-package launcher

Issue https://github.com/kwiscion/machinekind-matura/issues/83, branch `issue-83-Bukareszt-portable-launcher`, started 2026-09-26 18:10 Europe/Warsaw. Scope exception authorized by the lead for `agentsLog/kwiscion/run_gemma_package.py` and `offline_rehearsal.py`. CPU/mocked work only: **zero model calls, zero remote/H100 operations, no downloads.** `infer.py`, temperature defaults and the official schema are unchanged.

## What changed

- Runtime-specific values now come from a profile: binary, nvidia-smi, model store, server `PATH`, Ollama version, context and the host-endpoint check. `run_gemma_package.py --runtime-profile PATH` selects a profile. If the option is omitted, the built-in `LAPTOP_PROFILE` in `offline_rehearsal.py` applies. It is the qualified WSL / Ollama 0.30.7 / context 4096 recipe with exactly the same server command, env and nvidia-smi command. A test checks this against literal pre-#83 values.
- The whole profile, its canonical sha256 and the source file's sha256 are written to the dry-preflight record and `launch.json`. The profile sha is also written to `readiness.json`. The profile file and the pinned binary are added to `frozen_files`, which inside mode re-hashes. Inside mode also re-validates the profile and refuses it if the recorded sha differs.
- Follow-up wording fix (PR #93 review): the `launch.json` `endpoint_change` text now takes the pinned config `base_url` (never contacted) and the profile's host-check port from the actual values, instead of hard-coding laptop port 11434. Only this text changes. The context check runs after each response, not before each request.
- Before any output directory or child exists, `execute` now runs these checks: platform (a native profile refuses a WSL kernel), host endpoint idle, exclusive-worker guard, binary sha, model assets, then an **isolation probe**. The probe runs `unshare -rn` into a new namespace, and it fails with a concrete message if `unshare`/`ip` are missing, if `unshare` exits nonzero (stderr quoted, e.g. `uid_map: Operation not permitted`), or if the probe stays in the host namespace. This probe is the one addition to the laptop path; it creates nothing and only fails fast where the child would fail anyway.
- The following are unchanged for every profile: server and runner in one `unshare -rn` namespace (network proof inside), arbitrary IDs and template order, full images, call, output-token and wall budgets, the prompt-usage cap of 2816 and the completion cap of 1024 (**context 32768 does not relax them**), exact raw answers, failed and unsent IDs as blanks, no retries or warmup, package/config/code hashes, fresh private output, the lock file and cleanup limited to the owned process group and namespace. The synthetic `offline_rehearsal.py --execute` remains laptop-only.

## Profile schema (all keys required, no extra keys)

| Key | Laptop default | H100 template |
| --- | --- | --- |
| `profile_id` | `laptop-wsl2-ollama-0.30.7-ctx4096` | `h100-native-linux-ollama-0.34.4-ctx32768` |
| `platform` | `wsl2` | `native-linux` (refused on a WSL kernel) |
| `ollama_version` | `0.30.7` (exact match with `/api/version`) | `0.34.4` |
| `ollama_binary` | `/usr/local/bin/ollama` | PLACEHOLDER (root #81) |
| `ollama_binary_sha256` | `null` (the laptop run never pinned it; `null` is allowed only for `wsl2`) | PLACEHOLDER (required 64-hex) |
| `server_path_env` | `/usr/local/bin:/usr/bin:/bin:/usr/sbin:/usr/lib/wsl/lib` | PLACEHOLDER |
| `nvidia_smi` | `/usr/lib/wsl/lib/nvidia-smi` | PLACEHOLDER |
| `model_cache` | `/usr/share/ollama/.ollama/models` | PLACEHOLDER |
| `model`, `manifest_digest`, `assets` | the launcher pins; any difference is refused | same pins (`4eb23ef1…`, model `1278394b…` 7,381,382,048 B, projector `675ad6e6…` 175,115,584 B) |
| `context_length` | `4096` (checked against `/api/ps` after each response, before the next request is reserved) | `32768` |
| `namespace_method` | `unshare-rn` (the only value accepted) | `unshare-rn` |
| `host_endpoint_check` | `{port 11434, require_reachable true}` | `{port 11436, require_reachable false}`. A resident model fails; a refused connection passes. |
| `block_foreign_ollama` | `false` | `true` (required for native): any `ollama serve`/`runner` outside the owned group blocks |
| `verify_all_manifest_blobs` | `false` | `true` (required for native): the config and every layer blob are checked for size and sha |

Files are in `scripts/Bukareszt/runtime_profiles/`: `laptop-wsl2-ollama-0.30.7.json` (sha256 `85e51c33…65b2`, canonical profile sha `40e90b7a…8c7b`) and `h100-native-linux-ollama-0.34.4.template.json` (sha256 `04b226a4…6f90`). Any string containing `PLACEHOLDER` makes the launcher stop with exit 2 and list the fields, even for a dry preflight.

## What remains for root (#81)

1. Copy the template to a private path (for example `agentsLog/kwiscion/private/h100-runtime-profile.json`). Fill in the published absolute paths: the project-owned 0.34.4 binary and its sha256 (the executable, not the archive), nvidia-smi, the verified model store and the server `PATH`. Do not change any pin.
2. Stop the readiness server on 11436 (the guard blocks a foreign `ollama serve`) and make sure `nvidia-smi` lists no compute apps. The repository must be a git checkout (`git rev-parse HEAD` is recorded).
3. Dry preflight, then run `--execute` with `--runtime-profile <filled file>`. If the Brev container denies user namespaces, the launcher stops with `Network isolation denied: …` before creating any output. In that case no offline claim is possible and the blocker needs a separate decision.

## Commands and evidence (macOS, Python 3.14; CPU only)

```sh
cd agentsLog/kwiscion && python3 -m unittest test_runtime_profile test_final_offline test_offline_rehearsal   # 30 tests OK
python3 -B agentsLog/kwiscion/run_gemma_package.py --exam-dir agentsLog/Bukareszt/submission/fixtures/tiny-package \
  --config <CRLF copy of the pinned config> --output agentsLog/kwiscion/private/i83-dry --max-calls 4 \
  --max-output-tokens-total 4096 --wall-seconds 1800            # laptop profile 40e90b7a…, model_calls 0
# the same command with --runtime-profile scripts/Bukareszt/runtime_profiles/h100-native-linux-ollama-0.34.4.template.json
# → STOP: Runtime profile has unfilled PLACEHOLDER field(s): … (exit 2, no output dir)
```

`test_final_offline.py` now falls back to a CRLF copy of the tracked config when the WSL path `outputs/local-smoke/…` is absent. The pinned hash `3d9c5018…` is still enforced. New tests (`test_runtime_profile.py`, 15) cover: laptop equality with legacy literals; native path, env and context selection with the profile hash in provenance; version and context mismatch (laptop and native); a context mismatch stopping the real request loop after one call with the rest unsent; pin, type, path, placeholder and extra-key refusal; profile tampering after launch; full-manifest blob verification; the isolation-denied messages; `execute` stopping before any output or child; native refused on a WSL kernel; host-endpoint semantics; the foreign-Ollama guard; and cleanup limited to the owned process group.

Limitations: nothing has been run on Linux or the H100 yet. The `/proc` and namespace behavior are mocked. The effective full-context fit on the H100 is unproven (`context_fit: UNPROVEN`).
