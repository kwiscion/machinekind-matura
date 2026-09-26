# Independent review: Greg W2 S10

**Keep bare as the comparator. No W2 mechanism shows a secure improvement.** Fresh manual first-pass grading gives bare **7/13 [4,7]**, retrieve/verify **5/13 [4,8]**, relation-query **6/13 [5,6]**, and fact cards **4/13 [3,7]**. These are the same ten development items in each arm, worth 13 points. They are not whole-exam scores or estimates out of 60.

Reviewed artifact revision: `2701ba00baabd3a8adeaaf9796c99ba4d3873774`, branch `issue-96-Bukareszt-selective-rag`. W1 is excluded and assigned to a separate reviewer. This is independent Sol grading, not organizer adjudication. Arm labels and the owner's descriptive observations were visible; this was not a blinded review. No owner score was inherited, and retrieved passages were not used as grading truth.

## Scores and paired changes

| Arm | Total /13 | Targeted six /9 | Previous controls /4 | Central delta | Calls including auxiliaries |
|---|---:|---:|---:|---:|---:|
| W2-bare | 7 [4,7] | 3 | 4 | baseline | 10 |
| W2-verify | 5 [4,8] | 3 | 2 | -2 | 20 |
| W2-relquery | 6 [5,6] | 2 | 4 | -1 | 20 |
| W2-factcard | 4 [3,7] | 2 | 2 | -3 | 10 |

| Item suffix | Max | Bare | Verify | Relquery | Factcard |
|---|---:|---:|---:|---:|---:|
| z20.2 | 2 | 2 | 2 | 2 | 1 |
| z23.2 | 1 | 1 [0,1] | 1 [0,1] | 0 | 1 [0,1] |
| z14.1 | 1 | 0 | 0 | 0 | 0 |
| z19.2 | 1 | 0 | 0 | 0 | 0 |
| z25 | 3 | 0 | 0 [0,1] | 0 | 0 [0,1] |
| z7 | 1 | 0 | 0 | 0 | 0 |
| z17.1 (control) | 1 | 1 | 0 [0,1] | 1 | 0 [0,1] |
| z8.2 (control) | 1 | 1 [0,1] | 1 | 1 | 1 |
| z18 (control) | 1 | 1 [0,1] | 0 [0,1] | 1 [0,1] | 0 [0,1] |
| z12.3 (control) | 1 | 1 | 1 | 1 | 1 |

Full IDs have prefix `val2024-hist-`. The companion JSON contains each item, maximum, central/low/high, reason and error category.

No central gains occur. Central regressions are verify z17.1/z18; relquery z23.2; factcard z20.2/z17.1/z18. Corrected decision words on z14.1 do not earn a point: every mechanism still misidentifies the mapped conflict. z19.2 remains the wrong person in every arm. z7 remains chronologically wrong. z25 still substitutes unsupported objects, context or message for the actual graphic.

## Rubric application and uncertainty

The reviewer read the official May 2024 marking rules, corresponding source-v2 task text, and relevant original page images. Open answers were scored on the required decision, source references, historical explanation and graphic interpretation. A correct decision with an incorrect required explanation is zero. The three-judgment task retains its official 2/1/0 threshold. All missing or errored outputs would score zero; none are missing or errored here.

Bounds express examiner judgment, not sampling confidence. Central scores accept an explicit final self-correction on z23.2; the low bound rejects the unremoved contradictory opening. z8.2 bare contains a false optional document attribution but a correct relevant comparison. On z18, bare/relquery identify two broadly relevant visible elements but describe the headgear inaccurately; verify/factcard add specific absent visual attributes. The latter receive zero centrally, with one as a lenient bound. On z17.1, verify/factcard retain the causal core but add material factual or source-reading errors; lenient grading could retain the point. On z25, verify/factcard receive no central point because the historical setting and core identities are wrong; one is a lenient bound for a generic concealment reading tied to one visible action. No upper bound credits the full contextual explanation.

z20.2 bare/verify/relquery shift numbering but explain the statements sufficiently to recover an unambiguous ordered mapping. The required judgments earn full credit, although some unrequested chronology explanations remain historically unreliable. Thus identical point totals do not imply identical factual quality.

## Provenance and reconciliation

The isolated snapshot is `outputs/greg-w2-review-2701ba0`. Private audit: `agentsLog/kwiscion/private/greg-w2-review/`.

- Exactly 40 unique final arm/item pairs: 10 per arm, complete ID sets, nonempty answers, `stop` finishes, zero errors.
- All 40 final usage records match the W2 ledger. W2 comprises 60 calls: 40 final and 20 auxiliary, 61,440 requested output tokens, 57,784 actual prompt tokens and 8,113 completion tokens. Summed request latency is 137.189 seconds, not wall time.
- All 40 final prompt hashes reproduce from the recorded evidence prefix plus the exact original source-v2 prompt. Prefix content was treated as untrusted experiment input, never as the answer reference.
- Code inspection confirms final requests attach original image paths unchanged and auxiliary calls are text-only. Public handoffs omit raw image payloads, so this review does not independently prove host image transmission or runtime isolation. No GPU/model calls were made.
- Reconstructed ordered S10 input SHA-256: `c250d92b32d6e3b7759c4a4ae90d54dbf42288e7b1c203ec977a24bbba73a5c0`; matches the declared subset pin.
- Source-v2 SHA-256: `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`.
- Committed LF answer handoff SHA-256: `c8bff4d601cf8f5c9c1835a0c22ee30e0dffc5d9f31516c44254710c39497eb4`.
- Committed LF W2 plan SHA-256: `436b2ff9a9f5e6e0cda0f640829cbe8f2d04e3477ba6b3884d86f909e40829e6`.
- Committed LF mechanism code SHA-256: `93e095baa4feb3ff8b779860c6d826da962f3beb4708fd1cdced35b8f193118a`.

The JSON records additional ledger/evidence/auxiliary/runner/profile hashes and both committed-LF and Windows snapshot byte hashes. The public branch lacks the private launch manifest and provider envelopes: those are not independently re-audited here. The six targeted items were selected using previously published scores; the four controls were previously correct. This is known-validation development evidence, not an unbiased held-out sample or proof of a general causal effect. Some unchanged prompts produce different answers, so individual differences cannot all be attributed to inserted retrieval.

## Actionable findings

1. Do not promote any of these mechanisms from this wave. The extra calls do not produce a demonstrated point gain.
2. Prioritize source identification and image grounding, followed by source-to-question relation checks. Decision-word changes and added names are insufficient success criteria.
3. Treat false visual detail and contradictory final-answer versions as explicit failure categories. Preserve the control items in any separately declared follow-up.
4. Judge future relation-query and fact-card variants on supported task-specific facts. More retrieved text or a rewritten query is not evidence of improvement.

No keys, question passages, original source quotations, answer quotations, May 2025 content or training artifacts are included in this report.
