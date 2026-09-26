#!/usr/bin/env python3
"""Build adversarial SYNTHETIC output fixtures for matura_harness.py (issue #11).

Every item, key, and answer here is invented (fictional places such as "Źródłogród",
fictional years). Nothing is taken from any CKE sheet, key, or marking rubric.

Writes (deterministically) into ../fixtures/:
  adversarial_eval_keys.jsonl  synthetic keys (split DEV)
  adversarial_outputs.jsonl    raw output records exercising format/record edge cases
  adversarial_labels.jsonl     expected harness verdict per case (or expected exclusion)
  blind_essay_keys.jsonl       six synthetic essay keys for the blind two-rater dry run

Run:  python3 agentsLog/Pewciu6/harness/build_adversarial_fixtures.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(os.path.dirname(HERE), "fixtures")

# ----------------------------------------------------------------- rubric templates
CHOICE_B = {"task_type": "multiple_choice", "rubric": {"max_points": 1, "mode": "choice",
                                                        "expected_choice": ["B"]}}
CHOICE_A = {"task_type": "multiple_choice", "rubric": {"max_points": 1, "mode": "choice",
                                                        "expected_choice": ["A"]}}
CHOICE_AC = {"task_type": "multiple_choice", "rubric": {"max_points": 1, "mode": "choice",
                                                         "expected_choice": ["A", "C"]}}
ENTITY = {"task_type": "short_answer", "distractors": ["Mrokowo"],
          "rubric": {"max_points": 1, "mode": "criteria", "criteria": [
              {"criterion_id": "city", "kind": "entity", "points": 1, "any_of": ["Źródłogród"]}]}}
DATE = {"task_type": "short_answer", "expected_years": [1234],
        "rubric": {"max_points": 1, "mode": "criteria", "criteria": [
            {"criterion_id": "year", "kind": "date", "points": 1, "any_of": ["1234"]}]}}
DECISION = {"task_type": "source_analysis",
            "rubric": {"max_points": 1, "mode": "criteria", "criteria": [
                {"criterion_id": "decision", "kind": "decision", "points": 1, "gate": True,
                 "any_of": ["tak"], "options": ["tak", "nie"]}]}}
ORDER = {"task_type": "chronology", "rubric": {"max_points": 1, "mode": "order",
                                                "expected_order": ["3", "1", "2"]}}
ESSAY = {"task_type": "essay", "rubric": {"max_points": 15, "mode": "criteria", "criteria": [
    {"criterion_id": "min-words", "kind": "structure", "points": 0, "min_words": 300,
     "zeroes": ["B-coherence"]},
    {"criterion_id": "A-narrative", "kind": "content", "points": 12, "manual_only": True},
    {"criterion_id": "B-coherence", "kind": "structure", "points": 3, "manual_only": True}]}}

FILLER = "Kronikarz opisuje targi, mosty i spichlerze fikcyjnego miasta. "
LONG = "Odpowiedź: B. " + FILLER * 400  # ~3,600 words

C, I, R = "correct", "incorrect", "needs_review"

# (case id, template, output record fields, expected) ; expected is either
# (status, points, [error categories]) or {"exclusion": reason} or {"orphan": True}
CASES = [
    # --- choice format variants
    ("c-plain", CHOICE_B, {"raw_response": "B"}, (C, 1, [])),
    ("c-paren", CHOICE_B, {"raw_response": "B)"}, (C, 1, [])),
    ("c-dot", CHOICE_B, {"raw_response": "B."}, (C, 1, [])),
    ("c-lower", CHOICE_B, {"raw_response": "b"}, (C, 1, [])),
    ("c-odp", CHOICE_B, {"raw_response": "odp. B"}, (C, 1, [])),
    ("c-odp-lower", CHOICE_B, {"raw_response": "odp. b"}, (C, 1, [])),
    ("c-sentence", CHOICE_B, {"raw_response": "Prawidłowa odpowiedź to B, ponieważ kronika tak podaje."},
     (C, 1, [])),
    ("c-conj-a", CHOICE_B, {"raw_response": "A zatem poprawna jest odpowiedź B."}, (C, 1, [])),
    ("c-rejects-others", CHOICE_B,
     {"raw_response": "Odpowiedź: B. Opcja A jest błędna, C również, a D dotyczy innego wieku."},
     (C, 1, [])),
    ("c-md", CHOICE_B, {"raw_response": "**Odpowiedź: B**"}, (C, 1, [])),
    ("c-repeat", CHOICE_B, {"raw_response": "B\n\nOdpowiedź: B"}, (C, 1, [])),
    ("c-english", CHOICE_B, {"raw_response": "The answer is B."}, (C, 1, [])),
    ("c-json-str", CHOICE_B,
     {"raw_response": "{\"answer\": \"B\", \"explanation\": \"A i C odpadają.\"}"}, (C, 1, [])),
    ("c-json-fenced", CHOICE_B, {"raw_response": "```json\n{\"odpowiedz\": \"B\"}\n```"}, (C, 1, [])),
    ("c-json-obj", CHOICE_B, {"raw_response": {"answer": "B"}}, (C, 1, [])),
    ("c-openai-shape", CHOICE_B,
     {"raw_response": {"choices": [{"message": {"role": "assistant", "content": "B"}}]}}, (C, 1, [])),
    ("c-think", CHOICE_B, {"raw_response": "<think>Może A? Albo C… nie, kronika mówi o B.</think>\nB"},
     (C, 1, [])),
    ("c-overlong", CHOICE_B, {"raw_response": LONG}, (C, 1, [])),
    ("c-hedge-lub", CHOICE_B, {"raw_response": "B lub C"}, (I, 0, ["content_incorrect"])),
    ("c-hedge-slash", CHOICE_B, {"raw_response": "B/C"}, (I, 0, ["content_incorrect"])),
    ("c-hedge-marker", CHOICE_B, {"raw_response": "Odpowiedź: B albo C"}, (I, 0, ["content_incorrect"])),
    ("c-two-markers", CHOICE_B, {"raw_response": "Odpowiedź: B.\nOstatecznie odpowiedź: C."},
     (I, 0, ["content_incorrect"])),
    ("c-wrong", CHOICE_B, {"raw_response": "D"}, (I, 0, ["content_incorrect"])),
    ("c-empty", CHOICE_B, {"raw_response": ""}, (I, 0, ["abstention"])),
    ("c-null", CHOICE_B, {"raw_response": None, "error": None}, (I, 0, ["abstention"])),
    ("c-whitespace", CHOICE_B, {"raw_response": "  \n\t "}, (I, 0, ["abstention"])),
    ("c-unsure", CHOICE_B, {"raw_response": "Nie wiem, chyba B."}, (I, 0, ["abstention"])),
    ("a-letter", CHOICE_A, {"raw_response": "A"}, (C, 1, [])),
    ("a-sentence", CHOICE_A, {"raw_response": "A. Kronika wymienia tylko tę możliwość."}, (C, 1, [])),
    ("a-marker", CHOICE_A, {"raw_response": "Odpowiedź: A"}, (C, 1, [])),
    ("m-ok", CHOICE_AC, {"raw_response": "A, C"}, (C, 1, [])),
    ("m-and", CHOICE_AC, {"raw_response": "Odpowiedź: A i C"}, (C, 1, [])),
    ("m-partial", CHOICE_AC, {"raw_response": "A"}, (I, 0, ["content_incorrect"])),
    ("m-extra", CHOICE_AC, {"raw_response": "A, C, D"}, (I, 0, ["content_incorrect"])),
    # --- entity with Polish diacritics
    ("e-diac", ENTITY, {"raw_response": "Źródłogród"}, (C, 1, [])),
    ("e-nodiac", ENTITY, {"raw_response": "Zrodlogrod"}, (C, 1, [])),
    ("e-upper", ENTITY, {"raw_response": "ŹRÓDŁOGRÓD"}, (C, 1, [])),
    ("e-nfd", ENTITY, {"raw_response": "Źródłogród"}, (C, 1, [])),
    ("e-sentence", ENTITY, {"raw_response": "Chodzi o miasto Źródłogród nad rzeką."}, (C, 1, [])),
    ("e-distractor", ENTITY, {"raw_response": "Mrokowo"}, (I, 0, ["entity_confusion"])),
    ("e-hedge", ENTITY, {"raw_response": "Źródłogród albo Mrokowo"}, (R, 0, [])),
    # known limitation: inflected form is not in the key's variants -> lexical miss
    ("e-inflected", ENTITY, {"raw_response": "Źródłogrodu"}, (I, 0, ["content_incorrect"])),
    # --- dates
    ("y-ok", DATE, {"raw_response": "W roku 1234."}, (C, 1, [])),
    ("y-wrong", DATE, {"raw_response": "W roku 1243."}, (I, 0, ["chronology"])),
    ("y-hedge", DATE, {"raw_response": "1234 lub 1243"}, (R, 0, [])),
    # --- decision gate
    ("d-ok", DECISION, {"raw_response": "Rozstrzygnięcie: tak"}, (C, 1, [])),
    ("d-nodiac", DECISION, {"raw_response": "Rozstrzygniecie: Tak"}, (C, 1, [])),
    ("d-lead", DECISION, {"raw_response": "Tak, ponieważ kronika to potwierdza."}, (C, 1, [])),
    ("d-hedge", DECISION, {"raw_response": "Tak / nie"}, (I, 0, ["content_incorrect"])),
    ("d-wrong", DECISION, {"raw_response": "Rozstrzygnięcie: nie"}, (I, 0, ["content_incorrect"])),
    ("d-json", DECISION, {"raw_response": "{\"decision\": \"tak\", \"uzasadnienie\": \"...\"}"},
     (C, 1, [])),
    # --- order
    ("o-ok", ORDER, {"raw_response": "3, 1, 2"}, (C, 1, [])),
    ("o-arrow", ORDER, {"raw_response": "3 → 1 → 2"}, (C, 1, [])),
    ("o-json", ORDER, {"raw_response": "{\"order\": [3, 1, 2]}"}, (C, 1, [])),
    ("o-wrong", ORDER, {"raw_response": "1, 2, 3"}, (I, 0, ["chronology"])),
    # known limitation: list enumerators are read as labels
    ("o-enumerated", ORDER, {"raw_response": "1) 3\n2) 1\n3) 2"}, (I, 0, ["chronology"])),
    # --- record-level edge cases
    ("r-timeout", CHOICE_B, {"raw_response": None, "error": "timeout after 120 s"},
     {"exclusion": "inference_error"}),
    ("r-error-obj", CHOICE_B, {"error": {"type": "oom", "message": "out of memory"}},
     {"exclusion": "inference_error"}),
    ("r-error-empty-string", CHOICE_B, {"raw_response": "B", "error": ""}, (C, 1, [])),
    ("r-missing-output", CHOICE_B, None, {"exclusion": "missing_output"}),
    ("900", CHOICE_B, {"id": 900, "raw_response": "B"}, (C, 1, [])),          # int id vs "900"
    ("r-truncated-empty", CHOICE_B, {"raw_response": "", "finish_reason": "length"}, (I, 0, [])),
    ("r-truncated-openai", CHOICE_B, {"raw_response": {"choices": [{"message": {"content": "B"},
                                                                     "finish_reason": "length"}]}},
     (C, 1, [])),
    ("r-ws-id", CHOICE_B, {"id": " r-ws-id ", "raw_response": "B"}, (C, 1, [])),
]

# record-level cases that emit several records or no key
EXTRA_RECORDS = [
    # retry: an error record then a successful retry for the same id -> the retry is scored
    ("r-retry", [{"raw_response": None, "error": "timeout"}, {"raw_response": "B"}]),
    # conflicting duplicates: first success kept, second logged as duplicate_output
    ("r-dup-conflict", [{"raw_response": "B"}, {"raw_response": "C"}]),
    # exact duplicate
    ("r-dup-same", [{"raw_response": "B"}, {"raw_response": "B"}]),
]
EXTRA_EXPECT = {"r-retry": (C, 1, []), "r-dup-conflict": (C, 1, []), "r-dup-same": (C, 1, [])}
ORPHANS = [{"id": "adv-not-in-keys", "raw_response": "B"}, {"raw_response": "B"}]  # unknown id, no id

META = {"backend": "fixture", "model": "synthetic-adversarial", "model_revision": "none",
        "usage": {"prompt_tokens": 10, "completion_tokens": 3}, "latency_s": 0.1}


# Six template essays of deliberately varied quality (fixture "model B" for the blind dry run).
_FACTS = ("Królestwo Ardenii powstało w roku 1234, gdy książę Borzysław zjednoczył trzy doliny. "
          "Stolicą został Źródłogród. W roku 1261 Statut Dolinny ograniczył władzę wojewodów. "
          "Wojna z Mrokowem trwała od 1302 do 1305 roku. ")
_ARG = ("Po pierwsze, Statut Dolinny odebrał wojewodom sądy, więc król zyskał kontrolę nad dolinami. "
        "Po drugie, stolica w Źródłogrodzie leżała w centrum, co ułatwiało zarząd. "
        "Po trzecie, pokój z 1305 roku utrwalił granice królestwa. ")
ESSAYS = {
    "essay-1": "Teza: zjednoczenie było trwałe dzięki reformom. " + _FACTS + _ARG * 6 +
               "Podsumowanie: reformy Borzysława utrwaliły państwo.",           # strong, >300 words
    "essay-2": "Ardenia była królestwem. Miała stolicę. Była też wojna.",        # very weak, short
    "essay-3": _FACTS * 2 + "Tak było.",                                         # facts, no argument
    "essay-4": "Uważam, że Statut Dolinny wzmocnił króla. " + _ARG * 3 +
               "Jednak wojna z Mrokowem osłabiła skarb. " * 3 + "Wniosek: bilans jest dodatni.",
    "essay-5": "Kawa jest napojem popularnym w wielu krajach. " * 20,         # off-topic
    "essay-6": "- 1234 zjednoczenie\n- 1261 statut\n- 1302-1305 wojna\n- stolica Źródłogród",  # bullets
}


def key_for(cid, tpl):
    k = {"id": cid, "split": "DEV", "era": "synthetic", "topic": "synthetic",
         "source_ids": [], "source_group_id": "adv-" + cid}
    k.update(json.loads(json.dumps(tpl)))
    k["rubric"]["rubric_id"] = "adv-r-" + cid
    return k


def record(cid, fields):
    r = {"id": cid}
    r.update(META)
    r["error"] = None
    r.update(fields)
    return r


def label(cid, exp, why=""):
    if isinstance(exp, dict):
        lab = {"id": cid}
        lab.update({"expected_" + k: v for k, v in exp.items()})
    else:
        lab = {"id": cid, "expected_status": exp[0], "expected_points": exp[1],
               "expected_error_categories": exp[2]}
    if why:
        lab["why"] = why
    return lab


KNOWN_LIMITS = {"e-inflected": "known limitation: inflected form not in key variants",
                "o-enumerated": "known limitation: list enumerators read as order labels",
                "c-unsure": "policy: an explicit 'nie wiem' counts as abstention even with a guess",
                "e-hedge": "entity plus a key distractor -> routed to review, 0 auto points",
                "y-hedge": "expected year plus another year -> routed to review, 0 auto points",
                "r-truncated-empty": "hit max_tokens with no answer: 0 points, flagged truncated_output, "
                                     "not counted as abstention",
                "r-dup-conflict": "first success kept; second logged as duplicate_output"}


def build():
    keys, outs, labels = [], [], []
    for cid, tpl, fields, exp in CASES:
        keys.append(key_for(cid, tpl))
        if fields is not None:
            outs.append(record(cid, fields))
        labels.append(label(cid, exp, KNOWN_LIMITS.get(cid, "")))
    for cid, recs in EXTRA_RECORDS:
        keys.append(key_for(cid, CHOICE_B))
        outs.extend(record(cid, f) for f in recs)
        labels.append(label(cid, EXTRA_EXPECT[cid], KNOWN_LIMITS.get(cid, "")))
    for o in ORPHANS:
        r = dict(META, error=None)
        r.update(o)
        outs.append(r)
    return keys, outs, labels


def write(name, rows):
    with open(os.path.join(FIX, name), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    keys, outs, labels = build()
    write("adversarial_eval_keys.jsonl", keys)
    write("adversarial_outputs.jsonl", outs)
    write("adversarial_labels.jsonl", labels)
    write("blind_essay_keys.jsonl", [key_for("essay-%d" % i, ESSAY) for i in range(1, 7)])
    write("blind_essay_outputs_fixture.jsonl",
          [record(cid, {"model": "synthetic-essay-template", "raw_response": t}) for cid, t in ESSAYS.items()])
    print(json.dumps({"keys": len(keys), "output_records": len(outs), "labels": len(labels)}))
