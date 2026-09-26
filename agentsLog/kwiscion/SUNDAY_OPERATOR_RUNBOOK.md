# Sunday operator runbook — bare Gemma working candidate

Prepared 26 September, 17:10 Europe/Warsaw. **Operator draft, not a launch authorization or final candidate freeze.** Recheck `WINNING_PLAN.md` and the lead's final decision before Sunday 11:00 freeze. Bare Gemma remains the working candidate (provisional 35/60); policy/crops/RAG are not promoted. Full RAG adjudication is now 27/60 [22,33] (PR #79); see [review](../Pewciu6/2026-09-26T1747-score-gemma-rag-full.md).

## Preflight and declaration

- One attended operator owns the GPU queue. Confirm no other inference worker, including a waiting dispatcher; never stop another owner's process. Acquire the organizer package through the actual organizer channel; keep `exam.json`, `answers-template.json`, PNGs, raw results and team code private. Do not open May 2025 as a rehearsal.
- Use the verified Python 3.10+ / Ollama 0.30.7 runtime and frozen `gemma4:12b-it-q4_K_M`. Endpoint is **http://127.0.0.1:11434/v1**, with no `--allow-remote`; loopback alone is not proof of offline execution. The server and runner must share the reviewed, proven offline environment before final use.
- Verify installed tag digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, effective loaded context **4096**, thinking off, config SHA-256 `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`. The config does not itself enforce context or weight identity. Read-only `/api/tags`, `/api/show`, `/api/version` and `/api/ps` provide runtime evidence; an unloaded model loads on the first authorized real request, not an extra warmup.
- Saved model blob `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606`: 7,381,382,048 bytes; projector `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842`: 175,115,584 bytes. **Total7,556,497,632bytes; remaining1,243,502,368 under the new aggregate8.8GB cap.** Organizer clarification limits ALL submitted model weights together. Inventory every included weight, including adapters/auxiliary models conservatively; exclude development caches and duplicate models. Verify actual files, not GPU allocation. Existing `offline_rehearsal.py` checks the baseline cache, not completeness of the final package inventory. See [current rule](../../docs/SUBMISSION_WEIGHT_BUDGET.md).
- Declare package item count `N`, at most `N` calls, `N*1024` requested output tokens, 420 seconds/request, $0, no retries, finish deadline and exclusive queue owner. Preserve original sampling defaults (observed temperature 1/top-k 64/top-p .95; seed unset). New package context fit is unproven; inspect source/image completeness and reserve enough time. The simple CLI below enforces calls/tokens/request timeout, **not** a global deadline, concurrency or runtime/context guard; those remain an attended operator obligation. If that cannot be maintained, do not launch this CLI unattended.

## Prepared bounded offline launcher (#66; synthetic runtime proof complete)

`run_gemma_package.py` now supplies a separate generic package path. Default mode performs CPU preflight only and leaves the future output directory absent. After independent review and separate queue/runtime authorization, append `--execute` to the same command. Execution prepares input/config, isolates server and runner together, verifies assets/runtime/context, reserves each call, stops on the first error or insufficient full-timeout budget, cleans only its owned server group, then finalizes all template IDs (failed/unsent answers blank; launcher validation failures are retained as row-level errors with original raw responses preserved). It uses the same exclusive lock as the two-case rehearsal. The only config change is the isolated endpoint port 11435; sampling remains unchanged.

```bash
python3 agentsLog/kwiscion/run_gemma_package.py \
  --exam-dir "$PKG" --config "$CFG" --output "$RUN" \
  --max-calls "$N" --max-output-tokens-total "$((N*1024))" --wall-seconds 3600
# Add --execute only after review and explicit launch declaration; do not run concurrently.
```

Set `PKG`, `CFG`, `RUN`, `N` as below; select and declare an appropriate wall bound rather than assuming 3600 seconds meets the event allowance. Nine CPU tests and seven edge checks passed. A four-item synthetic dry preflight launched no model. The generic launcher has now also completed a separate two-item synthetic runtime qualification in an isolated server/runner namespace: both outputs were nonempty, with no errors or unsent items. CUDA was active on the laptop RTX 2000 Ada (35/49 layers); the projector stayed on CPU because VRAM was limited. This does not establish real-exam correctness, 40-item context fit or completion inside the event window. See [qualification result](2026-09-26-final-launcher-qualification-result.md). Raw results remain private; final failure report is `failures.json`. The following decomposed commands remain useful for diagnosis, but are not a substitute for isolation.

