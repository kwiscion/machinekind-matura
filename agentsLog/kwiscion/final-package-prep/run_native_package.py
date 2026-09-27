"""Arbitrary organizer packages, native Gemma thinking; CPU preflight by default.

Only the separately declared Linux guardian path can start the owned server.
No retries, fallback, retrieval, automatic essay detection, or model downloads.
"""
import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import sys
import time
import urllib.request

sys.dont_write_bytecode = True
MODEL = 'gemma4:12b-it-q4_K_M'
CONTEXT = 32768
ESSAY_POLICY = ('Wybierz dokładnie jeden z podanych tematów. Napisz wyłącznie gotowe '
                'wypracowanie na ten temat, 400–500 słów ciągłego tekstu. Uwzględnij wszystkie '
                'wymagane aspekty i materiały wybranego tematu. Bez planu, komentarzy o pisaniu, '
                'liczniku słów ani drugiego wypracowania. Pozostałych tematów nie opracowuj. '
                'Jeżeli oryginalny format odpowiedzi wymaga numeru wybranego tematu, podaj ten numer przed wypracowaniem; nie usuwaj go jako metadanych.')
PINS = {
    'run_gemma_offline.py': 'd4f26d319b88d479ad3eaa0a7afe2d4ce68706e4dd75324e5d4d4d83fa1c036b',
    'guard.py': '8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473',
    'offline_rehearsal.py': '376298ea5a17c603521b66ed9922485ea76f0033eacb0f53642fa0827986f7a5',
    'infer.py': 'd307356518aa8b35534525ceff39b9f3478366204ef5c3c81dd1299b3aacd782',
    'scripts/Bukareszt/matura_package.py': 'bec8b33731e24ff1ea845e7c7b0908d3227121986125cef8967fc384a1d8af74',
}


class GlobalStop(RuntimeError):
    """Runtime, identity, ownership, context, budget or evidence violation."""


