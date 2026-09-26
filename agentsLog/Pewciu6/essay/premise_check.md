# Premise Check — dev_fixtures.jsonl (essay topics)

- **Checker**: independent Claude Sonnet subagent (not the prompt author)
- **Date**: 2026-09-26
- **Method**: WebFetch of each cited source's pinned `oldid` revision (pl.wikipedia.org, public, free) from `data/przemeknowak781/sources.jsonl`. Asked only for the specific date/name facts embedded in the topic wording. No source text copied beyond short (<=15-word) locator phrases.
- **Scope**: factual premises embedded in the topic wording only (dates/ranges, event/person names, that the named event existed and matches the stated dates). Historical facts not stated in the prompt (e.g. Akademia Krakowska founding year) were out of scope and not checked.

| Fixture ID | Topic | Premise checked | Source ID (oldid) | Verdict | Note / locator |
|---|---|---|---|---|---|
| dev-essay-001 | 1. Kazimierz III Wielki | "panowania Kazimierza III Wielkiego (1333–1370)" | src-plwiki-kazimierz-iii-wielki (oldid=80516899) | supported | "król Polski w latach 1333–1370" |
| dev-essay-001 | 2. Unia lubelska | "unii lubelskiej zawartej w 1569 roku" | src-plwiki-unia-lubelska (oldid=80758426) | supported | union concluded 1569 |
| dev-essay-002 | 1. Potop szwedzki | "potopu szwedzkiego (1655–1660)" | src-plwiki-potop-szwedzki (oldid=79761633) | supported | "Wojna polsko-szwedzka (1655–1660)... potop szwedzki" |
| dev-essay-002 | 2. Powstanie listopadowe | "powstania listopadowego (1830–1831)" | src-plwiki-powstanie-listopadowe (oldid=80808124) | supported | began night 29/30 Nov 1830, ended 21 Oct 1831 |
| dev-essay-003 | 1. Stanisław August Poniatowski | "panowania Stanisława Augusta Poniatowskiego (1764–1795)" | src-plwiki-stanislaw-august-poniatowski (oldid=80466808) | supported | "król Polski w latach 1764–1795" |
| dev-essay-003 | 2. Polityka pruska vs rosyjska wobec Polaków (2. poł. XIX w.) | that a Prussian anti-Polish policy and a Russian anti-Polish policy both existed in the 2nd half of the 19th c. | src-plwiki-kulturkampf (oldid=79686870); src-plwiki-rusyfikacja (oldid=77703362) | supported | Kulturkampf 1871–1878 (Prussia/German Empire, anti-Polish in Prussian partition); Russification intensified through 19th c., esp. post-1863 |
| dev-essay-004 | 1. Powstanie styczniowe | "powstania styczniowego (1863–1864)" | src-plwiki-powstanie-styczniowe (oldid=80712129) | supported | began 22 Jan 1863, lasted "do jesieni 1864" |
| dev-essay-004 | 2. Przemiany ustroju II RP 1921–1935 | that constitutional/system changes occurred within 1921–1935, bounded by named events | src-plwiki-konstytucja-marcowa (oldid=80733076); src-plwiki-przewrot-majowy (oldid=80117142); src-plwiki-konstytucja-kwietniowa (oldid=79919558) | supported | March Constitution adopted 1921; May Coup 12–15 May 1926; April Constitution signed 23 Apr 1935 — all within the stated range |
| dev-essay-005 | 1. Polskie Państwo Podziemne | "w latach 1939–1945" | src-plwiki-polskie-panstwo-podziemne (oldid=80165141) | supported | established 27 Sep 1939, self-dissolved 1 Jul 1945 (within stated range) |
| dev-essay-005 | 2. Sierpień 1980 → Okrągły Stół 1989 | that August 1980 strikes and the 1989 Round Table both occurred as named/dated | src-plwiki-sierpien-1980 (oldid=79319929); src-plwiki-okragly-stol-polska (oldid=80186895) | supported | strikes Aug 1980 (Gdańsk Shipyard from 14 Aug); Round Table 6 Feb–5 Apr 1989 |

## Summary

- Topics checked: **10** (5 fixtures × 2 topics each)
- supported: **10**
- supported-with-caveat: **0**
- not-supported: **0**
- no-source: **0**

No not-supported premises found. All embedded dates/ranges and named events matched the cited pinned Wikipedia revisions exactly.

## Suggested wording fixes

None required — all premises as worded are factually supported by their cited sources. One minor observation (not a defect): dev-essay-005 topic 2's implied span extends slightly beyond its own polling year boundary text ("od strajków z sierpnia 1980... do... 1989"), but this matches historical convention and both endpoints are independently supported, so no change is suggested.