## Verified adapter command interface (Bash/WSL, repository root)

Replace the three paths and set `N` from the checked real package, never the mock's count. Use a fresh run directory. These commands are prepared, not executed by this document.

```bash
PKG=agentsLog/kwiscion/private/sunday/package
RUN=agentsLog/kwiscion/private/sunday/run-01
CFG=outputs/local-smoke/gemma4-12b-val40-1024.config.json
N=40  # EXAMPLE ONLY: replace with checked organizer item count
python3 scripts/Bukareszt/matura_package.py check --exam-dir "$PKG" --expect-items "$N"
python3 scripts/Bukareszt/matura_package.py prepare --exam-dir "$PKG" --output "$RUN/input.jsonl"
sha256sum "$CFG" "$RUN/input.jsonl" "$RUN/input.jsonl.manifest.json" infer.py scripts/Bukareszt/matura_package.py
python3 infer.py --config "$CFG" --input "$RUN/input.jsonl" --output "$RUN/raw.jsonl" --max-calls "$N" --dry-run
# STOP: confirm declaration, actual hashes, offline proof and exclusive queue before this command.
python3 infer.py --config "$CFG" --input "$RUN/input.jsonl" --output "$RUN/raw.jsonl" --max-calls "$N"
# Run finalize even when inference exits 1; inspect its failure report rather than retrying.
python3 scripts/Bukareszt/matura_package.py finalize --exam-dir "$PKG" --raw "$RUN/raw.jsonl" --manifest "$RUN/input.jsonl.manifest.json" --output "$RUN/answers.json"
python3 scripts/Bukareszt/matura_package.py validate "$RUN/answers.json" --exam-dir "$PKG"
sha256sum "$RUN/answers.json" "$RUN/answers.json.failures.json"
```

The direct runner accepts 1–100 items. A larger package needs a separately declared reviewed batching plan; do not silently increase the budget. `check` validates package/template IDs, required fields and PNG assets; `prepare` preserves task/source text and writes resolvable image paths plus provenance. Runner images are local data URLs, maximum 20 MiB each. Visually check full source panels, legends and cross-page material; format checks cannot establish source fidelity.

`infer.py`: exit 0 success, 1 includes failed cases, 2 invalid preparation. `finalize`: exit 1 can still produce valid JSON with blanks. Missing IDs, errors, empty finals and length-truncated/incomplete responses remain `""` in template order and are recorded in `answers.json.failures.json`; duplicate/unknown IDs are refused. Do not paraphrase, silently repair answers, drop IDs or rerun failures. Preserve partial raw files; malformed partial JSONL requires explicit recovery review. `validate` proves schema/ID validity, not correctness or acceptance by the organizer. Submit only via the real instructed channel, retain its receipt, and never publish the team code.

## Evidence and remaining gates

Two distinct two-item synthetic rehearsals now pass: the [fixed offline rehearsal](2026-09-26-offline-rehearsal-result.md) verified isolated Gemma/CUDA execution and cleanup, and the [generic final-launcher qualification](2026-09-26-final-launcher-qualification-result.md) exercised the generic package path with two nonempty outputs, zero errors, isolated networking and cleanup. Both used synthetic fixtures; neither is an exam score, full-package context/throughput proof, organizer receipt or final-candidate approval. The generic runtime used partial CUDA offload (35/49 layers) and kept the projector on CPU.

The bare Gemma baseline remains the working candidate at provisional 35/60. The disjoint first-pass RAG result remains 26/60 [23,31] as historical evidence; PR #79 full adjudication is 27/60 [22,33] and RAG is not promoted. See [full review](../Pewciu6/2026-09-26T1747-score-gemma-rag-full.md). Piotrek’s PR #73 supplies independently reviewed RTX 5090 synthetic readiness for a separately declared full40 source-v2 runtime-transfer control; it is not the RAG runtime or an exam result. Owner-supplied H100 access is being checked by the separate [readiness declaration](2026-09-26-h100-readiness-launch.md); remote H100 runtime/model/context and image readiness are not yet verified. Laptop rehearsal evidence does not transfer automatically to H100 Ollama 0.34.4/context 32768. Follow `WINNING_PLAN.md` and the active launch declarations for ownership.

Still unproven: final package arrival/schema/count and allowed runtime; confirmed Sunday operator/registration/team-code custody; RTX 5090 full-exam run; H100 remote runtime/readiness verification; real-package context fit and full-window throughput; final candidate freeze; organizer acceptance and submission receipt. No submission endpoint or final hardware qualification is assumed.
