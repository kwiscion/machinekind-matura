"""Independent MALFORMED SYNTHETIC essay outputs for the #80 contract tests (no model produced them).

Hand-written by the #80 worker (Claude, 2026-09-26) for mechanical tests only; provenance: synthetic.
Every case targets DEV fixture dev-essay-001 (topic 1: Kazimierz III Wielki; aspects polityczny,
gospodarczy, kulturalny). The prose is generic and deliberately simple; it is not graded content.
"""

from __future__ import annotations

import json

TOPIC = 1
ITEM = "dev-essay-001"

INTRO = ("Panowanie Kazimierza III Wielkiego w latach 1333–1370 było okresem, w którym państwo polskie "
         "zostało wewnętrznie scalone i wzmocnione. Uważam, że był to najważniejszy etap odbudowy Królestwa "
         "po rozbiciu dzielnicowym.")
POL = ("W aspekcie politycznym król zawarł w 1335 roku układ w Wyszehradzie, a w 1343 roku pokój w Kaliszu "
       "z zakonem krzyżackim, dzięki któremu odzyskał Kujawy i ziemię dobrzyńską. Ujednolicił też prawo, "
       "wydając statuty wiślicko-piotrkowskie, co umacniało władzę monarchy w całym kraju. ")
GOS = ("W aspekcie gospodarczym rozwijano miasta i handel, lokowano nowe osady na prawie niemieckim i "
       "reformowano skarbowość, między innymi przez wprowadzenie grosza krakowskiego. Kupcy korzystali z "
       "przywilejów, a żupy solne w Wieliczce i Bochni przynosiły skarbowi stały dochód. ")
KUL = ("W aspekcie kulturalnym najważniejsze było założenie w 1364 roku Akademii Krakowskiej, pierwszego "
       "uniwersytetu w Polsce. Wznoszono też murowane zamki, kościoły i mury miejskie, stąd powiedzenie, że "
       "król zastał Polskę drewnianą, a zostawił murowaną. ")
END = ("Podsumowując, polityka, gospodarka i kultura czasów Kazimierza Wielkiego potwierdzają tezę, że jego "
       "panowanie trwale wzmocniło państwo polskie i przygotowało je do roli, jaką odegrało w epoce Jagiellonów.")


def essay(repeat: int = 3) -> str:
    return "\n\n".join([INTRO, POL * repeat, GOS * repeat, KUL * repeat, END])


def as_json(body: str, topic: int = TOPIC) -> str:
    return json.dumps({"topic_id": topic, "body": body}, ensure_ascii=False)


KONST = ("W 1791 roku uchwalono Konstytucję trzeciego maja, która ograniczała liberum veto i wzmacniała "
         "władzę wykonawczą.")  # the lead's regression sentence (content, not a heading)
UNIA = "Unia lubelska została zawarta w 1569 roku."  # the lead's regression sentence

LEGIT_OTO = ("Oto jeden z najważniejszych okresów w dziejach średniowiecznej Polski: panowanie Kazimierza III "
             "Wielkiego w latach 1333–1370 przyniosło scalenie Królestwa. " + INTRO)

