"""Frozen four-case assembly and semantic driver; CLI is CPU check only."""
import argparse
import base64
import copy
import hashlib
import json
import mimetypes
from pathlib import Path

import structured_routes as routes

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_cases(repo):
    repo = Path(repo).resolve()
    panel = json.loads((HERE / 'prompt-study-panel.json').read_text(encoding='utf8'))
    budget = json.loads((HERE / 'prompt-study-budget-v2.json').read_text(encoding='utf8'))
    for name, expected in budget['freeze_pins'].items():
        if sha((HERE / name).read_bytes()) != expected:
            raise ValueError('proposal pin changed: ' + name)
    source = repo / 'agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2.jsonl'
    if sha(source.read_bytes()) != panel['source_v2_sha256']:
        raise ValueError('known validation input changed')
    rows = {r['id']: r for r in map(json.loads, source.read_text(encoding='utf8').splitlines())}
    essays = {r['item']: r for r in json.loads((HERE / 'prepared-v1/inputs.json').read_text(encoding='utf8'))}
    cases = []
    for item in panel['items']:
        ident = item['id']
        text = essays[ident]['full_task'] if item['route'] == 'essay' else rows[ident]['prompt']
        if sha(text.encode('utf8')) != item['prompt_sha256']:
            raise ValueError('exact prompt pin changed: ' + ident)
        images = []
        if item['route'] != 'essay':
            original_images = rows[ident].get('images', [])
            if len(original_images) != len(item['images']):
                raise ValueError('image count changed')
            for original, pinned in zip(original_images, item['images']):
                name = original.get('path') if isinstance(original, dict) else original
                if name != pinned['path']:
                    raise ValueError('image order changed')
                f = source.parent / name
                raw = f.read_bytes()
                if sha(raw) != pinned['sha256']:
                    raise ValueError('complete image pin changed')
                mime = mimetypes.guess_type(name)[0]
                if mime not in ('image/png', 'image/jpeg', 'image/webp'):
                    raise ValueError('unsupported image MIME')
                images.append({'type': 'image_url', 'image_url': {'url': 'data:' + mime + ';base64,' + base64.b64encode(raw).decode()}})
        content = [{'type': 'text', 'text': text}, *images] if images else text
        case = {'id': ident, 'content': content, 'kind': 'essay' if item['route'] == 'essay' else 'question',
                'structured_route': {'open_source': 'open'}.get(item['route'], item['route'])}
        if item['route'] == 'essay':
            case['essay_item'] = essays[ident]
        cases.append(case)
    if [x['id'] for x in cases] != budget['items']:
        raise ValueError('panel order differs from budget')
    return cases, budget


def run_study(cases, invoke, emit):
    """Host owner supplies its audited bounded callback and durable sink.

    No authorization, wallclock, reservation, retry or export logic lives here.
    The invoker enforces case.study_arm and the matched item wall allowance.
    No new route starts after a fatal/ownership/deadline exception.
    """
    jobs = []
    for index, original in enumerate(cases):
        for arm in (('strong_single', 'structured_routes') if index % 2 == 0 else ('structured_routes', 'strong_single')):
            case = copy.deepcopy(original)
            case.update(id=original['id'] + '__' + arm, source_case_id=original['id'], study_arm=arm)
            route = 'control' if arm == 'strong_single' else original['structured_route']
            jobs.append((case, route))
    results = [{'case_id': case['id'], 'route': route, 'final': None, 'final_output_kind': None,
                'complete': False, 'selection': 'unsent', 'candidates': [], 'scheduled_slots': 0,
                'stopped': None} for case, route in jobs]
    emit({'event': 'study_slots_frozen', 'slots': copy.deepcopy(results)})
    for index, (case, route) in enumerate(jobs):
        result = routes.orchestrate(case, route, invoke, emit)
        results[index] = result
        if result['stopped']:
            emit({'event': 'study_stopped', 'case_id': case['id'], 'reason': result['stopped'],
                  'all_slots': copy.deepcopy(results)})
            return results
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=HERE.parents[2])
    args = ap.parse_args()
    cases, budget = load_cases(args.repo)
    print(json.dumps({'status': 'PREPARED_CHECK_PASS_NOT_AUTHORIZED', 'cases': [c['id'] for c in cases],
                      'arms': budget['variants'], 'primary_stage_slots': budget['primary_max_calls'],
                      'max_calls_including_recovery': budget['max_calls'], 'model_calls': 0,
                      'max_requested_tokens': budget['max_requested_tokens']}))
