# Gemma 4 12B question-policy arm: adjudicated score vs bare Gemma (issue #11)

**Provisional.** This is @Pewciu6's independent agent adjudication of the lead's two disjoint Sol first passes (PR #59), on the same basis as PR #53/#58. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here.

## Headline

| Gemma 4 12B Q4, thinking off, 1024 out / 4096 ctx | Automatic | Sol first pass | **Adjudicated** | Range |
|---|---|---|---|---|
| Bare, source-v2 composite (#53 + v2 z13, #58) | 11.0 | — | **35** | 28–40 |
| Question-policy, source-v2 (PR #59, `a625b2e7…`) | 7.0 | 30 (24–34) | **32** | 22–35 |
| **Δ policy − bare** | −4.0 | | **−3** | |

- **Verdict: neutral to slightly harmful.** The point estimate is −3, and the ranges overlap heavily. The policy is not a lever toward 48, so do not promote it. Bare Gemma 35 stays the working base.
- **Where it helps:** clean single answers on short and closed items. z3.1 is no longer hedged, z11.1 and z23.2 no longer carry conflicting decisions, and "lub" alternatives are nearly gone. It also improved recall on z1, z17.2 and z19.1.
- **Where it hurts:** the essay (−2; it switched to topic 3, and the diplomatic and political aspects are thin with anachronisms), one wrong-subtask answer (z14.2 re-answers 14.1 and gives no letter), a wrong letter (z10), a lost hierarchy statement (z6), and two image items where the justification rests on invented visual detail (z13, z18).
- Having the source-v2 image did **not** fix z13. The image was present, but the answer invents a head and a sword and misreads the date.

## Adjudication vs Sol (40 items)

I agree with Sol on 38 of 40 items and disagree on 2. Each disagreement moves the total up by 1.

| Item | Sol | Me | One-line reason |
|---|---|---|---|
| z9 | 0 | **1** (0–1) | uses the inscription's meaning and a crown/eagle element that is visible on the woodcut; mislabelling the group's confession is peripheral |
| z17.1 | 0 | **1** (0–1) | the Sedan → unification → proclamation causal chain and both sources are present; naming the wrong Napoleon in passing is peripheral |

Sol-flagged items where I agree on the point but record a different range: z2 (1, the peripheral date slip doesn't change it), z13 (0, range 0–1 because the event is right), z14.1 (0, range 0–1: the decision is now correct but the map is invented as a 1905 conflict), and z26 (6, range 4–7 vs Sol 5–8). I also agree on z3.1 (1), z6 (1), z14.2 (0), z18 (0), z19.1 (1), z19.2 (0), z20.2 (2, range 0–2 for shifted labels), z23.2 (0), z24 (0) and z25 (0). Per-item agree/disagree lines are in the JSON (`sol_adjudication`).

## Paired item deltas vs bare 35

| Item | Bare | Policy | Cause | Reason |
|---|---|---|---|---|
| z1 | 0 | 1 | recall/image fixed | correct relief chosen, crown symbolism tied to the text |
| z3.1 | 0 | 1 | format fixed | correct name, no competing alternative |
| z17.2 | 0 | 1 | recall fixed | correct dynasty |
| z19.1 | 0 | 1 | recall | two of three judgments correct |
| z6 | 2 | 1 | reasoning | three figures, but no hierarchy or religious order stated |
| z10 | 1 | 0 | recall | wrong letter |
| z13 | 1 | 0 | source/image | invented head and sword, date misread (bare v2 composite 1) |
| z14.2 | 1 | 0 | format | re-answers 14.1 with the opposite decision, no letter |
| z18 | 1 | 0 | source/image | justification rests on an invented portrait, and the beast's headgear is not used |
| z26 | 8 | 6 | reasoning + errors | switched topic 1 → 3; two thin aspects; 3+ factual errors or anachronisms |

Four gains (+4) and six losses (−7), for a net of −3. The other 30 items keep their points: 20 are **carried** (same substance as bare, so the #53 grade is reused) and 10 were reviewed **fresh** at the same score. Three of those are worth noting. On z11.1 and z23.2 the conflicting answers are gone, but both are still wrong. On z14.1 the decision is now correct, but the map is invented.

## Where the points go

| Slice | Max | Bare | Policy |
|---|---|---|---|
| source_analysis | 14 | 8 | 8 |
| short_answer | 24 | 14 | 14 |
| multiple_choice | 7 | 5 | 4 |
| essay | 15 | 8 | 6 |
| mod:image | 33 | 18 | 17 |
| mod:text | 27 | 17 | 15 |

(Modality labels come from the key file, where z13 is labelled text, so the image slice max here is 33; #58 counted z13 as image, giving 34.)

| Cause (points lost) | Bare | Policy |
|---|---|---|
| Source/image misread or invented detail | 7 | **9** |
| Factual recall | 9 | **10** |
| Reasoning / shallow argument (incl. essay) | 5 | **8** |
| Answer format (hedged/conflicting, wrong subtask, essay preamble) | 4 | **1** |
| **Total lost** | 25 | 28 |

**Reading:** the question policy did what the format prefix did, but more cleanly. Format loss fell from 4 to 1, and the only wrong-subtask answer I saw was z14.2. The losses on the essay and image fidelity outweigh that gain. The remaining gap to 48 is recall (10) and image reading (9), and a prompt policy fixes neither.

## Hashes and reproduction

- Policy answers `a625b2e70834867d2d726c0181e89ccf0f694fecf0e454ab70dcc930c93c8739`: verified, matches the manifest (40 records, 40 unique ids, all `stop`, 0 errors).
- Frozen policy input `3257dd89…`, source-v2 `6615fea2…`, model digest `4eb23ef1…` as recorded in the PR #59 manifest; keys `f66e3877…` are the same as #53.

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # git-ignored
git fetch origin pull/59/head:pr59
git show pr59:agentsLog/kwiscion/model-answers/question-policy-gemma-val40-answer-only.jsonl > $P/policy_answer_only.jsonl   # sha256 a625b2e7…
python3 -c "import json;[print(json.dumps({'id':r['id'],'raw_response':r['answer'],'error':r['error'],'finish_reason':r['finish_reason']},ensure_ascii=False)) for r in map(json.loads,open('$P/policy_answer_only.jsonl'))]" > $P/gemma_policy_contract.jsonl
python3 $H/matura_harness.py score --outputs $P/gemma_policy_contract.jsonl --keys $P/eval_keys.jsonl \
  --split VALIDATION --run-id gemma4-12b-val40-policy --scorecard $P/gemma_policy_auto.json --items $P/gemma_policy_auto_items.jsonl
# -> 7.0 (6 correct, 1 partial, 8 incorrect, 25 needs_review)
```

Machine-readable output (aggregates, item ids, points, ranges, carried/fresh basis, Sol verdicts, deltas): [`results/review_gemma-question-policy-val40.json`](results/review_gemma-question-policy-val40.json). Per-item private reasoning is kept only in git-ignored `private/`.

**Limitations:** one agent rater for the 20 fresh items, with no second rater or human examiner. The carried items inherit #53's two-rater adjudication. The essay band is the least certain (4–7). The Sol first passes were disjoint halves, so each item has exactly one Sol rating. The range 22–35 sums per-item uncertainty and does not account for correlation between items. Sampling used provider defaults with no seed, so a −3 difference on one run is within run-to-run noise. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0; no model calls by the scorer.
