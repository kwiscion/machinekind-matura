# Independent C3 replication review: DEV009–012

**Do not promote C3 pending rubric calibration.** My provisional review gives single-pass A **35/60** and grounded critic/rewrite C3 **39/60 (+4)** across these four original DEV topics. The owner's grades are **14/60 →27/60 (+13)**. The direction is similar, but the magnitude and absolute levels are not replicated. The largest disagreement concerns whether formulaic but relevant causal explanations merit satisfactory3 or superficial1; neither grader is assumed correct.

This review is independent, **not blind** to the reported gain. I read only the eight requested final responses and their four original fixtures before freezing scores at **18:46:17 UTC**. I then opened `grades.dev.jsonl`. The frozen precomparison hash and every exact response SHA256 are preserved in the accompanying JSON; the initial JSON is retained privately. No model calls, keys, May2025 data, training changes or Git mutations were used.

## Method and scores

The general [official essay guidance, pages7–10](https://www.oke.waw.pl/wp-content/uploads/OKE_WARSZAWA/EM/EM_2023/Materia%C5%82y_dodatkowe/2024/Material_dodatkowy_historia_wypracowanie.pdf) distinguishes broad, detailed analysis from satisfactory factual reasoning and superficial generalities. I used4/3/1/0 per required aspect, then the1/2/3-point factual-error deductions, plus coherence0–3. The requested300-word gate follows the2023/2024 footnote. Unsupported precision earns no factual credit but was not automatically counted as a proven falsehood. Error counts are claim-level, not repeated-mention counts.

All eight select topic1, address its three aspects, and already exceed300 body words. Fixtures require historical knowledge, not mandatory use of source excerpts; their `source_ids` are reference-only metadata. Thus there is **no length-gate rescue** in this comparison. Counts below remove topic/aspect/Teza/conclusion labels and punctuation-only whitespace tokens; the JSON also records raw whitespace counts. This differs from the owner's count by one word per response without affecting eligibility.

| Topic / arm | Body words | Three aspect points | Error deduction | Coherence | My total | Owner total |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
|009 A|369|1/3/3|1|3|9|3|
|009 C3|442|3/3/3|1|3|11|8|
|010 A|398|3/1/1|1|3|7|3|
|010 C3|459|3/1/1|2|3|6|6|
|011 A|343|3/3/3|1|2|10|3|
|011 C3|424|3/3/3|1|3|11|6|
|012 A|364|3/1/3|1|3|9|5|
|012 C3|391|3/3/3|1|3|11|7|

Aspect order is the fixture order: political/military/religious; constitutional/fiscal/territorial; constitutional/domestic/international; military/political/territorial. No aspect receives rich4 in my assessment. Repeated assertions that a fact “confirms the thesis” do not themselves supply depth. The JSON contains each rationale and judgment-sensitivity range; those ranges are not statistical confidence intervals.

## Factual gains and failures

- **009:** C3 repairs the hereditary-rule/administrative-union confusion by explaining a personal union. It then introduces recovery of Pomerania within Jagiełło's reign; Gdańsk Pomerania returned in1466, after that reign. [Historical study](https://bazhum.muzhp.pl/media/texts/rocznik-bezpieczenstwa-miedzynarodowego/20112012-tom-6/rocznik_bezpieczenstwa_miedzynarodowego-r2011_2012-t6-s155-169.pdf). I disagree with the owner's categorical dismissal of any Kalmar causal connection: the [UJ historical presentation](https://buk.wzks.uj.edu.pl/grunwald/postaci/index.php?osoba=06_01_ulrich-von-jungingen) describes two-front pressure and the Gotland settlement before war with Poland–Lithuania. The essay remains compressed/overstated, but that is insufficient to label the entire connection invented.
- **010:** Both arms inadequately assess the actual execution movement. C3's denial of stable-revenue military financing conflicts with the **kwarta/wojsko kwarciane** mechanism. [Government education material](https://zpe.gov.pl/watek/LP6A43JBQH/19/a/ruch-egzekucyjny/DA1OC2RLX). The Polesie incorporation error persists; the relevant1569 provinces were Podlasie, Volhynia, Bracław and Kyiv. [Incorporation account](https://zpe.gov.pl/a/droga-do-unii-realnej/DB6cUAxPR). C3 also compresses the1551 drafting commission into a statutory revision and shifts the transfer of hereditary Lithuanian rights from1564 to1569. [Wilanów museum](https://wilanow-palac.pl/pasaz-wiedzy/drugi-statut-litewski-1566), [succession account](https://zpe.gov.pl/a/wolna-elekcja/D11JYInQ4). Its simultaneous-integration wording blurs Oświęcim/Zator1564 with Royal Prussia1569. Two chronology readings are context-sensitive; the three firmer errors alone still trigger the same2-point deduction. More dates and names do not establish improvement here.
- **011:** C3 fixes the first/second-partition confusion and clarifies the thesis, but **retains Bar Confederation1792**. The actual period is1768–1772. [Government education account](https://zpe.gov.pl/a/przeczytaj/DonoeTv4p). I did not count A's loose “Konstytucja Sejmowa1791” wording as an additional invented event: its referent is identifiable. This differs from the owner's extra factual deduction.
- **012:** A misnames/dates the central defence institution: the **Rada Obrony Państwa was established1July1920**, not a national committee in1919. [Contemporary act/documentation](https://1920.gov.pl/1-lipca-1920/). C3 removes this but introduces a chronology problem by assigning the response to the December1919 peace offer to premier Paderewski. His government ended9December; the formal Soviet offer was22December under Skulski. [Archival dismissal record](https://www.aan.gov.pl/paderewski/page22.html), [published cabinet records](https://rcin.org.pl/Content/239860/WA303_276185_II15098-4_Gmurczyk-Wronska.pdf). This does not deny his earlier discussion of Entente policy.

These are genuine repairs mixed with preserved/new errors, not merely formatting changes. However, the critic is not a reliable factual verifier. Even my more generous grading finds a regression on010, and the all-passing length condition cannot explain the gains.

## Calibration handoff

Adjudicate **dev-essay-011__A and dev-essay-011__C3** first, reading their exact strings from `answers.dev.jsonl`. This pair has the largest combined disagreement:

- A: mine3/3/3−1+2=10; owner1/1/1−2+2=3.
- C3: mine3/3/3−1+3=11; owner3/1/1−1+2=6.

I treated veto/constitutional repair, Targowica/elite division and named neighbour intervention as relevant causal reasoning sufficient for3, despite shallow analysis. The owner treated much of it as rhetorical generality sufficient only for1. The official distinction must be applied to these actual paragraphs before choosing a calibration. Separately adjudicate whether C3's organization has a concrete coherence disturbance warranting2 rather than3; factual errors and repetitive style alone should not automatically become coherence deductions.

**Recommendation:** retain C3 as an experimental factual-repair candidate, preserve both scorecards, and use the lead's calibration adjudication before any promotion claim. The four-topic result is small and selected; it does not establish broad factual reliability or a full-exam gain.

## Lead adjudication appended after this review

Root Astra independently read the exact011 pair and topic and returned **A8/15 → C310/15**, for this pair only: A3/3/1−1+2; C33/3/3−1+2. The lead judged A's international paragraph too generic and chronologically wrong for satisfactory credit, while C3's specific partition participants/dates supported3. Neither response securely earned full coherence because of repetition/overstatement. The lead agreed that the recognisable1791 constitution label should not be counted as another invented event. Checks used [ZPE's collapse account](https://zpe.gov.pl/a/upadek-rzeczypospolitej-obojga-narodow/DrSK5HUTC) and the [Sejm resolution](https://orka.sejm.gov.pl/proc9.nsf/uchwaly/1111_u.htm).

This is **one-pair adjudication, not whole-packet calibration**. My frozen35→39 and the owner's14→27 remain unchanged and separately attributable. Direction is promising; magnitude remains uncalibrated. Do not present a claimed+3.42 points per essay as established by this review.
