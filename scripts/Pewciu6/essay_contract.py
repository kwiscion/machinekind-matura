"""Essay output contract for issue #80: one frozen topic, machine-checked {topic_id, body}, clean prose.

Stdlib only, no model calls. The bounded live loop is scripts/Pewciu6/essay_contract_run.py.

  parse_task       full task -> global requirements + per-topic text, aspects, required sources
  selection        deterministic policy, or a strict parse of a one-line model choice (ambiguous -> None)
  writer_task      ONLY the selected topic + every global and selected-topic requirement (the full
                   original task is kept separately for audit by the caller)
  parse_output     model text -> {topic_id, body}; strict JSON, unambiguous wrappers only
  clean_body       deterministic removal of unambiguous wrappers (preamble, plans, grader comments,
                   word-count notes, structural headings). Whole lines/paragraphs only; never edits a
                   sentence. v2: a Markdown heading marker ("# ", "**...**") is stripped and its prose
                   KEPT; only a whitelist of structural labels is removed wholesale, and a short
                   non-whitelisted heading is ambiguous (-> regenerate).
  count_words      body-only Polish word counter (headings/metadata/wrappers excluded)
  validate         hard gate: single topic and minimum length (topic identity and JSON/body shape are
                   checked in parse_output/contract_check). 400-500 target is soft; the lexical
                   aspect/source-marker checks are ADVISORY diagnostics only (v2). Length is a gate,
                   never a quality score.
  render_answer    "Temat nr N" + clean prose: the only thing that reaches answers.json
"""

from __future__ import annotations

import hashlib
import json
import re

CONTRACT_REVISION = "essay-contract-v2"  # v2: content-preserving cleaner, advisory lexical checks
TARGET_MIN, TARGET_MAX = 400, 500
DEFAULT_MIN_WORDS = 300
MAX_REPAIRS = 2
# cleanup may remove at most this share of body words; more means the output is not a wrapped essay
MAX_REMOVED_SHARE = 0.25

WORD = re.compile(r"[0-9A-Za-zÀ-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]")
MIN_REQ = re.compile(r"(?:minimum|co najmniej|nie mniej niż|przynajmniej)\s+(\d{3})\s+(?:słów|wyrazów)", re.I)
TOPIC_START = re.compile(r"(?m)^[ \t]*(?:Temat[ \t]+(?:nr[ \t]*)?)?(\d{1,2})\.[ \t]+(?=\S)")
TRAILER = re.compile(r"(?m)^[ \t]*(?:WYPRACOWANIE\b|\[miejsce na odpowiedź\])")
ASPECT_LIST = re.compile(r"aspekt(?:y|ów)?\s*:\s*([^.]+)", re.I)
SOURCE_SENT = re.compile(r"[^.\n]*\b(?:źródł\w*|tekst\w* źródłow\w*|materiał\w* źródłow\w*)[^.\n]*[.]?", re.I)
YEAR = re.compile(r"(?<!\d)(\d{3,4})(?!\d)")

# ---- wrappers (anchored, specific; a generic "Oto ..." sentence is prose, not a wrapper)
PREAMBLE = re.compile(
    r"^\s*(?:(?:Oczywiście|Jasne|Dobrze|Rozumiem|Świetnie|Z przyjemnością)[!,.]?\s*)?"
    r"(?:(?:Oto|Poniżej)\s+(?:(?:jest|znajduje się|przedstawiam|prezentuję|zamieszczam)\s+)?"
    r"(?:moj[aeą]\s+|gotow[eay]\s+|przykładow[eay]\s+|pełn[eay]\s+)?"
    r"(?:odpowiedź|wypracowanie|wypracowania|tekst|esej|propozycj[aę]|rozprawk[aę]|praca)\b"
    r"|(?:Przedstawiam|Prezentuję)\s+(?:moje\s+|moją\s+)?(?:wypracowanie|odpowiedź|esej)\b"
    r"|(?:Wybieram|Wybrałem|Wybrałam|Piszę na)\s+temat\b)",
    re.I)
