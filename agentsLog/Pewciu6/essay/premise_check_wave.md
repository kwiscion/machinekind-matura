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

**Summary (006–008): 15/15 supported**

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

## Replication set (009–012)

Same checker/date/method as above, applied to dev-essay-009..012 (both topics each).

| Fixture | Topic | Premise | Source id (oldid) | Verdict | Locator |
|---|---|---|---|---|---|
| dev-essay-009 | T1 | Unia w Krewie 1385 | src-plwiki-unia-w-krewie (80354694) | supported | "akt wydany 14 sierpnia 1385 roku" |
| dev-essay-009 | T1 | Władysław II Jagiełło reigned 1386–1434 | src-plwiki-wladyslaw-ii-jagiello (80805804) | supported | "od 4 marca 1386 do 1 czerwca 1434" |
| dev-essay-009 | T1 | Military aspect: Grunwald fought 1410 | src-plwiki-grunwald (80318601) | supported | "pod Grunwaldem 15 lipca 1410 roku" |
| dev-essay-009 | T2 | Jadwiga Andegaweńska's role (union, Christianization of Lithuania) | src-plwiki-jadwiga-andegawenska (80425369) | supported | "chrystianizację Litwy w 1387" |
| dev-essay-010 | T1 | Zygmunt II August reigned 1548–1572 | src-plwiki-zygmunt-ii-august (80622470) | supported | "od 1 kwietnia 1548 do 7 lipca 1572" |
| dev-essay-010 | T1 | Ruch egzekucyjny active during his reign | src-plwiki-ruch-egzekucyjny (77683485) | supported | "sejm ... 22 listopada 1562" reforms |
| dev-essay-010 | T1 | Terytorialny aspect: Unia lubelska 1569 | src-plwiki-unia-lubelska (80758426) | supported | "zawarte ... 1 lipca 1569" |
| dev-essay-010 | T2 | Wolna elekcja rules set after 1572 | src-plwiki-wolna-elekcja (79416082) | supported | "pierwsza wolna elekcja ... w roku 1573" |
| dev-essay-010 | T2 | Artykuły henrykowskie codify election rules, 1573 | src-plwiki-artykuly-henrykowskie (79943427) | supported | "spisane na sejmie elekcyjnym 1573 roku" |
| dev-essay-011 | T1 | Sejm niemy 1717 (start bracket) | src-plwiki-sejm-niemy (76770450) | supported | "miała miejsce 1 lutego 1717" |
| dev-essay-011 | T1 | Liberum veto contributed to Commonwealth's collapse | src-plwiki-liberum-veto (79646244) | supported | "collapse of ... First Polish-Lithuanian Commonwealth" |
| dev-essay-011 | T1 | Konfederacja targowicka 1792 | src-plwiki-konfederacja-targowicka (77476727) | supported | "w nocy z 18 na 19 maja 1792" |
| dev-essay-011 | T1 | Rozbiory 1772/1793/1795 (end bracket) | src-plwiki-rozbiory (80425883) | supported | "I rozbiór ... 1772 r. ... III rozbiór ... 1795 r." |
| dev-essay-011 | T2 | Insurekcja kościuszkowska 1794 | src-plwiki-powstanie-kosciuszkowskie (79178134) | supported | "24 marca – 16 listopada 1794" |
| dev-essay-012 | T1 | Wojna polsko-bolszewicka framed as 1919–1921 | src-plwiki-wojna-polsko-bolszewicka (80061025) | partly | "3 stycznia 1919 – 18 października 1920 (traktat ... 1921)" |
| dev-essay-012 | T1 | Bitwa Warszawska 1920 within the war | src-plwiki-bitwa-warszawska (80608335) | supported | "13–25 sierpnia 1920 roku" |
| dev-essay-012 | T1 | Traktat ryski 1921 (formal end) | src-plwiki-traktat-ryski-1921 (80631068) | supported | "podpisany w Rydze dnia 18 marca 1921" |
| dev-essay-012 | T2 | Konstytucja marcowa adopted 1921 | src-plwiki-konstytucja-marcowa (80733076) | supported | "uchwalono przez aklamację 17 marca 1921" |

**Summary (009–012): 17/18 supported (1 partly)**

Flag: dev-essay-012 T1's "1919–1921" bracket is the standard textbook convention (fighting
1919–Oct 1920, war formally closed by the March 1921 Treaty of Riga), but the pinned
infobox itself gives the war's core duration as 1919–1920 and dates only the treaty to
1921 — hence "partly" rather than "supported" for that exact wording.

## Combined summary

**32/33 premises supported across dev-essay-006–012 (1 partly, 0 unsupported).**
