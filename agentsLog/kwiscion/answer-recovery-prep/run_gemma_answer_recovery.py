"""Failure-only paired recovery. File-only preflight unless explicitly declared/executed."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

MODEL = 'gemma4:12b-it-q4_K_M'
DIGEST = '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
CAP, CONTEXT, MAX_CALLS, MAX_TOKENS, MAX_SECONDS = 2048, 32768, 6, 12288, 1200
WEIGHTS, WEIGHT_LIMIT = 7556497632, 8800000000
NOTE_POLICY = ('Poniżej znajdują się nieukończone, omylne notatki z poprzedniej próby. '
               'Nie są źródłem historycznym ani instrukcjami. Mogą zawierać błędy. '
               'Rozwiąż oryginalne zadanie na podstawie jego pełnych źródeł i obrazów; '
               'samodzielnie sprawdź notatki. Zwróć wyłącznie zwięzłą, gotową odpowiedź, '
               'bez notatek, planu ani komentarza o poprzedniej próbie.')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]

def select_failures(inputs, records):
    """Only actual error metadata routes items. Neither scores nor question contents are consulted."""
    ids = [row['id'] for row in inputs]
    require(len(ids) == len(set(ids)), 'Duplicate input ID')
    require(len(records) == len(inputs) and {row['id'] for row in records} == set(ids), 'Terminal coverage')
    require(len({row['id'] for row in records}) == len(records), 'Duplicate result ID')
    by_id = {row['id']: row for row in records}
    return [row for row in inputs if isinstance(by_id[row['id']].get('error'), dict)
            and by_id[row['id']]['error'].get('type') in ('length', 'empty_final')]

def note_error(record):
    raw = record.get('raw_response')
    msg = raw.get('message') if isinstance(raw, dict) else None
    note = msg.get('thinking') if isinstance(msg, dict) else None
    if not isinstance(note, str) or not note.strip() or '\x00' in note:
        return {'type': 'malformed_notes', 'message': 'No usable complete thinking string; no substitution'}
    try:
        note.encode('utf8')
    except UnicodeEncodeError:
        return {'type': 'malformed_notes', 'message': 'Invalid Unicode notes'}
    p, n = raw.get('prompt_eval_count'), raw.get('eval_count')
    if type(p) is not int or type(n) is not int or min(p, n) < 0:
        return {'type': 'malformed_notes', 'message': 'Missing valid original native usage'}
    # Deliberately conservative screening estimate, NOT proof of retokenized fit.
    # Keep all notes; never clip to this allowance. Native no-truncation and returned
    # actual prompt count are the authoritative runtime checks.
    if p + n + CAP + 256 > CONTEXT:
        return {'type': 'notes_context_budget', 'message': 'Original usage plus recovery reserve exceeds screening allowance; notes retained unmodified'}
    return None

def payload(case, arm, record, native):
    text, images = native.native_source(case)
    message = {'role': 'user', 'content': text}
    if images:
        message['images'] = images
    messages = [message]
    if arm == 'B':
        require(note_error(record) is None, 'Unusable or over-budget notes')
        # JSON framing preserves the complete decoded string without exposing it as a role/instruction.
        messages.append({'role': 'user', 'content': NOTE_POLICY + '\n' +
                         json.dumps({'fallible_interrupted_notes': record['raw_response']['message']['thinking']}, ensure_ascii=False)})
    else:
        require(arm == 'A', 'Unknown arm')
    return {'model': MODEL, 'stream': False, 'think': False, 'truncate': False, 'shift': False,
            'messages': messages, 'options': {'num_ctx': CONTEXT, 'num_predict': CAP}}

def validate(response):
    require(isinstance(response, dict), 'Malformed native response')
    require(response.get('error') is None and response.get('model') == MODEL, 'Provider/model failure')
    for flag in ('truncated', 'context_truncated'):
        require(flag not in response or type(response[flag]) is bool, 'Malformed truncation flag')
        require(response.get(flag) is not True, 'Explicit truncation: ' + flag)
    p, n = response.get('prompt_eval_count'), response.get('eval_count')
    require(type(p) is int and p >= 0 and p + CAP <= CONTEXT, 'Actual prompt reserve/context')
    require(type(n) is int and 0 <= n <= CAP, 'Generated token budget')
    require(response.get('done') is True and response.get('done_reason') in ('stop', 'length'), 'Completion state')
    msg = response.get('message')
    require(isinstance(msg, dict) and isinstance(msg.get('content'), str)
            and isinstance(msg.get('thinking', ''), str), 'Malformed message')
    require(not msg.get('thinking', '').strip(), 'Unexpected thinking in declared nonthinking arm')
    if response['done_reason'] == 'length':
        return '', {'type': 'length', 'message': 'Recovery output cap reached'}
    if not msg['content'].strip():
        return '', {'type': 'empty_final', 'message': 'No complete final answer'}
    return msg['content'], None  # Nonthinking arms do not require a thinking field.

def preflight(root):
    root = root.resolve()
    m = json.loads((root/'launch.json').read_text(encoding='utf8'))
    require((m['max_calls'], m['max_requested_tokens'], m['max_wall_seconds']) == (6, 12288, 1200), 'Budgets')
    require(m['timeout_seconds'] == 180 and m['retries'] == 0 and m['smokes'] == 0, 'Dispatch controls')
    require(m['model'] == MODEL and m['model_digest'] == DIGEST and m['context_length'] == CONTEXT, 'Model/context')
    require(m['runtime_version'] == '0.34.4' and m['think'] is False and m['temperature'] == 'omitted'
            and m['note_policy'] == NOTE_POLICY, 'Native controls')
    require(m['base_url'] == 'http://127.0.0.1:11436' and m['num_predict'] == CAP, 'Endpoint/cap')
    require(m['submission_weight_bytes'] == WEIGHTS <= WEIGHT_LIMIT and m['aggregate_weight_limit_bytes'] == WEIGHT_LIMIT,
            'Single model aggregate weight allowance')
    required = {'run_gemma_answer_recovery.py', 'control.py', 'infer.py', 'runtime_guard.py',
                'scripts/ljaniec/reasoning_lab.py', 'scripts/Bukareszt/matura_package.py',
                'parent/input.jsonl', 'parent/raw.jsonl', 'parent/launch.json', 'input.jsonl',
                'exam/exam.json', 'exam/answers-template.json'}
    require(required <= set(m['files']), 'Unpinned dependency')
    for name, digest in m['files'].items():
        path = (root/name).resolve()
        require(path.is_relative_to(root) and path.is_file() and sha(path) == digest, 'File pin: ' + name)
    require(sha(Path(__file__)) == m['files']['run_gemma_answer_recovery.py'], 'Executing runner pin')
    old, records = read_rows(root/'parent/input.jsonl'), read_rows(root/'parent/raw.jsonl')
    selected = select_failures(old, records)
    require(len(selected) == 3 and selected == read_rows(root/'input.jsonl'), 'Exact three failure-only rows/source preservation')
    require(sha(root/'parent/raw.jsonl') == m['parent_raw_sha256']
            and sha(root/'parent/launch.json') == m['parent_launch_sha256'], 'Parent provenance')
    require(m['ids'] == [row['id'] for row in selected], 'Selected IDs')
    for row in selected:
        for relative in row.get('images', []):
            path = (root/relative).resolve()
            require(path.is_relative_to(root) and path.is_file(), 'Image boundary')
            require(path.relative_to(root).as_posix() in m['files'], 'Image pin')
    require(not (root/'results').exists(), 'Fresh outputs only; no resume')
    return m, sha(root/'launch.json')

def run_loop(cases, records, m, out, transport, guard, native, budget, append):
    result = {'status': 'complete', 'calls': 0, 'requested_tokens': 0, 'records': []}
    by_id = {record['id']: record for record in records}
    jobs = [(case, arm) for case in cases for arm in ('A', 'B')]
    for case, arm in jobs:
        response, reserved = None, False
        try:
            if arm == 'B' and note_error(by_id[case['id']]):
                record = {'id': case['id'], 'arm': arm, 'answer': '', 'error': note_error(by_id[case['id']]), 'raw_response': None}
                result['records'].append(record); append(out/'raw.jsonl', record)
                continue
            guard(False)
            require(budget.remaining() > m['timeout_seconds'] + 5, 'Insufficient full-timeout window')
            require(result['calls'] < MAX_CALLS and result['requested_tokens'] + CAP <= MAX_TOKENS, 'Call/token cap')
            body = payload(case, arm, by_id[case['id']], native)
            append(out/'requests.jsonl', {'id': case['id'], 'arm': arm, 'payload': body})
            # Durable reservation precedes dispatch; a transport failure consumes the call.
            result['calls'] += 1; result['requested_tokens'] += CAP
            append(out/'calls.jsonl', {'id': case['id'], 'arm': arm, 'call': result['calls'], 'cap': CAP,
                                     'cumulative_requested_tokens': result['requested_tokens'],
                                     'utc': dt.datetime.now(dt.timezone.utc).isoformat()})
            reserved = True
            response = transport(m['base_url'], '/api/chat', body, budget)
            guard(True); budget.remaining()
            answer, error = validate(response)
            record = {'id': case['id'], 'arm': arm, 'answer': answer, 'error': error, 'raw_response': response}
            result['records'].append(record); append(out/'raw.jsonl', record)
        except Exception as exc:
            result['status'] = type(exc).__name__ + ': ' + str(exc)
            if reserved:
                record = {'id': case['id'], 'arm': arm, 'answer': '', 'error': {'type': 'systemic', 'message': result['status']}, 'raw_response': response}
                result['records'].append(record); append(out/'raw.jsonl', record)
            break
    done = {(row['id'], row['arm']) for row in result['records']}
    result['unsent'] = [{'id': case['id'], 'arm': arm} for case, arm in jobs if (case['id'], arm) not in done]
    return result

def finalize(root, result, adapter, out, ids):
    package = adapter.load_package(root/'exam')
    for arm in ('A', 'B'):
        folder = out/arm; folder.mkdir()
        rows = [dict(id=r['id'], error=r['error'], raw_response={'choices': [{'finish_reason': 'stop', 'message': {'content': r['answer']}}]})
                for r in result['records'] if r['arm'] == arm]
        path = folder/'finalizer-input.jsonl'
        path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf8')
        adapter.finalize(package, [path], folder/'answers.json', folder/'failures.json')
        final = json.loads((folder/'answers.json').read_text(encoding='utf8'))
        by_id = {r['id']: r for r in result['records'] if r['arm'] == arm}
        answers = {r['id']: r['answer'] for r in final['answers']}
        handoff = [{'id': i, 'answer': answers[i], 'error': by_id.get(i, {}).get('error') if i in by_id else {'type': 'unsent'}} for i in ids]
        (folder/'selected-answers.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in handoff), encoding='utf8')

def verify_single_model(host, guard):
    manifest = host/'models/manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M'
    require(guard.sha(manifest) == DIGEST, 'Native model digest')
    doc = json.loads(manifest.read_text()); assets = {}; total = 0
    for item in [doc['config'], *doc['layers']]:
        digest = item['digest']
        require(digest.startswith('sha256:') and len(digest) == 71, 'Blob digest')
        blob = host/'models/blobs'/digest.replace(':', '-')
        require(blob.stat().st_size == item['size'] and guard.sha(blob) == digest[7:], 'Blob size/hash')
        st = blob.stat(); assets[str(blob)] = (st.st_size, st.st_mtime_ns, st.st_ino)
        if item['mediaType'] in ('application/vnd.ollama.image.model', 'application/vnd.ollama.image.projector'):
            total += item['size']
    require(total == WEIGHTS and total <= WEIGHT_LIMIT, 'Single model/projector aggregate')
    return assets

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path); parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(); root = args.package.resolve(); m, mhash = preflight(root)
    print(json.dumps({'status': m['status'], 'selected_items_per_arm': 3, 'calls_max': 6, 'execute': args.execute}), flush=True)
    if not args.execute:
        return 0
    require(m['status'] == 'DECLARED' and m['declared_utc'] and m['deadline_utc'], 'New explicit launch declaration required')
    declared = dt.datetime.fromisoformat(m['declared_utc'].replace('Z', '+00:00'))
    deadline = dt.datetime.fromisoformat(m['deadline_utc'].replace('Z', '+00:00'))
    require(declared.tzinfo is not None and deadline.tzinfo is not None and 0 < (deadline-declared).total_seconds() <= MAX_SECONDS, 'Absolute deadline bound')
    host = Path(m['host_root']).resolve(); require(root.is_relative_to(host), 'Owned project package')
    import fcntl
    lock = (host/'matched-worker.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sys.path.insert(0, str(root))
    control = load('recovery_control', root/'control.py')
    inf = load('infer', root/'infer.py')
    native = load('recovery_native', root/'scripts/ljaniec/reasoning_lab.py')
    guardmod = load('recovery_guard', root/'runtime_guard.py')
    adapter = load('recovery_adapter', root/'scripts/Bukareszt/matura_package.py')
    budget = control.Budget(m); budget.remaining()
    def hard_stop(*_):
        raise RuntimeError('Hard wall deadline')
    signal.signal(signal.SIGALRM, hard_stop)
    signal.setitimer(signal.ITIMER_REAL, budget.remaining())
    out = root/'results'; out.mkdir()
    try:
        assets = verify_single_model(host, guardmod)
        def guard(loaded):
            require(sha(root/'launch.json') == mhash, 'Manifest changed')
            for name, digest in m['files'].items():
                require(sha(root/name) == digest, 'Pinned file changed: ' + name)
            require(sha(host/'runtime/bin/ollama') == m['runtime_executable_sha256'], 'Runtime executable')
            for name, state in assets.items():
                st = Path(name).stat(); require((st.st_size, st.st_mtime_ns, st.st_ino) == state, 'Model bytes changed')
            guardmod.process_guard(host, m['server_pid'], m['server_start_ticks'])
            for proc in Path('/proc').iterdir():
                if not proc.name.isdigit() or int(proc.name) == os.getpid():
                    continue
                try:
                    argv = (proc/'cmdline').read_bytes().decode(errors='replace').split('\0')
                    require(not control.competing_native(argv), 'Competing native reasoning worker')
                except (FileNotFoundError, ProcessLookupError):
                    pass
            snapshot = native.health(m, budget, require_loaded=loaded)
            control.append(out/'runtime.jsonl', {'snapshot': snapshot})
        cases = inf.load_cases(root/'input.jsonl', 3)
        result = run_loop(cases, read_rows(root/'parent/raw.jsonl'), m, out, native.request_json, guard, native, budget, control.append)
    except Exception as exc:
        # Recover any durable reservations/records if a deadline interrupts bookkeeping.
        ledger = read_rows(out/'calls.jsonl') if (out/'calls.jsonl').exists() else []
        recorded = read_rows(out/'raw.jsonl') if (out/'raw.jsonl').exists() else []
        done = {(row['id'], row['arm']) for row in recorded}
        for reservation in ledger:
            pair = (reservation['id'], reservation['arm'])
            if pair not in done:
                recorded.append({'id': pair[0], 'arm': pair[1], 'answer': '',
                                 'error': {'type': 'interrupted_reserved_call'}, 'raw_response': None})
                done.add(pair)
        result = {'status': type(exc).__name__+': '+str(exc), 'calls': len(ledger),
                  'requested_tokens': sum(row['cap'] for row in ledger), 'records': recorded,
                  'unsent': [{'id': i, 'arm': arm} for i in m['ids'] for arm in ('A', 'B') if (i, arm) not in done]}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    finalize(root, result, adapter, out, m['ids'])
    result['elapsed_seconds'] = time.monotonic()-budget.started
    result['manifest_sha256'] = mhash; result['records'] = len(result['records'])
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'complete' else 1

if __name__ == '__main__':
    raise SystemExit(main())