COURTESY = re.compile(r"^\s*(?:Oczywiście|Jasne|Dobrze|Rozumiem|Świetnie|Z przyjemnością)\s*[!,.]?\s*$", re.I)
TOPIC_HEADER = re.compile(
    r"^\s*(?:[#*_]+\s*)?(?:WYPRACOWANIE\s+)?(?:na\s+)?(?:Temat|TEMAT)\s*(?:nr\.?|numer)?\s*[:.]?\s*(\d{1,2})\b[^\n]*$")
WYPRACOWANIE_LINE = re.compile(r"^\s*(?:[#*_]+\s*)?WYPRACOWANIE\s*(?:na temat nr\s*[.…]*)?\s*[*_]*\s*$", re.I)
PLAN_HEAD = re.compile(r"^\s*(?:[#*_]+\s*)?(?:Plan(?:\s+wypracowania|\s+pracy)?|Konspekt|Szkic)\s*[:*_]*\s*$", re.I)
BULLET = re.compile(r"^\s*(?:[-*•–]|\d{1,2}[.)]|[IVX]+\.|[a-z]\))\s+")
TRAILING_META = re.compile(
    r"^\s*[(\[]?\s*(?:[*_]+\s*)?(?:Liczba\s+(?:słów|wyrazów)|Słów|Wyrazów|Długość(?:\s+tekstu)?|Word count)\s*[:=]?\s*~?\d+"
    r"|^\s*[(\[]?\s*(?:[*_]+\s*)?(?:Komentarz|Uwagi?|Uwaga|Ocena|Samoocena|Punktacja|Notatka|Nota|Komentarz egzaminatora"
    r"|Uwagi egzaminatora|Uwagi do oceny|Kryteria)\b[^\n]*:"
    r"|^\s*(?:Mam nadzieję|Czy chcesz|Jeśli chcesz|Daj znać|Chętnie (?:rozwinę|poprawię|pomogę)|Mogę (?:też|również))\b",
    re.I)
WORD_COUNT_NOTE = re.compile(
    r"^\s*[(\[]?\s*(?:[*_]+\s*)?(?:Liczba\s+(?:słów|wyrazów)|Słów|Wyrazów|Długość(?:\s+tekstu)?|Word count)\s*[:=]?\s*~?\d+[^\n]{0,30}$",
    re.I)
MD_HEADING = re.compile(r"^\s*#{1,6}\s+(?=\S)")
BOLD_ONLY = re.compile(r"^\s*(?:\*\*|__)([^*_\n]{1,200}?)(?:\*\*|__)\s*(:?)\s*$")
# v2 whitelist: the ONLY heading texts removed wholesale (structural labels, never content). A year
# or any sentence punctuation inside makes the line content, not a label.
STRUCTURAL_LABEL = re.compile(
    r"^(?:Wstęp|Wprowadzenie|Rozwinięcie|Zakończenie|Podsumowanie|Wnioski?|Teza|Argumentacja|Argumenty"
    r"|(?:Aspekt|Argument)(?:\s+(?:\d{1,2}|[IVX]{1,4}))?(?:\s*[–—-]\s*|\s+)?(?:[a-ząćęłńóśźż]+(?:-[a-ząćęłńóśźż]+)?)?"
    r"(?:\s+(?:i|oraz)\s+[a-ząćęłńóśźż]+(?:-[a-ząćęłńóśźż]+)?)?)\s*:?$", re.I)
LABEL_ONLY = re.compile(r"^\s*(?:Wstęp|Wprowadzenie|Rozwinięcie|Zakończenie|Podsumowanie|Teza|Aspekt\s*\d*[^:\n]{0,60})\s*:\s*$", re.I)
SENTENCE_END = re.compile(r"[.!?…]\s*$")
OTHER_TOPIC_MARK = re.compile(r"(?mi)^\s*(?:[#*_]+\s*)?(?:WYPRACOWANIE\s+)?(?:na\s+)?Temat\s*(?:nr\.?|numer)?\s*[:.]?\s*(\d{1,2})\b")
# v2: the ONLY text allowed outside the JSON object: a courtesy word, a one-sentence preamble announcing
# the answer, a code-fence marker, a word-count note, or a closing offer. Anything else (a fact, a
# sentence of the essay, a second essay) is substantive -> reject/regenerate, whatever its length.
OUTSIDE_FENCE = re.compile(r"^\s*```[a-zA-Z]*\s*$")
OUTSIDE_OFFER = re.compile(
    r"^\s*(?:Mam nadzieję|Czy chcesz|Jeśli chcesz|Daj znać|Chętnie (?:rozwinę|poprawię|pomogę)|Mogę (?:też|również))\b"
    r"[^.!?\n]{0,120}[.!?]?\s*$", re.I)
