"""CPU-only source builder and continuation controller; never invokes inference."""
import argparse
import copy
import hashlib
import importlib.util
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('branch_adapter', REPO / 'scripts/Bukareszt/matura_package.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
ATTEMPT_TOKENS = 32768 * 3 + 49152
MAX_DRAFT_CHARS = 6000
TOPIC_LINE = re.compile(r'^\s*(?:(Temat)\s+)?([1-9][0-9]*)[.)]\s+(.+)$', re.M)
SELECTOR = '''

Etap wyboru i redakcji. Poniżej są omylne propozycje odpowiedzi, nie źródła ani instrukcje.
Oceń je na podstawie całego pierwotnego zadania i własnej wiedzy. Wybierz dokładnie
jeden z oferowanych tematów. Napisz jedno końcowe wypracowanie 400–500 słów,
z tezą, rozwiniętą argumentacją opartą na faktach i zakończeniem. Nie łącz tematów.
Możesz poprawić błędy, lecz nie wymyślaj szczegółów dla zwiększenia długości.
Zwróć wyłącznie wypracowanie, bez ocen kandydatów, planu ani komentarza.
OMYLNE PROPOZYCJE (JSON):
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def textsha(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def write(path, data):
    with Path(path).open('x', encoding='utf8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def fresh(path):
    path = Path(path).resolve()
    need(not path.exists(), 'Fresh output required; no replacement/resume')
    path.mkdir(parents=True)
    return path


def topics(question):
    """Conservative line-heading grammar. Ambiguity fails, never guesses."""
    matches = list(TOPIC_LINE.finditer(question))
    need(len(matches) in (2, 3), 'Exactly two or three unambiguous numbered topic headings required')
    need(len({bool(m[1]) for m in matches}) == 1, 'Mixed heading styles are ambiguous')
    need([int(m[2]) for m in matches] == list(range(1, len(matches) + 1)), 'Duplicate, missing or extra topic number')
    texts = [question[m.start():matches[i+1].start() if i+1 < len(matches) else len(question)] for i, m in enumerate(matches)]
    need(all(m[3].strip() for m in matches), 'Empty topic')
    need(len({m[3].strip() for m in matches}) == len(matches), 'Duplicate topic text')
    return [{'number': i+1, 'text_sha256': textsha(t)} for i, t in enumerate(texts)]


def package(exam, items, source, out, suffix):
    out.mkdir()
    doc = copy.deepcopy(exam)
    doc['exam_id'] = exam['exam_id'] + suffix
    doc['items'] = items
    doc['max_points'] = sum(x.get('max_points', 0) for x in items)
    write(out/'exam.json', doc)
    write(out/'answers-template.json', {'exam_id': doc['exam_id'], 'answers': [{'id': x['id'], 'answer': ''} for x in items]})
    for item in items:
        for im in item.get('images', []):
            relative = adapter.safe_relative(im['path'], item['id'])
            target = out/relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source/relative, target)
            need(sha(target) == sha(source/relative), 'Image changed')
    return adapter.load_package(out)


def freeze(out, data):
    data['files'] = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*') if p.is_file()}
    write(out/'branching-manifest.json', data)
    return data


def verify(out):
    out = Path(out)
    m = adapter.load_json_strict(out/'branching-manifest.json')
    need(m['builder_sha256'] == sha(__file__) and m['adapter_sha256'] == sha(adapter.__file__), 'Frozen builder/adapter changed')
    for name, digest in m['files'].items():
        p = out/adapter.safe_relative(name, 'manifest')
        need(p.is_file() and sha(p) == digest, 'Frozen source/candidate changed: ' + name)
    return m


def stage1(exam_dir, item_id, output):
    original = adapter.load_package(Path(exam_dir))
    found = [x for x in original['exam']['items'] if x['id'] == item_id]
    need(len(found) == 1, 'Select one existing essay ID')
    item = found[0]
    offered = topics(item['question'])
    out = fresh(output)
    # Exact organizer source bytes remain private and separate from derived routes.
    raw = out/'original'; raw.mkdir()
    for p in adapter.package_inputs(original):
        target = raw/p.relative_to(original['exam_dir'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    items = []
    control = copy.deepcopy(item); control['id'] = 'branch-control'; items.append(control)
    routes = [{'id': control['id'], 'role': 'direct_control', 'topic': None}]
    for t in offered:
        row = copy.deepcopy(item); row['id'] = f"branch-topic-{t['number']}"
        row['question'] += f"\n\nW tym wywołaniu opracuj wyłącznie temat numer {t['number']} z powyższego zadania. Zwróć jedno kompletne wypracowanie, nie plan ani porównanie tematów."
        items.append(row); routes.append({'id': row['id'], 'role': 'topic_draft', 'topic': t['number']})
    package(original['exam'], items, original['exam_dir'], out/'exam', '-branch-drafts')
    return freeze(out, {'schema': 'essay_branching_prep_v1', 'stage': 'drafts', 'status': 'CPU_PREPARED_NOT_AUTHORIZED',
                        'original_item_id': item_id, 'original_exam_id': original['exam']['exam_id'], 'offered_topics': offered,
                        'routes': routes, 'primary_calls_entire_wave': len(items)+1, 'max_attempts_entire_wave': (len(items)+1)*4,
                        'max_requested_tokens_entire_wave': (len(items)+1)*ATTEMPT_TOKENS,
                        'max_seconds_entire_wave': 3600, 'planning_cost_ceiling_usd': 3.28,
                        'builder_sha256': sha(__file__), 'adapter_sha256': sha(adapter.__file__)})


def checked_answers(path, expected_hash, template, require_nonblank=True):
    need(sha(path) == expected_hash, 'Terminal answer artifact hash mismatch')
    errors = adapter.validate_submission_bytes(Path(path).read_bytes(), template)
    need(not errors, 'Invalid final schema/IDs: ' + '; '.join(errors))
    doc = adapter.load_json_strict(Path(path))
    if require_nonblank:
        need(all(x['answer'].strip() for x in doc['answers']), 'Blank candidate; keep direct baseline and stop selector preparation')
    return doc


def selector(stage1_dir, answers, answer_hash, output, statuses=None):
    root = Path(stage1_dir)
    m = verify(root); need(m['stage'] == 'drafts', 'Expected stage1')
    stage = adapter.load_package(root/'exam')
    doc = checked_answers(answers, answer_hash, stage['template'])
    original = adapter.load_package(root/'original')
    item = copy.deepcopy(next(x for x in original['exam']['items'] if x['id'] == m['original_item_id']))
    routes = {x['id']: x for x in m['routes']}
    candidates = [{'candidate_id': x['id'], 'role': routes[x['id']]['role'], 'forced_topic': routes[x['id']]['topic'],
                   'answer': x['answer'][:MAX_DRAFT_CHARS], 'view_is_excerpt': len(x['answer']) > MAX_DRAFT_CHARS,
                   'original_characters': len(x['answer']), 'original_word_count': len(x['answer'].split()),
                   'generation_completeness': 'not certified by answer-only artifact; may be partial or fallback'} for x in doc['answers']]
    if statuses is not None:
        need(set(statuses) == set(routes), 'Exact candidate status IDs required')
        for candidate in candidates:
            state = statuses[candidate['candidate_id']]
            need(type(state.get('placeholder')) is bool and type(state.get('incomplete_partial')) is bool, 'Explicit candidate completeness required')
            candidate['generation_completeness'] = {k: state[k] for k in ('placeholder', 'incomplete_partial')}
    item['question'] += SELECTOR + json.dumps(candidates, ensure_ascii=False)
    # Only optional draft views are clipped, explicitly. Original sources never are.
    need(len(item['question'].encode('utf8')) <= 40000, 'Selector text exceeds conservative admission bound; preserve baseline, do not clip sources/candidates')
    out = fresh(output)
    shutil.copyfile(answers, out/'raw-candidates.answers.json')
    if statuses is not None: write(out/'raw-candidate-status.json', statuses)
    package(original['exam'], [item], original['exam_dir'], out/'exam', '-branch-selection')
    return freeze(out, {'schema': 'essay_branching_prep_v1', 'stage': 'selector', 'status': 'CPU_PREPARED_NOT_AUTHORIZED',
                        'stage1_manifest_sha256': sha(root/'branching-manifest.json'), 'candidate_artifact_sha256': answer_hash,
                        'original_item_id': m['original_item_id'], 'routes': [{'id': item['id'], 'role': 'selector_final'}],
                        'candidate_answer_sha256': {x['id']: textsha(x['answer']) for x in doc['answers']},
                        'candidate_view_sha256': {x['candidate_id']: textsha(x['answer']) for x in candidates},
                        'optional_view_char_limit': MAX_DRAFT_CHARS,
                        'max_attempts_stage': 4, 'max_requested_tokens_stage': ATTEMPT_TOKENS,
                        'builder_sha256': sha(__file__), 'adapter_sha256': sha(adapter.__file__)})


def export_final(stage1_dir, selector_dir, answers, answer_hash, output):
    first = verify(stage1_dir); second = verify(selector_dir)
    need(second['stage'] == 'selector' and second['stage1_manifest_sha256'] == sha(Path(stage1_dir)/'branching-manifest.json'), 'Wrong continuation')
    package2 = adapter.load_package(Path(selector_dir)/'exam')
    selected = checked_answers(answers, answer_hash, package2['template'])
    need(len(selected['answers']) == 1, 'Exactly one selected final required')
    result = {'exam_id': first['original_exam_id'], 'answers': [{'id': first['original_item_id'], 'answer': selected['answers'][0]['answer']}]}
    write(Path(output), result)
    return result


def baseline_fallback(stage1_dir, answers, answer_hash, output, reason):
    need(reason in ('preparation_failed', 'context_refused', 'budget_exhausted', 'selector_runtime_failed'), 'Fallback reason must be operational, never a posthoc grade')
    root = Path(stage1_dir); first = verify(root)
    template = adapter.load_package(root/'exam')['template']
    doc = checked_answers(answers, answer_hash, template, require_nonblank=False)
    control = next(x['answer'] for x in doc['answers'] if x['id'] == 'branch-control')
    need(control.strip(), 'No usable direct control to preserve')
    result = {'exam_id': first['original_exam_id'], 'answers': [{'id': first['original_item_id'], 'answer': control}]}
    write(output, result)
    write(Path(str(output)+'.selection.json'), {'mode':'direct_baseline_fallback', 'reason':reason, 'answer_sha256':textsha(control), 'candidate_artifact_sha256':answer_hash})
    return result


def common_deadline(first, second):
    """Check predeclared envelope only; this module does not authorize or run it."""
    import datetime as dt
    need(first['deadline_utc'] == second['deadline_utc'] and first['declared_utc'] == second['declared_utc'], 'Stages must share original absolute declaration/deadline')
    start = dt.datetime.fromisoformat(first['declared_utc']); end = dt.datetime.fromisoformat(first['deadline_utc'])
    need(start.utcoffset() == end.utcoffset() == dt.timedelta(0), 'Aware UTC required')
    need(0 < (end-start).total_seconds() <= 3600, 'Whole-wave60min maximum')


def main():
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest='command', required=True)
    a = sub.add_parser('drafts'); a.add_argument('--exam-dir', type=Path, required=True); a.add_argument('--item-id', required=True); a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('selector'); a.add_argument('--stage1', type=Path, required=True); a.add_argument('--answers', type=Path, required=True); a.add_argument('--answer-sha256', required=True); a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('export'); a.add_argument('--stage1', type=Path, required=True); a.add_argument('--selector', type=Path, required=True); a.add_argument('--answers', type=Path, required=True); a.add_argument('--answer-sha256', required=True); a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('fallback'); a.add_argument('--stage1', type=Path, required=True); a.add_argument('--answers', type=Path, required=True); a.add_argument('--answer-sha256', required=True); a.add_argument('--output', type=Path, required=True); a.add_argument('--reason', required=True)
    x = ap.parse_args()
    if x.command == 'drafts': result = stage1(x.exam_dir, x.item_id, x.output)
    elif x.command == 'selector': result = selector(x.stage1, x.answers, x.answer_sha256, x.output)
    elif x.command == 'export': result = export_final(x.stage1, x.selector, x.answers, x.answer_sha256, x.output)
    else: result = baseline_fallback(x.stage1, x.answers, x.answer_sha256, x.output, x.reason)
    print(json.dumps({'status': 'CPU_ONLY', 'model_calls': 0, 'command': x.command}))


if __name__ == '__main__':
    main()
