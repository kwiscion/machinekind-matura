# Issue #5 overnight handoff — @ljaniec

Prepared at the 2026-09-26 08:00 Europe/Warsaw run cutoff. Branch: `issue-5-ljaniec-smoke-harness`. Scheduling authority: [issue #5](https://github.com/kwiscion/machinekind-matura/issues/5). Detailed source metadata, commands, and evaluator integration: [smoke-harness.md](smoke-harness.md).

This report covers the independent API runner session only. [PR #25](https://github.com/kwiscion/machinekind-matura/pull/25) from a parallel Łukasz session was merged at 09:42 and reported real Qwen3-8B CPU/Spark smoke on 20 synthetic history prompts. Its README, scripts, and measurements are preserved; those prompts are not the official fixed DEV or VALIDATION exam. Issue #5 was closed after that delivery. The lead now asks us to preserve this independent runner/recipe and stop Spark environment repair, duplicate model downloads, and specialist training.

## Delivered locally

- `scripts/ljaniec/run_local_smoke.py`: standalone localhost inference runner with local model/projector SHA-256 and byte checks, 8,000,000,000-byte enforcement, fixed-seed text/image request handling, append-only evaluator-compatible raw outputs, and run manifests.
- `scripts/ljaniec/model_candidates.json`: immutable model revisions, source-reported file hashes/bytes, license metadata, and model/projector relationships for the two requested candidate families.
- A no-training Blackwell load recipe, evaluator handoff, and source/split boundaries in the README.
- Eleven private May 2023 DEV text smoke inputs, hash `e5c36d25e4235a6d2361da842f5bea036f708d899e6b24f62f25164f50949bac`. They omit images and are load/failure diagnostics, not a complete exam benchmark. Exam text and all mutable monitor state stay git-ignored.

Python compilation, candidate-file match/mismatch rejection, temporary mock text/image endpoints, and evaluator output-schema validation passed in this session. These checks establish harness plumbing only; no mock response is a candidate result. `git diff --check` passes for the additive branch.

## Candidate evidence and missing measurements

| Candidate | Source-reported model + projector bytes | Local file verification | Real inference |
| --- | ---: | --- | --- |
| Google Gemma 4 12B QAT Q4_0 GGUF | 7,150,994,912 | Not performed | Not performed |
| Unsloth Qwen 3.5 9B Q4_K_M GGUF | 6,602,227,488 | Not performed | Not performed |

Both totals are below the saved-weight limit on metadata alone. Actual saved bytes, offline loading, runtime revision, tokenizer/template, vision compatibility, latency, and peak memory remain unverified. There is no selected working final model, scorecard, model-quality claim, or training result.

DEV accounting: 11 diagnostic inputs prepared; **0 inference calls attempted**, 0 outputs, and no score. VALIDATION: 0 calls, no keys acquired. SEALED_TEST: unopened. No TRAIN dataset or specialist pilot was delivered because the required real baseline did not become runnable.

## Access blockers and cutoff

Repeated `ssh -o BatchMode=yes -o ConnectTimeout=8 ljaniec@dell-gb10 'hostname'` checks reached the host but returned `Permission denied (publickey,password)`, including the 07:59 Warsaw check. No GPU job was started. The issue's 60-minute environment cap elapsed earlier; setup and training were stopped and the no-training fallback prepared. No new expensive run will begin after 08:00 under the overnight brief.

During the overnight window, every GitHub integration claim attempt returned HTTP 403 `Resource not accessible by integration`; the browser was signed out and `gh` unauthenticated. At the original cutoff this branch/report were local, with no remote claim or PR. The later recovery below supersedes this publication blocker.

## Handoff actions

1. Publish the scoped additive branch and report when GitHub write access works; use `needs-review` for this incomplete evidence handoff and retain the blocker in #5.
2. The lead can use the pinned manifest and recipe on an authorized machine. Verify actual hashes/bytes and runtime/template before a future baseline; respect the issue cutoff or obtain a new scheduling instruction in GitHub.
3. The evaluator's [final handoff](../Pewciu6/2026-09-26T0745-final-handoff.md) is ready for real outputs. It still requires matched denominators and provisional grading; only 18/60 validation points are fully automatic and 29/40 items need images.

No purchases, paid calls, credentials sharing, answer-key leakage, copyrighted exam publication, or sealed-test access occurred. The user's 15-minute monitor remains active until explicitly stopped and will continue checking new assignments after this overnight experiment cutoff. Pass the standing brief, repository rules, and this log to every future subagent, Orka, or Claude Code session.

## 09:00 monitoring update

The lead's morning status and AGENTS.md extend operational work through 10:47 Warsaw, new model calls through 10:30, and handoffs through 10:40. Earlier cutoff statements above describe the original overnight checkpoint. Source/split rules and the 60-minute Spark environment cap are unchanged. Spark remains unpromoted; both access blockers persist and no new run began. The 15-minute monitor continues under the user's standing instruction.

## 09:39 GitHub recovery and review

The user authorized `gh`; the CLI now authenticates as `ljaniec` with repository push/triage permissions. [The first claim comment](https://github.com/kwiscion/machinekind-matura/issues/5#issuecomment-5844334212) succeeded and the issue is `in-progress`. ETA is 10:00 for reviewed code/handoff publication. Spark SSH remains denied; no real inference or training has run.

Independent Sol review found malformed response shapes could crash before a manifest was saved. The runner now preserves malformed responses as per-item errors, saves an initial manifest, and finalizes actual output counts on interruption. It also reports empty/truncated answers as errors and refuses redirects/proxies for localhost requests. Four targeted failure-path tests, Python compilation, and `git diff --check` pass. These are plumbing checks using invented prompts and fake weights, not model results.

Sol approved the fixed additive runner and handoff after independently rerunning three non-network failure tests and reviewing the localhost redirect check. Approval covers the code and its honest limitations; candidate bytes, runtime compatibility, performance, and model quality remain unverified. A hard kill or disk failure can still prevent the final manifest update.