COURTESY_PREFIX = re.compile(r"^\s*(?:Oczywiście|Jasne|Dobrze|Rozumiem|Świetnie|Z przyjemnością)\s*[!,.]?\s*", re.I)
FENCE = re.compile(r"^\s*```[a-zA-Z]*\s*\n(.*)\n\s*```\s*$", re.S)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- task

def parse_task(body: str) -> dict:
    """Split an essay task into global requirements and per-topic segments (verbatim text)."""
    starts = []
    for m in TOPIC_START.finditer(body):
        if int(m.group(1)) == len(starts) + 1:
            starts.append(m)
    trailer = TRAILER.search(body, starts[-1].end()) if starts else None
    end = trailer.start() if trailer else len(body)
    topics = {}
    for i, m in enumerate(starts):
        stop = starts[i + 1].start() if i + 1 < len(starts) else end
        text = re.sub(r"\s+", " ", body[m.end():stop]).strip()
        topics[int(m.group(1))] = text
    global_text = body[:starts[0].start()].strip() if starts else body.strip()
    req = MIN_REQ.search(body)
    task = {"global": global_text, "topics": topics, "min_words": int(req.group(1)) if req else DEFAULT_MIN_WORDS,
            "aspects": {n: topic_aspects(t) for n, t in topics.items()},
            "sources": {n: SOURCE_SENT.findall(t) for n, t in topics.items()},
            "global_sources": SOURCE_SENT.findall(global_text), "full_task_sha256": sha256_text(body)}
    return task


def topic_aspects(text: str) -> list[str]:
    match = ASPECT_LIST.search(text)
    if not match:
        return []
    raw = re.split(r",|\s+i\s+|\s+oraz\s+", match.group(1))
    return [a.strip() for a in raw if a.strip()]


def aspect_stems(aspect: str) -> list[str]:
    """Stems that must appear in the body for an aspect ("społeczno-gospodarczy" -> both parts)."""
    parts = [p for p in re.split(r"[-\s]+", aspect.lower()) if len(p) >= 4]
    return [p[:5] if len(p) >= 7 else p[:max(4, len(p) - 2)] for p in parts]


# ---------------------------------------------------------------- selection

def select_deterministic(task: dict, policy: str) -> int:
    """'first' | 'fixed:N' | 'most-aspects' (ties -> lowest number). Always a permitted topic."""
    permitted = sorted(task["topics"])
    if not permitted:
        raise ValueError("task has no enumerated topics")
    if policy == "first":
        return permitted[0]
    if policy.startswith("fixed:"):
        n = int(policy.split(":", 1)[1])
        if n not in permitted:
            raise ValueError(f"topic {n} not permitted {permitted}")
        return n
    if policy == "most-aspects":
        return max(permitted, key=lambda n: (len(task["aspects"][n]), -n))
    raise ValueError(f"unknown selection policy {policy}")


SELECT_LINE = re.compile(r"^\s*(?:\*\*)?\s*Temat\s*(?:nr\.?)?\s*:?\s*(\d{1,2})\s*(?:\*\*)?\s*[.]?\s*$", re.I)


def parse_selection(text: str, permitted: list[int]) -> tuple[int | None, str]:
    """Strict: exactly one 'Temat: N' line naming a permitted topic, and no other topic number."""
    lines = [l for l in (text or "").strip().splitlines() if l.strip()]
    if not lines:
        return None, "empty"
    hits = [SELECT_LINE.match(l) for l in lines]
    chosen = {int(h.group(1)) for h in hits if h}
    if len(chosen) != 1:
        return None, "ambiguous" if chosen else "no_selection_line"
    n = chosen.pop()
    if n not in permitted:
        return None, f"not_permitted:{n}"
    return n, "ok"


