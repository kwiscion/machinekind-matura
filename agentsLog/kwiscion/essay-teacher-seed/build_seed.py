"""Rebuild the eight DRAFT records from authored targets and evidence metadata."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATE = "2026-09-26"
MODEL = "OpenAI Codex teacher session; Astra requested by parent; exact runtime snapshot not independently verified"
STATUS = "synthetic_draft_pending_independent_review"

TOPICS = [
    ("solon", "history-solon-reforms", "antiquity", "Oceń, w jakim stopniu reformy Solona ograniczyły konflikt społeczny w Atenach. Rozważ ochronę wolności osobistej, dostęp do życia politycznego i granice kompromisu.", ["wiki-solon", "mit-aristotle"], ["Solon", "Solonian reforms", "seisachtheia", "reformy Solona", "Athenian Constitution parts 2-14"]),
    ("casimir", "history-casimir-iii-statebuilding", "middle_ages", "Wyjaśnij, jak dyplomacja i działania wewnętrzne Kazimierza Wielkiego wzajemnie wspierały wzmacnianie Królestwa Polskiego. Uwzględnij obronność, prawo i szkolnictwo.", ["wiki-casimir", "uj-archive"], ["Casimir III the Great", "Kazimierz Wielki", "Kazimierz III", "University of Krakow foundation 1364", "UJ foundation"]),
    ("lublin", "history-lublin-union-1569", "early_modern", "Oceń unię lubelską jako kompromis między integracją Polski i Litwy a zachowaniem odrębności. Powiąż przyczyny porozumienia, sposób jego zawarcia i rozwiązania ustrojowe.", ["wiki-lublin", "agad-lublin"], ["Union of Lublin", "Unia lubelska", "Liublino unija", "Lublin union 1569", "AGAD parchment 5627"]),
    ("january", "history-january-uprising-peasant-policy", "nineteenth_century", "Wyjaśnij znaczenie kwestii chłopskiej dla strategii powstania styczniowego. Oceń relację między programem uwłaszczeniowym, jego wykonaniem i polityką rosyjską w latach 1863–1864.", ["wiki-january"], ["January Uprising", "Powstanie styczniowe", "1863 uprising", "peasant reform Congress Poland 1864", "uwłaszczenie 1864"]),
]

# Each tuple: actor; event/factual claim; date; consequence (explicit fact or synthesis);
# source locator; kind; essay paragraphs (one-based). No copied source passages.
CARDS = {
 "solon": [
  ("Solon", "Objęcie archontatu tradycyjnie datowane na 594 p.n.e.", "594 BCE (traditional)", "Działalność w czasie konfliktu społecznego.", "wiki-solon#Archonship; mit-aristotle part 5", "fact", [2]),
  ("Dłużnicy ateńscy", "Zabezpieczanie długu osobą dłużnika groziło niewolą.", "before Solon's reforms", "Zależność ekonomiczna zagrażała wolności osobistej.", "wiki-solon#Seisachtheia; mit-aristotle part 2", "fact", [2]),
  ("Solon", "Tradycja przypisuje seisachthei zniesienie długów, uwolnienie Ateńczyków zniewolonych za długi i zakaz takich zabezpieczeń na przyszłość.", "early sixth century BCE", "Ochrona obywateli przed niewolą za długi; zakres historyczny pozostaje przedmiotem debaty.", "wiki-solon#Seisachtheia; mit-aristotle parts 6, 12", "fact_with_source_uncertainty", [3]),
  ("Obywatele Aten", "Cztery klasy majątkowe różnicowały dostęp do urzędów; teci nie mogli ich sprawować.", "Solonian settlement", "Poszerzenie dostępu nie oznaczało równości politycznej.", "wiki-solon#Classes; mit-aristotle part 7", "fact_and_inference", [4]),
  ("Obywatele, w tym teci", "Tradycja przypisuje Solonowi udział ogółu obywateli w zgromadzeniu i sądach.", "Solonian settlement", "Możliwa podstawa późniejszej kontroli władzy, nie gotowa demokracja klasyczna.", "wiki-solon#Constitutional; mit-aristotle parts 7, 9", "fact_and_inference", [5]),
  ("Późniejsi autorzy starożytni", "Świadectwa o reformach są późne i fragmentaryczne; ich szczegóły są dyskutowane.", "later transmission", "Ostrożność wobec przenoszenia późniejszych instytucji w czasy Solona.", "wiki-solon lead; Solon's reforms", "fact", [5]),
  ("Pizystrat", "Po reformach trwały konflikty i ostatecznie ustanowiono tyranię.", "after Solon", "Kompromis nie zapewnił trwałego pokoju; ocena długofalowego znaczenia jest syntezą autora.", "wiki-solon#Travels; mit-aristotle parts 13-14", "fact_and_inference", [1,6]),
 ],
 "casimir": [
  ("Kazimierz III", "Objął władzę w 1333 roku w trudnym położeniu politycznym.", "1333", "Konieczność ustalenia priorytetów jest interpretacją sytuacji.", "wiki-casimir#Reign", "fact_and_inference", [1,2]),
  ("Jan Luksemburski; zakon krzyżacki; Węgry", "Pretensje czeskie i spór z zakonem współistniały z sojuszem węgierskim.", "early reign", "Dyplomacja ograniczała zagrożenia; jej związek z reformami to synteza.", "wiki-casimir#Reign, opening diplomatic paragraphs", "fact_and_inference", [2]),
  ("Kazimierz III", "Budowano zamki i miejskie mury obronne.", "reign 1333-1370", "Wzmocnienie obronności; materialna obecność władzy jest interpretacją.", "wiki-casimir#Reign, fortifications paragraph", "fact_and_inference", [3]),
  ("Kazimierz III", "Porządkowano prawo w statutach dla Wielkopolski i Małopolski.", "fourteenth century; precise dating intentionally omitted", "Regionalna odrębność pokazuje stopniowy charakter integracji; przewidywalność prawa to argument interpretacyjny.", "wiki-casimir#Reforms", "fact_and_inference", [4]),
  ("Kazimierz III", "Ufundował uniwersytet w Krakowie w 1364 roku.", "1364 (UJ archive specifies 12 May)", "Powstanie możliwości kształcenia, bez twierdzenia o natychmiastowym pełnym funkcjonowaniu uczelni.", "wiki-casimir#Reforms; uj-archive#Historia Uniwersytetu / Czasy dawne", "fact_and_inference", [5]),
  ("Kazimierz III", "Ekspansja na Ruś rozszerzyła terytorium i dostęp do kierunku handlu czarnomorskiego.", "reign 1333-1370", "Zmiana kierunku ekspansji jako przykład ustalania priorytetów jest syntezą.", "wiki-casimir#Politics_and_expansion", "fact_and_inference", [6]),
  ("Monarchia Kazimierza", "Powiązanie dyplomacji, prawa, edukacji i obronności w spójny argument o sile państwa.", "reign 1333-1370", "Teza autorska, a nie cytat ani przyjęty z góry werdykt źródła.", "all preceding casimir evidence cards", "author_synthesis", [1,6]),
 ],
 "lublin": [
  ("Zygmunt II August", "Brak potomstwa uzasadniał dążenie do utrwalenia związku poza więzią dynastyczną.", "1569", "Potrzeba trwałych zasad wspólnej monarchii.", "wiki-lublin#Background", "fact_and_inference", [2]),
  ("Wielkie Księstwo Litewskie", "Zagrożenie moskiewskie i wojna sprzyjały dążeniu do ściślejszej współpracy.", "mid-sixteenth century", "Bezpieczeństwo wiązało się z debatą ustrojową.", "wiki-lublin#Background", "fact_and_inference", [2]),
  ("Magnateria litewska; Zygmunt August", "Obawy magnatów i wyjazd większości delegacji poprzedziły królewskie inkorporacje Podlasia, Wołynia, Bracławszczyzny i Kijowszczyzny.", "1569 negotiations", "Nacisk polityczny zmienił warunki porozumienia; nie przypisano wszystkim inkorporacjom jednej daty.", "wiki-lublin#Background; Sejm of 1569", "fact_and_inference", [3]),
  ("Strony unii", "Akt z 1 lipca 1569 ustanowił wspólnego wybieranego władcę, sejm i wspólną politykę zagraniczną.", "1569-07-01", "Instytucjonalizacja współdziałania wykraczająca poza samą osobę monarchy.", "wiki-lublin lead / Political; agad-lublin opening archival description", "fact_and_inference", [1,4]),
  ("Wielkie Księstwo Litewskie", "Zachowało osobne prawo, urzędy, skarb i wojsko.", "1569 settlement", "Unia nie była pełnym administracyjnym zespoleniem.", "wiki-lublin#Political; Military; Legal", "fact_and_inference", [5]),
  ("Szlachta", "Formalne prawa polityczne dotyczyły stanu szlacheckiego, nie całej ludności.", "Commonwealth settlement", "Nie należy utożsamiać wspólnoty politycznej z powszechną równością.", "wiki-lublin#Cultural; Political", "fact_and_inference", [5]),
  ("Polska i Litwa", "Ocena unii jako integracji połączonej z kompromisem i naciskiem.", "1569 and institutional aftermath", "Autorska synteza korzyści i ograniczeń, bez tezy o nieuchronnej późniejszej klęsce.", "preceding lublin evidence cards", "author_synthesis", [1,6]),
 ],
 "january": [
  ("Czerwoni; ziemianie", "Spór społeczny obejmował warunki uwłaszczenia oraz odszkodowania.", "before January 1863", "Powiązanie reformy z poparciem społecznym.", "wiki-january#Background", "fact_and_inference", [2]),
  ("Powstańczy rząd tymczasowy", "Na początku walk ogłoszono własność użytkowanej ziemi dla chłopów i odszkodowanie ziemian ze środków państwa.", "January 1863", "Próba pogodzenia emancypacji chłopów z interesem właścicieli.", "wiki-january#Call_to_arms_in_the_Kingdom_of_Poland", "fact_and_inference", [3]),
  ("Oddziały powstańcze", "Przeważała partyzantka, występowały niedostatki uzbrojenia i przewaga wojsk rosyjskich.", "1863-1864", "Ograniczona możliwość egzekwowania reform to wniosek z warunków działania.", "wiki-january lead; Call to arms in the Kingdom of Poland", "fact_and_inference", [4]),
  ("Chłopi", "Udział chłopów występował, lecz mobilizacja nie była powszechna i zależała od warunków lokalnych.", "1863-1864", "Unikanie uogólnienia o całkowitej bierności wsi.", "wiki-january#Uprising_spreads_to_Lithuania; Evolution of events", "fact_with_regional_caution", [4]),
  ("Romuald Traugutt", "Objął kierownictwo jesienią 1863; reorganizował walkę i dążył do realizacji polityki uwłaszczeniowej.", "October 1863 onward", "Związek reformy społecznej ze strategią mobilizacji.", "wiki-january#Romuald_Traugutt", "fact_and_inference", [5]),
  ("Mocarstwa zachodnie", "Oczekiwana interwencja wojskowa nie nastąpiła.", "1863-1864", "Brak zewnętrznego rozstrzygnięcia wojny na korzyść powstańców.", "wiki-january#Evolution_of_events; Call to arms in the Kingdom of Poland", "fact", [5]),
  ("Aleksander II", "Carskie uwłaszczenie w Królestwie Polskim wprowadzono 2 marca 1864.", "1864-03-02 Gregorian", "Osłabiało mobilizacyjną siłę programu powstańczego.", "wiki-january lead; Romuald Traugutt", "fact_and_inference", [6]),
  ("Powstanie styczniowe", "Powstanie zakończyło się klęską militarną, mimo trwałej zmiany stosunków własnościowych.", "1864", "Ocena reformy jako emancypacji i politycznej rywalizacji stanowi autorską syntezę.", "wiki-january lead", "fact_and_inference", [1,6]),
 ],
}

def write_jsonl(name, records):
    (ROOT / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

def count(text):
    return len(re.findall(r"\S+", text))

def main():
    essays, repairs, evidence, groups = [], [], [], []
    for slug, group, era, question, source_ids, aliases in TOPICS:
        response = (ROOT / f"essay-{slug}.txt").read_text(encoding="utf-8").strip()
        claims = []
        for index, (actor, event, date, consequence, locator, kind, paragraphs) in enumerate(CARDS[slug], 1):
            claim = {"claim_id": f"{slug}-claim-{index:02}", "actor": actor, "event": event,
                     "date": date, "consequence": consequence, "evidence_locator": locator,
                     "support_type": kind, "essay_paragraphs": paragraphs,
                     "source_ids": [sid for sid in source_ids if sid in locator] or source_ids, "source_group_id": group,
                     "review_status": "generator_checked_pending_independent_review"}
            claims.append(claim)
            evidence.append(claim)
        prompt = question + " Napisz jedno spójne wypracowanie po polsku, liczące 400–500 słów. Zwróć wyłącznie tekst wypracowania, bez tytułu, planu, komentarza do zadania ani innych tematów."
        row = {"id": "astra-seed-essay-" + slug, "source_group_id": group, "prompt": prompt,
               "response": response, "body_word_count": count(response), "fact_claims": claims,
               "source_ids": source_ids, "synthetic_model": MODEL, "generation_date": DATE,
               "status": STATUS, "era": era, "task_type": "essay", "split": None,
               "normalized_prompt_sha256": hashlib.sha256(" ".join(prompt.casefold().split()).encode()).hexdigest()}
        row["crosscheck_source_ids"] = ["mhp-peasants", "radom-peasants"] if slug == "january" else []
        essays.append(row)
        paragraphs = response.split("\n\n")
        if slug == "solon":
            defects = ["preamble", "closing_meta_comment"]
            bad = "Oczywiście! Poniżej przedstawiam gotowe wypracowanie.\n\n" + response + "\n\nMam nadzieję, że ta odpowiedź pomoże w nauce."
        elif slug == "casimir":
            defects = ["underlength"]
            bad = "\n\n".join(paragraphs[:2])
        elif slug == "lublin":
            defects = ["multiple_topic_answers", "headings"]
            # The second response is made ONLY from this essay's original prose.
            # It answers a separate narrow question in the SAME source family.
            bad = "Temat 1: Unia jako kompromis.\n\n" + response + "\n\nTemat 2: Jakie odrębności ustrojowe zachowała Litwa?\n\n" + paragraphs[4]
        else:
            defects = ["underlength", "preamble", "closing_meta_comment"]
            bad = "Wybrałem temat dotyczący kwestii chłopskiej. Oto moja odpowiedź:\n\n" + "\n\n".join(paragraphs[:2]) + "\n\nDalszą część mogę dopisać na życzenie."
        repair_prompt = ("Popraw poniższy szkic tak, aby odpowiadał wyłącznie wskazanemu tematowi. "
                         "Usuń komentarze i odpowiedzi na inne pytania. Uzupełnij zbyt krótki tekst do 400–500 słów, "
                         "zachowując poprawność historyczną. Zwróć wyłącznie gotowe wypracowanie.\n\n"
                         "Wskazany temat: " + question + "\n\nSzkic do poprawy:\n" + bad)
        repair = {**row, "id": "astra-seed-repair-" + slug, "prompt": repair_prompt,
                  "task_type": "essay_repair", "parent_essay_id": row["id"],
                  "defects": defects, "corrupted_response": bad,
                  "corrupted_response_word_count_including_wrappers": count(bad),
                  "construction": "Deterministic corruption of the paired original target; no external model output.",
                  "normalized_prompt_sha256": hashlib.sha256(" ".join(repair_prompt.casefold().split()).encode()).hexdigest()}
        repairs.append(repair)
        groups.append({"source_group_id": group, "aliases": aliases, "source_ids": source_ids,
                       "example_ids": [row["id"], repair["id"]],
                       "crosscheck_source_ids": row["crosscheck_source_ids"],
                       "split": None, "grouping_rule": "All aliases, translations, topic variants, repair inputs and duplicate targets remain together. Cross-corpus matching remains pending."})
    write_jsonl("essays.jsonl", essays)
    write_jsonl("repairs.jsonl", repairs)
    write_jsonl("evidence-cards.jsonl", evidence)
    write_jsonl("source-groups.jsonl", groups)
    print(json.dumps({"essays": len(essays), "repairs": len(repairs), "unique_targets": len(essays),
                      "evidence_cards": len(evidence), "word_counts": {r["id"]: r["body_word_count"] for r in essays}}))

if __name__ == "__main__":
    main()
