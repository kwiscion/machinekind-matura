# Premise check — dev-essay-006/007/008

- **Checker**: independent Claude Sonnet subagent (not the fixture author)
- **Date**: 2026-09-26
- **Method**: WebFetch of each source's pinned `url` (pl.wikipedia.org oldid) from
  `data/przemeknowak781/sources.jsonl`; premises in the fixture topic wording compared
  against short locator quotes (<=15 words) from the pinned revision. No repo file edited.

| Fixture | Topic | Premise | Source id (oldid) | Verdict | Locator |
|---|---|---|---|---|---|
| dev-essay-006 | T1 | Bolesław I Chrobry reigned 992–1025 | src-plwiki-boleslaw-i-chrobry (80807212) | supported | "od 25 maja 992 do 17 czerwca 1025" |
| dev-essay-006 | T1 | Church aspect exists (Zjazd gnieźnieński, metropolia) | src-plwiki-zjazd-gnieznienski (80006828) | supported | "zjazd odbył się ... 1000 roku w Gnieźnie" |
| dev-essay-006 | T2 | Rozbicie dzielnicowe follows 1138 succession statute | src-plwiki-testament-boleslawa-krzywoustego (79586801) | supported | "weszły w życie tuż po śmierci ... w 1138" |
| dev-essay-006 | T2 | Rozbicie dzielnicowe period starts 1138 | src-plwiki-rozbicie-dzielnicowe-w-polsce (80629521) | supported | "po śmierci Bolesława Krzywoustego w 1138 roku" |
| dev-essay-007 | T1 | Great War with Teutonic Order 1409–1411 | src-plwiki-wielka-wojna-z-zakonem-krzyzackim (80790485) | supported | "Czas: 14 sierpnia 1409 – 1 lutego 1411" |
| dev-essay-007 | T1 | Grunwald fought 1410 | src-plwiki-grunwald (80318601) | supported | "pod Grunwaldem 15 lipca 1410 roku" |
| dev-essay-007 | T1 | First Peace of Toruń 1411 | src-plwiki-pierwszy-pokoj-torunski (80790355) | supported | "traktat pokojowy zawarty 1 lutego 1411" |
| dev-essay-007 | T1 | Thirteen Years' War 1454–1466 | src-plwiki-wojna-trzynastoletnia (79824899) | supported | "stoczona w latach 1454–1466" |
| dev-essay-007 | T1 | Second Peace of Toruń 1466 ends the war | src-plwiki-drugi-pokoj-torunski (80789011) | supported | "zawarty w Toruniu 19 października 1466 roku" |
| dev-essay-007 | T2 | Nihil novi enacted 1505 | src-plwiki-nihil-novi (80568268) | supported | "konstytucji sejmowej uchwalonej 30 maja 1505 r." |
| dev-essay-008 | T1 | Pozytywizm warszawski ~1864–1880s | src-plwiki-pozytywizm-warszawski (74987360) | supported | "ofensywa ... trwała do ok. 1880" |
| dev-essay-008 | T1 | Kulturkampf, anti-Polish dimension, Prussian partition | src-plwiki-kulturkampf (79686870) | supported | "strong anti-Polish element" (1871–1878) |
| dev-essay-008 | T1 | Russification intensifies after 1863/1864 | src-plwiki-rusyfikacja (77703362) | supported | "zaostrzenie rusyfikacji ... po upadku powstania styczniowego" |
| dev-essay-008 | T1 | Galician autonomy, Austrian partition | src-plwiki-autonomia-galicyjska (76175430) | supported | "prawa ... które Galicja uzyskała w latach 1869–1873" |
| dev-essay-008 | T2 | Revolution of 1905 occurred in Królestwo Polskie | src-plwiki-rewolucja-1905-roku-w-krolestwie-polskim (80703935) | supported | "napięta sytuacja ... utrzymywała się od co najmniej 1904" |

**Summary: 15/15 supported**

## Flags (wording, not factual errors)

- dev-essay-007 T1 phrasing "wojny ... z zakonem krzyżackim w latach 1409–1466" brackets two
  separate conflicts (1409–1411 and 1454–1466) with ~43 years of peace between them; plural
  "wojny" makes this defensible, but a careless reading could imply continuous warfare.
- dev-essay-006 T1 "panowania ... (992–1025)" spans his time as duke (from 992) plus king
  (crowned 1025, died same year); standard historiographic convention, not misleading.
- dev-essay-008 T1's four sources each cover a narrower sub-range within 1864–1905 (e.g.
  Kulturkampf 1871–1878); topic frames them as illustrative episodes within the span, not as
  each spanning the full 41 years — reading is sound.

No unsupported or contradicted premises found.
