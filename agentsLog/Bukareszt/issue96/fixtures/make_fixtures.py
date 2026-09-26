#!/usr/bin/env python3
"""Write the issue #96 synthetic relevance fixtures (deterministic, stdlib only).

Every source passage, bibliography and question below was written for this fixture set by the #96 worker.
Nothing is copied or paraphrased from any matura sheet, key, rubric or source pack (2023/2024/2025 or other);
the bibliographic entries are invented (authors/titles/years are fictitious) and exist only to reproduce the
query-contamination mechanism (publication years and page numbers entering the chrono year boost).
Labels (`relevant_source_ids`, `expected_route`, `expected_gate`) are the fixture author's judgement, fixed
before any ablation was run. The two answer-instruction headers are the generic templates used by the bare
validation builder and the organizer adapter (no exam content).

    python3 agentsLog/Bukareszt/issue96/fixtures/make_fixtures.py   # rewrites synthetic_fixtures.jsonl
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "synthetic_fixtures.jsonl"

BARE = (
    "Rozwiąż poniższe zadanie z egzaminu maturalnego z historii (poziom rozszerzony). "
    "Odpowiadaj po polsku, zwięźle i na podstawie źródeł zamieszczonych w zadaniu oraz własnej wiedzy. "
    "Jeżeli zadanie wymaga rozstrzygnięcia, zacznij odpowiedź od linii 'Rozstrzygnięcie: ...', "
    "a następnie podaj 'Uzasadnienie: ...'. W zadaniach typu prawda/fałsz podaj numer zdania i literę P albo F. "
    "W zadaniach zamkniętych podaj literę wybranej odpowiedzi. Obrazy stron arkusza są dołączone, jeśli zadanie "
    "zawiera materiał ikonograficzny lub kartograficzny.\n\n"
)


def organizer(question, source="", fmt="Krótka odpowiedź."):
    parts = ["Egzamin maturalny. Odpowiedz na jedno zadanie.", "Zadanie S (maks. 1 pkt)\n" + question]
    if source:
        parts.append("Materiał źródłowy:\n" + source)
    parts.append("Wymagany format odpowiedzi:\n" + fmt)
    parts.append("Przykłady w formacie odpowiedzi pokazują tylko składnię, nie są rozwiązaniem.\n"
                 "Zwróć wyłącznie końcową odpowiedź po polsku, bez rozumowania i komentarzy.")
    return "\n\n".join(parts)


F = []


def add(fid, category, prompt, relevant, route, gate, note):
    F.append({"id": fid, "split": "SYNTHETIC", "category": category, "prompt": prompt,
              "relevant_source_ids": relevant, "expected_route": route, "expected_gate": gate, "note": note})


# --- publication-year contamination: bibliography years point to an unrelated era -----------------------
add("syn-pub-01", "pub_year_contamination", BARE + (
    "Zadanie 1. (0–1)\nTekst źródłowy\nSzlachta różnych wyznań zobowiązała się, że spory o wiarę nie będą "
    "prowadzić do rozlewu krwi ani do konfiskaty dóbr, a przyszły król ma to zaprzysiąc.\n"
    "Za: J. Wiśniewski, Wybór tekstów do dziejów sejmu, Warszawa 1945, s. 112.\n"
    "Podaj nazwę aktu, którego fragment przytoczono, oraz rok jego uchwalenia."),
    ["plwiki-konfederacja-warszawska", "plws-akt-konfederacji-warszawskiej-1573", "plwiki-artykuly-henrykowskie"],
    "mixed", "retrieve", "publication year 1945 would boost WWII chunks")
add("syn-pub-02", "pub_year_contamination", BARE + (
    "Zadanie 2. (0–2)\nTekst źródłowy\nPo zwycięstwie w polu wielki mistrz zakonu poległ, a król nie ruszył "
    "od razu na stolicę zakonu, co później wypominali mu kronikarze.\n"
    "Za: A. Lis, Średniowiecze w źródłach, Kraków 1990, s. 45.\n"
    "Wyjaśnij, dlaczego zwycięstwo opisane w tekście nie przyniosło zdobycia Malborka. Odwołaj się do własnej wiedzy."),
    ["plwiki-bitwa-pod-grunwaldem"], "mixed", "retrieve", "1990 has 41 graph chunks (late PRL/III RP)")
add("syn-pub-03", "pub_year_contamination", BARE + (
    "Zadanie 3. (0–1)\nTekst źródłowy\nPosłowie zebrani w stolicy obradowali dłużej niż zwykle; w końcu przyjęli "
    "ustawę, która znosiła liberum veto i wprowadzała trójpodział władzy.\n"
    "Źródło: M. Kot, Parlamentaryzm dawnej Rzeczypospolitej, Wrocław 1998, t. 2, s. 233.\n"
    "Podaj nazwę sejmu, o którym mowa w tekście."),
    ["plwiki-sejm-wielki", "plwiki-konstytucja-3-maja", "plws-konstytucja-3-maja-1791"],
    "mixed", "retrieve", "1998 boosts NATO/UE; page 233 is a 3-digit pseudo-year")
add("syn-pub-04", "pub_year_contamination", BARE + (
    "Zadanie 4. (0–1)\nTekst źródłowy\nObradujący w Wiedniu monarchowie i ministrowie ustalili nowe granice, "
    "a z części ziem polskich utworzono królestwo związane unią z Rosją.\n"
    "Za: P. Nowak, Europa po Napoleonie, Poznań 2001, s. 180.\n"
    "Podaj nazwę państwa utworzonego na mocy postanowień opisanych w tekście."),
    ["plwiki-kongres-wiedenski", "plwiki-krolestwo-polskie-kongresowe"], "mixed", "retrieve",
    "2001 boosts EU/NATO; 180 pseudo-year")
add("syn-pub-05", "pub_year_contamination", BARE + (
    "Zadanie 5. (0–1)\nTekst źródłowy\nRobotnicy stoczni ogłosili strajk okupacyjny i przedstawili władzom "
    "listę postulatów, wśród których pierwszy dotyczył wolnych związków zawodowych.\n"
    "Za: K. Zając, Kronika PRL, Lublin 1969, s. 301.\n"
    "Podaj nazwę porozumienia, którym zakończył się opisany strajk."),
    ["plwiki-porozumienia-sierpniowe", "plwiki-solidarnosc"], "mixed", "retrieve",
    "fictitious 1969 edition predates the event: publication year must not steer chronology")

# --- bibliography carries useful topic words (whole-line deletion should lose the hit) ------------------
add("syn-bib-01", "useful_bibliography", BARE + (
    "Zadanie 6. (0–1)\nTekst źródłowy\nOd tego dnia oba narody mają jednego władcę, wybieranego wspólnie, "
    "jeden sejm i wspólną monetę, lecz każdy zachowa swój skarb, urzędy i wojsko.\n"
    "Za: T. Wrona, Unia lubelska i jej skutki, Lublin 1969, s. 14.\n"
    "Oceń, czy opisany akt prowadził do powstania państwa federacyjnego. Uzasadnij odpowiedź."),
    ["plwiki-unia-lubelska"], "mixed", "retrieve", "the topic appears only in the bibliography title")
add("syn-bib-02", "useful_bibliography", BARE + (
    "Zadanie 7. (0–1)\nTekst źródłowy\nKsiążę przyjął nową wiarę razem z drużyną; odtąd na jego dworze pojawili "
    "się duchowni przybyli z południa.\n"
    "Za: E. Sowa, Chrzest Polski w kronikach, Gniezno 1966, s. 7.\n"
    "Wyjaśnij jedną polityczną przyczynę decyzji władcy opisanej w tekście."),
    ["plwiki-chrzest-polski", "plwiki-mieszko-i"], "mixed", "retrieve",
    "topic words in the bibliography title; fictitious 1966 millennium edition")
add("syn-bib-03", "useful_bibliography", BARE + (
    "Zadanie 8. (0–1)\nTekst źródłowy\nOskarżony zakonnik nie odwołał swoich twierdzeń i oświadczył, że sumienie "
    "wiąże go tylko słowem Pisma.\n"
    "Za: R. Kruk, Marcin Luter i sejm w Wormacji, Warszawa 1983, s. 58.\n"
    "Podaj nazwę ruchu religijnego zapoczątkowanego przez postać opisaną w tekście."),
    ["plwiki-reformacja", "plwiki-marcin-luter"], "mixed", "retrieve", "topic words in bibliography title")

# --- BCE and ambiguous dates -------------------------------------------------------------------------------
add("syn-bce-01", "bce_date", BARE + (
    "Zadanie 9. (0–1)\nW 490 p.n.e. na równinie nad morzem hoplici ateńscy pokonali wojska wysłane przez króla "
    "Dariusza.\nPodaj nazwę konfliktu, w którego trakcie doszło do opisanej bitwy."),
    ["plwiki-wojny-perskie"], "external_fact", "retrieve", "490 BCE must not boost 490 CE chunks")
add("syn-bce-02", "bce_date", BARE + (
    "Zadanie 10. (0–1)\nW 336 p.n.e. władzę w Macedonii objął syn Filipa II, który następnie wyruszył na podbój "
    "imperium perskiego.\nPodaj imię tego władcy."),
    ["plwiki-aleksander-macedonski"], "external_fact", "retrieve", "BCE year; graph has no BCE sign")
add("syn-bce-03", "bce_date", BARE + (
    "Zadanie 11. (0–1)\nWedług tradycji w 509 p.n.e. mieszkańcy miasta nad Tybrem wypędzili ostatniego króla "
    "i powierzyli władzę dwóm corocznie wybieranym urzędnikom.\nPodaj nazwę ustroju, który wtedy powstał."),
    ["plwiki-republika-rzymska"], "external_fact", "retrieve", "509 BCE vs 509 CE chunks")
add("syn-bce-04", "bce_date", BARE + (
    "Zadanie 12. (0–1)\nW XVIII w. p.n.e. władca Babilonu kazał wyryć prawa na kamiennej steli.\n"
    "Podaj nazwę tego zbioru praw."),
    ["plwiki-kodeks-hammurabiego"], "external_fact", "retrieve", "century-only BCE; no year may be invented")
add("syn-amb-01", "ambiguous_date", BARE + (
    "Zadanie 13. (0–1)\nW 1920 r. wojska polskie powstrzymały ofensywę Armii Czerwonej pod stolicą, a rok później "
    "zawarto pokój.\nPodaj nazwę traktatu, który zakończył tę wojnę."),
    ["plwiki-traktat-ryski", "plwiki-wojna-polsko-bolszewicka"], "external_fact", "retrieve",
    "event year 1920 must remain; the answer event is 1921 and not explicit")
add("syn-amb-02", "ambiguous_date", BARE + (
    "Zadanie 14. (0–1)\nW połowie XVII wieku armia króla szwedzkiego zajęła większość ziem Korony, a obrona "
    "jasnogórskiego klasztoru stała się symbolem oporu.\nPodaj nazwę tego najazdu."),
    ["plwiki-potop-szwedzki"], "external_fact", "retrieve", "century only; no invented year")
add("syn-amb-03", "ambiguous_date", organizer(
    "Na podstawie tekstu i własnej wiedzy podaj nazwę powstania, którego dotyczy manifest.",
    "Wzywamy wszystkich synów Polski do broni; od dziś każdy rolnik staje się właścicielem ziemi, którą uprawia.\n"
    "Za: B. Gil, Odezwy i manifesty XIX wieku, Warszawa 1963, s. 90.", "Nazwa powstania."),
    ["plwiki-powstanie-styczniowe", "plws-manifest-22-stycznia-1863"], "mixed", "retrieve",
    "fictitious 1963 edition = centenary; organizer-style header/footer")

# --- plain external facts with the organizer header (header regression) ------------------------------------
add("syn-ext-01", "external_fact", organizer("Podaj nazwę okresu w dziejach Polski, który rozpoczął się po śmierci "
    "Bolesława Krzywoustego."), ["plwiki-rozbicie-dzielnicowe", "plwiki-boleslaw-krzywousty"], "external_fact",
    "retrieve", "organizer template around a plain fact question")
add("syn-ext-02", "external_fact", organizer("Podaj nazwę dokumentu z 1215 roku, który ograniczył władzę króla Anglii "
    "wobec baronów."), ["plwiki-wielka-karta-swobod"], "external_fact", "retrieve", "event year 1215 in question")
add("syn-ext-03", "external_fact", BARE + "Zadanie 15. (0–1)\nWyjaśnij, czym była praca organiczna i podaj jeden jej "
    "przykład z zaboru pruskiego.", ["plwiki-praca-organiczna"], "external_fact", "retrieve", "bare header")
add("syn-ext-04", "external_fact", BARE + "Zadanie 16. (0–1)\nPodaj nazwę planu pomocy gospodarczej USA dla Europy "
    "ogłoszonego po II wojnie światowej.", ["plwiki-plan-marshalla"], "external_fact", "retrieve",
    "bare header; a header noun 'źródeł' is irrelevant")

# --- supplied-source only (router must NOT retrieve) ----------------------------------------------------------
add("syn-src-01", "supplied_source", BARE + (
    "Zadanie 17. (0–1)\nTekst źródłowy\nW mieście było trzy tysiące domów, z czego połowa spłonęła w pożarze; "
    "kupcy odbudowali rynek w ciągu dwóch lat.\nZa: H. Mazur, Miasta i pożary, Toruń 1987, s. 12.\n"
    "Na podstawie tekstu podaj, ile domów spłonęło w pożarze."), [], "supplied_source", "abstain",
    "answer is inside the supplied text")
add("syn-src-02", "supplied_source", BARE + (
    "Zadanie 18. (0–1)\nTekst 1.\nAutor twierdzi, że reformy przyniosły wzrost dochodów skarbu.\nTekst 2.\n"
    "Autor uważa, że reformy doprowadziły do zubożenia chłopów.\n"
    "Porównaj oceny reform przedstawione w obu tekstach. Wskaż jedną różnicę."), [], "supplied_source", "abstain",
    "source comparison only")
add("syn-src-03", "supplied_source", BARE + (
    "Zadanie 19. (0–1)\nIlustracja przedstawia plakat z hasłem wzywającym do pracy przy odbudowie.\n"
    "Na podstawie ilustracji wypisz hasło umieszczone na plakacie."), [], "supplied_source", "abstain",
    "visual source extraction")

# --- outside the pinned corpus (gate must abstain) -------------------------------------------------------------
add("syn-ooc-01", "out_of_corpus", BARE + "Zadanie 20. (0–1)\nPodaj nazwę okresu reform w Japonii, rozpoczętego w 1868 "
    "roku, który doprowadził do modernizacji cesarstwa.", [], "external_fact", "abstain", "Japan not in corpus")
add("syn-ooc-02", "out_of_corpus", BARE + "Zadanie 21. (0–1)\nPodaj nazwę dynastii chińskiej, za której panowania "
    "zbudowano Zakazane Miasto.", [], "external_fact", "abstain", "China not in corpus")
add("syn-ooc-03", "out_of_corpus", BARE + "Zadanie 22. (0–1)\nWyjaśnij, jaki był cel budowy Kanału Sueskiego otwartego "
    "w 1869 roku.", [], "external_fact", "abstain", "Suez not in corpus")
add("syn-ooc-04", "out_of_corpus", BARE + "Zadanie 23. (0–1)\nPodaj imię faraona, dla którego wzniesiono największą "
    "piramidę w Gizie.", [], "external_fact", "abstain", "Egypt not in corpus")

# --- essays (excluded from RAG initially) -------------------------------------------------------------------
add("syn-ess-01", "essay", BARE + (
    "Zadanie 24. (0–15)\nNapisz wypracowanie na temat: Scharakteryzuj przemiany ustrojowe Rzeczypospolitej w XVI "
    "wieku. W wypracowaniu uwzględnij co najmniej trzy aspekty."), [], "essay", "abstain", "essay excluded")
add("syn-ess-02", "essay", organizer("Oceń skutki reform Kazimierza Wielkiego dla państwa polskiego.",
    fmt="Wypracowanie (wypowiedź argumentacyjna)."), [], "essay", "abstain", "essay via answer format")

# --- added after root's PR #104 review (19:07): same-entity/wrong-relation, source-only answer verbs, essay phrasing --
add("syn-rel-01", "wrong_relation", BARE + "Zadanie 25. (0–1)\nPodaj imię nauczyciela gry na lutni króla Stefana "
    "Batorego.", [], "external_fact", "abstain", "entity in corpus, requested relation not")
add("syn-rel-02", "wrong_relation", BARE + "Zadanie 26. (0–1)\nPodaj nazwisko rzeźbiarza, który wykonał najstarszy "
    "pomnik Bolesława Chrobrego w Gnieźnie.", [], "external_fact", "abstain", "entity in corpus, monument maker not")
add("syn-rel-03", "wrong_relation", organizer("Podaj nazwę ulubionej potrawy króla Kazimierza Wielkiego."), [],
    "external_fact", "abstain", "entity in corpus, no-answer relation")
add("syn-rel-04", "wrong_relation", BARE + "Zadanie 27. (0–1)\nPodaj imię konia, na którym Mieszko I przybył na "
    "swój chrzest.", [], "external_fact", "abstain", "same entity + event, invented relation")
add("syn-src-04", "supplied_source", BARE + (
    "Zadanie 28. (0–1)\nTekst źródłowy\nWędrowiec usiadł pod starym dębem przy drodze i czekał na kupców z miasta.\n"
    "Na podstawie tekstu podaj nazwę drzewa, pod którym usiadł wędrowiec."), [], "supplied_source", "abstain",
    "answer verb 'podaj nazwę' restricted to the text")
add("syn-src-05", "supplied_source", BARE + (
    "Zadanie 29. (0–1)\nTekst źródłowy\nKupcy opuścili miasto, gdy rada podniosła cła na sól i sukno.\n"
    "Na podstawie tekstu wyjaśnij, dlaczego kupcy opuścili miasto."), [], "supplied_source", "abstain",
    "'wyjaśnij' restricted to the text")
add("syn-ess-03", "essay", BARE + "Zadanie 30.\nNapisz rozprawkę na temat znaczenia unii Polski z Litwą. Twoja praca "
    "powinna liczyć co najmniej 300 słów. Sformułuj tezę, podaj argumenty i zakończenie.", [], "essay", "abstain",
    "rozprawka + word count")
add("syn-ess-04", "essay", organizer("Przedstaw w dłuższej wypowiedzi przyczyny upadku Rzeczypospolitej w XVIII "
    "wieku.", fmt="Tekst ciągły."), [], "essay", "abstain", "long-form phrasing without the word wypracowanie")
add("syn-ess-05", "essay", BARE + "Zadanie 31.\nOceń politykę Kazimierza Wielkiego. Napisz tekst (około 250 słów), "
    "w którym sformułujesz tezę i podasz argumenty.", [], "essay", "abstain", "word count + thesis/arguments")

if __name__ == "__main__":
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in F), encoding="utf-8")
    print(f"wrote {len(F)} fixtures -> {OUT}")