SELECT_PROMPT = """\
Przeczytaj polecenie poniżej. Dla każdego tematu oceń, ile pewnych faktów z datami i nazwami własnymi znasz, i wybierz JEDEN temat, na który napiszesz najlepiej udokumentowane wypracowanie. Odpowiedz wyłącznie jedną linią w formacie „Temat: N”, bez uzasadnienia.

POLECENIE:
{body}
"""


def select_prompt(body: str) -> str:
    return SELECT_PROMPT.format(body=body)


# ---------------------------------------------------------------- writer

WRITER_RULES = """\
Napisz wypracowanie maturalne z historii na JEDEN, już wybrany temat nr {topic}. Pozostałe tematy z arkusza nie są częścią zadania: nie pisz o nich i nie wspominaj ich.

Odpowiedz WYŁĄCZNIE jednym obiektem JSON, bez żadnego tekstu przed nim ani po nim:
{{"topic_id": {topic}, "body": "<treść wypracowania>"}}

Wymagania dotyczące pola "body":
- Sama treść wypracowania: bez tytułu, bez nagłówków, bez numeru tematu, bez planu, bez komentarzy do oceniającego, bez podawania liczby słów, bez zwrotów typu „Oto moja odpowiedź”.
- Długość: {tmin}–{tmax} słów (bezwzględne minimum: {min_words}). Jeśli brakuje słów, rozwijaj argumenty konkretnymi faktami (rok, nazwa własna, związek z tezą), nigdy powtórzeniami ani ogólnikami.
- Akapity oddzielaj pustą linią (w JSON: \\n\\n). Pierwszy akapit: krótkie wprowadzenie i wyraźne stanowisko (teza). Potem co najmniej jeden akapit na każdy wymagany aspekt. Ostatni akapit: wniosek, który wraca do tezy.
- Podawaj tylko fakty, których jesteś pewien; nie wymyślaj nazw, terminów ani dat. Pisz po polsku.
"""


def writer_task(task: dict, topic: int) -> str:
    """Only the selected topic and every requirement that applies to it (global + topic-specific)."""
    lines = ["WYMAGANIA OGÓLNE Z POLECENIA:", task["global"], "", f"TEMAT nr {topic}:", task["topics"][topic]]
    if task["aspects"][topic]:
        lines.append("Wymagane aspekty (każdy musi zostać omówiony): " + ", ".join(task["aspects"][topic]))
    sources = task["global_sources"] + task["sources"][topic]
    if sources:
        lines.append("Wymagane źródła/materiały (odwołaj się do nich): " + " | ".join(s.strip() for s in sources))
    lines.append(f"Minimalna długość z polecenia: {task['min_words']} słów.")
    return "\n".join(lines) + "\n"


def writer_prompt(task: dict, topic: int, extra: str = "") -> str:
    return (WRITER_RULES.format(topic=topic, tmin=TARGET_MIN, tmax=TARGET_MAX, min_words=task["min_words"])
            + extra + "\n" + writer_task(task, topic))


# ---------------------------------------------------------------- parse model output

def _balanced_objects(text: str) -> list[str]:
    """Top-level {...} spans, string-aware."""
    out, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"' and depth:
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                out.append(text[start:i + 1])
    return out


def outside_is_wrapper(outside: str) -> bool:
    """True only if every non-empty line outside the JSON is a recognized non-substantive wrapper."""
    for line in outside.splitlines():
        s = line.strip()
        if not s or OUTSIDE_FENCE.match(s) or COURTESY.match(s) or WORD_COUNT_NOTE.match(s):
            continue
        if YEAR.search(re.sub(r"~?\d+\s*(?:słów|wyrazów)", "", s)):
            return False  # a date outside the JSON is content
        if OUTSIDE_OFFER.match(s) and words(s) <= 25:
            continue
        rest = COURTESY_PREFIX.sub("", s, count=1)
        # one announcing clause: "Oto wypracowanie w wymaganym formacie:" (no second sentence)
        if PREAMBLE.match(rest) and words(rest) <= 15 and not re.search(r"[.!?…]", rest.rstrip(" :.!…")):
            continue
        return False
    return True


