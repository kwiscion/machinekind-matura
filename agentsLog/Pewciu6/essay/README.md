# Essay route (issue #80): first CPU deliverable

Owner: @Pewciu6. Written 2026-09-26, about 19:20 Europe/Warsaw. **No model calls, training or inference were run.** The pilot below needs the lead to assign a host and publish a launch record first.

## Hypothesis

A dedicated long-form essay prompt removes the conflict between the global instructions and the essay task. It should raise both length and aspect coverage. The global header asks for concise answers ("zwięźle") and for `Rozstrzygnięcie/Uzasadnienie` labels. Planning first (plan/write) may also improve how well the facts support the claims, at a matched final cap. Choosing the topic is a separate ablation and is **off** by default.

## Files

| Path | Purpose |
|---|---|
| `scripts/Pewciu6/essay_route.py` | Stdlib router and prompt builder. `build` handles single-pass, plan or both. `write-from-plan` runs after the plan stage. `--dry-run` prints the envelope and writes nothing. |
| `scripts/Pewciu6/essay_report.py` | Deterministic post-hoc report with no model calls: word count (headings and labels excluded), `underlength` (<300), thesis, labelled aspects, conclusion, distinct years, a named-term proxy, `preamble` and `solver_format_leak`. |
| `scripts/Pewciu6/essay_pilot_run.py` | **Bounded launcher, the only sanctioned launch path** (added by the PR #102 review fix). One global 30-minute deadline, per-call timeout `min(420 s, time left)`, ledger of at most 6 calls / 7168 requested tokens, no retries, deterministic stop, `run_manifest.json` on every exit. |
| `scripts/Pewciu6/test_essay_route.py`, `test_essay_pilot_run.py` | 48 unit tests on synthetic fixtures, fake backends/clocks and a loopback stub HTTP server only. |
| `agentsLog/Pewciu6/essay/dev_fixtures.jsonl` | 5 ORIGINAL development essay prompts, 2 topics each, 10 topics across eras from medieval to 1989. They use two prompt layouts ("Temat N." and numbered "N." with "WYPRACOWANIE na temat nr"). |
| `agentsLog/Pewciu6/essay/premise_check.md` | Independent premise check (a separate Sonnet subagent, not the author) against the pinned `oldid` revisions: **10/10 supported**. The author re-verified all 14 cited oldids against `data/przemeknowak781/sources.jsonl`. |
| `agentsLog/Pewciu6/essay/lora_feasibility.md` | Stretch: an essay-only LoRA feasibility and export desk study. No training. |
| `agentsLog/Pewciu6/essay/2026-09-26-fix-dryrun.json` | Output of the sanctioned CPU check `build … --mode both --limit 2 --dry-run` (ids and hashes only). |
| `agentsLog/Pewciu6/essay/.gitignore` | Ignores `private/`, `*.output.jsonl`, `write.input.jsonl`, `run_manifest.json`. |

`pilot-v1/` was removed in the review fix: its commands wrote raw provider output to non-ignored paths. It never held model output (inputs, configs and manifest only; no `raw_response` anywhere).

## Routing and prompt contract

- **Detection uses question structure only, never ids.** An item is an essay when it contains an essay keyword (`wypracowani…`/`WYPRACOWANIE`) and also one of these: a word-count requirement (`minimum|co najmniej N słów|wyrazów`), at least two `Temat N.` headings, or at least two enumerated `N.` topics plus the word "temat". A passing mention of an essay without that structure is **not** routed, so the item keeps the bare fallback. On the May 2024 validation input, detection selects exactly one of 40 items: the essay, with 3 enumerated topics. I checked this locally with booleans and counts only; no text was published.
- **Original requirements are preserved.** The item body is copied verbatim, and a test checks that it appears as a substring. Only an **explicitly recognized** solver header is removed: a first paragraph that opens with `Rozwiąż … zadani…`, contains `Odpowiadaj` and a concision word, and has no essay keyword (the shape of the harness `PROMPT_HEADER`). Any other first paragraph, such as a source saying a chronicler wrote `krótko`, is kept verbatim (review P1). Its SHA-256 goes in the manifest.
- **Prompt rules** (`essay-route-v1`): the first line is `Temat nr N`, with no preamble. At least 300 words of body text, target 350–450. A `Teza:` sentence. Three labelled `Aspekt 1–3 – …:` sections, using the aspects the topic names; if it names two, the third covers their links or effects. At least two dated, named facts per aspect, each tied to the thesis. A `Zakończenie:` paragraph. Only facts the model is sure of.
- **Topic:** `--topic 1` is the default and is the same for every arm. `--select-topic` is the ablation, where the model picks the topic it knows best.
- **Plan/write:** the plan call (cap 512) produces at most 200 words of plan. Its text goes into the write call (cap 1536) on the same topic. If a plan is missing, errored or truncated, that write slot falls back to the single-pass prompt. There is no retry, and the fallback is logged in `write.record.json`.

## Pilot envelope and bounded launch

The input is `dev_fixtures.jsonl` `--limit 2` → `dev-essay-001` (named topics) and `dev-essay-002` (numbered layout), both on fixed topic 1.

| Stage | Calls | Cap | Requested tokens |
|---|---:|---:|---:|
| single | 2 | 1536 | 3072 |
| plan | 2 | 512 | 1024 |
| write | 2 | 1536 | 3072 |
| **total** | **6** | | **7168** |

0 retries, at most 30 minutes wall time, $0. The configs derive from `agentsLog/kwiscion/gemma4-12b-val40-1024.config.json` (`gemma4:12b-it-q4_K_M`, loopback Ollama, `reasoning_effort: none`, timeout 420 s); only `max_output_tokens` changes.

**Only after the lead's launch declaration**, on the assigned host, from the repo root (`<run_id>` must be new):

```sh
python scripts/Pewciu6/essay_route.py build --input agentsLog/Pewciu6/essay/dev_fixtures.jsonl --out-dir agentsLog/Pewciu6/essay/private/<run_id> --mode both --limit 2 --base-config agentsLog/kwiscion/gemma4-12b-val40-1024.config.json
# either run on matura-pawel itself, or open a tunnel first: ssh -N -L 11434:127.0.0.1:11434 matura-pawel
python scripts/Pewciu6/essay_pilot_run.py --manifest agentsLog/Pewciu6/essay/private/<run_id>/manifest.json --source agentsLog/Pewciu6/essay/dev_fixtures.jsonl --base-url http://127.0.0.1:11434 --api ollama --num-ctx 32768 --check
python scripts/Pewciu6/essay_pilot_run.py --manifest agentsLog/Pewciu6/essay/private/<run_id>/manifest.json --source agentsLog/Pewciu6/essay/dev_fixtures.jsonl --base-url http://127.0.0.1:11434 --api ollama --num-ctx 32768
python scripts/Pewciu6/essay_report.py --input agentsLog/Pewciu6/essay/private/<run_id>/single.output.jsonl --markdown
python scripts/Pewciu6/essay_report.py --input agentsLog/Pewciu6/essay/private/<run_id>/write.output.jsonl --markdown
```

Requests: `--api ollama` (default) posts to `<base-url>/api/chat` with `stream: false`, **`think: false`** and `options: {num_predict: <stage cap>, num_ctx: 32768, temperature}`. Without `think: false`, Gemma on Ollama 0.34.4 spent the budget on hidden thinking and returned empty answers with `done_reason=length` (host smoke on matura-pawel). `--temperature` is sent only when given; the base config declares none, so the pilot keeps the server default unless the launch record declares a value (then add `--temperature <value>`). `--api openai` posts to `/chat/completions` with the same `think`/`options` extras. The reply is wrapped into the chat-completions shape, and `done_reason=length` or empty text counts as an error. `run_manifest.json` records `request_options`.

Privacy (review launch gate a): `build` refuses any `--out-dir` that is not a git-ignored `private/` dir inside the repo, and refuses an existing dir. Raw provider output (`*.output.jsonl`) and the plan-bearing `write.input.jsonl` exist only there. The launcher writes answer-only handoffs `answers.single.jsonl` / `answers.write.jsonl` (`id, stage, answer, error_type`; no plan, no raw response). These and the report aggregates are the only publishable outputs, after a manual check.

Bounds (review launch gate b), all enforced in `essay_pilot_run.py`, not declared:
- one global deadline 30 min from start; each call gets `min(420, seconds left)`; no call starts with < 10 s left;
- each call runs in a worker thread; if it overruns its timeout (+5 s grace) it is abandoned and the run stops (`call_overran`);
- a ledger reserves each call's cap before sending; it stops at the first call that would exceed 6 calls or 7168 tokens (`call_limit` / `token_limit`), and refuses a manifest planning more;
- no retries: every id is sent at most once per stage; a failed or missing plan falls back to the single-pass prompt in its write slot, with reason `failed_plan:<type>` or `missing_plan`;
- deterministic order (single, plan, write; manifest item order) and a `run_manifest.json` on every exit (`complete` or `stopped` + `stop_reason`, calls, per-call timeouts and elapsed, `failed_calls`, `unsent` ids, fallbacks, handoff hashes);
- a `run.lock` (O_EXCL) and a freshness check stop a second run in the same dir.

`write-from-plan` (manual path) now rejects duplicate, unexpected or malformed plan records (missing `raw_response`/`error`, non-object error, `error: null` with no provider object or empty text, bad JSON) instead of letting the last row win (review P2). `essay_report.py` (`essay-report-v2`) treats any row with an error as not completed, even with 301 words of partial text: it counts in `empty_or_error` and `partial_with_error`, keeps `partial_diagnostics`, and never enters `min_words`/`max_words` or the structural counts (review P2).

Tests: `python -m unittest discover -s scripts/Pewciu6 -p 'test_essay*.py'`.

## Hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| prompt templates (`prompt_template_sha256`) | `a133eb51972d0a1becf1ba71a14eac4498ea03a7556e12c3cbc0a271bc84fd9c` |
| `dev_fixtures.jsonl` | `fa546faf595b00dd13d70ea700ed8f70ade12227261313b3f24bb09866bbbf71` |
| dry-run item body hashes | `dev-essay-001` `b401de8f…35cdc`, `dev-essay-002` `f23a1a0c…21953` (unchanged from pilot-v1) |

## Known-validation diagnostic (single item, not a score)

I ran `essay_report.py` on the four already-reviewed z26 essays: RTX, format, policy and RAG40. I read them locally and publish aggregates only.

| Arm | Words | Labelled aspects | Distinct years | Preamble | Solver-label leak | Reviewed points |
|---|---:|---:|---:|---|---|---:|
| RTX bare | 302 | 0 | 1 | no | **yes** (`Rozstrzygnięcie/Uzasadnienie`) | 8 |
| format | 337 | 0 | 1 | **yes** | no | 8 |
| policy | 369 | 0 | 3 | no | no | 6 |
| RAG40 | 301 | 0 | 3 | no | no | 2 |

Every arm sits just above the 300-word threshold, cites only 1–3 distinct years and labels no aspects. The bare header's decision/justification format leaks into the RTX essay. This supports the concision-conflict hypothesis, but one essay per arm cannot establish an effect.

## Limits and rights

- The fixtures were written by Claude Opus 5.5 (`provenance: synthetic`) for #80. **No** DEV 2023, VALIDATION 2024 or SEALED 2025 item, key, rubric or paraphrase was used in any prompt, fixture or test. A boolean key-term check found no overlap between the fixtures and the validation essay. I did not open SEALED 2025. The cited sources are CC BY-SA 4.0 pl.wikipedia revisions from Przemek's manifest, used for reference only, and no source text is copied. `rights_status: clear`. These are development prompts, not training data; the training-data review is separate (#97).
- The report's checks are heuristics (regex for labels, years and capitalized terms). They are not grades. Grading of this candidate goes to root or other independent graders, not only the author.
- CI: the shared workflow does not run `scripts/Pewciu6` tests. I ran them locally on Python 3.9, 3.11 and 3.12 (48/48 OK after the review fix) and did not edit the shared workflow.
