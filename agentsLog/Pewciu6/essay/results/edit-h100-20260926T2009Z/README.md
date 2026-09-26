# Constrained claim-edit wave (issue #80, lead authorization 5849201046)

DEVELOPMENT-split fixtures. Not a promotion result, not an exam score. All figures below are
independently graded (two fresh Opus graders, blind, calibration protocol below); this file
reports what was run and what those graders found — it does not adjudicate correctness itself.

## What ran

Six DEV fixtures (`dev-essay-001,003,004,005,009,010`), preselected topic 1. Per topic, exactly
three calls: **T-draft** (think:true, 20480 tokens), **N-draft** (think:false, 4096 tokens,
alternating draft-arm order per topic), then one **verify** call on the T-draft only (think:true,
20480 tokens) that proposes a small set of exact-span edits with evidence, never a rewrite.

- **Host**: `matura-pawel` via SSH tunnel, Ollama 0.34.4, `gemma4:12b-it-q4_K_M`
  (digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`), context 32768,
  temperature omitted.
- **Envelope enforced**: 18 calls / 270,336 requested tokens / 1 mechanism family / 0 retries /
  0 smokes, sequential. Wave start `2026-09-26T20:09:13Z`, absolute deadline
  `2026-09-26T21:09:00Z`. **Actual**: 18/18 calls completed, 270,336/270,336 tokens reserved,
  finished well inside the deadline, `stop_reason: null`.
- **Deviation from the declaration**: the separately-labelled known-VALIDATION essay diagnostic
  (thinking draft only) was **not executed**. No frozen VALIDATION-split essay item (task text)
  was found in any locally reachable `agentsLog/*/private/validation_2024/` artifact across every
  worktree — the shared `runner_input.jsonl`/`eval_keys.jsonl` files stop at `val2024-hist-z26`
  (the short-answer/source-analysis items only); the essay task itself was never transcribed.
  Building one now would have meant fresh exam-page transcription outside this run's frozen
  manifest, so it was deferred rather than attempted. The ledger reserved the 19th call / 20,480
  tokens as a `declared_ceiling`, separate from the enforced 18-call envelope, so nothing could
  spend that budget by accident.
- **Pre-execution gates**: a focused independent code review (fresh Opus subagent, 3 rounds — see
  below) of `essay_edit_run.py`/`essay_think_export.py` before the first call; frozen
  manifest + hashes + absolute deadline posted to #80 before executing
  ([comment 5849486726](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5849486726)).

## Mechanism (edit verifier)

The verify call returns `{"edits": [{"original", "replacement", "reason"}], "notes"}` — never a
full essay. Applied deterministically, CPU-only, with every one of the following checked before an
edit is accepted:

- `original` must occur in the T-draft's cleaned text **exactly once** (overlap-safe count) —
  invented or ambiguous (multiple-occurrence) spans are rejected outright.
- No two accepted edits may overlap.
- A single span is capped at 500 characters / 30% of the draft; a replacement may expand a span by
  at most 1.5x + 80 characters, and may not contain a newline, `{`, `` ``` ``, or `#` (blocks a
  disguised paragraph-level rewrite or format leakage).
- The **whole edit set** for an item is rejected (falls back to zero edits) if more than 8 edits
  would be accepted, or if the accepted spans together exceed 25% of the draft, or if their net
  character growth exceeds 15% of the draft — this stops many individually-small edits from adding
  up to a disguised rewrite.
- After applying the surviving edits, the patched text is re-run through the identical contract
  gate the T-draft itself had to pass (`essay_contract.check_body`), requiring the cleaned output
  to equal the patched text exactly (no fresh wrapper/heading/prose artifact) and to still meet the
  minimum word count and single-topic requirement.
- **On any failure** — verify call error/truncation, invalid JSON, or a failed revalidation — the
  final answer is the already-validated **T-draft, unchanged, labelled FALLBACK**. No retries.

## Independent code review (before the first call)

Two rounds against a fresh Opus subagent with no prior context, each ending PASS:
1. **Round 1** found a hard bug: `cmd_init` omitted `"families": []` from the ledger, which would
   have raised `KeyError` on the very first reservation (before any tokens were spent) — fixed.
   Also flagged three real risks, all fixed before executing: no cumulative edit-size budget, an
   over-loose replacement-expansion limit (4x+200 → tightened to 1.5x+80), and no "still valid
   prose after patch" gate (added the `check_body` re-run above).
2. **Round 2** (after the lead separately flagged a grading-aggregator bug, see below) reviewed
   both the edit-wave fixes and the aggregator fix together; found one further bug in the
   aggregator (see below); confirmed fixed in round 3.

Separately, the lead flagged
([comment 5849237309](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5849237309))
that `essay_think_export.cmd_aggregate` silently overwrote a second grader's row for the same
anonymized essay code (`grades[row["code"]]=row`), which would have broken the two-rater review
this wave needed. Fixed: rater id comes only from the grade file's name, ratings are kept per
`(rater_id, code)`, missing/duplicate ratings hard-error, and disagreement (>2 total points, or a
1-vs-3 aspect split, per the calibration protocol) is flagged `needs_adjudication` and never
auto-resolved by picking a score — a within-tolerance gap resolves to the mean of the two raters,
never either rater's own number. Review also caught that "within tolerance" originally required
*exact* equality (so a 1-point gap fell through to an unresolvable `total: null`); fixed to resolve
to the mean whenever `needs_adjudication` is false. A separate `adjudicate` subcommand writes
`aggregate_adjudicated.json`, leaving the original untouched, and refuses to touch any cell that
wasn't actually flagged. 160 unit tests pass across the touched files (0 failures).

## Grading

Two independent fresh Opus graders scored the anonymized 18-slot packet (6 items x
{N-draft, T-draft, T-patched}), blind to arm/model/family, using the published calibration
protocol
([`agentsLog/kwiscion/2026-09-26-essay-grading-calibration.md`](https://github.com/kwiscion/machinekind-matura/blob/main/agentsLog/kwiscion/2026-09-26-essay-grading-calibration.md),
published on main before grading started): per-aspect (3 aspects) 0/1/3/4 with quoted supporting
passage and listed factual claims; a separately-sourced factual-error deduction applied once;
coherence graded 0-3 separately; /15 per topic, 90 per family across 6 topics. **Protocol version
used: the published file, in full** (not the earlier ad-hoc rubric).

**Zero cells needed adjudication** — both graders agreed (identically or within the protocol's
tolerance) on every one of the 18 codes; no 1-vs-3 aspect split occurred anywhere. Both raters'
individual scores are kept in `grades_graderA.json`/`grades_graderB.json`; `aggregate.json` has the
per-cell detail.

| family | sum / 90 | mean / 15 | n graded | needs adjudication |
|---|---|---|---|---|
| N-draft | 46 | 7.67 | 6/6 | 0 |
| T-draft | 57.5 | 9.58 | 6/6 | 0 |
| T-patched | 57.5 | 9.58 | 6/6 | 0 |

Edits/fallbacks (counted separately, per the authorization):
- 6/6 T-drafts and N-drafts passed their own contract check (no failures).
- 5/6 items **patched** (verify call succeeded, JSON parsed, edits — 0 or more — applied and
  revalidated): `dev-essay-001` (2 edits proposed, 2 accepted, 0 rejected — both grounded in the
  retrieved evidence: a mis-attributed event and a mis-attributed treasury revenue source), plus
  `dev-essay-003,004,009,010` (0 edits proposed by the model; verify succeeded finding nothing to
  fix, so T-patched is byte-identical to T-draft for these four).
- 1/6 (`dev-essay-005`) **fallback**: the verify call spent its entire 20,480-token budget on
  thinking (60,010 thinking characters) and returned empty content at `done_reason: length` — a
  genuine truncation, correctly falling back to the unchanged, already-validated T-draft.
- 0/6 **failed** (no T-draft was itself invalid).

`dev-essay-001`'s two accepted edits did not change its graded total (11/15 unchanged): the edits
corrected two facts the retrieved evidence covered (which event Casimir's 1335 actions concerned,
and which crown revenue source was meant), but both graders still deducted one point for a
residual, unrelated error the evidence didn't cover (the 1335 date itself, versus 1333). This is a
useful, honest result: grounded verification fixed what it was shown, not everything a grader
would want, which is exactly the "no full rewrite, only unambiguous grounded spans" design intent
— and a caution against treating T-patched vs T-draft parity here as "the edit did nothing."

T-draft/T-patched clearly outscore N-draft (9.58 vs 7.67 mean/15), consistent with the prior
K-think wave (PR #129).

## Rights, provenance, limitations

- All essay text, tasks and evidence excerpts are from the existing DEV fixture set and the
  already contamination-checked (#13) #6 BM25 corpus (109 pl.wikipedia/wikisource CC BY-SA /
  public-domain sources); no VALIDATION/SEALED_TEST material was used as model-facing input.
  `index_sha256 350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`.
  `retrieval.py sha256 5ce9918fcc0151c8e15391781ace98deaf4b786977a69e6e773ccc9d7b0a51a3`.
- Grader provenance: `provider=anthropic`, `model=claude-opus`, two independent sessions, no
  shared context, blind to which family/item produced each code.
- This is a 6-item DEVELOPMENT sample; no exam-wide or promotion conclusion follows from it.
  Grading rests on the graders' own historical knowledge (no external sources were given to them),
  so factual corrections in `grades_graderA.json`/`grades_graderB.json` are graders' judgments, not
  an official answer key.
- Cost: host billed at the previously-declared 3.28 USD/h unverified planning-proxy rate; the wave
  ran well under an hour end to end (execution + export + grading), actual elapsed time recorded
  in `ledger.json`/`manifest.json`.

## Reproduction

```sh
python scripts/Pewciu6/essay_edit_run.py freeze --run-dir agentsLog/Pewciu6/essay/private/edit-X \
  --retriever agentsLog/Bukareszt/scripts/retrieval.py --index agentsLog/Bukareszt/index/bm25_index.json
python scripts/Pewciu6/essay_edit_run.py init --run-dir agentsLog/Pewciu6/essay/private/edit-X \
  --deadline-utc <ISO> --declared-start-utc <ISO>
python scripts/Pewciu6/essay_edit_run.py run --run-dir agentsLog/Pewciu6/essay/private/edit-X --batch t1
python scripts/Pewciu6/essay_edit_export.py export --run-dir agentsLog/Pewciu6/essay/private/edit-X --batch t1 \
  --out agentsLog/Pewciu6/essay/results/edit-X
python scripts/Pewciu6/essay_edit_export.py packet --run-dir agentsLog/Pewciu6/essay/private/edit-X --batch t1 \
  --out agentsLog/Pewciu6/essay/private/edit-X/grading/g1
# grade grading/g1/packet.jsonl -> grades_<rater>.json x2
python scripts/Pewciu6/essay_edit_export.py aggregate --grading agentsLog/Pewciu6/essay/private/edit-X/grading/g1
```

Files here: `bundle.json` (frozen items/topics/evidence), `ledger.json`/`manifest.json` (the call
ledger and batch record), `answers.jsonl` (every N-draft/T-draft/T-patched answer, public),
`packet.jsonl` (the anonymized grading packet), `grades_graderA.json`/`grades_graderB.json` (each
grader's own scores), `aggregate.json`/`grading_key.json` (the scored, de-anonymized table).
Raw model text (with `message.thinking` character counts only, never the thinking text itself) and
prompts stay private under `agentsLog/Pewciu6/essay/private/edit-h100-20260926T2009Z/`.