def parse_output(raw: str, allow_keys: tuple = ()) -> dict:
    """-> {ok, topic_id, body, wrappers:[...], extras, error}. Only unambiguous wrappers are peeled.

    allow_keys: extra JSON fields a caller declared in its prompt (e.g. a review note); they are
    returned in `extras`, never merged into the body, and exempt from the substantive-key rule.
    """
    wrappers, text = [], (raw or "").strip()
    if not text:
        return {"ok": False, "error": "empty", "wrappers": wrappers}
    fence = FENCE.match(text)
    if fence:
        text, _ = fence.group(1).strip(), wrappers.append("code_fence")
    obj = None
    try:
        obj = json.loads(text, strict=False)
    except json.JSONDecodeError:
        parsed = []
        for span in _balanced_objects(text):
            try:
                cand = json.loads(span, strict=False)
            except json.JSONDecodeError:
                continue
            if isinstance(cand, dict) and "body" in cand:
                parsed.append((span, cand))
        if len(parsed) == 1:
            span, obj = parsed[0]
            outside = text.replace(span, "\n").strip()
            if outside and not outside_is_wrapper(outside):  # v2: no length allowance for unknown text
                return {"ok": False, "error": "ambiguous_text_outside_json", "wrappers": wrappers,
                        "outside": outside}
            if outside:
                wrappers.append("text_around_json")
        elif len(parsed) > 1:
            return {"ok": False, "error": "multiple_json_objects", "wrappers": wrappers}
        else:
            return {"ok": False, "error": "invalid_json", "wrappers": wrappers}
    if not isinstance(obj, dict):
        return {"ok": False, "error": "json_not_object", "wrappers": wrappers}
    body, topic_id = obj.get("body"), obj.get("topic_id")
    if isinstance(topic_id, str) and topic_id.strip().isdigit():
        topic_id = int(topic_id.strip())
    if not isinstance(topic_id, int) or isinstance(topic_id, bool):
        return {"ok": False, "error": "missing_topic_id", "wrappers": wrappers}
    if not isinstance(body, str) or not body.strip():
        return {"ok": False, "error": "missing_body", "wrappers": wrappers, "topic_id": topic_id}
    extras = {k: obj[k] for k in allow_keys if k in obj}
    extra = sorted(set(obj) - {"topic_id", "body"} - set(allow_keys))
    for key in extra:  # v2: an extra field may not carry discarded prose (a number/short label is fine)
        val = obj[key]
        if isinstance(val, (dict, list)) or (isinstance(val, str) and (words(val) > 12 or YEAR.search(val))):
            return {"ok": False, "error": f"substantive_extra_key:{key}", "wrappers": wrappers}
    if extra:
        wrappers.append("extra_keys:" + ",".join(extra))
    return {"ok": True, "topic_id": topic_id, "body": body.replace("\r\n", "\n"), "wrappers": wrappers, "extras": extras, "error": None}


# ---------------------------------------------------------------- cleanup

def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def words(text: str) -> int:
    return sum(1 for tok in text.split() if WORD.search(tok))


def heading_text(line: str) -> tuple[str, str] | None:
    """(marker-free text, marker kind) if the line is formatted as a heading, else None."""
    s = line.strip()
    m = MD_HEADING.match(s)
    if m:
        inner = s[m.end():].strip()
        b = BOLD_ONLY.match(inner)
        return ((b.group(1) + b.group(2)).strip() if b else inner.strip("*_ ").strip()), "md_heading"
    b = BOLD_ONLY.match(s)
    if b:
        return (b.group(1) + b.group(2)).strip(), "bold_line"
    if LABEL_ONLY.match(s):
        return s, "label_line"
    return None


def is_structural_label(text: str) -> bool:
    """Whitelisted structural label (removable wholesale). Never a year, never a sentence."""
    t = text.strip().rstrip(":").strip()
    if not t or YEAR.search(t) or re.search(r"[.!?…;]", t):
        return False
    return bool(STRUCTURAL_LABEL.match(t) or WYPRACOWANIE_LINE.match(t)
                or (TOPIC_HEADER.match(t) and words(t) <= 25))


def is_heading_line(line: str) -> bool:
    """A purely structural line (whitelisted label or topic header): excluded from the body count."""
    s = line.strip()
    if WYPRACOWANIE_LINE.match(s) or (TOPIC_HEADER.match(s) and words(s) <= 25):
        return True
    h = heading_text(s)
    return bool(h and is_structural_label(h[0]))


