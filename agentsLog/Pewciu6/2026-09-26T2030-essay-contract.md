# #80 priority 1: essay output contract (family K "contract-first"), 2026-09-26 20:30 Warsaw

Lead instruction: https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848599114.
Launch record: https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848691583.
Label: **DEVELOPMENT** (original DEV fixtures only). This is not a VALIDATION score or promotion evidence.

## What was built (CPU, stdlib, tests)

| file | role |
|---|---|
| `scripts/Pewciu6/essay_contract.py` | Task parser (global requirements; per-topic text, aspects, required sources; trailer removed). Selection: a strict one-line parse or a deterministic policy. Writer task (selected topic only). JSON `{topic_id, body}` parser. Deterministic wrapper cleanup, body-only word counter, validators, precise repair prompts, `render_answer`. |
| `scripts/Pewciu6/essay_contract_run.py` | Bounded loop: select → draft → contract check after every call → ≤2 conditional repairs → optional grounded C3 critic+rewrite (needs ≥2 calls of headroom) → final = last contract-passing version. Reuses the `essay_wave_run.Wave` ledger (reloaded before every call, absolute deadline, watchdog, 0 retries, run.lock). `offline` checks legacy outputs with no calls. |
| `scripts/Pewciu6/contract_synthetic.py` | 14 independent **malformed synthetic** outputs plus expected verdicts (provenance: synthetic, written by hand, no model). |
| `scripts/Pewciu6/test_essay_contract.py` | 21 tests: `cd scripts/Pewciu6 && python3 -m unittest test_essay_contract -v` |

