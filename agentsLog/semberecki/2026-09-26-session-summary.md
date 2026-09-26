# Session summary — 2026-09-26 (Claude Code, owner semberecki)

Session ID: `06a3ea25-892d-4648-adc6-90842bcea2e0`
Transcript: `~/.claude/projects/-home-piosemb-workspace-other-machinekind-matura/06a3ea25-892d-4648-adc6-90842bcea2e0.jsonl`
Window: ~14:49–17:05 CEST (12:49–15:05 UTC). Working directory: repo root on `main` (clean at start).

## Owner instructions received (standing)

- Watch GitHub issues addressed to Piotr every quarter of an hour; on new items dispatch a subagent task.
- Post results into the triggering issue; open new issues marking Piotr for discovered follow-ups; inform other agents.
- Results go to `agentsLog/` (`agentsLog/semberecki/`) as the shared knowledge center.
- Keep polling while subagents run. Do not wait for owner approval to merge scoped additive PRs.
- NEVER buy anything. Pass these rules verbatim to every subagent / Claude Code session.
- Use the SSH key `id_ed25519` copied into the repo directory.

## Findings

- Piotr = GitHub `semberecki`, assignee of #33 (RTX 5090 Gemma readiness). `Pewciu6` is Paweł Litwin, not Piotr.
- Machine: NVIDIA GeForce RTX 5090 Laptop GPU, 24,463 MiB; 62 GB RAM; ~112 GB free disk; no Ollama at start.
- Open issues mentioning Piotr at first poll (~15:52 UTC): #3 (lead), #11 (Pawel), #33 (mine, `ready`), #38 (Lukasz).
- #33 @13:52Z (kwiscion): Gemma provisional 35/60 vs Qwen 24/60 (Paweł 26/60); Gemma is the working base. Lead asks Piotrek to **claim RTX preparation with actual runtime/VRAM/model readiness and ETA**; no Piotrek acknowledgment had reached the issue. Do not start a full arm or change the prompt; synthetic checks stay within the four-call envelope. A ready RTX would help the 18:00 target.
- #11: consolidated provisional tally (PR #53) Gemma 35/60, Qwen 25/60; format arm auto 10 vs 11 not a valid numeric rejection; Luna exporting format40 answers + one-item source-v2 correction (ETA 16:12).
- #33 @13:47Z (Bukareszt): chrono index staging handoff from #44 / PR #50 (`scripts/Bukareszt/stage_index.py stage`), nothing to run now.

## Actions taken

- SSH key `id_ed25519` located in repo root (perms 600/644), excluded from tracking via `.git/info/exclude` (shared `.gitignore` untouched); verified `ssh -T git@github.com` → "Hi semberecki!". Git ls-remote over SSH works.
- Created (later removed from the working tree by an unknown party before 17:05 — needs recreating): `agentsLog/semberecki/README.md` (owner handoff), `watcher/poll-issues.sh` (unauthenticated read-only poller, curl + python3, filters assignee/mentions of semberecki/Piotr/Piotrek with full comment bodies), `watcher/2026-09-26-watcher-log.md` (tick 0), `private/watcher-state.json` (gitignored snapshot, 4 issues).
- Saved persistent memory notes (watcher instructions; identity/credentials).
- Later in the session (per updated memory): `gh` CLI v2.101.0 installed at `~/.local/bin/gh` and logged in as `semberecki` with `repo` scope — issue comments, labels and PRs are now possible.

## Not completed / blocked

- Subagent dispatch for bounded #33 RTX prep (user-local Ollama, native `gemma4:12b-it-q4_K_M`, hash/byte verification, ≤4 smoke calls, no full arm) was attempted three times; each was blocked by transient tool-permission classifier timeouts. Not started.
- The 15-minute cron watcher (`7,22,37,52 * * * *`) was rejected by the user at creation; no scheduler is running. Per AGENTS.md, an issue prompt alone is not a daemon — polling requires an explicit scheduler.
- No claim comment has been posted on #33 yet. Draft claim (to post via `gh`): session ID above, start time, ETA, route `gemma4:12b-it-q4_K_M` via user-local Ollama on RTX 5090 (24,463 MiB actual), commitment to ≤4 smoke calls and no full arm until the lead declares the next arm.
- Nothing from this session is committed.

## Continuation — session `01a0de3f-e03d-75ba-8a97-eb400acb36a2` (pi agent, started 17:05 CEST)

The owner asked this session to continue the standing watcher prompt (same
verbatim rules). Actions completed by ~17:20 CEST:

1. **Watcher scaffold recreated** (the earlier scaffold was wiped before
   17:05): `watcher/poll_issues.py` (stdlib, unauthenticated REST API, ETag
   conditional GETs, read-only), `watcher/poll-issues.sh`, log tick at
   15:10:22Z with 31 findings across 8 relevant issues (#33, #34, #36, #38,
   #39, #40, #44, #46), state under `agentsLog/semberecki/private/`
   (gitignored). Two script bugs fixed during bring-up: REST comments use
   `user.login` (not `author.login`), and issue keys are normalized to strings
   to avoid int/str state crashes.
2. **#33 claim posted** 17:15 CEST:
   https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847357936
   — actual GPU/runtime facts (RTX 5090 Laptop GPU 24,463 MiB; only
   `gnome-remote-desktop-daemon` on the GPU, no project inference worker on
   this host; Ollama not yet installed; route `gemma4:12b-it-q4_K_M`),
   commitments (≤4 synthetic smoke calls, $0, no full arm, no duplicate
   baseline), ETA. Label `ready` → `in-progress`.
3. **Quarter-hour cron restored** (owner re-consented in the continuation
   request): `7,22,37,52 * * * *` → `watcher/poll-issues.sh`, output in
   `watcher/.cache/cron.log` (git-excluded via `.git/info/exclude`).
4. **Bounded RTX prep started**: official Ollama `ollama-linux-amd64.tar.zst`
   (v0.34.4, 1.43 GB, free) downloading to `/tmp`; next: extract to
   `~/.local/ollama`, serve with `OLLAMA_MODELS=~/.ollama/models`, pull
   `gemma4:12b-it-q4_K_M`, verify bytes + manifest `4eb23ef1…`, then ≤4 smoke
   calls. Details: `agentsLog/semberecki/2026-09-26-rtx5090-gemma-prep.md`.
5. **Scoped additive PR #69 opened and self-merged** (watcher/ +
   agentsLog/semberecki/ only; regular merge, no admin/force):
   https://github.com/kwiscion/machinekind-matura/pull/69 (commit 65aa0b9).
6. **RTX prep completed ~17:35 CEST**: Ollama 0.34.4 user-local installed;
   `gemma4:12b-it-q4_K_M` pulled and **verified against the pinned recipe**
   (served ID `4eb23ef187e2`, model+projector 7,556,497,632 B — exactly the
   Spark-handoff bytes); **2/4 smoke calls used, both PASS** (text + synthetic
   image, thinking off, $0); model 100% GPU, llama-server 9,184 MiB VRAM.
   Results posted to #33 (comment 5847461530); report + JSON:
   `agentsLog/semberecki/2026-09-26-rtx5090-gemma-prep.{md,json}`.

## Next actions (standing)

1. Keep the quarter-hour watcher polling (cron running; check
   `watcher/2026-09-26-watcher-log.md` for new findings each tick).
2. Await the lead's frozen RTX handoff (visual diagnostic or bounded RAG on
   #57); do not start any full arm independently.

## Manifest v2 + throughput — 17:50 CEST

The 17:22 cron tick caught reviewer feedback predating the 17:35 artifact:
@ljaniec (independent #38 review of PR #69) asked to fix the stale `tgz`
filename and complete the provenance manifest; @kwiscion asked for RTX
throughput evidence vs the few-minutes-per-answer rule concern. Completed by
~17:50 CEST:

- **Smoke 3/4 used** (longer synthetic generation, generic content): 233 tok in
  4.32 s = **54.0 tok/s sustained warm**; smoke 4 reserved. Envelope: 3/4, all
  PASS, $0, no exam material.
- **Provenance complete** (source metadata kept separate from load evidence):
  archive `ollama-linux-amd64.tar.zst` v0.34.4 sha256 `c238986e…b9533`;
  executable sha256 `ad9c5344…92ff4`; driver NVIDIA 13.2, backend CUDA
  (`ollama,cuda_v13`); full local manifest layer digests; effective context
  32768 from actual `/api/ps`; stale `tgz` corrected.
- **Throughput vs rules concern**: laptop reference mean 37.4 s per completed
  answer (partial CPU offload); RTX warm ~4–5 s per 116-word answer — roughly
  **8× faster per answer**; a full 40-call arm fits the rule with margin. Cold
  load ≈ 58 s incl. model load.
- Manifest posted to #33 (comment 5847487636) + pointer on #38 (comment
  5847489914). Committed on `issue-33-semberecki-smoke`, merged as **PR #73**
  (3ca2a54). Artifacts:
  `agentsLog/semberecki/2026-09-26-rtx5090-gemma-prep.{md,json}`.

Owner question "should I install ollama?" answered ~17:40: no — user-local
0.34.4 install already done and verified; system-wide install unnecessary;
no-systemd caveat documented (relaunch via `OLLAMA_MODELS=$HOME/.ollama/models
~/.local/ollama/bin/ollama serve` after a reboot).

## Manifest v3 + control check — 17:45 CEST

Continuation tick at 15:37:04Z (17:37 CEST) caught @ljaniec's independent
acceptance checklist (predating v2) and @kwiscion's image-token control
request. Completed ~17:45 CEST, zero model calls, smoke 4 still reserved:

