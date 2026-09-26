# RTX 5090 offline handoff — issue #38

26 September 2026. First delivery: PR #67; follow-up refreshed at 17:23 Europe/Warsaw against main `d610cfdb70e1d669f4d735324c289030971f8efd`. **Documentation/config checks only: zero model calls, GPU/SSH operations, weight/exam downloads, installs or paid spend.** Piotrek/@semberecki owns #33 execution; Greg owns adapter changes. Read current issue comments and [WINNING_PLAN.md](../../WINNING_PLAN.md) before using commands. The original 16:00 delivery ETA was missed; this records actual delivery, not an earlier completion.

## Current decision and pending evidence

Author [scope update](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5846547824) supersedes the original full-GPU-baseline order. The laptop Gemma v1 baseline has now completed all 40 answers; bare Gemma is the working 35/60 candidate, below the 48/60 target. The lead owns the current bounded RAG queue; no second controller or duplicate baseline. Piotrek may prepare his RTX and perform his assigned synthetic smoke; the **next RTX arm waits for a lead-declared intervention**, using corrected v2 input. This runbook authorizes no additional calls. Both Blackwells are unavailable; ljaniec's Spark/CPU Gemma work is stopped.

First delivery used the known native reference; this follow-up incorporates [Piotrek's claim](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847357936) and merged #69. He reports **RTX5090 Laptop GPU, 24,463 MiB total**, about 2.5 GiB desktop/remote-desktop use, native tag selected and user-local Linux **Ollama 0.34.4 being acquired**. These are reported host facts, not independently sampled by ljaniec. Exact OS/driver/backend, installed executable hash, actual local weight verification, effective context, image delivery, successful offline rehearsal and completed-response timings are **pending**. A version/tag or downloaded file does not establish serving, throughput or score. Do not assume desktop 32 GB capacity, default 32K context or 16K fit. No second runtime download is requested. HF QAT remains a separate alternative, not the chosen route.

## 1. Pinned prerequisites, acquired before offline operation

Use existing compatible Ollama, or unpack the **already acquired chosen** official archive into a fresh project-private directory. Keep its bundled libraries together; no global installer, systemd/tray changes or CUDA toolkit install. **The proven lead laptop baseline uses 0.30.7; Piotrek now reports 0.34.4. The earlier 0.32.14 Spark/native reference remains historical, not an instruction to upgrade the frozen lead endpoint or acquire another runtime.** Official release metadata checked 26 September:

| Platform archive | Published SHA-256 |
| --- | --- |
| Chosen Linux v0.34.4 `ollama-linux-amd64.tar.zst` ([release](https://github.com/ollama/ollama/releases/tag/v0.34.4)), 1,427,703,051 bytes | `c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533` |
| Historical Linux v0.32.14 `ollama-linux-amd64.tar.zst` ([release](https://github.com/ollama/ollama/releases/tag/v0.32.14)) | `c620917a71e146ab3a7f893084f066069c4c65d144ef8379a91c3cbe8b27de8f` |
| Historical Windows v0.32.14 `ollama-windows-amd64.zip` | `5ae5bca5f0d297f5e35665e01db399a69a8eac3f8fad89cd9d2531fd495c9457` |

Linux example, from the repo root, after supplying the actual pre-acquired archive path (tar must already support zstd):

```sh
set -eu
RUNTIME=agentsLog/semberecki/private/ollama-v0.34.4
ARCHIVE=/absolute/path/ollama-linux-amd64.tar.zst
printf '%s  %s\n' c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533 "$ARCHIVE" | sha256sum -c -
# Continue only after the hash passes; mkdir refuses an existing destination.
mkdir "$RUNTIME"
tar --zstd -xf "$ARCHIVE" -C "$RUNTIME"
TASK_OLLAMA_BIN="$PWD/$RUNTIME/bin/ollama"
sha256sum "$TASK_OLLAMA_BIN"
"$TASK_OLLAMA_BIN" --version
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,memory.free --format=csv
```

Parent `agentsLog/semberecki/private/` must already exist. Record the archive/executable hashes and extracted layout; archive digest is not the executable digest. Windows: verify with `Get-FileHash -Algorithm SHA256`, `Expand-Archive` into a fresh private directory, retain bundled libraries, use its `ollama.exe`. [Windows requirements](https://docs.ollama.com/windows): Windows 10 22H2 or newer. [Linux binary setup](https://docs.ollama.com/linux).

[Ollama GPU docs](https://docs.ollama.com/gpu) list RTX 5090 / compute capability 12.0. NVIDIA's [Linux 570.86.16 supported-chip table](https://download.nvidia.com/XFree86/Linux-x86_64/570.86.16/README/supportedchips.html) includes RTX 5090 (2B85); [Windows 572.16 launch driver](https://www.nvidia.com/en-au/geforce/news/geforce-rtx-5090-5080-dlss-4-game-ready-driver/) supports it. These are examples, not a downgrade/install instruction. Generic driver >=550 or CUDA12-family >=525 is insufficient proof of this card/backend combination. [CUDA12.8 introduces SM120](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/); [CUDA13-family compatibility needs >=580](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html). Record **actual selected bundled backend, driver and load logs**. Nominal 32 GB is not measured free VRAM.

For Piotrek's **Laptop** variant, NVIDIA's [Linux 590.48.01 table](https://download.nvidia.com/XFree86/Linux-x86_64/590.48.01/README/supportedchips.html) explicitly lists RTX5090 Laptop IDs 2C18/2C58. This documents a supporting driver example; it does not verify his installed driver or require changing it. #69's prep table says `.tgz`, while its continuation says v0.34.4 `.tar.zst`; the release has the latter asset and no Linux AMD64 `.tgz`. [Review report to #33](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847417442) requests actual archive/executable hashes before calling preparation verified.

## 2. Native saved assets and serving identity

[PR #36 inventory](2026-09-26-gemma-spark-load.md) verified this bundle on Spark, separately from its failed load:

| Asset | SHA-256 | Weight bytes |
| --- | --- | ---: |
| Native manifest | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` | — |
| Q4_K_M model | `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606` | 7,381,382,048 |
| BF16 projector | `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842` | 175,115,584 |
| Total | | **7,556,497,632** |

Below the 8,000,000,000-byte saved-model cap including projector. Verify **every** local manifest-referenced blob's size and SHA, plus the manifest, before serving. Preserve config/license/parameter blobs too; native retained license is Apache-2.0. The mutable tag must still match this immutable manifest. No ARM runtime binary hash carries over to RTX's AMD64 binary. [Registry manifest](https://registry.ollama.ai/v2/library/gemma4/manifests/12b-it-q4_K_M), [publisher model page](https://ollama.com/library/gemma4:12b).

Use a task-owned store containing only this manifest and its required blobs, not an entire user `.ollama` directory with identity material. After setting `MODEL_STORE` to its absolute path, this read-only check refuses differing/missing bytes:

```sh
python3 - "$MODEL_STORE" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=root/'manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(m)=='4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
doc=json.loads(m.read_text()); total=0
for a in [doc['config'],*doc['layers']]:
    p=root/'blobs'/a['digest'].replace(':','-')
    assert p.stat().st_size==a['size'] and sha(p)==a['digest'].split(':',1)[1]
    if a['mediaType'] in ('application/vnd.ollama.image.model','application/vnd.ollama.image.projector'): total+=a['size']
assert total==7556497632 and total<=8000000000
print('All referenced native assets verified; weight bytes:',total)
PY
```

Requires Python >=3.11 for this hash snippet; the existing runner/adapter need no OpenAI SDK. HF QAT is a different alternative in [model_candidates.json](../../scripts/ljaniec/model_candidates.json): revision `29d097773436b69ff9feafd636ab4cf873786537`, 7,150,994,912 combined bytes. Its projector and quantization differ. No speculative second download.

## 3. Task-only local start, configuration and checks

If Piotrek already has an endpoint, identify its owner/model/configuration first. Do not restart shared Ollama/VLLM or launch another server against a shared writable store. The following foreground command is for a **new task-owned endpoint only**, on confirmed unused port 11435, after weights/dependencies are present:

```sh
# In a dedicated task shell, also used for the Python runner:
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY=localhost,127.0.0.1,::1 no_proxy=localhost,127.0.0.1,::1
# Set MODEL_STORE and TASK_OLLAMA_BIN to the verified absolute paths above.
CTX=16384  # reference preference in #33; owner must confirm it fits full input + images + 1024 output tokens
set -C  # refuse overwriting the private stderr log
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS="$MODEL_STORE" OLLAMA_NO_CLOUD=1 \
OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_CONTEXT_LENGTH="$CTX" \
"$TASK_OLLAMA_BIN" serve 2>agentsLog/semberecki/private/ollama-task.stderr.log
```

Use a **fresh log path** for each attempt. Windows PowerShell in a separate task console: remove process environment `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` (names case-insensitive); set `$env:NO_PROXY='localhost,127.0.0.1,::1'`; set the same `OLLAMA_*` variables and run `& $TASK_OLLAMA_BIN serve`. Context is frozen by the execution owner after fitting; 16K is not proven here and differs from laptop v1's 4K. Capture effective `context_length`/processor placement through `/api/ps` after the owner's authorized load, plus peak memory samples and interval. Do not alter flash attention, KV quantization or sampling as an undeclared improvement.

Metadata-only checks from the matching task shell (no generation):

```sh
curl --noproxy '*' --fail http://127.0.0.1:11435/api/version
curl --noproxy '*' --fail http://127.0.0.1:11435/api/tags
curl --noproxy '*' --fail http://127.0.0.1:11435/api/ps
curl --noproxy '*' --fail -H 'Content-Type: application/json' \
  -d '{"model":"gemma4:12b-it-q4_K_M"}' http://127.0.0.1:11435/api/show
```

For the chosen reference verify API version 0.34.4, tags digest equals pinned manifest, local model/projector, capabilities and actual resident allocation. `/api/show`'s `{{ .Prompt }}` template is **not** proof of the fully rendered input. Preserve actual image count/hash/dimensions and private rendered-input or prompt-token evidence. Local base64 images, disabled cloud and localhost alone are not offline proof. Author [rehearsal instruction](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5847092093) requires **both server and runner in one isolated network namespace/container**, with external requests failing and local text/image answers succeeding. Never disconnect the whole laptop or change host firewall/network; another project is running there.

Stop a task-owned foreground server with Ctrl-C in **its own console**. Any PID cleanup requires recorded task ownership and current verification. Never `pkill`, terminate shared services, unload unrelated models or touch unavailable Blackwells. No start/stop occurred in this review.

Copy [native example config](../../scripts/ljaniec/gemma4-native-ollama.example.json) into the execution owner's private run folder and set its **actual verified** endpoint/model/revision. `model_revision` annotates provenance; it does not enforce serving identity. The runner forwards only supported payload fields: model/messages/max_tokens/reasoning_effort. Adding config `options`, `temperature` or `num_ctx` has no effect.

[Pinned OpenAI conversion](https://github.com/ollama/ollama/blob/v0.34.4/openai/openai.go) maps `reasoning_effort:none` to native `think:false`, and max_tokens to num_predict. It lacks context/truncate/shift controls. [Pinned native handler](https://github.com/ollama/ollama/blob/v0.34.4/server/routes.go) defaults truncate and shift to true. Thus OpenAI HTTP200 cannot certify no prompt truncation; require sufficient effective context and backend evidence. Native `think:false, truncate:false, shift:false` is documented behavior, not permission to replace the existing runner. Output must be nonempty **final content**, explicit normal finish, error null; reasoning-only, missing finish, length/timeouts/HTTP errors remain failures.

## 4. Existing input and organizer commands

Validation v1 remains preserved. [Lead key-free bootstrap/v2 repair](../kwiscion/validation-2024-keyfree/README.md) publishes v2 SHA `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`, 40 items / 60 points, 30 image-labelled and ten text-labelled rows. Keep its referenced pages and generated manifest together. Acquisition is a prior online step; local-PDF bootstrap and repair reuse existing assets. No keys enter generation. **Do not execute another full arm until the author declares it.** Retain the assigned 1024-token budget / <=600-second timeout; Greg's essay advice of 2048–4096 does not override the arm contract. Never open May2025 or build exam-derived retrieval/training.

Organizer final input is its own `exam.json`, `images/`, `answers-template.json`, with its own IDs/counts. Do not hardcode the 37-item May2023 mock or 40-item validation counts. [Greg's existing offline adapter](../Bukareszt/submission/README.md) is stdlib-only and invokes `infer.py`, not another runner. Safe **zero-call** local check, with a fresh ignored work directory:

```sh
python3 scripts/Bukareszt/matura_package.py run \
  --exam-dir agentsLog/Bukareszt/submission/fixtures/tiny-package \
  --config scripts/ljaniec/gemma4-native-ollama.example.json \
  --workdir agentsLog/ljaniec/private/issue38-synthetic-dry-run --dry-run
```

Final operator sequence, **only during an assigned rehearsal/final**, after configuring `PKG`, `RUN`, `CFG` to existing package, fresh ignored run directory and verified model config:

```sh
python3 scripts/Bukareszt/matura_package.py check --exam-dir "$PKG"
python3 scripts/Bukareszt/matura_package.py run --exam-dir "$PKG" --config "$CFG" --workdir "${RUN}-dry" --dry-run
# Both RUN-dry and RUN must be fresh; dry-run creates prepared files.
python3 scripts/Bukareszt/matura_package.py run --exam-dir "$PKG" --config "$CFG" --workdir "$RUN"
python3 scripts/Bukareszt/matura_package.py validate "$RUN/answers.json" --exam-dir "$PKG"
```

Check every command status. Run/finalize exit1 can leave a valid file with blank failed answers; read the failure report rather than treating existence/format as correctness. [Follow-up #45](https://github.com/kwiscion/machinekind-matura/issues/45) was fixed by merged #48 (explicit completion/error/source fields), and #49 fixes inherited proxies for loopback in infer.py. Use those merged revisions or newer; shell proxy clearing remains useful defense. No shared code changed by ljaniec.

[Organizer guide](https://matura-json-guide.ania-olchowik.chatgpt.site/) requires full question/source/instructions and actual PNGs (verify hashes), exact string IDs, Polish answer strings, and only `exam_id`/`answers` with `id`/`answer`. UTF8 file <=1MiB, each answer <=100,000 characters; retain failed IDs as blank strings. Answer-format examples are syntax, not solutions. Lead privately manages team code/registration/submission receipt; receipt/format acceptance is separate from scoring. Raw questions/keys/provider/reasoning envelopes stay private. Current owner allows public **answer-only** handoffs only after copied-source audit, preserving IDs/errors/provenance.

### Prepared isolated rehearsal: reuse the lead's accepted helper

The lead already implemented [offline_rehearsal.py](../kwiscion/offline_rehearsal.py) in #63/#64 while this handoff was overdue. Reuse it; do not add a second rehearsal controller. **Lead only, after a separate declaration and an empty owned GPU queue**: at most two invented text/image requests, 1024 tokens each /2048 total, thinking off, context4096, timeout420s, no retries/warmup, $0. It uses the lead's existing WSL cache/binaries and WSL-specific nvidia-smi path; it is not yet a configurable RTX/Windows deployment helper.

```powershell
wsl --exec python3 -B /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/offline_rehearsal.py --execute --output /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/private/offline-rehearsal-run-01
```

Use a fresh output directory. Preconditions: existing `unshare`, `ip`, Python, GPU visibility, `/usr/local/bin/ollama`, bundled llama-server and `/usr/share/ollama/.ollama/models`; no active GPU compute/known inference process, no host resident model. The lead separately decides whether to unload **their own** resident model; the helper does not unload it or stop the daemon. No downloads/install/whole-machine isolation. The helper creates `unshare -rn`, activates only its loopback, verifies external IPv4/IPv6 failure, distinct host namespace and matching server/runner namespaces. Cold load is in request one; resident digest/context is checked before request two. Cleanup targets only its recorded server group/namespace.

[Independent lead review](../kwiscion/2026-09-26-offline-rehearsal-independent-review.md) reports a successful namespace-only capability probe and six mocked CPU checks; **not a completed GPU offline rehearsal**. Ljaniec has not executed `--execute`, created a namespace, or called a model. Full CUDA load, two complete responses, real valid answers.json and cleanup evidence remain pending. Allow up to980s plus prior asset hashing. Actual success must include `network-proof.json`, `readiness.json`, `success.json`, `cleanup.json`, validated answers and no failure/blank IDs; namespace creation alone is insufficient. If prerequisites fail, preserve logs and report the blocker rather than using host networking. See [resource assumptions and bound](../kwiscion/2026-09-26-offline-rehearsal-fallback.md).

## 5. Stage-time budget and later optimization gate

**RTX estimate pending completed RTX evidence.** Needed: total and complete/failure counts, finite positive per-item wall latency, cold-load time, image/text/essay classification, usage prompt/completion tokens where reported, and effective context/offload. Include prepare/hash, cold-load, inference, finalize/validate and submission/rehearsal reserve measured separately. A failed Spark startup's 2.392s is not throughput. Laptop timings are not RTX evidence.

Completed Qwen laptop reference only: answer-only file `agentsLog/kwiscion/model-answers/qwen35-9b-val40-1024.jsonl`, SHA `731c0ca3c18212e8ad50590c9bd4fce5fef4fa013c4fcc3249fdaede4a8a2418`: **36 complete /40 total**, mean completed latency **76.934s**, median **80.242s**, sum **2769.641s**. Four length stops stay in the 40-item scoring denominator; this completed subset is not whole-run elapsed time or a 5090 forecast. That answer-only handoff has no usage, so no tokens/sec can be derived.

Completed native Gemma laptop reference: `agentsLog/kwiscion/model-answers/gemma4-12b-val40-1024.jsonl`, SHA `39a5dbbb5b7262b8fb15bacfea051f27258951c9a2af3a48c52fce1c213aeaf3`: **40/40 complete**, mean **37.435s**, median **29.688s**, summed request latency **1497.381s**. Its manifest reports Ollama0.30.7, context4096, 1024 output tokens, timeout420s, inputv1. Answer-only rows have no usage; cold-load/prefill/decode separation and isolated peak GPU memory remain unavailable here. These are serial observed laptop requests, not final-stage elapsed time or RTX forecast.

After the selected serial RTX arm completes, compute for each category c: complete count n_c, mean and p95 completed latency L_c; report excluded failure/timeout counts separately. Planning midpoint = measured prepare + cold-load + sum(final package N_c * mean L_c) + measured finalize/validate + explicit operator reserve. **For this formula, subtract independently measured cold-load from the affected request before deriving L_c. If that separation is unavailable, use end-to-end request latency and omit the separate cold-load term; never count it twice.** Planning upper scenario uses p95 instead of mean, **not a guaranteed deadline**; singleton/unsampled categories and validation-to-final distribution changes remain uncertain. Prefer actual full-arm wall time for the observed dataset, including failed waits. 40*600s = 6h40 is merely the validation request-timeout envelope, excluding overhead; not expected duration.

Use backend usage/timings only when retained: completion tokens divided by decode seconds is decode rate; total complete tokens /sum completed wall latency is end-to-end rate. Do not conflate them or infer missing counts. Final package item count is unknown until release; do not promise a deadline from 40-item validation alone.

Only if measured serial runtime threatens the available stage window, the concrete supported candidate is **two independent request slots via `OLLAMA_NUM_PARALLEL=2`**, with fixed model/context/settings and sufficient measured KV/VRAM headroom. [Ollama concurrency docs](https://docs.ollama.com/faq) explain parallel context memory multiplication. This is a conditional proposal, **not implementation or authorization**: keep parallel=1 now; existing runner is serial. A lead-assigned bounded comparison would retain IDs/order/errors and total stage time, not rerun a full baseline speculatively. No array-of-messages “batch”, unverified `n>1`, new runner or silent token/context change.

## Handoff and continued review

Checks actually performed by ljaniec on this refreshed repository: the existing invented four-item/two-image adapter fixture passed `run --dry-run` with the new config, zero requests; `python3 -m unittest discover -s scripts/Bukareszt -p test_matura_package.py` passed **51 tests**, and `python3 -m unittest test_infer` passed **10 tests**, including proxy transport guards. An independent Sol reviewer rechecked the #48 acceptance fixes and complete Gemma timing/hash calculations. Documentation/config review identified the cold-load double-count risk above and it was corrected. No namespace/server/model or runtime extraction/hash command was executed. Primary guide retrieved with a normal descriptive User-Agent; only format requirements are summarized, no source passages republished. Source/version links distinguish documented support from measured results.

Request from #33: exact OS; archive and executable SHA; actual version/driver/backend/VRAM; all manifest/layer hashes/bytes; effective context and rendered image delivery; text/image completed smoke evidence; offline proof; full declared-arm latency/usage and failures. These measured fields remain open. Coordinate pinned retrieval deployment only via Greg #44, preserving index SHA `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`, 107 sources /3,481 chunks; staging does not authorize an RAG arm.

The 15-minute issue/comment monitor continues, with durable IDs/state under `agentsLog/ljaniec/private/`. Pass the user's whole standing brief and current repo/issue rules to every delegated session. No purchases/reset credits, no duplicate workers, private raw evidence preserved, no claimed completion without proof. #5 stays closed; #38 continues measured-manifest review after this first delivery.