The 5 lead points, and how each is met:
1. **One frozen topic.** A model one-liner `Temat: N` is parsed strictly. Two numbers, a non-permitted number or free text give `None`, which falls back to the declared `most-aspects` policy (recorded, never a silent pick). The writer prompt contains only `TEMAT nr N` plus the global requirements, the aspects and the required sources; a test checks that the other topics' text is absent. The full original task goes to `task_audit.jsonl` with its sha256.
2. **Internal `{topic_id, body}`, clean render.** Strict JSON. Only unambiguous wrappers are peeled: a code fence, a ≤40-word text wrapper around exactly one JSON object, a courtesy/preamble line, a topic header, a plan block, standalone headings, trailing word-count notes and grader comments/offers. Cleanup removes whole lines or paragraphs only and never edits a sentence (a test proves `clean words + removed words = body words` and that every paragraph is verbatim). Ambiguous output → regenerate: another topic marked, two JSON objects, an essay outside the JSON, a labelled closing paragraph that contains a year, >25% removed, or a removed span with ≥2 years and ≥30 words. `answers.json` gets only `Temat nr N\n\n<prose>`.
3. **Word counter and validators.** Body-only count (headings, metadata and wrappers excluded; a dash is not a word). Hard checks: single topic, the task minimum (300), every required aspect named in the *development* paragraphs (not only the intro or conclusion), and a source reference when a source is required. Soft trigger: <400 (target 400–500). Length is a gate only and never a quality score. The repair text demands concrete facts, "nigdy powtórzeniami ani ogólnikami".
4. **Bounded repair.** At most 2 conditional revision calls per item, each driven by the recorded trigger list and rechecked. The mechanical contract check is separate from the factual critic (C3's grounded critic prompts are reused unchanged). The initial, every failed and the final version are kept with their triggers. Per-item caps are declared before calls: select 128, draft 2048, critic 1024, rewrite 2048, repair 2×2048 (worst case 6 calls/9,344 tokens). The run ledger is the hard stop.
5. **Tests.** The synthetic cases cover all 3 topics answered, an appended extra essay, a preamble (inside and outside the JSON), underlength, legitimate prose starting with "Oto …" (kept), a labelled conclusion with a year (not deleted → regenerate), invalid JSON, plain text, two JSON objects, a wrong topic_id, a missing aspect, grader comments and a plan. The exhausted budget is tested both in the loop (`unsent: budget_exhausted`, no answer) and in the real `Wave` ledger (`StopWave call_limit` at max_calls). All 12 original DEV fixtures parse (≥8 required).

## Live probe (remaining wave allowance only)

Verified remaining allowance: wave `wave-h100-20260926T172925Z` had used 116/120 calls and 165,760/240,000 tokens, leaving **4 calls and 74,240 tokens**, deadline 19:05:20Z. It moved to a new ledger (`contract-h100-20260926T1822Z`: max 4 calls, 74,240 tokens, 1 family, same absolute deadline). The old wave dir carries `allowance_transfer.json`.

Host: `matura-pawel` H100, Ollama 0.34.4, `gemma4:12b-it-q4_K_M`, `think:false`, `num_ctx` 32768, temperature not sent. Item: `dev-essay-009` with `--select model --critic`.

| stage | eval tokens | s | contract | triggers | cleanup ops |
|---|---:|---:|---|---|---|
| select | 6 | 4.8 | `Temat: 1` parsed ok | – | – |
| draft | 827 | 8.4 | **pass** (356 body words) | `below_target:356<400` (soft) | none (valid JSON, no wrappers) |
| repair1 | 978 | 10.7 | **pass** (423 words) | – | `code_fence` peeled |
| critic/rewrite | – | – | unsent: `budget_below_2_calls` | | |

Ledger: **3/4 calls, 4,224/74,240 requested tokens used**. **1 call and 70,016 tokens were left unused** (nothing useful fits in 1 call) and are not carried forward. The final answer is `Temat nr 1` plus 423 words of prose (`results/contract-h100-20260926T1822Z/answers.jsonl`). The contract held: one topic, no wrapper, no headings, all 3 aspects in the development. Content is a separate matter (see the grader section): the contract does not fix facts. The repaired essay contains the garbled token "Czechy ięści" and dubious claims ("dominacja w basenie Morza Bałtyckiego", "odzyskanie wpływów na Pomorzu" right after Grunwald). That is exactly the gap the grounded critic stage targets.

## Offline: the same contract on the 56 real wave outputs (original vs cleaned, no calls)

The legacy prompt asked for `Temat nr N` and `Aspekt k – …:` headings, so every output had a topic header and headings removed. "Original" word counts include those headings; "clean" is body-only.

| family | n | hard pass | underlength <300 | missing aspect | below 400 | median words original→clean |
|---|---:|---:|---:|---:|---:|---|
| A single | 12 | 12 | 0 | 0 | 10 | 385.5→375.5 |
| B facts-first | 8 | 6 | 1 | 1 | 2 | 414.5→404.5 |
| B3 facts grounded | 8 | 5 | 0 | 3 | 4 | 406.0→396.0 |
| C critic | 8 | 8 | 0 | 0 | 3 | 425.0→412.5 |
| C3 critic grounded | 12 | 11 | 0 | 1 | 2 | 432.0→419.5 |
| D select | 8 | 7 | 0 | 1 | 6 | 389.0→376.0 |

49/56 pass the hard contract after cleanup. Caveat on the 6 missing-aspect flags: the check is lexical (a 5-letter stem must appear in a development paragraph). Some legacy outputs named the aspect only in the removed `Aspekt k – …:` heading, so a flag means "the prose never names it", not proof that the argument is absent. Per-row data is in `results/contract-h100-20260926T1822Z/offline_wave_contract.jsonl`.

## Independent fidelity grader (fresh blind Opus subagent)

A fresh Opus subagent (not the builder) got 17 shuffled (original, cleaned) pairs with no labels. It saw 2 probe versions, 7 synthetic cases and 8 randomly sampled real wave outputs (seed 80), and the length-repair delta from the probe. Files: `results/contract-h100-20260926T1822Z/fidelity_{pairs,grades,key}.json`.

- **Cleanup: 17/17 faithful. 0 pairs invented text, 0 deleted essay prose, 0 lost essential content.** Only wrappers were removed: preambles, topic headers, standalone `Aspekt k – …:`/`Zakończenie:` lines, a plan, a word-count note, an examiner note, "Mam nadzieję…", JSON syntax. No removed heading was the only place an aspect was named. The legitimate "Oto jeden z najważniejszych okresów…" opening was correctly kept.
- **The length-only repair did not help (probe, n=1).** The 356→423-word repair added no correct, specific fact. It added one new error (regaining "wpływy na Pomorzu" under Jagiełło; Pomerania returned only in 1466) and a garbled token ("Czechy ięści"). It fixed none of the draft's errors, which remain: "Baltic dominance" after Grunwald; Krewo making *Poland* enter Latin Christendom; "vast eastern territories" gained via what was only a personal union; "borders stable for decades" despite the wars of 1414, 1422 and 1431–35. The grader rates it as filler, slightly worse on facts than the draft.
- **Consequence, already applied in code:** a below-400 soft trigger alone no longer spends a repair call (`--soft-repair` is now opt-in; probe k1 ran with it on). Repair calls are for hard contract failures. Added length must come from the grounded critic/rewrite stage, which brings excerpts.

## Limits

- One live item. Contract behaviour on a real 3-topic sheet is shown only on synthetic and parsed tasks (z26 parses into 3 topics and 3×3 aspects). No new VALIDATION call was made.
- Validators are mechanical proxies: an aspect stem appearing ≠ the aspect argued; the source check is lexical.
- The below-400 soft trigger spends repair calls on outputs that already pass. The full plan keeps it, because the lead asked for a 400–500 target; the repair prompt requires concrete facts, not filler.
- The organizer 2023/24/25 answers and the user's Bielik example were not used (development-only, never training or retrieval).

## Next bounded plan (proposed on #80; needs the lead's declaration, not started)

- 1 family (K), host `matura-pawel`, same model/settings. Items: the **12 original DEV fixtures** `dev-essay-001..012`, with `--select model --critic`; soft repair off. Grounded C3 critic uses the #6 BM25 index sha256 `350800b1…`.
- Caps per item: select 128, draft 2048, critic 1024, rewrite 2048, ≤2 hard-failure repairs ×2048. Worst case **72 calls / 112,128 requested tokens**; expected ≈48 calls. **45-minute enforced wall deadline** (expected ≈10 min at the observed 5–11 s/call), 0 retries.
- Read-outs, no extra calls: contract pass rate for initial vs final. K-pre (the last contract-passing version before the critic) vs K-final vs the existing wave C3 answers, in one blind Opus packet (DEVELOPMENT grading), plus the same cleanup-fidelity grader on every cleaned output.