def other_topics_marked(text: str, topic: int) -> list[int]:
    return sorted({int(n) for n in OTHER_TOPIC_MARK.findall(text) if int(n) != topic})


def clean_body(body: str, topic: int) -> dict:
    """-> {ok, text, ops:[{op, text}], error}. Removes whole wrapper lines/paragraphs only."""
    ops = []
    others = other_topics_marked(body, topic)
    if others:
        return {"ok": False, "text": None, "ops": ops, "error": f"multi_topic:{others}"}
    paras = paragraphs(body)
    total = words(body)

    def drop(kind, text):
        ops.append({"op": kind, "text": text})

    # leading: courtesy, preamble (short, ends the intro to the essay), topic header, plan block
    while paras:
        head = paras[0]
        first, _, rest = head.partition("\n")
        if COURTESY.match(first) or (PREAMBLE.match(first) and (first.rstrip().endswith(":") or words(first) <= 20)
                                      and not YEAR.search(first.split(":")[0] if ":" in first else "")):
            if words(first) > 30:
                return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_preamble"}
            drop("preamble", first)
            paras[0] = rest.strip()
            if not paras[0]:
                paras.pop(0)
            continue
        if TOPIC_HEADER.match(first) or WYPRACOWANIE_LINE.match(first):
            n = TOPIC_HEADER.match(first)
            if n and int(n.group(1)) != topic:
                return {"ok": False, "text": None, "ops": ops, "error": f"wrong_topic_header:{n.group(1)}"}
            if words(first) > 25:
                return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_topic_header"}
            drop("topic_header", first)
            paras[0] = rest.strip()
            if not paras[0]:
                paras.pop(0)
            continue
        if PLAN_HEAD.match(first):
            lines = head.splitlines()[1:]
            block = [first]
            if lines and all(BULLET.match(l) or not l.strip() for l in lines):
                block += lines
                paras.pop(0)
                # a plan may continue in following bullet-only paragraphs
                while paras and all(BULLET.match(l) or not l.strip() for l in paras[0].splitlines()):
                    block.append(paras.pop(0))
                drop("plan", "\n".join(block))
                continue
            if not lines:
                paras.pop(0)
                while paras and all(BULLET.match(l) or not l.strip() for l in paras[0].splitlines()):
                    block.append(paras.pop(0))
                if len(block) == 1:
                    return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_plan"}
                drop("plan", "\n".join(block))
                continue
            return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_plan"}
        break
    # trailing: word-count notes, grader/self comments, offers; everything after the first such
    # paragraph is removed only if it is short (a comment block, not a second essay)
    cut = None
    for i in range(len(paras) - 1, -1, -1):
        if TRAILING_META.match(paras[i]):
            cut = i
        elif cut is not None:
            break
    if cut is not None:
        tail = paras[cut:]
        if words("\n\n".join(tail)) > 80:
            return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_trailing_block"}
        # a labelled closing paragraph that names a year may be a real conclusion ("Ocena: ... 1370"):
        # not unambiguous, so regenerate instead of deleting it
        if any(YEAR.search(p) and not WORD_COUNT_NOTE.match(p) for p in tail):
            return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_trailing_block"}
        for p in tail:
            drop("trailing_meta", p)
        paras = paras[:cut]
    # headings inside the essay (v2): a whitelisted structural label is removed wholesale; any other
    # heading-formatted line loses only its Markdown marker and its text is KEPT as prose when it is a
    # sentence; a short non-whitelisted heading that is not a sentence is ambiguous (-> regenerate).
    kept = []
    for p in paras:
        lines = p.splitlines()
        body_lines = []
        for line in lines:
            if WYPRACOWANIE_LINE.match(line.strip()) or (TOPIC_HEADER.match(line.strip()) and words(line) <= 25):
                n = TOPIC_HEADER.match(line.strip())
                if n and int(n.group(1)) != topic:
                    return {"ok": False, "text": None, "ops": ops, "error": f"wrong_topic_header:{n.group(1)}"}
                drop("heading", line)
                continue
            h = heading_text(line)
            if h is None:
                body_lines.append(line)
            elif is_structural_label(h[0]):
                drop("heading", line)
            elif SENTENCE_END.search(h[0]) and words(h[0]) >= 4:
                ops.append({"op": "heading_marker_stripped", "text": "", "marker": h[1], "kept": h[0]})
                body_lines.append(h[0])
            else:
                return {"ok": False, "text": None, "ops": ops, "error": "ambiguous_heading"}
        if body_lines:
            kept.append("\n".join(body_lines).strip())
    text = "\n\n".join(re.sub(r"[ \t]*\n[ \t]*", " ", p) for p in kept).strip()
    removed = sum(words(o["text"]) for o in ops)
    if total and removed / total > MAX_REMOVED_SHARE:
        return {"ok": False, "text": None, "ops": ops, "error": "cleanup_removed_too_much"}
    for o in ops:  # a removed span must never carry historical content in quantity
        if o["op"] != "plan" and len(YEAR.findall(o["text"])) >= 2 and words(o["text"]) >= 30:
            return {"ok": False, "text": None, "ops": ops, "error": "cleanup_would_remove_content"}
    return {"ok": True, "text": text, "ops": ops, "error": None}


