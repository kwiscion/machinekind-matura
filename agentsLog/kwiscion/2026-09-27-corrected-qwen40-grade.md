# Corrected Qwen40: frozen single-pass grade

**36/60 =33/45 nonessay +3/15 essay**, versus corrected Gemma **39/60 =31+8** on the same exact corrected inputs. Qwen improves nonessay by2 but loses5 on the essay. No overall promotion is supported by this full-exam result.

All40 final answers are complete, with zero blanks/placeholders. Exact joins to organizer answers, all40 IDs/60 maximum points,21 crop hashes and32 image references passed. The declared runtime reports41 calls: one timeout recovered; its final answer was still historically incorrect. No raw reasoning was used.

| Loss category | Points |
|---|---:|
| incomplete_source_explanation | 1 |
| historical_fact | 8 |
| visual_source_interpretation | 2 |
| incomplete_identification | 1 |
| essay_argument_depth | 9 |
| essay_factual_deduction | 2 |
| essay_coherence | 1 |
| blank_or_placeholder | 0 |

Essay topic3 has433 body words. Aspects diplomatic/military/political-constitutional each1; narrative3 minus2 for three factual errors, plus coherence2 =3/15. The army and diplomatic institution names are corrupted, and the1921 constitutional discussion incorrectly invokes later presidents. A Roman-fragmentation sentence breaks the diplomatic argument, and the conclusion shifts from chiefly responsible to exclusively responsible. This is a content failure despite mechanical completion. [IPN army history](https://ipn.gov.pl/pl/historia-z-ipn/231218,Blekitna-armia-generala-Hallera.html), [State Archives regency record](https://pamiecpolski.archiwa.gov.pl/rada-regencyjna-do-narodu-polskiego-afisz/), [IPN diplomatic actors](https://bialystok.ipn.gov.pl/pl1/aktualnosci/181807,Artykuly-historykow-Oddzialu-Instytutu-Pamieci-Narodowej-w-Bialymstoku-o-Romanie.html), [Sejm constitution chronology](https://www.sejm.gov.pl/KonstytucjaMarcowa.nsf/).

Item12.2 receives credit: renuncjacja tronu is an attested renunciation term, not a mandatory-keyword failure. [WSJP PAN](https://wsjp.pl/haslo/podglad/117908/renuncjacja). Recognizable spelling in17.2 also receives credit.

| Item with changed grade | Gemma | Qwen | Delta |
|---|---:|---:|---:|
| 3.1 | 0 | 1 | +1 |
| 3.2 | 0 | 1 | +1 |
| 6 | 0 | 1 | +1 |
| 8.1 | 1 | 0 | -1 |
| 9 | 1 | 0 | -1 |
| 10 | 1 | 0 | -1 |
| 11.1 | 1 | 0 | -1 |
| 17.2 | 0 | 1 | +1 |
| 18 | 0 | 1 | +1 |
| 19.2 | 1 | 0 | -1 |
| 20.2 | 1 | 2 | +1 |
| 24 | 1 | 0 | -1 |
| 25 | 1 | 3 | +2 |
| 26 | 8 | 3 | -5 |

Changed items: Qwen better on7, worse on7, tied on26. Complete40-item delta and exact answer hashes: [comparison JSON](2026-09-27-corrected-qwen-gemma40-comparison.json). Neither per-item oracle composition nor cross-model ensemble is an eligible observed score.

Judgment sensitivity33–40 (not a confidence interval): item6 implicit hierarchy, item9 erroneous graphic relation, item18 ropes/weapon wording, item25 generic second graphic interpretation, and essay aspect/coherence level. Central grades are frozen before reading Gemma item scores. This is one model-unblinded, known-validation agent pass; no second judge or organizer confirmation. Legacy38 used full-page inputs and is not the matched comparator.

Grade JSON SHA256 `09923ca319a65f187391ce53267f98f249abb10b75a915df1cc7151c3b753e90`; [full grade](2026-09-27-corrected-qwen40-grade.json). Comparison JSON SHA256 `eb2be829656de127553b2aa485b8c86aca08fc780e06993eb5131eb808941c46`. Answer packet `68bc66c59a3104167a22d6b1711d565d510566967f573040f5701cf80b6de3bf`; organizer answers `a05028ccf868dd1e90538cbaf885745ba2aedd7fbb09843f242a64a9426cd966`; corrected exam `e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6`. All21 crops were visually rechecked in the four QA contacts;9 and18 were inspected separately.

Public report contains original assessment and provenance only; original source questions, official key text and raw runtime reasoning remain private.
