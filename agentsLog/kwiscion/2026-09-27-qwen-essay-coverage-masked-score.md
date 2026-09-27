# Qwen coverage diagnostic: frozen masked essay grades

Model and prompt author known; arm mapping and runtime answer records not opened before this freeze. Earlier experiment grades known, not used as score targets. Four repeated known-validation essays, not a full exam or organizer score. Ranges are judgment sensitivity, not confidence intervals. Whitespace body count removes the initial chosen-topic heading.

| Mask | Topic | Body words | Aspects | Deduction | Coherence | Score | Sensitivity |
|---|---:|---:|---|---:|---:|---:|---|
| 5e71b24e2f8045d2 | 1 | 403 | 3/3/3 | 1 | 3 | 11/15 | 10–11 |
| 33516b405f0c4269 | 3 | 443 | 3/3/1 | 2 | 3 | 8/15 | 7–9 |
| 8bf6024a56df435f | 1 | 430 | 3/3/3 | 1 | 3 | 11/15 | 10–12 |
| 0ec0b5abf7d246be | 2 | 387 | 3/1/1 | 2 | 3 | 6/15 | 4–7 |

## 5e71b24e2f8045d2
Answer SHA256: `eb5cc0d125036cc92e8549379c52af8e02f925c37e5a5870232eb8b437cfeccf`.

- Political: coronation by Leo III in 800 and missi dominici are connected to restored imperial legitimacy and administrative control; satisfactory, not a rich comparison with other revival attempts.
- Socioeconomic: monetary coordination and Capitulare de villis are connected to exchange and estate management; developed despite the erroneous metal/coin claim.
- Cultural: manuscript preservation, schools and Carolingian minuscule explain continuity and integration; satisfactory.
- Factual correction: Stable united western empire until the end of the tenth century is chronologically false: the Carolingian empire divided in 843.
- Factual correction: The monetary reform is incorrectly based on a gold solidus; the reformed currency was silver deniers.
- Uncertainty: Ambiguous Einhard school leadership and capitulary assemblies are not independently counted as definite additional errors. Janowca and inflected Latin are malformed wording, not invented extra events.

## 33516b405f0c4269
Answer SHA256: `a1917b3fc0252fbb4a43d014ac02eb84aed781b915b665961ef56cf133f00a18`.

- Diplomatic: the military leverage to Riga settlement causal link is concrete enough for satisfactory credit; the surrounding personal-negotiation and recognition assertions are unreliable.
- Military: centralization of forces in 1918 and Warsaw defence in 1920 are explained as conditions of survival; satisfactory rather than rich.
- Political-constitutional: temporary government/administrative unity is mostly generic and the March Constitution explanation is wrong; superficial.
- Factual correction: Attributes direct personal negotiations with Bolsheviks to Pilsudski; the relevant negotiations were conducted through representatives, not his direct participation.
- Factual correction: Places official confirmation of sovereignty by west and east in December 1918; international recognition was a sequence, with key Allied recognitions in 1919.
- Factual correction: Treats the March Constitution as arising from Pilsudskis anti-monarchical reform drive; its parliamentary design limited the executive and was not his constitutional programme.
- Uncertainty: Riga deriving partly from military leverage is not an error merely because its settlement differed from Pilsudskis federal aims. Podkarpacie wording is vague and not an additional proved error.

## 8bf6024a56df435f
Answer SHA256: `fe8cf0be6260ae09d32032e06920004621eb7e824e322cce9d277487f6e070bb`.

- Political: 800 coronation, imperial authority, missi and capitularies form a developed legitimacy/administration argument.
- Socioeconomic: denarius reform and exchange stability are linked to commerce and state revenue, with less well supported infrastructure/social claims; satisfactory.
- Cultural: Alcuin, Latin standardization and preservation in named monasteries explain continuity of learning; sufficient development despite awkward terminology.
- Factual correction: Claims a uniform law throughout the empire overriding local customs; Carolingian legal plurality persisted and capitularies supplemented distinct laws (Einhard, chapter 29).
- Uncertainty: Renesans Ksiestwa is treated as a malformed label for the recognizable Carolingian renaissance, not a separately invented event. Claims about Aristotle copying and peasant protection are imprecise/unsupported, not automatically additional factual deductions.

## 0ec0b5abf7d246be
Answer SHA256: `0b1a9b0c8cc2e39c6dd581da3c1c497c5a2ce436647f603abc89f568a935a9fd`.

- Military: Chocim and Vienna plus the drain on troops/resources support a causal military argument, although the Kamieniec example is wrong and the comparative claim remains underproved.
- Political: generic tax disputes and magnate obstruction, without a concrete demonstrated constitutional or diplomatic episode, remain superficial.
- Socioeconomic: requisitions, production decline and trade loss are mostly generic; the asserted principal geography is wrong and no specific economic example establishes primacy over Swedish wars.
- Factual correction: Dates the fall/major siege of Kamieniec Podolski to 1673 rather than 1672.
- Factual correction: Groups that Kamieniec episode among Commonwealth military victories; the fortress fell to the Ottomans.
- Factual correction: Locates the principal Ottoman-war devastation in Vistula and Pripyat regions instead of the southeastern theatre; this confuses the geographic basis of the argument.
- Uncertainty: Speculative foreign loans and comparison with smaller armies in other wars weaken support; they are not separately counted without adequate verification. Military aspect 1 versus 3 and the third error account for the sensitivity range.

All four finals complete; all answer hashes and 53 archive member hashes verified. No arm key read before freeze.

Correction evidence: [currency](https://ikmk.smb.museum/object?id=18245129&lang=en), [partition](https://zpe.gov.pl/a/przeczytaj/DuH5YozJ1), [law_primary](https://www.ancienttexts.org/library/latinlibrary/ein.html), [constitution](https://www.sejm.gov.pl/KonstytucjaMarcowa.nsf/), [pilsudski_constitution](https://muzeumpilsudski.pl/wp-content/uploads/2018/07/Odrodzenie-Rzeczypospolitej-w-mysli-politycznej-Jozefa-Pilsudskiego-1918-1922.pdf), [recognition](https://czasopisma.ltn.lodz.pl/Studia-Prawno-Ekonomiczne/article/download/312/274/533), [ottoman](https://zpe.gov.pl/a/przeczytaj/DHTBK1R4p).

Packet SHA256: `e76311596961ae9103ed5b435a311ad4ee872aeb78e062da7ecb0bf9369deebd`. JSON contains exact final answers and component grades; no official source passages or raw reasoning.
