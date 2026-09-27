# Per-topic drafts plus same-model selection — issue168

CPU implementation only; **no generation authorized or performed**. The executable sequential wrapper is documented in [WAVE.md](WAVE.md). Preparation never starts a server; future explicitly declared execution delegates both stages to the unchanged qualified recovery CLI. No shared runner was edited and no answer is chosen using grades.

## Mechanism and bound

Stage1 derives one immutable organizer package: unchanged direct-control question, then one complete-essay request per offered topic. The only draft-specific instruction is numerical topic forcing; it adds no historical facts. Original instructions, complete question, source text and image bytes remain. Stage2 derives a fresh package containing the complete original task and all stage1 terminal answers (including the direct control) as explicitly fallible candidate views. The same Gemma writes one final essay. Output schema contains exactly the original item ID and one answer, not a posthoc best candidate.

Topic parsing accepts conservative line-start forms `Temat 1. ...`, or `1. ...` (also closing-parenthesis delimiters), with exactly2 or3 consecutive unique numbers. Mixed styles, gaps, duplicate headings/text and extra topics fail preparation. Ambiguous source packages retain the baseline path rather than guessing. This grammar is intentionally narrower than every conceivable organizer format.

For3 topics: **3 drafts +1 direct control +1 selector =5 primary slots;20 maximum attempts;737,280 requested output tokens** under the unchanged four-attempt32768/49152/32768/32768 recovery envelope. Two topics give4 slots/16 attempts/589,824 tokens. Proposed whole-wave bound: **60minutes and$3.28**, one common absolute deadline, not60minutes per stage. Actual cost is not estimated from token ceilings.

Full candidate answers are preserved byte-for-byte in private evidence. Each selector view is capped at6,000 characters, with explicit excerpt flag, original length/word count, and a warning that an answer-only artifact does not certify generation completeness. Full original sources/images are never clipped. The builder refuses selector question text above40,000 UTF-8 bytes rather than removing source material. That is a finite payload guard, **not proof of tokenizer/context fit**. The actual scheduler retains its context admission/escalation checks, `truncate:false`, `shift:false`, and runtime context verification. If preparation, context admission, time or selector execution fails, export the preserved direct control and record an operational fallback; never substitute a grader-selected draft. A retained terminal control may itself be partial/placeholder: its existing runtime status must remain attached and never be relabelled successful.

## CPU CLI

All source packages, answers and generated manifests belong under ignored `agentsLog/kwiscion/private/`; the builder is generic and does not embed validation IDs.

```sh
python -B branching.py drafts --exam-dir PRIVATE_ORIGINAL --item-id RECEIVED_ESSAY_ID --output PRIVATE_STAGE1_SOURCE
python -B branching.py selector --stage1 PRIVATE_STAGE1_SOURCE --answers STAGE1_RESULTS/answers.json --answer-sha256 EXACT_TERMINAL_SHA --output PRIVATE_STAGE2_SOURCE
python -B branching.py export --stage1 PRIVATE_STAGE1_SOURCE --selector PRIVATE_STAGE2_SOURCE --answers STAGE2_RESULTS/answers.json --answer-sha256 EXACT_TERMINAL_SHA --output PRIVATE_SELECTED_JSON
python -B branching.py fallback --stage1 PRIVATE_STAGE1_SOURCE --answers STAGE1_RESULTS/answers.json --answer-sha256 EXACT_TERMINAL_SHA --reason budget_exhausted --output PRIVATE_FALLBACK_JSON
```

The export is a one-item diagnostic answer artifact, not a replacement full-exam submission. Original evidence and the executed diagnostics stay separate and immutable.

## Executable runtime reuse

`staged_wave.py` now snapshots the existing qualified adapter/preparation/runtime closure, prepares stage1, and builds stage2 only from exact terminal candidate artifacts. [WAVE.md](WAVE.md) contains the concrete prepare/check/declare/execute recipe and failure handling. One outer shared host lock and absolute guardian enclose both stages; existing inner stage locks, retries, contexts and cleanup are retained. CPU fake-operator tests pass, while actual runtime qualification remains unperformed.

The wrapper preserves a900-second selector window including the existing600-second recovery reserve, uses one common deadline, and fails back to the exact direct control if selection is unavailable or incomplete. Candidate partial/placeholder flags remain attached. Fresh diagnostic cache views are never an eligible combined final package: the final submission must contain only one pinned Gemma model/projector pair.

## Prospective evaluation

One masked pass grades direct control, each forced-topic draft, and the actual selector final under the applicable topic rubric. Keep selected-topic identity, argument development, verified factual errors, coherence and task compliance. Report selector-versus-control, the retrospectively best candidate (oracle diagnostic only), and selector regret separately. Never promote the oracle answer or infer selector success from candidate quality alone. Compare incomparable topic/aspect totals qualitatively rather than manufacturing a shared denominator. Original sources remain private; publish only rights-safe own outputs/grades.

CPU verification: `python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/essay-branching-prep -p test_branching.py -v`. Eight tests cover2/3-topic forms, ambiguity/extra-topic refusal, duplicate IDs, full text/image preservation, exact budget arithmetic, raw candidate retention/excerpt labeling, source/hash drift, single-final schema, operational baseline fallback and shared deadline. No real inference or historical-answer generation is part of these tests.