def count_words(text: str) -> int:
    """Body-only word count: headings/metadata lines excluded; tokens need a letter or digit."""
    return sum(words(line) for line in (text or "").splitlines() if line.strip() and not is_heading_line(line)
               and not TRAILING_META.match(line))


# ---------------------------------------------------------------- validate

def validate(text: str, task: dict, topic: int) -> dict:
    hard, soft = [], []
    n = count_words(text or "")
    others = other_topics_marked(text or "", topic)
    if others:
        hard.append(f"multi_topic:{others}")
    if n < task["min_words"]:
        hard.append(f"underlength:{n}<{task['min_words']}")
    elif n < TARGET_MIN:
        soft.append(f"below_target:{n}<{TARGET_MIN}")
    if n > TARGET_MAX + 150:
        soft.append(f"above_target:{n}>{TARGET_MAX}")
    low = (text or "").lower()
    paras = paragraphs(low)
    # an aspect must be named in the development, not only in the introduction or the conclusion
    middle = "\n".join(paras[1:-1]) if len(paras) >= 3 else low
    # v2: lexical stems are ADVISORY diagnostics only. An argument can cover the political aspect
    # without the stem "polit" or use a source without the word "źródło"; coverage belongs to the
    # independent critic/grader, never to a hard gate that spends repairs or discards prose.
    advisory = []
    missing = [a for a in task["aspects"].get(topic, []) if not all(s in middle for s in aspect_stems(a))]
    if missing:
        advisory.append("lexical_aspect_absent:" + ",".join(missing))
    if (task["sources"].get(topic) or task["global_sources"]) and not re.search(r"źródł", low):
        advisory.append("lexical_source_marker_absent")
    return {"ok": not hard, "hard": hard, "soft": soft, "advisory": advisory, "words": n,
            "missing_aspects": missing,
            "note": "mechanical contract only; length never awards coherence/quality; advisory never gates"}


def check_body(body: str, task: dict, topic: int, result: dict | None = None) -> dict:
    """Cleanup + validation of an already extracted body (also used on legacy plain-text outputs)."""
    result = dict(result or {})
    cleaned = clean_body(body, topic)
    if not cleaned["ok"]:
        return {**result, "ok": False, "triggers": [cleaned["error"]], "clean": None, "validation": None,
                "ops": cleaned["ops"], "body_words_before_cleanup": count_words(body)}
    val = validate(cleaned["text"], task, topic)
    triggers = list(val["hard"]) + [s for s in val["soft"] if s.startswith("below_target")]
    return {**result, "ok": val["ok"], "triggers": triggers, "clean": cleaned["text"], "validation": val,
            "ops": cleaned["ops"], "body_words_before_cleanup": count_words(body)}


def contract_check(raw: str, task: dict, topic: int, allow_keys: tuple = ()) -> dict:
    """Full mechanical check of one model output. Never rewrites historical claims."""
    parsed = parse_output(raw, allow_keys)
    result = {"raw_words": words(raw or ""), "parse": {k: parsed.get(k) for k in ("ok", "error", "wrappers", "topic_id")}}
    if not parsed["ok"]:
        return {**result, "ok": False, "triggers": [parsed["error"]], "clean": None, "validation": None, "ops": []}
    if parsed["topic_id"] != topic:
        return {**result, "ok": False, "triggers": [f"wrong_topic_id:{parsed['topic_id']}"], "clean": None,
                "validation": None, "ops": []}
    return check_body(parsed["body"], task, topic, result)


