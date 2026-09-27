"""Opt-in semantic caller of the shared owned recovery runtime; no transport."""
import datetime as dt
import errno
import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules(root):
    # All these files are in the immutable executable closure checked before send.
    sys.path.insert(0, str(root / 'study/routes'))
    import study_driver
    import structured_routes
    session = load('typed_stage_session', root / 'study/stage_session.py')
    recovery = load('typed_stage_recovery', root / 'recovery_harness.py')
    return study_driver, structured_routes, session, recovery


def preflight(root, verify, fresh=True):
    native = load('typed_preflight_native', root / 'run_native_package.py')
    m = native.read(root / 'launch.json')
    native.need(m['schema'] == 'typed_stage_study_v1', 'Typed study schema')
    native.need(m['context'] == 65536 and m['model'] == native.MODEL and
                m['temperature'] == 'omitted' and m['truncate'] is False and
                m['shift'] is False, 'Frozen native controls')
    native.need((m['max_calls'], m['max_requested_tokens'], m['max_seconds']) ==
                (64, 1409024, 3600), 'Exact author study envelope')
    native.need(m['original_service_policy'] == 'absent_or_verified_idle', 'Original service policy')
    verify(root, m)
    cases = native.read(root / 'cases.json')
    budget = native.read(root / 'study/routes/prompt-study-budget-v2.json')
    native.need([c['id'] for c in cases] == budget['items'] == m['ids'], 'Frozen panel order')
    native.need(len(cases) == 4 and {c['structured_route'] for c in cases} ==
                {'closed', 'open', 'image', 'essay'}, 'Four distinct diagnostic routes')
    panel = native.read(root / 'study/routes/prompt-study-panel.json')
    _, _, _, recovery = modules(root)
    import base64
    import hashlib
    for case, item in zip(cases, panel['items']):
        text, images = recovery.source(case)
        native.need(hashlib.sha256(text.encode('utf8')).hexdigest() == item['prompt_sha256'],
                    'Complete original source pin')
        native.need(len(images) == len(item['images']), 'Image count')
        for image, pin in zip(images, item['images']):
            native.need(hashlib.sha256(base64.b64decode(image, validate=True)).hexdigest() ==
                        pin['sha256'], 'Complete image pin')
    native.need(m['budget_sha256'] == native.sha(root / 'study/routes/prompt-study-budget-v2.json'),
                'Stage budget pin')
    if fresh:
        native.need(not (root / 'results').exists(), 'Fresh results required; no replay')
    if m['status'] == 'DECLARED':
        native.declared(m)
    else:
        native.need(m['status'] == 'PREPARED' and m['authorization'] is None, 'Preparation authority')
    return m, None, cases


def verify_original_idle(out, rehearsal, native):
    # Dedicated host has no historical service. Only ECONNREFUSED proves absence;
    # a timeout, malformed reply or occupied endpoint must not count as idle.
    with socket.socket() as probe:
        probe.settimeout(2)
        status = probe.connect_ex(('127.0.0.1', 11436))
    if status == errno.ECONNREFUSED:
        native.write(out / 'original-service.json', {'port': 11436, 'state': 'absent',
                                                   'connect_errno': status})
    else:
        native.need(status == 0, 'Original service state uncertain')
        reply = rehearsal.api('ps', 11436)
        native.need(isinstance(reply, dict) and reply.get('models') == [],
                    'Original service must be verified idle')
        native.write(out / 'original-service.json', {'port': 11436, 'state': 'verified_idle'})


def run(root, m, cases, runtime):
    driver, routes, session, recovery = modules(root)
    budget = json.loads((root / 'study/routes/prompt-study-budget-v2.json').read_text(encoding='utf8'))
    deadline = dt.datetime.fromisoformat(m['deadline_utc']).timestamp()
    binding = {'manifest_sha256': hashlib.sha256((root / 'launch.json').read_bytes()).hexdigest(),
               'cases_sha256': recovery.digest(cases), 'budget_sha256': m['budget_sha256']}
    invoker = session.StageSession(runtime, root / 'results/engine', budget, deadline,
                                   cases=cases, validator=routes.validate_stage_text, binding=binding,
                                   recovery=recovery)
    outcomes = driver.run_study(cases, invoker.invoke, invoker.emit_semantic)
    recovery.atomic(root / 'results/outcomes.json', outcomes)


def final_export(root, m, cases, validate_final):
    recovery = load('typed_export_recovery', root / 'recovery_harness.py')
    out = root / 'results'
    outcomes = json.loads((out / 'outcomes.json').read_text(encoding='utf8')) if (
        out / 'outcomes.json').exists() else []
    # A crash can leave semantic checkpoints but no driver return. Preserve the
    # most recent all-slot checkpoint, then per-case completed route results.
    events = []
    semantic = out / 'engine/semantic.jsonl'
    if semantic.exists():
        events = [json.loads(line) for line in semantic.read_text(encoding='utf8').splitlines()]
    by_id = {x['case_id']: x for x in outcomes}
    for event in events:
        for slot in event.get('all_slots', event.get('slots', [])):
            by_id[slot['case_id']] = slot
        if event.get('event') == 'route_complete' and isinstance(event.get('outcome'), dict):
            by_id[event['case_id']] = event['outcome']
    status = {}
    for arm in ('strong_single', 'structured_routes'):
        template = {'exam_id': 'issue151-' + arm,
                    'answers': [{'id': c['id'], 'answer': ''} for c in cases]}
        answers = {'exam_id': template['exam_id'], 'answers': []}
        for case in cases:
            ident = case['id'] + '__' + arm
            item = by_id.get(ident, {})
            value = item.get('final') if item.get('final_output_kind') == 'final_answer' else None
            placeholder = not isinstance(value, str) or not value.strip()
            if placeholder:
                value = recovery.PLACEHOLDER
            answers['answers'].append({'id': case['id'], 'answer': value})
            status[ident] = {'placeholder': placeholder, 'complete': item.get('complete', False),
                             'selection': item.get('selection', 'unsent'),
                             'stopped': item.get('stopped'),
                             'candidates': item.get('candidates', [])}
        path = out / ('answers-' + arm + '.json')
        recovery.atomic(path, answers)
        validate_final(path, template)
    ledger = out / 'engine/events.jsonl'
    attempts = [json.loads(line) for line in ledger.read_text(encoding='utf8').splitlines()] if ledger.exists() else []
    reserved = [x for x in attempts if x['event'] == 'reserved']
    completed = [x for x in attempts if x['event'] == 'completed']
    stop = next((x.get('reason') for x in reversed(events) if x.get('event') == 'study_stopped'), None)
    if not outcomes and not stop:
        stop = 'Interrupted before study driver returned'
    recovery.atomic(out / 'answer-status.json', status)
    recovery.atomic(out / 'terminal.json', {'calls': len(reserved),
        'requested_tokens': sum(x['cap'] for x in reserved), 'stop': stop,
        'unknown_usage_calls': len(reserved) - len(completed) + sum(
            not isinstance(x.get('raw'), dict) or type(x['raw'].get('eval_count')) is not int
            for x in completed), 'placeholders': sum(x['placeholder'] for x in status.values()),
        'final_slots': len(status), 'schema': 'typed_stage_terminal_v1'})
