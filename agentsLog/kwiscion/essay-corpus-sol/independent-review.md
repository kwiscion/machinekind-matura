# Independent Sol corpus content review

**Accept with limitations: 8 essays, 8 faithful repair pairs and 32 evidence cards. These contain 8 unique target essays. No target-text factual repair is required.** All canonical records remain DRAFT/export pending; this is content acceptance only, not training clearance.

The JSON provides an accept/revise/reject decision for every record/card, exact response and prompt SHA-256, corrupted-input hashes, all source hashes and source revisions. Metadata additions alone do not invalidate unchanged target-content decisions.

| Essay family | Body words | Essay / repair | Content finding |
|---|---:|---|---|
| augustus | 442 | Accept / accept | Military asymmetry, accumulated republican powers and elite accommodation form three functional arguments. Actium, Egypt,27BCE settlement/title and later powers are supported. The target avoids equating preserved republican forms with restored institutional balance; it does not falsely claim he held every office or an official kingship. |
| investiture | 441 | Accept / accept | Bishops’ temporal roles explain the conflict;1076/1077 distinguish sanction from final resolution;1122 compromise correctly separates spiritual investiture from retained secular/election influence. Canossa is not treated as permanent papal victory or modern church-state separation. |
| augsburg | 444 | Accept / accept | Legal recognition, territorial rather than individual choice, emigration burdens and ecclesiastical reservation support a qualified judgment. Calvinism is denied separate equal status rather than simplistically erasing all practical exceptions. Primary1555text confirms reservation and emigration conditions. No inevitable-war claim. |
| vienna | 440 | Accept / accept | France’s diplomatic reintegration, Polish-Saxon compromise and territorial arrangements demonstrate a negotiated balance rather than literal restoration. Polish Kingdom/Posen/Cracow,39-state federation, Netherlands and Austrian Italian position are correctly presented. National aspirations and dynastic legitimacy are not conflated. |
| industrial | 446 | Accept / accept | Textile mechanisms, coal/coke and improved steam, and factory/social change are developed together. Domestic jenny use and continued water power prevent false instant-transition claims.1833law is described as an attempt to limit abuses, not a complete solution. Productivity gains are distinguished from immediate universal welfare. |
| meiji | 454 | Accept / accept | Accept.1868restoration,1871domain abolition,1873conscription, stipend conversion and industrial/rail/export policies support the centralization argument. Old elites and agricultural costs remain visible; no automatic equal-rights claim. Target avoids erroneous exact service-age/duration detail in pinned secondary article. |
| league | 450 | Accept / accept | Sovereignty/unanimity with exceptions, absent US membership, and dependence on member resources connect to Manchuria and Ethiopia. Investigation/condemnation are distinguished from enforcement. Oil and Suez omissions are supported; no claim that Japan withdrew instantly or that unanimity had no exceptions. |
| marshall | 447 | Accept / accept | Accept.1947announcement versus1948implementation, recovery assistance, OEEC coordination and Cold War objectives are distinct. Preexisting recovery and disputed marginal impact are acknowledged. No claim of an immediate common market, sole cause of growth, or sole origin of European division. |

## Evidence and structure

I read all eight complete targets and repair inputs, checked all 32 cards against their pinned reference text, and checked additional claims and the function of evidence in each argument. Each essay has a thesis, three developed argumentative paragraphs and a conclusion. Counts independently reconcile to 442, 441, 444, 440, 446, 454, 450 and 447 words. Arguments explain mechanisms and limits rather than merely listing dates. These are useful examples, not claims of exhaustive coverage or an official full-mark score.

Primary and institutional checks were used where details mattered:
- [Worms reciprocal grants1122](https://sourcebooks.web.fordham.edu/source/worms1.asp)
- [Augsburg1555 §§15-18,24](https://germanhistorydocs.org/en/from-the-reformations-to-the-thirty-years-war-1500-1648/ghdi:document-4386)
- [Vienna institutional history](https://www.bundeskanzleramt.gv.at/en/federal-chancellery/visit-us/history/the-congress-of-vienna.html)
- [Factory Act1833](https://www.parliament.uk/about/living-heritage/transformingsociety/livinglearning/19thcentury/overview/factoryact/)
- [Japanese conscription1873](https://www.archives.go.jp/ayumi/kobetsu/m06_1873_01.html)
- [League Covenant5/15/16](https://www.ungeneva.org/en/about/league-of-nations/covenant)
- [League crises](https://www.ungeneva.org/en/about/league-of-nations/at-work)
- [Marshall1948law](https://www.archives.gov/milestone-documents/marshall-plan)

The Augsburg primary text supports conditional emigration and the ecclesiastical reservation; it does not warrant treating every resident as freely able to practice any faith locally. The target’s qualified wording is sound. The Meiji source contains questionable precise service-age/duration claims; the target does not repeat them. Japan’s National Archives confirms the 1873 law used by the target. The League Covenant confirms exceptions to unanimity, which the essay preserves.

## Repairs and dependencies

All repair targets exactly equal their checked parent essays. Wrapper-only pairs preserve content; truncated pairs restore verified argumentation. The two multitopic negatives contain the chosen full essay plus the other essay’s introduction, clearly labeled unselected. Removing that introduction is faithful, but it is a limited fixture rather than evidence of robust choice between two full essays.

**Keep Augsburg connected to Vienna, and League connected to Marshall.** Those dependencies are explicitly recorded in the repair metadata. Eight topic groups therefore form six local connected components before any wider source/topic merges. Greg owns canonical grouping, multilingual aliases, cross-corpus near-duplicates, contamination checks and evaluation-topic allocation. This review does not perform or certify those tasks.

## Provenance and limitations

All eight HTML hashes, actual wgRevisionId values and CC BY-SA 4.0 links were verified. The derived-text hashes match after LF normalization; Windows files contain CRLF, so raw byte hashes differ. The generator fixed this metadata before final freeze: text_sha256 now explicitly denotes LF-normalized text, and text_file_sha256 records actual bytes. Both independently match. Evidence locators were also clarified before freeze. Final essay and repair JSONL hashes match the generator’s stability confirmation; all sixteen response/prompt decisions target that frozen content.

The acquisition script lists general historical references and the builder uses owned target prose and deterministic corruptions. Generator provenance declares independent topic selection and no exam access. No benchmark ingestion path was found, but this is not proof of semantic nonoverlap or novelty to pretrained weights. The reviewer opened no new exam and added no benchmark-derived content.

One secondary article per topic limits source diversity. Preserve source attribution, revisions and applicable share-alike treatment; embedded media and separately credited passages have separate rights. Primary crosschecks here are references, not newly licensed training text. Exact teacher checkpoint, dataset/model licensing, export compatibility, training efficacy and LoRA/runtime feasibility remain unverified. No teacher file, canonical status, Git state or model runtime was modified.
