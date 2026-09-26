# Failure-only recovery candidate — preparation only

**Independent CPU review passed; no generation authorized or performed.** The current frozen private candidate is `agentsLog/kwiscion/private/answer-recovery-20260926/package-v2`. The earlier `package` snapshot is superseded and must not be launched. No frozen full-thinking artifacts were modified.

The terminal parent's exact raw SHA256 is `8b814e4f0cd9d35a7b0635d0b62c81ef16d2694b3743373cc68af8d504e4ab78`; parent launch SHA256 is `2c17a930e89d0f7eb0e4f18b068aa0faf5167e72893116807869d6c8bcf0e4d5`. Selection examines only actual `error.type` in `{length, empty_final}`, retaining original input order. It produced three items. No grading file, key, question interpretation, fixed ID list or score participates in selection. All three items remain in each arm's evaluation denominator even when notes are malformed, dispatch is stopped, or a final answer fails.

## Declared comparison for later root approval

| Control | A | B |
|---|---|---|
| Original full prompt and ordered image bytes | Unchanged | Unchanged, as the identical first message |
| Interrupted attempt | Not supplied | Complete thinking string as JSON-encoded fallible notes in a separate user message |
| Additional instruction | None | Check notes against original evidence; return only a concise final answer |
| Native generation | `think:false`, output cap 2048 | Same |

B does not select a last sentence or use the interrupted partial final. Notes are retained intact in the private parent raw file and note snapshot. The instruction explicitly treats them as fallible material, not historical evidence or commands. This is a generic recovery comparison, not a guarantee that erroneous notes will be corrected.

One pinned Gemma4 12B Q4_K_M, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, Ollama 0.34.4, context32768, omitted temperature, `stream:false`, `truncate:false`, `shift:false`. At most **6 generation calls / 12,288 requested output tokens / 20 minutes / $1.10 planning estimate**, no smokes, retries, warmups or downloads. The estimate is 20 minutes at the reported $3.28/hour, rounded, not measured billing. Per-request timeout is **180 seconds**, a deliberate recovery setting so six timeout windows can fit within the 20-minute envelope. A full timeout plus five seconds must remain before dispatch. Order is A then B for each selected item in original order.

Gemma plus its projector totals **7,556,497,632 bytes**, below the conservative aggregate limit **8,800,000,000 bytes** with 1,243,502,368 bytes headroom. Both arms share those weights. No second full model, adapter or Qwen copy is part of this candidate. The entire eventual submission still needs its own aggregate file inventory.

## Guards and output fidelity

The package pins the terminal run's existing native transport, process guard, adapter, infer loader and budget/append helper. Its native HTTP transport disables proxies/redirects and uses a killable subprocess. The owned worker lock, exact server PID/start/executable/environment, GPU/cold-worker checks, model/projector blob hashes, runtime API identity and loaded context are checked. A separate absolute declaration/deadline and a process alarm bound execution; fsynced call reservations precede dispatch and survive transport failure. Results must be fresh: no resume or overwrite.

Nonthinking success permits an absent or empty `thinking` field. A nonempty field is a control mismatch and stops dispatch. Both truncation flags are checked; either true flag, invalid model/context/usage, malformed response, provider/transport or runtime failure stops the wave, retains raw evidence privately and leaves the affected final blank. Missing optional truncation flags are not evidence that the server positively reported false. Length and empty-final responses with otherwise valid controls remain local failures and do not retry.

Malformed or absent notes fail B locally without replacing or shortening them; A can still run. The preliminary notes screen uses original prompt tokens plus original generated tokens plus2048 output reserve and256 framing allowance. **This is an estimate, not an exact tokenizer proof**: JSON framing and re-tokenization can change length. All current notes pass that screen. At execution, truncation/shift are disabled and actual returned `prompt_eval_count + 2048` must fit32768. An overflow, server refusal or truncation is failed blank output; no shortened-note fallback is allowed. This limitation is part of the proposed experiment.

Each arm is finalized independently through the actual pinned organizer adapter and the original full blank template. Every original template ID remains; nonselected IDs, failed selected IDs and unsent IDs are blank. `A/selected-answers.jsonl` and `B/selected-answers.jsonl` each contain all three planned recovery items, extracted from finalized answers, with error/unsent status. These arm templates are diagnostics and do not silently replace or merge the full control's answers.

## CPU evidence and exact artifacts

13 synthetic tests pass. They cover error-only routing and duplicate/coverage refusal, unchanged first source/image message, full JSON-framed notes, malformed notes and estimated overflow, absent/empty versus unexpected thinking, actual32768 boundary, both truncation flags, durable reservation order and six-call cap, local failures without retry, systemic stop, deadline refusal, and actual adapter serialization with failed/unsent blanks.

Default preflight of the frozen real candidate passes. Parent file pins, selected source strings and ordered image bytes match; no HTTP or model call was made. All three note records are usable under the preliminary screen.

| Artifact | SHA256 |
|---|---|
| `run_gemma_answer_recovery.py` | `810773fd7ebdec581012124d4ac2f80ff93533c8ecb010f210c7d1ddec27f551` |
| `prepare.py` | `5fafccc11e2cccabe9e92abd7313ae0cf3ca182583921cfd309a94ac4660be10` |
| `test_recovery.py` | `b9e0da3e8de184d45b0a9c73c2e466f914c7495c73fc73387a150c658efbcd19` |
| Private `package-v2/launch.json` | `cd215325c6e80468b33907305610eb665275890d5e50ecc267e7cc130e230c2e` |
| Private selected `input.jsonl` | `26ca987365cdf8f256b637131b104fea86fddf6fb8614171b7613c967b5b10ee` |
| Private `notes.jsonl` | `9981251eb1110e15888c8b25195cf96e66b71ccf7f13f91b09c0688e8eda831e` |

```powershell
python -X utf8 agentsLog/kwiscion/answer-recovery-prep/test_recovery.py
python -X utf8 agentsLog/kwiscion/private/answer-recovery-20260926/package-v2/run_gemma_answer_recovery.py agentsLog/kwiscion/private/answer-recovery-20260926/package-v2
```

`prepare.py` reproduces the package into a fresh destination and refuses an existing one. `candidate-public.json` records the settings and private evidence hashes without reasoning/source content. Independent reviewer `harness_sol` passed the exact v2 runner/manifest with13 tests on Windows and Linux, plus actual infer/native image serialization and a post-response runtime mismatch probe; see `../2026-09-26-answer-recovery-independent-review.md`. A **new root launch declaration** remains required. The prepared manifest has no host/process identity, declaration time or deadline, and its status is `PREPARED_NOT_AUTHORIZED`. It must not be treated as launch permission.