CASES = {
    # all three topics answered in one output (the organizer-Bielik failure shape)
    "all_topics": as_json("Temat 1\n\n" + essay(1) + "\n\nTemat 2\n\nUnia lubelska z 1569 roku utworzyła "
                          "Rzeczpospolitą Obojga Narodów ze wspólnym sejmem i królem.\n\nTemat 3\n\nTrzeci temat "
                          "dotyczy innego zagadnienia i jest tu omówiony skrótowo."),
    # conversational preamble + topic header before a valid essay
    "preamble": as_json("Oto moja odpowiedź na temat nr 1:\n\nTemat nr 1\n\n" + essay(3)),
    # preamble outside the JSON object (a thin wrapper, unambiguous)
    "preamble_outside_json": "Oczywiście! Oto wypracowanie w wymaganym formacie:\n" + as_json(essay(3)),
    # clean essay but far below the minimum length
    "underlength": as_json("\n\n".join([INTRO, POL, END])),
    # legitimate prose that starts like a wrapper ("Oto ...") and a thesis label: must be kept
    "legit_oto": as_json(LEGIT_OTO + "\n\n" + "\n\n".join([POL * 3, GOS * 3, KUL * 3, END])),
    # not JSON at all / broken JSON
    "invalid_json": '{"topic_id": 1, "body": "Panowanie Kazimierza III Wielkiego było ważne... ',
    "plain_text": essay(3),
    # grader comments, word count and an offer after the essay; a plan before it
    "grader_comments": as_json(essay(3) + "\n\nLiczba słów: 468\n\nKomentarz dla egzaminatora: praca spełnia "
                               "wszystkie wymagania formalne.\n\nMam nadzieję, że to pomoże!"),
    "plan_first": as_json("Plan:\n- Wstęp i teza\n- Aspekt polityczny\n- Aspekt gospodarczy\n- Aspekt kulturalny\n"
                          "- Zakończenie\n\n" + essay(3)),
    # an extra essay on another topic appended after the right one
    "extra_essay": as_json(essay(3) + "\n\nTemat 2\n\nUnia lubelska z 1569 roku połączyła Koronę i Litwę."),
    # the wrong topic id in the JSON
    "wrong_topic_id": as_json(essay(3), topic=2),
    # a required aspect is never discussed
    "missing_aspect": as_json("\n\n".join([INTRO, POL * 4, GOS * 4, END])),
    # a labelled conclusion with historical content: removing it would delete prose -> regenerate
    "labelled_conclusion": as_json(essay(3) + "\n\nOcena: panowanie z lat 1333–1370 wzmocniło Królestwo."),
    # two JSON objects (two answers)
    "two_json": as_json(essay(3)) + "\n" + as_json(essay(3), topic=2),
    # v2 regressions from the root review of PR119 (issue #80 comment 5848806894):
    # a complete factual sentence formatted as a Markdown heading must be KEPT (marker stripped)
    "heading_sentence": as_json("\n\n".join([INTRO, POL * 3, "# " + KONST, GOS * 3, KUL * 3, END])),
    # a substantive sentence after valid JSON is not a wrapper, whatever its length
    "fact_after_json": as_json(essay(3)) + "\n" + UNIA,
    # the same without a date: still unrecognized text -> reject
    "prose_after_json": as_json(essay(3)) + "\nTo była epoka, która trwale zmieniła państwo.",
    # structural headings (whitelisted labels) are removed, the prose stays
    "structural_headings": as_json("\n\n".join(["## Wstęp", INTRO, "**Aspekt 1 – polityczny**", POL * 3,
                                                 "### Aspekt gospodarczy", GOS * 3, "Aspekt kulturalny:", KUL * 3,
                                                 "## Zakończenie", END])),
    # a short non-whitelisted title is neither a label nor a sentence -> ambiguous, regenerate
    "title_heading": as_json("# Kazimierz Wielki budowniczy państwa\n\n" + essay(3)),
    # a heading-shaped label that carries a date is content, not a label -> ambiguous
    "dated_heading": as_json("\n\n".join([INTRO, "## Aspekt polityczny 1343", POL * 3, GOS * 3, KUL * 3, END])),
    # an extra JSON field carrying prose would be silently discarded -> reject
    "extra_key_prose": json.dumps({"topic_id": TOPIC, "body": essay(3), "uwagi": UNIA}, ensure_ascii=False),
    "extra_key_count": json.dumps({"topic_id": TOPIC, "body": essay(3), "word_count": 480}, ensure_ascii=False),
    # fenced JSON with a one-clause preamble and a closing offer: all recognized wrappers
    "fenced_with_wrappers": "Jasne! Oto odpowiedź:\n```json\n" + as_json(essay(3)) + "\n```\nMam nadzieję, że to pomoże!",
}

# what the contract must do with each case
EXPECT = {
    "all_topics": {"ok": False, "trigger": "multi_topic"},
    "preamble": {"ok": True, "ops": {"preamble", "topic_header"}},
    "preamble_outside_json": {"ok": True, "wrapper": "text_around_json"},
    "underlength": {"ok": False, "trigger": "underlength"},
    "legit_oto": {"ok": True, "ops": set()},
    "invalid_json": {"ok": False, "trigger": "invalid_json"},
    "plain_text": {"ok": False, "trigger": "invalid_json"},
    "grader_comments": {"ok": True, "ops": {"trailing_meta"}},
    "plan_first": {"ok": True, "ops": {"plan"}},
    "extra_essay": {"ok": False, "trigger": "multi_topic"},
    "wrong_topic_id": {"ok": False, "trigger": "wrong_topic_id"},
    # v2: lexical aspect presence is advisory only; the hard gate is topic/shape/length
    "missing_aspect": {"ok": True, "advisory": "lexical_aspect_absent"},
    "labelled_conclusion": {"ok": False, "trigger": "ambiguous_trailing_block"},
    "two_json": {"ok": False, "trigger": "multiple_json_objects"},
    "heading_sentence": {"ok": True, "ops": {"heading_marker_stripped"}},
    "fact_after_json": {"ok": False, "trigger": "ambiguous_text_outside_json"},
    "prose_after_json": {"ok": False, "trigger": "ambiguous_text_outside_json"},
    "structural_headings": {"ok": True, "ops": {"heading"}},
    "title_heading": {"ok": False, "trigger": "ambiguous_heading"},
    "dated_heading": {"ok": False, "trigger": "ambiguous_heading"},
    "extra_key_prose": {"ok": False, "trigger": "substantive_extra_key"},
    "extra_key_count": {"ok": True, "wrapper": "extra_keys:word_count"},
    "fenced_with_wrappers": {"ok": True, "wrapper": "text_around_json"},
}