# ---------------------------------------------------------------- repair

REPAIR_TEXT = {
    "invalid_json": "Poprzednia odpowiedź nie była poprawnym obiektem JSON. Zwróć wyłącznie obiekt JSON w wymaganym formacie.",
    "empty": "Poprzednia odpowiedź była pusta.",
    "multi_topic": "Poprzednia odpowiedź omawiała więcej niż jeden temat. Napisz wyłącznie o temacie nr {topic}.",
    "wrong_topic": "Poprzednia odpowiedź nie dotyczyła tematu nr {topic}. Pisz wyłącznie o temacie nr {topic}.",
    "underlength": "Poprzednia wersja miała tylko {words} słów, poniżej wymaganego minimum. Rozwiń ją do {tmin}–{tmax} słów, dodając konkretne, pewne fakty (rok, nazwa własna) i wyjaśniając ich związek z tezą; nie dodawaj powtórzeń ani ogólników.",
    "below_target": "Poprzednia wersja miała {words} słów. Rozwiń ją do {tmin}–{tmax} słów konkretnymi, pewnymi faktami powiązanymi z tezą; nie dodawaj powtórzeń ani ogólników.",
    "missing_aspects": "W poprzedniej wersji brakuje omówienia aspektów: {aspects}. Dodaj dla każdego z nich osobny akapit z konkretnymi faktami.",
    "missing_source_reference": "Polecenie wymaga odwołania się do wskazanego źródła; uwzględnij je w argumentacji.",
    "ambiguous": "Poprzednia odpowiedź zawierała tekst spoza wypracowania (wstęp, plan, komentarz albo drugi tekst). Zwróć tylko treść jednego wypracowania w polu body.",
}


def repair_instructions(triggers: list[str], topic: int, words_now: int | None, missing: list[str]) -> str:
    out = []
    for t in triggers:
        key = t.split(":", 1)[0]
        if key in ("json_not_object", "missing_topic_id", "missing_body", "multiple_json_objects"):
            key = "invalid_json"
        elif key.startswith("wrong_topic"):
            key = "wrong_topic"
        elif key.startswith("ambiguous") or key.startswith("cleanup_"):
            key = "ambiguous"
        text = REPAIR_TEXT.get(key)
        if text:
            out.append(text.format(topic=topic, words=words_now, tmin=TARGET_MIN, tmax=TARGET_MAX,
                                   aspects=", ".join(missing)))
    return "\n".join(f"- {line}" for line in dict.fromkeys(out))


REPAIR_RULES = """\
POPRAWKA FORMALNA (runda {round} z {max_rounds}). Popraw poprzednią wersję zgodnie z uwagami poniżej. Zachowaj wszystkie poprawne fakty i tezę; nie zmieniaj tematu.
UWAGI:
{instructions}

POPRZEDNIA WERSJA:
{previous}

"""


def repair_prompt(task: dict, topic: int, previous: str, check: dict, round_no: int) -> str:
    val = check.get("validation") or {}
    extra = REPAIR_RULES.format(round=round_no, max_rounds=MAX_REPAIRS,
                                instructions=repair_instructions(check["triggers"], topic, val.get("words"),
                                                                 val.get("missing_aspects", [])),
                                previous=(previous or "").strip()[:12000])
    return writer_prompt(task, topic, extra)


# ---------------------------------------------------------------- render

def render_answer(topic: int, text: str) -> str:
    return f"Temat nr {topic}\n\n{text.strip()}\n"


def template_sha256() -> str:
    return sha256_text("\x00".join([CONTRACT_REVISION, WRITER_RULES, SELECT_PROMPT, REPAIR_RULES,
                                    json.dumps(REPAIR_TEXT, sort_keys=True, ensure_ascii=False),
                                    str((TARGET_MIN, TARGET_MAX, MAX_REPAIRS, MAX_REMOVED_SHARE))]))
