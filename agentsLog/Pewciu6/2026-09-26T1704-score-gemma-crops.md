# Gemma 4 12B source-crop diagnostic (3 items): adjudicated vs bare Gemma (issue #11)

**Provisional.** This is @Pewciu6's independent agent adjudication of the lead's GPT-6 Sol first pass (PR #63, head `dcf2bd000ac5`), on the same basis as PR #53/#58/#61. It is not the organizer's score. Model answers were not edited. No key, rubric, prompt or source text appears here.

## Headline

| 3 items (z1, z6, z25), 6 points | Sol first pass | **Adjudicated** | Range |
|---|---|---|---|
| Bare Gemma (#53, unchanged in #58) | — | **2** | 1–2 |
| Source crops (PR #63) | 3 (2–3) | **3** | 1–3 |
| **Δ crop − bare** | +1 | **+1** | 0 to +1 (paired) |

I agree with Sol on 3 of 3 items. The only difference is that I give z6 a wider range.

| Item | Max | Bare | Crop | Sol | Verdict | One-line reason |
|---|---|---|---|---|---|---|
| z1 | 1 | 0 | **1** (0–1) | 1 (0–1) | agree | the correct relief is now chosen, and both sources are linked through the double-crown act; the invented glyph detail and the misidentified other relief are peripheral |
| z6 | 2 | 2 (1–2) | **2** (1–2) | 2 (2–2) | agree, wider range | three captioned figure groups are matched to estates and a hierarchy is stated; the hierarchy is generic and the central figure is missing, which is the same 1–2 risk as bare |
| z25 | 3 | 0 | **0** | 0 | agree | the cartoon is still misread as a different era; the lettering, the figure and the context are all wrong |

## Does cropping help the image-misread slice?

- Bare Gemma lost **7** points to source/image misreads (#53). Four of them are in this sample: z1 (1) and z25 (3). The crop run recovered **1 of 4**.
- **The z1 gain is not attributable to cropping.** The question-policy arm (PR #61) also fixed z1, without crops. With unfixed sampling on a single draw, z1 looks like a coin-flip item.
- z25 is a whole-scene misread: the model does not recognize the caricature subject or the partly hidden lettering. Cropping did not change the misread or the era.
- **Verdict: not demonstrated.** At best cropping helps slightly on fine-detail items, and it does not help on whole-scene misreads. **n=3 selected items is not evidence of a general effect.** Extending this to all 7 misread points would need a declared all-image-item arm, ideally with more than one draw on z1-type items.

## Hashes and checks

- Answers: the LF git blob is `2c9742fb…`, and after LF→CRLF conversion it is `dd5dc674…`, which **matches the manifest** (Windows checkout; parsed records are identical). There are 3 records, 3 unique ids, all `stop`, 0 errors and 0 unsent.
- Input `59f0d90e…`, model digest `4eb23ef1…`, keys `f66e3877…` (same as #53).
- Grader evidence: page renders p. 4, 9 and 28. I did not see the crop images themselves, which are private on the lead's machine.
- The keyscan leakcheck and the answer-string scan both found 0 hits on this note and the JSON.

Machine-readable output (ids, points, ranges, verdicts and aggregates only): [`results/review_gemma-source-crops-diag3.json`](results/review_gemma-source-crops-diag3.json).

**Limitations:** there was one agent rater and no human examiner, and there is one stochastic draw per item. The items were selected, not random. There is no full score, composite, routing or promotion. Rights: CKE material is cited, not redistributed. Cost: CPU only, $0, and the scorer made no model calls.
