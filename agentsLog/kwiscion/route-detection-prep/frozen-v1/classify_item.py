"""Conservative organizer-item route metadata; no prompts, I/O, models or IDs.

Call before the adapter merges source_text into the model prompt. Detection reads
only question, answer_format and images. Unknown means unchanged baseline.
"""
import re
import unicodedata
from collections.abc import Mapping

REVISION = 'instruction-route-v1'
ROUTES = frozenset(('essay', 'closed', 'open', 'unknown'))


def normalized(text):
    return unicodedata.normalize('NFC', text).casefold()


def classify_item(item, *, override=None):
    """Return route, visual flag, fixed reason and baseline-fallback metadata.

    override is an explicit route string; 'unknown' explicitly keeps baseline.
    No supplied text, IDs, historical facts or source contents enter the result.
    The caller retains the full original item for inference, unchanged.
    """
    if override is not None and override not in ROUTES:
        raise ValueError('override must be essay, closed, open or unknown')
    if not isinstance(item, Mapping):
        raise TypeError('item must be an organizer item mapping')
    images = item.get('images', [])
    visual = isinstance(images, list) and bool(images)

    def result(route, reason, explicit=False):
        return {'route': route, 'visual': visual, 'reason': reason,
                'baseline_fallback': route == 'unknown',
                'explicit_override': explicit, 'revision': REVISION}

    if override is not None:
        return result(override, 'explicit_override', True)
    question, fmt = item.get('question'), item.get('answer_format')
    if not isinstance(question, str) or not question.strip() or not isinstance(fmt, str) or not isinstance(images, list):
        return result('unknown', 'invalid_or_missing_instruction_fields')
    q, f = normalized(question.strip()), normalized(fmt.strip())
    # Reuse essay_route.py's structural principle, without its merged prompt,
    # old prompt templates, topic choice or output-budget implementation.
    direct_essay = bool(re.search(r'(?:^|[.!?\n]\s*|\bi\s+)(?:napisz|opracuj|przygotuj)\s+(?:(?:jedno|rozbudowane)\s+)?(?:wypracowanie|esej)\b', q))
    format_essay = bool(re.match(r'^(?:wypracowanie|esej)\b', f))
    essay_word = bool(re.search(r'\b(?:wypracowani\w*|esej\w*)\b', q))
    length = bool(re.search(r'(?:minimum|co najmniej|nie mniej niż)\s+\d{3,4}\s+(?:słów|wyrazów)', q+'\n'+f))
    topics = len(re.findall(r'(?m)^\s*temat\s+(?:nr\s+)?\d+[.:]', q)) >= 2
    choose_topic = bool(re.search(r'wybierz\s+(?:jeden\s+)?(?:z\s+(?:podanych\s+)?)?temat', q))
    essay = direct_essay or format_essay or (essay_word and choose_topic and (length or topics))

    # Choice route requires an explicit finite response form or actual option
    # labels plus a selection directive. 'Choose a topic' is not a closed item.
    closed_format = bool(re.search(r'^(?:jedna\s+)?litera\b|^(?:zapisz|podaj)\s+(?:jedną\s+)?literę\b|^(?:prawda\s*[/–-]\s*fałsz|p\s*/\s*f)\b', f))
    true_false = bool(re.search(r'(?:zaznacz|oznacz|oceń|określ)[^.!?\n]{0,140}(?:prawdziw|prawda)[^.!?\n]{0,100}(?:fałszyw|fałsz)', q))
    option_labels = len(re.findall(r'(?m)^\s*[a-f][.)]\s+\S', q)) >= 2
    choose_answer = bool(re.search(r'\b(?:wybierz|zaznacz|wskaż)\b', q)) and option_labels
    closed = closed_format or true_false or choose_answer
    if essay and closed:
        return result('unknown', 'conflicting_essay_and_closed_instructions')
    if essay:
        return result('essay', 'explicit_essay_instruction_or_format')
    if closed:
        return result('closed', 'explicit_finite_choice_or_true_false')
    open_format = bool(re.match(r'^(?:krótka\s+odpowiedź|odpowiedź\s+otwarta|uzasadnienie|tekst\s+ciągły)\b', f))
    open_instruction = bool(re.search(r'(?:^|[.!?\n]\s*)(?:wyjaśnij|uzasadnij|podaj|wymień|scharakteryzuj|porównaj|oceń|opisz|rozstrzygnij)\b', q))
    if open_format or open_instruction:
        return result('open', 'explicit_constructed_response_instruction')
    return result('unknown', 'no_unambiguous_supported_instruction')
