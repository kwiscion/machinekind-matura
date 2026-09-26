# Reasoning/decision lab — #38

Owner: @ljaniec. Prepared 2026-09-26; known May2024 validation development. Latest scheduling scope: [author assignment](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5848224753), [execution proxy](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5848270042). WINNING_PLAN/AGENTS/SOURCE/contracts govern. One dedicated owner-provisioned H100, no purchases or competing workers.

## Frozen panel and hypotheses

Question-only source-v2 SHA256 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`. Panel SHA256 `393d4b70ec748a899605cfbc52f4cf3301fb288f0e59ec16401fd42df88063b2`. Full sources, canonical prompt bytes and original ordered images retained privately; public ordered hashes in `2026-09-26-reasoning-panel.json`. Source bootstrap used the pinned official question PDF only; no answer key was acquired. Local110DPI Poppler image bytes are independently hashed, rather than assuming cross-platform PNG identity.

Nine items selected by question demand before inspecting old grades: z1,z2,z7,z10,z14.2,z19.1,z20.1,z20.2,z24. Covers closed/PF, chronology and decision with justification; six image items/three text items. Essay excluded. The existing independent RTX review confirms three previously correct controls after panel freeze: z2,z14.2,z20.1. This is provisional prior evidence, not imported quality or key-based routing. Panel denominator11points/9items; PF-specific comparison4points/2items. Fresh answers and independent grading are required.

| Frozen family | Calls | Change/hypothesis |
| --- | ---: | --- |
| Baseline |9|Native `think:false`, canonical prompt; fresh matched control.|
| Statement-wise PF |6|One independent source-preserving call per each of three explicitly reviewed statements in two PF items; off thinking, brief evidence justification, concatenate in statement order. This is decomposition, no voting claim.|
| Evidence critic |18|An independent off-thinking answer followed by a second call with the full original sources/images and proposed answer; ask for evidence-checked final answer.|
| Native thinking |9|Canonical prompt and native `think:true`; require nonempty actual thinking evidence and final answer within the same total generation cap.|

Frozen dispatch order: readiness if needed, all9baseline,6PF,18critic,9thinking. Total42generation calls/86,016requested output+reasoning tokens at2048/call. The lead proxy completed2successful text/image readiness calls before handoff,256requested output tokens each; [terminal evidence/handoff](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5848408299). Reuse these, with0new readiness calls. Count2calls/512requested tokens plus42experiment calls/86,016tokens:44total/86,528requested. Actual experiment input remains the frozen9-item panel393d… above. The optional original5/7 readiness fixture path is implemented and CPU-tested for genuinely unqualified future hosts; it is NOT dispatched on this qualified host. The first baseline is available for independent grading before potentially costly thinking. No hidden retries, sampling micro-tweaks, baseline text rewrite or selection of lucky saved answers.

One authorized wave maximum90minutes/120calls/240,000requested output+reasoning tokens/max4mechanism families. Reserve each call durably before request. A transport/identity/source/budget/length/empty-answer failure stops dispatch; failed and unsent items stay in denominators. Pivot after2uninformative probes or1destructive result without a repair hypothesis; another probe requires an explicit remaining-budget/deadline record, never an automatic reset. First independently scored subset due45minutes after actual readiness. No full-exam or promotion claim from this subset.

## Runtime and accounting

Pinned Ollama0.34.4 executable SHA256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`; `gemma4:12b-it-q4_K_M` served manifest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, context32768. Model/projector saved bytes total7,556,497,632 (<8,000,000,000); exact blobs pinned by supervisor. Runtime source and license provenance reuse the accepted owned Gemma runbook. Device SSH access is verified privately; owner supplied3.28/hour; own pinned assets are verified and lead proxy text/image readiness is complete; native thinking-on and offline isolation remain unproven. Do not substitute another lab or assume its rate.

