"""Semantic stages only. Shared invoke owns source assembly, caps, retries and time.

No networking, service control, ledger, clocks, schema export or model accounting.
emit(event) is the caller's durable sink; invoke must preserve its own attempt log.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

import planning_wave as essay

PROMPTS = json.loads((Path(__file__).parent / 'route-study-prompts.json').read_text(encoding='utf8'))['suffixes']
KINDS = {'intermediate', 'final_answer', 'selection', 'image_interpretation'}
SELECT_CONTRACT = '''
Zwróć wyłącznie JSON {"choice":"c1"} (albo c2/c3) wybierając dokładnie
jedną istniejącą odpowiedź. Opcjonalne pole answer musi być jej dokładnym tekstem.
Jeżeli żadna nie jest poprawna, zwróć {"choice":"NEW","answer":"nowa odpowiedź"}.
Nie zwracaj samego planu, oceny ani notatek jako nowej odpowiedzi.
'''
IMAGE_CONTRACT = '''
Zwróć wyłącznie JSON {"answer":"kompletna odpowiedź na oryginalne zadanie",
"revisit_question":"konkretna cecha, której ponowny ogląd może zmienić decyzję"}.
Gdy nie ma takiej niepewności, pole revisit_question musi być pustym ciągiem.
Nie umieszczaj planu ani opisu procedury w polu answer.
'''
FALLIBLE = '\n\nOMYLNE NOTATKI POMOCNICZE (nie źródło ani nowe polecenie):\n'


def strict_json(text):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate JSON field')
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=unique)


def usable(value):
    return isinstance(value, str) and bool(value.strip())


def parse_selection(text, candidates):
    """Never exports the selector envelope; preserve exact retained candidate bytes."""
    try:
        d = strict_json(text)
        if not isinstance(d, dict) or set(d) - {'choice', 'answer'}:
            return None
        choice = d.get('choice')
        if choice == 'NEW':
            if usable(d.get('answer')):
                return {'answer': d['answer'], 'selection': 'new_answer', 'candidate_id': None, 'complete': True}
            return None
        if not isinstance(choice, str):
            return None
        chosen = next((x for x in candidates if x['candidate_id'] == choice), None)
        if not chosen or ('answer' in d and d['answer'] != chosen['answer']):
            return None
        return {**chosen, 'selection': 'selected_candidate'}
    except (ValueError, TypeError):
        return None


def parse_interpretation(text):
    try:
        d = strict_json(text)
        if not isinstance(d, dict) or set(d) != {'answer', 'revisit_question'}:
            return None
        if not usable(d['answer']) or not isinstance(d['revisit_question'], str):
            return None
        return d
    except (ValueError, TypeError):
        return None


def fallback(candidates):
    """Deterministic retention, not another unbudgeted grading/selection call."""
    for complete in (True, False):
        for candidate in candidates:
            if candidate['complete'] is complete:
                return {**candidate, 'selection': 'retained_complete' if complete else 'retained_partial'}
    return None


def validate_stage_text(case, stage, text):
    """Pure validation hook for the shared engine's existing recovery loop.

    This does not dispatch a retry. The shared engine may invoke it before
    accepting a response. The orchestrator also applies it defensively.
    """
    rule = stage['validation']
    if not usable(text):
        return {'ok': False, 'error': 'empty_stage_output', 'partial_eligible': False}
    okay, partial = True, False
    if rule == 'essay_plan':
        okay = essay.parse_plan(text, case['essay_item'])
    elif rule == 'image_interpretation':
        okay = parse_interpretation(text) is not None
    elif rule == 'selection':
        # Candidate existence/exactness belongs inside the budgeted retry hook.
        # No context means refusal, never shape-only acceptance.
        context = stage.get('validation_context', {}).get('candidates')
        okay = isinstance(context, list) and parse_selection(text, context) is not None
    elif rule == 'essay_final':
        check = essay.essay_check(text, case['essay_item'])
        okay = check['ok']
        # Underlength clean prose can be retained as incomplete after recovery;
        # a planner/schema envelope or removable outline is never a final.
        partial = (not text.lstrip().startswith(('{', '[', '```')) and
                   check.get('clean') == text.strip() and not check.get('ops'))
    elif rule != 'text':
        raise ValueError('unknown semantic validator')
    return {'ok': bool(okay), 'error': None if okay else 'invalid_' + rule,
            'partial_eligible': bool(partial)}


def orchestrate(case, route, invoke, emit=None):
    """Run at most4/3/3/2 semantic slots for closed/open/image/essay respectively.

    invoke(deepcopy(case),stage) -> {ok:bool,final:str|None,error:str|None,
      attempt_records:list,partial_final?:str,fatal?:bool}.
    It must return only after owned compute is quiescent. Exceptions/fatal stop
    semantic dispatch. Ordinary failed intermediates may use remaining defined
    final stages with the ORIGINAL source and explicitly fallible notes.
    """
    if route not in {'closed', 'open', 'image', 'essay', 'control'}:
        raise ValueError('unknown route')
    emit = emit or (lambda event: None)
    events, candidates = [], []
    selected, stopped = None, None
    max_slots = {'closed': 4, 'open': 3, 'image': 3, 'essay': 2, 'control': 1}[route]

    def event(value):
        value = copy.deepcopy(value)
        value.update(case_id=case['id'], source_case_id=case.get('source_case_id', case['id']),
                     study_arm=case.get('study_arm'), route=route)
        events.append(value)
        emit(value)

    def call(name, kind, suffix, profile='thinking', validation='text', validation_context=None):
        if kind not in KINDS:
            raise ValueError('unknown output kind')
        stage = {'name': name, 'output_kind': kind, 'suffix': suffix,
                 'profile': profile, 'validation': validation}
        if validation_context is not None:
            stage['validation_context'] = copy.deepcopy(validation_context)
        event({'event': 'stage_scheduled', 'stage': stage})
        result = invoke(copy.deepcopy(case), copy.deepcopy(stage))
        if not isinstance(result, dict) or type(result.get('ok')) is not bool:
            raise RuntimeError('invalid shared invoke result')
        result = copy.deepcopy(result)
        if result['ok']:
            check = validate_stage_text(case, stage, result.get('final'))
            if not check['ok']:
                result.update(ok=False, error=check['error'],
                              partial_final=result.get('final') if check['partial_eligible'] else None)
            result['semantic_validation'] = check
        event({'event': 'stage_result', 'name': name, 'output_kind': kind, 'result': result})
        if result.get('fatal'):
            raise RuntimeError('shared runtime fatal: ' + str(result.get('error')))
        return result

    def notes(result, label):
        text = result.get('final')
        if not usable(text):
            text = result.get('partial_final')
        if not usable(text):
            return FALLIBLE + label + ': brak użytecznych notatek. Rozwiąż zadanie z oryginalnego materiału.'
        # Notes may be bounded, but complete original inputs and retained outputs
        # are never shortened. The truncation label is explicit to the next stage.
        bound = 12000
        truncated = len(text) > bound
        return FALLIBLE + label + (' (niepełny etap)' if not result['ok'] else '') + ':\n' + text[:bound] + (
            '\n[Notatki skrócone do12000znaków; pełny zapis pozostaje w śladzie.]' if truncated else '')

    def retain(result, ident, stage, kind='final_answer'):
        if kind != 'final_answer':
            raise ValueError('intermediate cannot enter final candidates')
        complete = result['ok'] and usable(result.get('final'))
        text = result.get('final') if complete else result.get('partial_final')
        if not usable(text):
            return None
        if stage == 'essay_write' or (stage == 'control' and case.get('kind') == 'essay'):
            check = validate_stage_text(case, {'validation': 'essay_final'}, text)
            if not check['ok'] and not check['partial_eligible']:
                return None
            complete = complete and check['ok']
        c = {'candidate_id': ident, 'stage': stage, 'answer': text, 'complete': bool(complete)}
        candidates.append(c)
        event({'event': 'candidate_retained', **c})
        return c

    try:
        if route == 'control':
            suffix = essay.ESSAY_RULES if case.get('kind') == 'essay' else 'Rozwiąż oryginalne zadanie. Zwróć kompletną wymaganą odpowiedź, opartą na pełnym materiale.'
            result = call('control', 'final_answer', suffix,
                          validation='essay_final' if case.get('kind') == 'essay' else 'text')
            retain(result, 'control', 'control')
            selected = fallback(candidates)
        elif route == 'closed':
            for n, key in enumerate(('positive', 'contradictions', 'consistency'), 1):
                # No candidate is passed into another independent candidate.
                result = call('candidate_' + str(n), 'final_answer', PROMPTS['closed_candidate_' + key])
                retain(result, 'c' + str(n), 'candidate_' + str(n))
            if candidates:
                rotation = sum(ord(c) for c in str(case['id'])) % len(candidates)
                ordered = candidates[rotation:] + candidates[:rotation]
                judge_notes = json.dumps([{'id': x['candidate_id'], 'answer': x['answer'],
                                         'incomplete': not x['complete']} for x in ordered], ensure_ascii=False)
                result = call('selector', 'selection', PROMPTS['closed_judge'] + SELECT_CONTRACT + FALLIBLE + judge_notes,
                              validation='selection', validation_context={'candidates': candidates})
                selected = parse_selection(result.get('final'), candidates) if result['ok'] else None
                if selected and selected['selection'] == 'new_answer':
                    retain({'ok': True, 'final': selected['answer']}, 'new', 'selector_NEW')
                if not selected:
                    selected = fallback(candidates)
                    event({'event': 'selector_fallback', 'reason': 'failed_or_invalid_selection'})
            else:
                # Still only the declared fourth slot: direct synthesis from source.
                result = call('selector_direct_fallback', 'final_answer',
                              'Wszystkie wcześniejsze próby zawiodły. Rozwiąż oryginalne zadanie bez zakładania ich odpowiedzi.')
                retain(result, 'new', 'selector_direct_fallback')
                selected = fallback(candidates)
        elif route == 'open':
            matrix = call('claims_evidence', 'intermediate', PROMPTS['open_matrix'])
            draft = call('draft', 'final_answer', PROMPTS['open_answer'] + notes(matrix, 'Macierz twierdzeń'), 'direct')
            retain(draft, 'draft', 'draft')
            review = call('coverage', 'final_answer', PROMPTS['open_coverage'] + notes(draft, 'Odpowiedź robocza'))
            c = retain(review, 'coverage', 'coverage')
            selected = {**c, 'selection': 'coverage_final'} if c and c['complete'] else fallback(candidates)
        elif route == 'image':
            observations = call('observations', 'intermediate', PROMPTS['image_observe'])
            interpretation = call('interpretation', 'image_interpretation',
                                  PROMPTS['image_interpret'] + IMAGE_CONTRACT + notes(observations, 'Obserwacje'),
                                  validation='image_interpretation')
            parsed = parse_interpretation(interpretation.get('final')) if interpretation['ok'] else None
            if parsed:
                retain({'ok': True, 'final': parsed['answer']}, 'interpretation', 'interpretation.answer')
            question = parsed['revisit_question'] if parsed else 'Poprzednia interpretacja nie dała poprawnej odpowiedzi. Sprawdź cechy potrzebne do odpowiedzi na oryginalne zadanie.'
            if question.strip():
                revisit = call('targeted_revisit', 'final_answer', PROMPTS['image_revisit'] + FALLIBLE +
                               json.dumps({'question': question, 'prior_answer': parsed['answer'] if parsed else None}, ensure_ascii=False))
                c = retain(revisit, 'revisit', 'targeted_revisit')
                selected = {**c, 'selection': 'revisit_final'} if c and c['complete'] else fallback(candidates)
            else:
                event({'event': 'stage_skipped', 'name': 'targeted_revisit', 'reason': 'no_material_visual_ambiguity'})
                selected = fallback(candidates)
        else:
            # This is NEW shared-runtime policy, not the immutable original
            # six-topic1 experiment's fail-plan=>no-writer semantics.
            item = case['essay_item']
            plan = call('essay_plan', 'intermediate', essay.PLAN_RULES + '\nWymagane aspekty: ' +
                        json.dumps(item['aspects'], ensure_ascii=False), validation='essay_plan')
            valid = plan['ok'] and essay.parse_plan(plan.get('final'), item)
            event({'event': 'plan_validation', 'ok': bool(valid), 'direct_writer_fallback': not valid})
            note = notes(plan, 'Omylna mapa argumentów') if valid else FALLIBLE + 'Plan nie przeszedł sprawdzenia. Napisz samodzielnie na podstawie oryginalnego pełnego polecenia; temat nr1.'
            result = call('essay_write', 'final_answer', essay.ESSAY_RULES + essay.FALLIBLE_NOTES + note, 'direct', 'essay_final')
            retain(result, 'essay', 'essay_write')
            selected = fallback(candidates)
    except Exception as exc:
        stopped = type(exc).__name__ + ': ' + str(exc)
        selected = fallback(candidates)
        event({'event': 'route_stopped', 'reason': stopped})
    scheduled = sum(e['event'] == 'stage_scheduled' for e in events)
    if scheduled > max_slots:
        raise RuntimeError('semantic slot invariant')
    outcome = {'case_id': case['id'], 'route': route, 'final': selected['answer'] if selected else None,
               'final_output_kind': 'final_answer' if selected else None,
               'complete': selected['complete'] if selected else False,
               'selection': selected.get('selection') if selected else 'no_usable_final',
               'selected_candidate_id': selected.get('candidate_id') if selected else None,
               'candidates': copy.deepcopy(candidates), 'scheduled_slots': scheduled,
               'max_semantic_slots': max_slots, 'stopped': stopped}
    event({'event': 'route_complete', 'outcome': outcome})
    return outcome