- Full synthetic-image SHA-256 `b33a595b…f5566d`; per-smoke load/prefill/decode
  split in the JSON; per-call context note (no override, 32768); memory
  reading qualified as a single nvidia-smi sample.
- Image-token control on 0.34.4: `--image-min-tokens`/`--image-max-tokens`
  exist in the bundled llama-server; `ollama serve` reads `LLAMA_ARG_*` env;
  serve process holds 72 inherited env vars; direct backend-env capture
  pending a runtime probe (llama-server unloads on keep_alive expiry).
- Posted to #33 (5847573297) and #38 (5847573439); merged as **PR #76**
  (ec06de5).
- WINNING_PLAN.md updated to a 17:12 decision record: lead's frozen bounded-RAG
  arm on the laptop (cutoff 17:40, in-flight 420 s requests to 17:47); 18:00
  gate = honest score vs 48/60; Sunday decision memo after 18:00. My RTX stays
  readiness-only until the lead declares a GPU job.

## RTX runtime-transfer control RUN — 17:46–17:56 CEST

The lead declared the frozen RTX runtime-transfer control on #33 @15:44:13Z
(comment 5847447636 thread, start claim 5847606619): full 40-item official
key-free source-v2 run on my verified host, superseding readiness-only for
this one job. Executed 17:46–17:56 CEST:

- **Input rebuilt and verified**: untouched key-free bootstrap (official
  question PDF `ad66a7c4…`, pdftoppm Poppler 24.02.0, 110 DPI, 21 pages) +
  explicit repair-v2 → `runner_input.v2.jsonl` SHA `6615fea2…015a4` — **exact
  frozen hash match**; raw exam artifacts stay private.
- **Run: 40/40 dispatched, 0 unsent, 0 errors, 0 empty, 0 length-stops** —
  40/40 complete answers in **2 min 26.6 s** (start 15:54:18Z, end 15:56:44Z;
  dispatch deadline 16:34:18Z not approached). Latency mean 3.66 s / median
  3.51 s / max 11.84 s; completion sum 6,513 (max 717); prompt max 1,979
  (no truncation); context 32768 preserved; thinking none; $0; no retry/warmup.
- **Owned wrapper** enforced the frozen envelope around untouched `infer.py`
  (deadline check per dispatch, per-result flush, 2-consecutive-infra stop,
  context-overflow stop). Driver "13.2" corrected to unverified per @ljaniec.
- **Answer-only handoff for @Pewciu6/#11**:
  `agentsLog/semberecki/model-answers/gemma4-12b-val40-v2-rtx-transfer.jsonl`
  (40 rows, sha256 `179ccf38…bef600b`); copied-source check done (flagged
  sequences are task-instruction echoes, not source copies). Results posted to
  #33 (5847700897) + #11 (5847701049); merged as **PR #85** (0ffd0a8).
- This is a runtime/context transfer comparison point, **not a score**; all
  previous attempts preserved; scoring owned by @Pewciu6 on #11.

## Independent adjudication + audit — 18:09–18:17 CEST

- **@Pewciu6 adjudication (PR #89, merged)**: RTX transfer **34/60 (25–39) vs
  bare Gemma 35 (28–40), Δ −1 — verdict EQUIVALENT**; differences look like
  sampling noise, not a systematic runtime/context effect. Answer SHA
  `179ccf38…bef600b` verified; keyscan 0 hits; $0.
- **@ljaniec full runtime audit (PR #90, merged)**: verified answer-file SHA,
  40 unique matching IDs, request sum 146.276 s, mean 3.6569 / median 3.508 /
  p95 7.278 / max 11.835, config hash matches; wrapper findings tracked on
  new issue #88; no repeat run required.
- **Watcher log repaired (PR #91)**: PR #87's stash-conflict resolution had
  dropped the 15:45:30Z/15:52:02Z/16:03:00Z tick content; cleared poller
  comment records and re-polled — tick 16:13:11Z re-logged the full window
  (49 findings). GitHub issues remain the scheduling authority.
- Stage-time estimate posted on #38 (5847735746): full 40-item arm fits in
  ~3 min warm / ~4 min cold on RTX-class hosts; no 560 image-token cap
  applied anywhere per the lead's 16:02:05Z warning.

**Session status at 18:17 CEST**: frozen RTX job complete + adjudicated
(equivalent); all handoffs delivered; logs repaired; watcher cron continues
(minutes 7,22,37,52); smoke envelope 3/4, smoke 4 reserved; awaiting the
lead's next declared GPU arm.

Key finding: the lead's "sole laptop worker" (frozen bare-source-v2 RAG arm,
cutoff 17:40) is NOT on this machine — no project inference process runs here,
so readiness prep cannot duplicate it.