Native `/api/chat` uses `stream:false`, explicit boolean `think`, raw base64 images in original order, `truncate:false`, `shift:false`, `num_ctx:32768`, `num_predict:2048`, no sampling override. [Pinned API types](https://github.com/ollama/ollama/blob/v0.34.4/api/types.go), [handler](https://github.com/ollama/ollama/blob/v0.34.4/server/routes.go), [backend](https://github.com/ollama/ollama/blob/v0.34.4/llm/llama_server.go) establish the native contract. `eval_count` is total generated tokens including reasoning; final-only/thinking-only token counts are unavailable and remain null. Thinking/final text remain separate private fields. Never add reasoning tokens twice or infer counts from characters.

Local executable/blob/manifest SHA checks, live version/served digest/show references/context and cached request image bytes bind execution. Acceptance requires no non-null error, no truncation, done=true, reason=stop, nonempty final answer, expected thinking behavior and conservative context accounting. These checks do not constitute organizer-path, offline-network or whole-system quality proof.

## Reproduce and execute

Acquire/rebuild question-only input in a fresh ignored owned folder (see accepted `agentsLog/kwiscion/validation-2024-keyfree/bootstrap.py` and `repair-v2.py`). Keep panel beside source-v2 so image paths remain valid:

```sh
python3 -B scripts/ljaniec/prepare_reasoning_panel.py \
  --source agentsLog/ljaniec/private/reasoning-lab-20260926/runner_input.v2.jsonl \
  --output agentsLog/ljaniec/private/reasoning-lab-20260926/reasoning-panel.jsonl
```

The standalone controller's default/check mode sends zeroHTTP. Before execute, provide an actual private manifest: run_id, owner=ljaniec, local hostname, runtime, loopback base_url, panel input_sha256, ordered image_hashes, actual positive hourly_rate_usd, explicit deadline_utc, max_calls/max_requested_tokens/max_wall_seconds/timeout_seconds, num_predict, readiness_calls, frozen dispatch_order, model/digest/context/assets, cuda_visible_devices=0 plus absolute ollama_binary/models_dir. Do not fill missing values from guesses. Publish safe hashes/config and estimated ceiling before dispatch; retain infrastructure details privately.

```sh
python3 -B scripts/ljaniec/reasoning_lab.py --manifest PRIVATE_MANIFEST --panel PRIVATE_PANEL
python3 -B scripts/ljaniec/reasoning_lab_supervisor.py \
  --manifest PRIVATE_MANIFEST --panel PRIVATE_PANEL
python3 -B scripts/ljaniec/reasoning_lab_supervisor.py \
  --manifest PRIVATE_MANIFEST --panel PRIVATE_PANEL \
  --run-dir NEW_OWNED_PRIVATE_RUN_DIRECTORY --execute
```

Only the supervisor may execute the controller. It starts a fresh pinned owned Ollama process on an unoccupied loopback endpoint, holds owner/runtime locks, verifies its listener/process identity and passes an inherited pipe lease. It bounds actual server/controller process groups by UTC/maxwall, kills only freshly started owned groups on expiry/termination/completion/server failure and reaps them. Existing services are never adopted or stopped. Client timeout alone cannot prove backend cancellation; the owned server supervisor supplies actual cleanup. Independent review approved the controller/supervisor; exact code hashes and PR checks are recorded before launch. Pinned Linux backend [process settings](https://github.com/ollama/ollama/blob/v0.34.4/llm/llm_linux.go) retain the server process group; an independent guardian owns the server and enforces the deadline even if the foreground supervisor is killed. A2second cleanup margin precedes the declared stop.

Raw requests/provider responses/thinking/source bytes stay private. `answers.jsonl` retains exact final answers, IDs/family/status/errors, usage and latency; public answer handoffs may include our exact answers but exclude embedded third-party source packs/keys/credentials. Back up private remote evidence locally after each bounded run; notify #11 independent grading and #38 findings. May2025sealed; fixed exam derivatives never training/RAG. Final promotion remains lead-owned and requires the complete organizer path.

## CPU evidence

Question-only acquisition and source-v2 repair succeeded;40prompts unchanged, z13image repaired, no keys. Panel reconstruction produced identical SHA/bytes. Controller tests cover reservation caps, hard client cancellation, ordered images/hash mutation, native thinking/finish/error/context guards, lock/no-overwrite, attemptedfailed versus unsent IDs and supervisor lease gating. Independent combined test discovery passed44CPU tests, including real child/group cancellation and guardian parent-death regressions. The pinned native runtime contract was independently checked from primary source; exact-head CI/provenance are recorded in the PR. Local preparation made zero model calls;2proxy readiness calls are counted separately. No experiment answers/score are claimed yet. The proxy server must be freshly re-identified before retiring only that owned process group, as expressly authorized by the handoff; preserve its evidence/runtime and all unrelated processes.
