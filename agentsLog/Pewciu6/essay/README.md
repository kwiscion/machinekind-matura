# Essay route (issue #80): first CPU deliverable

Owner: @Pewciu6. Written 2026-09-26, about 19:20 Europe/Warsaw. **No model calls, training or inference were run.** The pilot below needs the lead to assign a host and publish a launch record first.

## Hypothesis

A dedicated long-form essay prompt removes the conflict between the global instructions and the essay task. It should raise both length and aspect coverage. The global header asks for concise answers ("zwięźle") and for `Rozstrzygnięcie/Uzasadnienie` labels. Planning first (plan/write) may also improve how well the facts support the claims, at a matched final cap. Choosing the topic is a separate ablation and is **off** by default.

## Files

| Path | Purpose |
|---|---|
| `scripts/Pewciu6/essay_route.py` | Stdlib router and prompt builder. `build` handles single-pass, plan or both. `write-from-plan` runs after the plan stage. `--dry-run` prints the envelope and writes nothing. |
| `scripts/Pewciu6/essay_report.py` | Deterministic post-hoc report with no model calls: word count (headings and labels excluded), `underlength` (<300), thesis, labelled aspects, conclusion, distinct years, a named-term proxy, `preamble` and `solver_format_leak`. |
| `scripts/Pewciu6/test_essay_route.py` | 24 unit tests on synthetic fixtures only. |
| `agentsLog/Pewciu6/essay/dev_fixtures.jsonl` | 5 ORIGINAL development essay prompts, 2 topics each, 10 topics across eras from medieval to 1989. They use two prompt layouts ("Temat N." and numbered "N." with "WYPRACOWANIE na temat nr"). |
| `agentsLog/Pewciu6/essay/premise_check.md` | Independent premise check (a separate Sonnet subagent, not the author) against the pinned `oldid` revisions: **10/10 supported**. The author re-verified all 14 cited oldids against `data/przemeknowak781/sources.jsonl`. |
| `agentsLog/Pewciu6/essay/lora_feasibility.md` | Stretch: an essay-only LoRA feasibility and export desk study. No training. |
| `agentsLog/Pewciu6/essay/pilot-v1/` | A frozen, portable pilot: inputs, per-stage configs and `manifest.json`. |

## Routing and prompt contract

- **Detection uses question structure only, never ids.** An item is an essay when it contains an essay keyword (`wypracowani…`/`WYPRACOWANIE`) and also one of these: a word-count requirement (`minimum|co najmniej N słów|wyrazów`), at least two `Temat N.` headings, or at least two enumerated `N.` topics plus the word "temat". A passing mention of an essay without that structure is **not** routed, so the item keeps the bare fallback. On the May 2024 validation input, detection selects exactly one of 40 items: the essay, with 3 enumerated topics. I checked this locally with booleans and counts only; no text was published.
- **Original requirements are preserved.** The item body is copied verbatim, and a test checks that it appears as a substring. Only a leading generic solver paragraph that asks for concision and has no essay keyword is removed. Its SHA-256 goes in the manifest.
- **Prompt rules** (`essay-route-v1`): the first line is `Temat nr N`, with no preamble. At least 300 words of body text, target 350–450. A `Teza:` sentence. Three labelled `Aspekt 1–3 – …:` sections, using the aspects the topic names; if it names two, the third covers their links or effects. At least two dated, named facts per aspect, each tied to the thesis. A `Zakończenie:` paragraph. Only facts the model is sure of.
- **Topic:** `--topic 1` is the default and is the same for every arm. `--select-topic` is the ablation, where the model picks the topic it knows best.
- **Plan/write:** the plan call (cap 512) produces at most 200 words of plan. Its text goes into the write call (cap 1536) on the same topic. If a plan is missing, errored or truncated, that write slot falls back to the single-pass prompt. There is no retry, and the fallback is logged in `write.record.json`.

## Pilot envelope (`pilot-v1`)

The input is `dev_fixtures.jsonl` `--limit 2` → `dev-essay-001` (named topics) and `dev-essay-002` (numbered layout), both on fixed topic 1.

| Stage | Calls | Cap | Requested tokens |
|---|---:|---:|---:|
| single | 2 | 1536 | 3072 |
| plan | 2 | 512 | 1024 |
| write | 2 | 1536 | 3072 |
| **total** | **6** | | **7168** |

Other limits: 0 retries, at most 30 minutes wall time, $0. The build refuses anything over 6 calls or 7168 tokens. The configs derive from `agentsLog/kwiscion/gemma4-12b-val40-1024.config.json` (sha256 `bc3c91d9…94e3`: `gemma4:12b-it-q4_K_M`, loopback Ollama, `reasoning_effort: none`, timeout 420 s). Only `max_output_tokens` changes. The sampling defaults are unchanged, so every arm is a single stochastic draw.

Commands, run from the repo root once a launch record exists (the same lines are in `manifest.json`):

```sh
python infer.py --config agentsLog/Pewciu6/essay/pilot-v1/config.final.json --input agentsLog/Pewciu6/essay/pilot-v1/single.input.jsonl --output agentsLog/Pewciu6/essay/pilot-v1/single.output.jsonl --max-calls 2
python infer.py --config agentsLog/Pewciu6/essay/pilot-v1/config.plan.json --input agentsLog/Pewciu6/essay/pilot-v1/plan.input.jsonl --output agentsLog/Pewciu6/essay/pilot-v1/plan.output.jsonl --max-calls 2
python scripts/Pewciu6/essay_route.py write-from-plan --manifest agentsLog/Pewciu6/essay/pilot-v1/manifest.json --source agentsLog/Pewciu6/essay/dev_fixtures.jsonl --plan-output agentsLog/Pewciu6/essay/pilot-v1/plan.output.jsonl
python infer.py --config agentsLog/Pewciu6/essay/pilot-v1/config.final.json --input agentsLog/Pewciu6/essay/pilot-v1/write.input.jsonl --output agentsLog/Pewciu6/essay/pilot-v1/write.output.jsonl --max-calls 2
python scripts/Pewciu6/essay_report.py --input agentsLog/Pewciu6/essay/pilot-v1/single.output.jsonl --markdown
python scripts/Pewciu6/essay_report.py --input agentsLog/Pewciu6/essay/pilot-v1/write.output.jsonl --markdown
```

To rebuild or preview: `python scripts/Pewciu6/essay_route.py build --input agentsLog/Pewciu6/essay/dev_fixtures.jsonl --out-dir <new dir> --mode both --limit 2 --base-config <config> [--dry-run]`. Tests: `python -m unittest scripts/Pewciu6/test_essay_route.py`.

## Hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| prompt templates (`prompt_template_sha256`) | `a133eb51972d0a1becf1ba71a14eac4498ea03a7556e12c3cbc0a271bc84fd9c` |
| `dev_fixtures.jsonl` | `fa546faf595b00dd13d70ea700ed8f70ade12227261313b3f24bb09866bbbf71` |
| `pilot-v1/single.input.jsonl` | `d0702b275f767bd8b8ee7ced2e5d58722797bd9af5649cad3f0f268c1ec9c13c` |
| `pilot-v1/plan.input.jsonl` | `d0c8f44bef39fabf95d2ecf425ed4e90ba39f7ce5f14e9a8464ef1ce90b1231c` |
| `pilot-v1/config.final.json` / `config.plan.json` | `afe8330a…d7b4` / `290d12fa…0282` |

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
- CI: the shared workflow does not run `scripts/Pewciu6` tests. I ran them locally on Python 3.9 and 3.11 (24/24 OK) and did not edit the shared workflow.
