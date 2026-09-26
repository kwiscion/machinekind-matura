# Prepared offline rehearsal fallback — 26 September 2026

**Prepared, not executed.** This is a lead-owned fallback for the overdue runtime handoff on [#38](https://github.com/kwiscion/machinekind-matura/issues/38); @ljaniec retains attribution and ownership of that handoff. It does not claim a verified offline model run or replace his work.

[offline_rehearsal.py](offline_rehearsal.py) runs the accepted organizer adapter on exactly two explicitly invented tasks: one text task and one image task using the adapter's synthetic fixture. The script uses existing `/usr/local/bin/ollama` and `/usr/local/lib/ollama/llama-server`, with the **already downloaded** cache `/usr/share/ollama/.ollama/models`. No download, alternate runtime, exam material, key, or unrelated project configuration is needed.

## Launch prerequisites — lead only

1. Finish the active RAG/other GPU queue and hold exclusive ownership for up to 17 minutes. The script refuses any host resident model, known inference runner, or GPU compute process. The lead must separately and explicitly unload only their own resident model if necessary; this recipe never stops the host daemon or unloads a host model.
2. WSL needs working `unshare -rn`, `ip`, Python 3, NVIDIA visibility, the installed Ollama binary, and read access to the model cache. Executable presence and cache permissions were checked; namespace execution and CUDA access inside a user namespace remain **unverified**. Failure is a blocker, not permission to change host network/firewall, driver settings, or install anything.
3. Preserve the existing cache and frozen model: `gemma4:12b-it-q4_K_M`, manifest SHA-256 `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; model blob `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606` (7,381,382,048 bytes) plus BF16 projector `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842` (175,115,584 bytes). The script verifies full hashes before launch: total **7,556,497,632 bytes**, below 8,000,000,000. No weights are copied or modified.
4. Predeclare **maximum two sequential model requests, no retries or warmup, 1024 output tokens each / 2048 total, $0**. Same model defaults, thinking off, context 4096, request timeout 420 seconds. Two timeouts consume 14 minutes; readiness gets 45 seconds; outer process bound is 980 seconds. Hash verification happens before that runtime bound, so allow preparation time separately. Reserve the queue accordingly.

Prepared PowerShell command (do not run until the lead declares the budget and queue available):

```powershell
wsl --exec python3 -B /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/offline_rehearsal.py --execute --output /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/private/offline-rehearsal-run-01
```

The output must be a fresh directory under this owner's ignored private tree. Existing directories are refused; there is no resume behavior that could silently repeat calls.

## Isolation and evidence

The outer process checks host `/api/ps`, GPU/worker ownership and pinned assets, then starts `unshare -rn -- python3 ... --inside`. **Both the new Ollama server and the infer.py runner execute inside that network namespace.** Only its loopback interface is brought up; the script asserts no other interfaces or external routes, proves IPv4 and IPv6 external connections fail, and records different host/child namespace identities. It verifies the server's actual namespace matches the runner before using it. It does not disconnect the laptop or alter a global firewall.

The isolated server binds only **127.0.0.1:11435**, with explicit existing `OLLAMA_MODELS`, a fresh private runtime home, context 4096, one parallel slot and one loaded model. A small allowlisted environment avoids inherited proxies, credentials and other configuration. Metadata-only readiness checks `/api/version` and `/api/tags` without model loading. The first real synthetic request performs any necessary cold load; `/api/ps` must then prove the pinned digest and actual context 4096 before request two. Each request is reserved and flushed before sending; each response is flushed before checking errors. Error, unexpected token accounting, context mismatch or a competitor stops the run without retry.

Success requires the accepted `scripts/Bukareszt/matura_package.py` adapter to finalize and validate `answers.json` with exact template IDs and no empty/failed answers. This verifies transport/package behavior, **not history quality or submission receipt**. Outputs include `launch.json`, `network-proof.json`, `readiness.json`, server PID/namespace/log records, call reservations, raw responses, `answers.json`, adapter failures, actual usage and cost in `success.json`, and `cleanup.json`.

Cleanup signals only the newly created server process group; a parent safety net additionally matches the recorded process group **and namespace** before cleanup after a timeout/interruption. The host Ollama daemon is preserved. Use normal Ctrl+C so cleanup can run; forcibly killing the parent with SIGKILL cannot provide a cleanup guarantee. No `pkill`, global process-name kill, firewall change, restart or whole-laptop disconnection is used.

## Checks actually completed

Four focused tests in [test_offline_rehearsal.py](test_offline_rehearsal.py) passed on native Python and WSL Python: two synthetic tasks prepare correctly; exactly two mocked requests carry a combined 2048-token cap; the accepted adapter finalizes and validates the mock answers; outside/private-root/existing output destinations are refused; a host-namespace identity is rejected before any `ip` mutation; missing execution arguments cannot launch a process. The transport/fixture check monkeypatches socket creation to fail. These tests contain **zero real model calls** and launch neither Ollama nor a namespace.

```powershell
wsl --exec python3 -B -m unittest discover -s /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion -p test_offline_rehearsal.py -v
```

Remaining evidence is intentionally pending: actual namespace isolation failure probes, server readiness, GPU load within the namespace, two real responses and real `answers.json`. If any prerequisite fails, preserve the private logs and return the concrete blocker; do not quietly run the host server as an offline substitute.