class ItemFailure(ValueError):
    """A terminal, accounted request produced no usable complete final."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GlobalStop('HTTP redirect forbidden; no implicit extra request')


def need(condition, message):
    if not condition:
        raise GlobalStop(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def textsha(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'), object_pairs_hook=no_duplicates)


def line(value):
    # ensure_ascii escapes Unicode line separators; prompt strings decode unchanged.
    return json.dumps(value, ensure_ascii=True) + '\n'


def write(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as f:
        f.write(line(value)); f.flush(); os.fsync(f.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf8', newline='\n') as f:
        f.write(line(value)); f.flush(); os.fsync(f.fileno())


def rows(path):
    return [json.loads(x, object_pairs_hook=no_duplicates)
            for x in Path(path).read_text(encoding='utf8').split('\n') if x.strip()]


def safe_file(root, name):
    rel = PurePosixPath(name)
    need(isinstance(name, str) and rel.as_posix() == name and not rel.is_absolute()
         and '..' not in rel.parts and '\\' not in name and ':' not in name, 'Relative POSIX file path')
    p = root
    for part in rel.parts:
        p = p / part
        need(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)(), 'No links/junctions')
    need(p.is_file() and p.resolve().is_relative_to(root), 'Contained regular file')
    return p


def verify_files(root, m):
    for name, digest in m['files'].items():
        need(sha(safe_file(root, name)) == digest, 'Frozen file changed: ' + name)
    need(sha(Path(__file__)) == m['files']['run_native_package.py'], 'Executing runner changed')
    for name, digest in PINS.items():
        need(m['files'].get(name) == digest, 'Reviewed helper pin changed: ' + name)


def modules(root):
    return (load('native_offline_helpers', root / 'run_gemma_offline.py'),
            load('native_weights', root / 'guard.py'),
            load('native_rehearsal', root / 'offline_rehearsal.py'),
            load('native_adapter', root / 'scripts/Bukareszt/matura_package.py'),
            load('native_serializer', root / 'infer.py'))


def build_routes(original, essay_ids, no_essay):
    ids = [r['id'] for r in original]
    need(len(ids) == len(set(ids)) and ids, 'Nonempty unique item IDs')
    need(type(no_essay) is bool and bool(essay_ids) != no_essay, 'Explicit essay IDs OR explicit no-essay')
    need(len(essay_ids) == len(set(essay_ids)) and set(essay_ids) <= set(ids), 'Essay IDs must be unique received IDs')
    routed, routes = [], []
    for before in original:
        after = dict(before)
        essay = before['id'] in essay_ids
        if essay:
            after['prompt'] += '\n\n' + ESSAY_POLICY
        routed.append(after)
        routes.append({'id': before['id'], 'route': 'essay' if essay else 'ordinary',
                       'cap': 20480 if essay else 10240,
                       'original_prompt_sha256': textsha(before['prompt']),
                       'routed_prompt_sha256': textsha(after['prompt']),
                       'images': before['images']})
    return routed, routes


def declared(m, now=None):
    now = time.time() if now is None else now
    need(m['status'] == 'DECLARED', 'Root declaration required')
    times = []
    for name in ('declared_utc', 'deadline_utc'):
        value = dt.datetime.fromisoformat(m[name])
        need(value.utcoffset() == dt.timedelta(0), 'Aware UTC timestamps required')
        times.append(value.timestamp())
    start, end = times
    need(start <= now < end and 0 < end - start <= m['max_seconds'], 'Absolute declaration window')
    auth = m['authorization']
    need(isinstance(auth, dict) and auth.get('owner') == 'root' and
         isinstance(auth.get('reference'), str) and auth['reference'].strip(), 'Root authorization reference')
    need(auth.get('max_calls') == m['max_calls'] and
         auth.get('max_requested_tokens') == m['max_requested_tokens'] and
         auth.get('max_seconds') == m['max_seconds'], 'Exact authorized bounds')
    if m['max_requested_tokens'] > 240000:
        need(auth.get('above_240k_explicit') is True, 'Explicit root exception above 240000 tokens')
    return end - now


def remaining(m):
    return declared(m)


def preflight(root, fresh=True):
    m = read(root / 'launch.json')
    need(m['schema'] == 'native_organizer_package_v1', 'Manifest schema')
    need(m['status'] in ('PREPARED', 'DECLARED'), 'Manifest status')
    need(m['model'] == MODEL and m['think'] is True and m['temperature'] == 'omitted'
         and m['context'] == CONTEXT and m['truncate'] is False and m['shift'] is False
         and m['retries'] == 0, 'Native controls')
    need(type(m['max_seconds']) is int and 60 <= m['max_seconds'] <= 86400 and
         type(m['request_timeout']) is int and 30 <= m['request_timeout'] <= 3600 and
         m['request_timeout'] + 20 < m['max_seconds'], 'Finite time bounds')
    for name in ('cache', 'binary', 'lock'):
        need(isinstance(m[name], str) and m[name].startswith('/') and '..' not in PurePosixPath(m[name]).parts,
             'Explicit absolute Linux runtime paths')
    verify_files(root, m)
    _, _, _, adapter, inf = modules(root)
    package = adapter.load_package(root / 'exam')
    original = rows(root / 'input.original.jsonl')
    ids = [x['id'] for x in package['exam']['items']]
    need([x['id'] for x in original] == ids == m['ids'], 'Original item IDs/order')
    # Rebuild each adapter prompt independently of the prepared records.
    for row, item in zip(original, package['exam']['items']):
        need(row['prompt'] == adapter.build_prompt(package['exam'], item), 'Verbatim adapter prompt')
        expected = ['exam/' + adapter.safe_relative(x['path'], item['id']).as_posix() for x in item.get('images', [])]
        need(row['images'] == expected, 'Complete original image order')
    routed, routes = build_routes(original, m['essay_ids'], m['no_essay'])
    need(rows(root / 'input.jsonl') == routed and read(root / 'routes.json') == routes, 'Exact route contract')
    need(m['routes_sha256'] == sha(root / 'routes.json') and m['essay_policy_sha256'] == textsha(ESSAY_POLICY), 'Route/policy hashes')
    need(type(m['max_calls']) is int and m['max_calls'] == len(ids) and
         type(m['max_requested_tokens']) is int and m['max_requested_tokens'] == sum(r['cap'] for r in routes), 'Exact N and sum of caps')
    expected = set(PINS) | {'run_native_package.py', 'prepare_native_package.py', 'operator_native.sh',
                          'input.original.jsonl', 'input.original.jsonl.manifest.json', 'input.jsonl', 'routes.json'}
    expected |= {p.relative_to(root).as_posix() for p in adapter.package_inputs(package)}
    need(set(m['files']) == expected, 'Exact package dependency membership')
    original_manifest = read(root / 'input.original.jsonl.manifest.json')
    need(original_manifest['prepared_sha256'] == sha(root / 'input.original.jsonl') and
         original_manifest['ids'] == ids and all(original_manifest[k] == package['summary'][k]
         for k in ('exam_json_sha256', 'template_sha256')), 'Adapter manifest binding')
    if fresh:
        need(not (root / 'results').exists(), 'Fresh package/results required; never resume')
    if m['status'] == 'DECLARED':
        declared(m)
    else:
        need(m['declared_utc'] is None and m['deadline_utc'] is None and m['authorization'] is None, 'Prepared is not authorized')
    cases = inf.load_cases(root / 'input.jsonl', len(ids))
    need([c['id'] for c in cases] == ids, 'Serialized IDs')
    return m, package, cases, routes


def payload(case, cap, helper):
    result = helper.payload(case)
    result['options']['num_predict'] = cap
    return result


def accepted(response, cap, adapter):
    need(isinstance(response, dict) and response.get('model') == MODEL and response.get('error') is None,
         'Provider/model identity or terminal transport error')
    need(not any(response.get(k) is True for k in ('truncated', 'context_truncated')), 'Context truncation')
    p, n = response.get('prompt_eval_count'), response.get('eval_count')
    need(type(p) is int and 0 <= p and p + cap <= CONTEXT and type(n) is int and 0 <= n <= cap,
         'Missing/excess usage or context reserve')
    need(response.get('done') is True, 'Unterminated response')
    message = response.get('message')
    need(isinstance(message, dict), 'Malformed message')
    if response.get('done_reason') == 'length':
        raise ItemFailure('Output token limit; partial final not submitted')
    need(response.get('done_reason') == 'stop', 'Unknown termination reason')
    need(isinstance(message.get('thinking'), str) and message['thinking'].strip(), 'Missing requested thinking')
    content = message.get('content')
    if not isinstance(content, str) or not content.strip():
        raise ItemFailure('Empty final')
    if len(content) > adapter.MAX_ANSWER_CHARS or adapter.utf16_units(content) > adapter.MAX_ANSWER_CHARS:
        raise ItemFailure('Original final exceeds organizer per-answer size limit')
    row = {'raw_response': {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}}
    normalized, failure = adapter.extract_answer(row)
    if failure is not None or normalized != content.strip():
        raise ItemFailure('Adapter rejected final or would remove embedded reasoning')
    return content


def dispatch(cases, routes, m, out, helper, adapter, send, check, verify):
    """Item-local terminal failures continue; any uncertain/global failure stops."""
    sent, tokens, completed = 0, 0, []
    stop = None
    for case, route in zip(cases, routes):
        response = None
        row = {'id': case['id'], 'error': None, 'raw_response': None}
        started = time.monotonic()
        reserved = False
        try:
            need(remaining(m) > m['request_timeout'] + 20, 'Insufficient full request/cleanup window')
            verify(); check(sent > 0)
            need(remaining(m) > m['request_timeout'] + 20, 'Insufficient window after pre-request checks')
            need(sent < m['max_calls'] and tokens + route['cap'] <= m['max_requested_tokens'], 'Ledger caps')
            body = payload(case, route['cap'], helper)
            append(out / 'requests.jsonl', {'id': case['id'], 'payload': body})
            append(out / 'reservations.jsonl', {'call': sent + 1, 'id': case['id'], 'cap': route['cap'],
                   'total_reserved_tokens': tokens + route['cap'], 'request_sha256': textsha(line(body)),
                   'utc': dt.datetime.now(dt.timezone.utc).isoformat()})
            sent += 1; tokens += route['cap']; reserved = True
            response = send(body)
            check(True); verify(); remaining(m)
            text = accepted(response, route['cap'], adapter)
            row['raw_response'] = {'choices': [{'finish_reason': 'stop', 'message': {'content': text}}]}
        except ItemFailure as exc:
            row['error'] = {'type': 'item_generation', 'message': str(exc)}
        except Exception as exc:
            row['error'] = {'type': 'global_stop', 'message': str(exc)}
            stop = str(exc)
        if reserved:
            append(out / 'native-raw.jsonl', {'id': case['id'], 'response': response, 'error': row['error'],
                   'latency_s': time.monotonic() - started})
            append(out / 'finalizer-input.jsonl', row)
            completed.append(row)
        if stop is not None:
            break
    return {'calls': sent, 'requested_tokens': tokens, 'stop': stop,
            'item_error_ids': [r['id'] for r in completed if r['error'] and r['error']['type'] == 'item_generation'],
            'unsent_ids': [c['id'] for c in cases[sent:]]}


def finalize(root, adapter, package):
    """Keep actual adapter output AND exact accepted native strings, same template."""
    out = root / 'results'
    raw = out / 'finalizer-input.jsonl'
    if not raw.exists():
        raw.touch(exist_ok=False)
    report = adapter.finalize(package, [raw], out / 'answers.adapter.json', out / 'failures.json',
                              root / 'input.original.jsonl.manifest.json')
    actual = read(out / 'answers.adapter.json')
    by_id = {r['id']: r for r in rows(raw)}
    for entry in actual['answers']:
        if entry['answer']:
            original = by_id[entry['id']]['raw_response']['choices'][0]['message']['content']
            need(entry['answer'] == original.strip(), 'Unexpected adapter final transformation')
            entry['answer'] = original
    encoded = adapter.encode_submission(actual)
    need(not adapter.validate_submission_bytes(encoded, package['template']), 'Original-string template validation')
    with (out / 'answers.json').open('xb') as f:
        f.write(encoded); f.flush(); os.fsync(f.fileno())
    write(out / 'answers-provenance.json', {'adapter_sha256': report['answers_sha256'],
          'answers_sha256': sha(out / 'answers.json'), 'exact_native_strings': True,
          'failures': report['failures'], 'scope': 'format only; no quality score'})
    return report


def cleanup_root(root, m, helper):
    return helper.cleanup_from_receipts(root / 'results', m['binary'])


def process_identity(pid, helper):
    return {'pid': pid, 'ticks': helper.ticks(pid),
            'executable': str(Path(f'/proc/{pid}/exe').resolve()),
            'argv': [x for x in Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\0') if x],
            'namespace': os.readlink(f'/proc/{pid}/ns/net')}


def inherited_parent_identity(pid, receipt):
    """New user namespaces cannot dereference the host parent's exe/ns links.

    Executable/namespace were verified by the locked host parent before unshare.
    Bind that receipt to live PID/start/argv plus the inherited FD challenge below;
    never interpret permission denial as an independently verified executable.
    """
    need(receipt.get('pid') == pid, 'Parent receipt PID')
    live_ticks = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[19]
    live_argv = [x for x in Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\0') if x]
    need(live_ticks == receipt.get('ticks') and live_argv == receipt.get('argv'), 'Parent identity changed')
    return dict(receipt)

def check_supervisor(root, m, parent, fd, host_net, helper):
    """Require the locked, guarded parent plus its inherited anonymous pipe."""
    need(type(fd) is int and fd >= 3 and os.getppid() == parent, 'Internal supervisor handshake required')
    proof = read(root / 'results/supervisor.json')
    identity = inherited_parent_identity(parent, proof['identity'])
    need(identity == proof['identity'] and identity['namespace'] == host_net and
         identity['executable'] == str(Path(sys.executable).resolve()) and
         identity['argv'][-4:] == [str(root / 'run_native_package.py'), str(root), '--execute', '--guarded'],
         'Genuine guarded supervisor identity required')
    timer = inherited_parent_identity(proof['guardian']['pid'], proof['guardian'])
    need(timer == proof['guardian'] and Path(timer['executable']).name == 'timeout' and
         timer['argv'][1:3] == ['--signal=TERM', '--kill-after=5s'], 'Live OS guardian ancestry')
    # Check actual ancestry, not only two separately live processes.
    parent_stat = Path(f'/proc/{parent}/stat').read_text().split(') ', 1)[1].split()
    need(int(parent_stat[1]) == timer['pid'], 'Supervisor guardian parent changed')
    need(proof['launch_sha256'] == sha(root / 'results/launch.json') and
         proof['weights_sha256'] == sha(root / 'results/weights.json'), 'Locked preflight receipts')
    need(stat.S_ISFIFO(os.fstat(fd).st_mode), 'Inherited pipe required')
    try:
        os.set_blocking(fd, False)
        challenge = os.read(fd, 33)
        need(len(challenge) == 32 and hashlib.sha256(challenge).hexdigest() == proof['challenge_sha256'],
             'Inherited supervisor challenge mismatch')
    finally:
        os.close(fd)


def inside(root, m, package, cases, routes, host_net, parent, supervisor_fd):
    helper, guard, rehearsal, adapter, _ = modules(root)
    check_supervisor(root, m, parent, supervisor_fd, host_net, helper)
    out = root / 'results'
    proof = rehearsal.network_proof(host_net)
    write(out / 'network-proof.json', proof)
    write(out / 'pre-process.json', helper.workers({os.getpid(), parent}))
    home = out / 'server-home'; home.mkdir()
    env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'OLLAMA_MODELS': m['cache'],
           'OLLAMA_HOST': '127.0.0.1:11435', 'OLLAMA_CONTEXT_LENGTH': '32768',
           'OLLAMA_NUM_PARALLEL': '1', 'OLLAMA_MAX_LOADED_MODELS': '1',
           'OLLAMA_NO_CLOUD': '1', 'OLLAMA_KEEP_ALIVE': '5m'}
    server = None
    record = None
    outcome = {'stop': 'Did not reach dispatch'}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def snapshot(loaded):
        need(server.poll() is None and helper.ticks(server.pid) == record['ticks'], 'Owned server identity')
        need(os.readlink(f'/proc/{server.pid}/ns/net') == proof['isolated_namespace'], 'Server namespace')
        need(Path(f'/proc/{server.pid}/exe').resolve() == Path(m['binary']), 'Server executable')
        actual = dict(x.split('=', 1) for x in Path(f'/proc/{server.pid}/environ').read_bytes().decode().split('\0') if '=' in x)
        need(all(actual.get(k) == v for k, v in env.items()), 'Server environment')
        snap = {k: rehearsal.api(k) for k in ('version', 'tags', 'ps')}
        guard.verify_snapshot(snap, guard.CANONICAL, loaded)
        helper.workers({os.getpid(), parent}, server.pid)
        append(out / 'runtime.jsonl', snap)

    try:
        with (out / 'server.log').open('xb') as log:
            server = subprocess.Popen([m['binary'], 'serve'], env=env, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
        record = {'pid': server.pid, 'ticks': helper.ticks(server.pid),
                  'namespace': os.readlink(f'/proc/{server.pid}/ns/net')}
        write(out / 'server-identity.json', record)
        until = time.monotonic() + 45
        while True:
            try:
                snapshot(False); break
            except OSError:
                need(time.monotonic() < until and server.poll() is None, 'Server readiness timeout')
                remaining(m); time.sleep(.25)

        def send(body):
            request = urllib.request.Request(helper.ENDPOINT + '/api/chat', data=json.dumps(body).encode(),
                                             headers={'Content-Type': 'application/json'})
            with opener.open(request, timeout=m['request_timeout']) as reply:
                return json.load(reply)

        outcome = dispatch(cases, routes, m, out, helper, adapter, send, snapshot,
                           lambda: verify_files(root, m))
    finally:
        try:
            if record:
                killed = helper.cleanup(record)
                server.wait(timeout=5)
                write(out / 'cleanup.json', {'owned': record, 'matched_pids': killed, 'returncode': server.returncode})
        finally:
            write(out / 'dispatch-terminal.json', outcome)
    return 2 if outcome['stop'] else (1 if outcome['item_error_ids'] else 0)


def execute(root, m, package, cases, routes):
    import fcntl
    helper, guard, rehearsal, adapter, _ = modules(root)
    need(sys.platform == 'linux', 'Linux execution only')
    remaining(m)
    lock = Path(m['lock']).open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        need(guard.fingerprint(Path(m['binary']))['sha256'] == guard.CANONICAL['runtime_binary_sha256'], 'Runtime binary pin')
        weights = guard.verify_inventory(m['cache'], guard.native_inventory(m['cache'], guard.CANONICAL))
        helper.workers({os.getpid()})
        rehearsal.isolation_probe()
        need(not rehearsal.api('ps', 11436)['models'], 'Host model resident; never unload automatically')
        remaining(m); verify_files(root, m)
        out = root / 'results'; out.mkdir()
        write(out / 'launch.json', m); write(out / 'weights.json', weights)
        receiver, sender = os.pipe()
        challenge = os.urandom(32)
        os.write(sender, challenge); os.close(sender)
        write(out / 'supervisor.json', {'identity': process_identity(os.getpid(), helper),
              'guardian': process_identity(os.getppid(), helper),
              'launch_sha256': sha(out / 'launch.json'), 'weights_sha256': sha(out / 'weights.json'),
              'challenge_sha256': hashlib.sha256(challenge).hexdigest()})
        command = ['unshare', '-rn', '--', sys.executable, '-B', str(Path(__file__).resolve()), str(root),
                   '--execute', '--inside', '--host-net', os.readlink('/proc/self/ns/net'), '--parent', str(os.getpid()),
                   '--supervisor-fd', str(receiver)]
        child = None
        status = 2
        try:
            child = subprocess.Popen(command, start_new_session=True, pass_fds=(receiver,))
            os.close(receiver); receiver = None
            status = child.wait(timeout=max(1, remaining(m) - 15))
        finally:
            try:
                if receiver is not None:
                    os.close(receiver)
                if child is not None and child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
                write(out / 'parent-cleanup.json', cleanup_root(root, m, helper))
                write(out / 'post-process.json', helper.workers({os.getpid()}))
            finally:
                verify_files(root, m)
                report = finalize(root, adapter, package)
                reservations = rows(out / 'reservations.jsonl') if (out / 'reservations.jsonl').exists() else []
                write(out / 'terminal.json', {'child_status': status, 'calls': len(reservations),
                      'requested_tokens': sum(r['cap'] for r in reservations),
                      'unsent_ids': [c['id'] for c in cases[len(reservations):]],
                      'answers_sha256': sha(out / 'answers.json'), 'failures': report['failures'],
                      'finished_utc': dt.datetime.now(dt.timezone.utc).isoformat()})
        return status if status else (1 if report['failures'] else 0)
    finally:
        lock.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--guarded', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--cleanup', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--host-net', help=argparse.SUPPRESS)
    parser.add_argument('--parent', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--supervisor-fd', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.package.resolve()
    if args.cleanup:
        m = read(root / 'results/launch.json')
        need(m == read(root / 'launch.json'), 'Cleanup declaration changed')
        verify_files(root, m)
        result = cleanup_root(root, m, modules(root)[0])
        append(root / 'results/guardian-cleanup.jsonl', result)
        print(json.dumps(result))
        return 0
    if args.execute:
        need(sys.platform == 'linux', 'Linux guardian required')
        # Install before potentially large input/image preflight, not only before weights.
        preliminary = read(root / 'launch.json')
        def deadline(*_):
            raise GlobalStop('Whole-operation absolute deadline')
        signal.signal(signal.SIGALRM, deadline)
        signal.signal(signal.SIGTERM, deadline)
        signal.setitimer(signal.ITIMER_REAL, max(.1, remaining(preliminary) - 15))
    m, package, cases, routes = preflight(root, fresh=not args.inside)
    if args.inside:
        need(args.execute and args.parent and args.host_net and m == read(root / 'results/launch.json'), 'Internal execution authorization')
        remaining(m)
        return inside(root, m, package, cases, routes, args.host_net, args.parent, args.supervisor_fd)
    if not args.execute:
        print(json.dumps({'preflight': 'PASS', 'calls': m['max_calls'], 'requested_tokens': m['max_requested_tokens'],
                          'status': m['status'], 'model_calls': 0}))
        return 0
    need(sys.platform == 'linux', 'Linux guardian required')
    remaining(m)
    if not args.guarded:
        # All ordinary execution automatically enters the pinned external guardian.
        signal.setitimer(signal.ITIMER_REAL, 0)
        os.execvp('bash', ['bash', str(root / 'operator_native.sh'), str(root), '--execute'])
    parent_args = Path(f'/proc/{os.getppid()}/cmdline').read_bytes().decode().split('\0')
    need(Path(f'/proc/{os.getppid()}/exe').resolve().name == 'timeout' and
         parent_args[1:3] == ['--signal=TERM', '--kill-after=5s'] and
         parent_args[3].endswith('s') and parent_args[3][:-1].isdigit() and
         0 < int(parent_args[3][:-1]) <= m['max_seconds'] - 10, 'External OS guardian required')
    try:
        return execute(root, m, package, cases, routes)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (GlobalStop, OSError, ValueError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
