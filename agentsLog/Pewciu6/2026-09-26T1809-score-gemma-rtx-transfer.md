# Gemma 4 12B RTX 5090 runtime-transfer control: reviewed score vs bare Gemma (issue #11)

**Provisional.** This is @Pewciu6's independent agent review against the official CKE rules, on the same basis as the consolidated scores in PR #53. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here.

## Headline

| Gemma 4 12B Q4, thinking off, 1024 tokens | Input | Wall time | Automatic | **Reviewed** | Range |
|---|---|---|---|---|---|
| Bare, laptop (PR #52/#53, `39a5dbbb…`) | v1 (z13 on v2, #58) | about 37 min | 11.0 | **35** | 28–40 |
| RTX 5090 transfer (#33/#85, `179ccf38…`) | v2 `6615fea2…`, ctx 32768 | **2 min 26.6 s** | 8.0 | **34** | 25–39 |
| **Δ RTX − bare** | | about 15× faster | −3.0 | **−1** | |

- **Verdict: equivalent within sampling noise.** The reviewed total is 34 vs 35. Five items change points: two gains and three losses. They have no common cause.
- **Paired deltas:** on the 39 items with identical input, the scores are 33 vs 34 (Δ −1). **z13**, reported separately against the v2 correction grade from #58, is 1 vs 1 (Δ 0). Both answers name the correct event and cite the engraving's date. The RTX answer garbles the king's surname, so the grade stays low-confidence (0–1).
- **The text is not reproduced, but the substance mostly is.** 1/40 answers are byte-identical (z15.1) and 2/40 have text similarity ≥ 0.90; the median similarity is 0.23. Sampling used provider defaults with no seed, so this is expected. 23/40 answers have the same substance as bare and carry the #53 grade. 35/40 items get the same points.
- **The automatic −3 is mostly a parser artefact.** It comes from z10 (a real loss), z11.1 (bare's self-corrected answer happened to match; both arms are 0 after review) and z20.2 (a real 1-point loss).
- **Context 32768 vs 4096 does not matter here.** The largest prompt was 1,979 tokens, so no item came near either limit. The run had 0 errors, 0 empty answers and 0 length stops.
- Neither arm is near 48.

## Item deltas vs bare Gemma (consolidated 35)

| Item | Bare | RTX | Cause | One-line reason |
|---|---|---|---|---|
| z3.1 | 0 | 1 | format fixed | a single clean name; bare hedged it with an invented alternative |
| z17.2 | 0 | 1 | recall fixed | correct dynasty (bare wrong) |
| z10 | 1 | 0 | new error | wrong letter with no reasoning (bare correct) |
| z15.2 | 1 | 0 | source misread | wrong version chosen; the tone of the source is read backwards |
| z20.2 | 2 | 1 | recall | two of three judgments correct (bare got all three) |

Net −1. All three losses and both gains appear, in other items or other directions, across the earlier arms: the format arm (#58) also fixed z3.1 and z17.2 and lost z10 and z15.2. These items flip between draws. The pattern fits run-to-run variance on a small set of unstable items, not a systematic runtime effect.

**Fresh reviews at the same score (12 items), worth noting:**

- **z5.1 and z14.1:** the decision flips from wrong to correct, but in both the map is placed in the wrong event or era. The source-2 reference is therefore wrong, so each gets 0, with a range of 0–1. Image misreading persists, just in a different form. In the z14.2 record, the model re-answers 14.1 with the *opposite* decision. Each record is graded only for its own item.
- **z8.2:** the document attribution is now correct (hedged), so the point is firm (bare was 0–1).
- **z11.1:** a single wrong first assignment with no self-correction. It gets 0, as bare did (bare was 0 because of conflicting answers).
- **z12.2:** the correct term is given alongside a near-synonym alternative. It gets 1 (0–1) under the multiple-answer rule.
- **z17.1:** the same causal chain with both sources, but it places the proclamation in the wrong city. It gets 1 (0–1).
- **z25:** the cartoon is misread in a new way. The sweeping figure is seen, but the country, era and label are wrong, so it stays at 0/3.
- **z26:** the same topic, stance and three-aspect structure as bare. The political and cultural aspects are satisfactory; the socio-economic aspect is superficial and has 2–3 errors (A about 6). It is 303 raw words, or 297–299 without the topic line and the labels. B gets 2 as the point estimate, with a range of 0–3. Total **8 (5–10)**, the same band as bare. The minimal preamble is an improvement over bare's chatty opening.

## Where the points go

| Slice | Max | Bare | RTX |
|---|---|---|---|
| source_analysis | 14 | 8 | 7 |
| short_answer | 24 | 14 | 16 |
| multiple_choice | 7 | 5 | 3 |
| essay | 15 | 8 | 8 |
| mod:image | 34 | 19 | 19 |
| mod:text | 26 | 16 | 15 |

| Cause (points lost) | Bare | RTX |
|---|---|---|
| Factual recall | 9 | **11** |
| Source/image misread or omitted | 7 | **8** |
| Reasoning / shallow argument (mostly the essay) | 5 | 5 |
| Answer format (hedged/conflicting) | 4 | **2** |
| Truncation | 0 | 0 |
| **Total lost** | 25 | **26** |

Answer shape: the total is 2,756 words vs 3,167 for bare (median 70 vs 76 per item). Items with "lub" alternatives drop from 10 to 8. The only answer that loses points to conflicting decisions is z23.2, the same failure as in bare.

## Runtime-transfer verdict

- **Score:** equivalent (34 vs 35, Δ −1). That is inside the per-item uncertainty. For comparison, the format arm changed 10 items for a net of 0 (#58).
- **Noise or systematic:** noise. The laptop and RTX answers differ in wording on 39/40 items because of default sampling. The five point changes are split across recall, format and source reading. The image slice is unchanged (19 vs 19), and there is no truncation or context effect.
- **Speed:** 2 min 26.6 s for 40 items (mean 3.66 s, median 3.51 s, max 11.84 s), against about 37 min on the laptop. The RTX host reproduces the laptop baseline's quality about 15× faster. That makes repeat draws or self-consistency voting affordable, which could reduce the item-flip variance seen here. This is a suggestion, not a tested claim.

## Hashes and reproduction

- Answers `179ccf382d2b0b87b4899240f604e0f922c1b8856273f4bedaccd9841bef600b`: verified, matches the #11 handoff and the manifest (40 rows, all `stop`, `error` null). Input source-v2 `6615fea2…`, model digest `4eb23ef1…`, as recorded in `agentsLog/semberecki/2026-09-26-rtx-runtime-transfer-manifest.md`. Keys `f66e3877…` are the same as #53.
- Bare reference `39a5dbbb…` (#53); z13 reference `64aa625c…` (#58).

```bash
H=agentsLog/Pewciu6/harness; P=agentsLog/Pewciu6/private/validation_2024   # git-ignored
cp agentsLog/semberecki/model-answers/gemma4-12b-val40-v2-rtx-transfer.jsonl $P/rtx_answer_only.jsonl   # sha256 179ccf38…
python3 -c "import json;[print(json.dumps({'id':r['id'],'raw_response':r['answer'],'error':r['error'],'finish_reason':r['finish_reason']},ensure_ascii=False)) for r in map(json.loads,open('$P/rtx_answer_only.jsonl'))]" > $P/gemma_rtx_contract.jsonl
python3 $H/matura_harness.py score --outputs $P/gemma_rtx_contract.jsonl --keys $P/eval_keys.jsonl \
  --split VALIDATION --run-id gemma4-12b-val40-v2-rtx-transfer --scorecard $P/gemma_rtx_auto.json --items $P/gemma_rtx_auto_items.jsonl
# -> strict 0.1333 (8.0 / 60)
python3 $P/build_rtx.py   # private grades -> results JSON
```

Machine-readable output (ids, points, ranges, basis, text similarity, deltas and aggregates only): [`results/review_gemma4-12b-val40-v2-rtx-transfer.json`](results/review_gemma4-12b-val40-v2-rtx-transfer.json). Per-item private reasoning stays in git-ignored `private/`.

**Limitations:**
- One agent rater reviewed the 17 fresh items, with no second rater or human examiner. The 23 carried items inherit #53's two-rater adjudication.
- The ranges sum per-item uncertainty and ignore correlation.
- The essay's B criterion depends on the word count (about 300). B = 0 is the strictest reading.
- One draw per configuration. Without a seed, a −1 cannot separate the runtime from sampling.
- The laptop bare run used v1 input (39 items are identical to v2). This arm used v2 for all 40.

Rights: CKE material is cited, not redistributed. Cost: CPU only, $0; the scorer made no model calls.
