"""Standalone owned Linux runner: frozen manifest, durable reservations, no retries.

Usage: python3 hetero-source-run.py /absolute/package --mode smoke|wave
The package must contain launch.json explicitly declaring that exact mode.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import signal
from pathlib import Path
import subprocess
import time
import urllib.request


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_body(body, case, config):
    expected = {'model': config['model'], 'messages': [{'role': 'user', 'content': case['content']}],
                'max_tokens': config['max_output_tokens'], 'reasoning_effort': 'none'}
    require(body == expected, 'Outgoing request differs from frozen source/model/controls')


def safe_file(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'Invalid pinned package path')
    return path


def verify_models(host, pins):
    """Full disk verification of every native manifest blob, once before calls."""
    assets = {}
    totals = {}
    for model, digest in pins.items():
        name, tag = model.split(':')
        manifest = host / 'models/manifests/registry.ollama.ai/library' / name / tag
        require(sha(manifest) == digest, 'Native manifest hash: ' + model)
        m = json.loads(manifest.read_text())
        total = 0
        for item in [m['config'], *m['layers']]:
            require(item['digest'].startswith('sha256:') and len(item['digest']) == 71,
                    'Invalid native digest')
            blob = host / 'models/blobs' / item['digest'].replace(':', '-')
            require(blob.stat().st_size == item['size'] and sha(blob) == item['digest'][7:],
                    'Native blob hash/size')
            stat = blob.stat()
            assets[str(blob)] = (stat.st_size, stat.st_mtime_ns, stat.st_ino)
            if item['mediaType'] in ('application/vnd.ollama.image.model',
                                     'application/vnd.ollama.image.projector'):
                total += item['size']
        require(0 < total <= 8000000000, 'Model over8GB or missing weights')
        totals[model] = total
    require(totals == {'qwen3.5:9b': 6594462816, 'gemma4:12b-it-q4_K_M': 7556497632},
            'Unexpected model weight totals')
    return assets, totals


def process_guard(host, server, start_ticks):
    require(int((host / 'server.pid').read_text()) == server, 'Server PID changed')
    proc = Path('/proc') / str(server)
    require(proc.joinpath('stat').read_text().split(') ', 1)[1].split()[19] == str(start_ticks),
            'Server process restarted')
    require(proc.joinpath('exe').resolve() == (host / 'runtime/bin/ollama').resolve(),
            'Unexpected server executable')
    env = dict(x.split('=', 1) for x in proc.joinpath('environ').read_bytes().decode().split('\0') if '=' in x)
    for k, v in {'OLLAMA_HOST': '127.0.0.1:11436', 'OLLAMA_MODELS': str(host / 'models'),
                 'OLLAMA_CONTEXT_LENGTH': '32768', 'OLLAMA_MAX_LOADED_MODELS': '1',
                 'OLLAMA_NUM_PARALLEL': '1', 'OLLAMA_NO_CLOUD': '1'}.items():
        require(env.get(k) == v, 'Server setting changed: ' + k)
    for line in subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
                                         '--format=csv,noheader,nounits'], text=True).splitlines():
        require(line.strip().isdigit() and os.getpgid(int(line)) == server,
                'Competing GPU process')
    names = {'infer.py', 'run_arm.py', 'smoke.py', 'run_source_observation.py',
             'hetero-source-run.py', 'run_local_smoke.py'}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            args = (p / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            executable = Path(args[0]).name
            worker = executable.startswith('python') and any(
                Path(x).name in names or Path(x).name.startswith(('run_gemma', 'run_qwen', 'run_rag', 'run_bounded'))
                for x in args[1:])
            backend = executable in ('llama-server', 'ollama_llama_server', 'ollama') or 'vllm' in executable
            require(not (worker or backend) or os.getpgid(int(p.name)) == server,
                    'Competing inference worker/server')
        except (FileNotFoundError, ProcessLookupError):
            pass


def main(argv=None):
    import fcntl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--mode', choices=('smoke', 'wave'), required=True)
    args = parser.parse_args(argv)
    root = args.package.resolve()
    m = json.loads((root / 'launch.json').read_text())
    require(m['mode'] == args.mode and m['status'] == 'DECLARED_' + args.mode.upper(),
            'No declared launch for this mode')
    host = Path(m['host_root']).resolve()
    require(root.is_relative_to(host), 'Package outside owned host root')
    require(not (root / 'results').exists(), 'No resume/overwrite')
    lock = (host / 'matched-worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    deadline = dt.datetime.fromisoformat(m['deadline_utc'])
    require(deadline.tzinfo is not None and m['max_elapsed_seconds'] == 1800, 'Bounded UTC deadline')
    remaining = min(1800, (deadline - dt.datetime.now(dt.timezone.utc)).total_seconds())
    require(remaining > 425, 'Launch deadline cannot fit timeout')
    def hard_deadline(_signum, _frame):
        raise TimeoutError('Process wall deadline reached')
    signal.signal(signal.SIGALRM, hard_deadline)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    started = time.monotonic()
    launch_hash = sha(root / 'launch.json')
    required = {'hetero-source-controller.py', 'run_source_observation.py', 'code/infer.py',
                'code/classifier.py', 'code/scripts/Bukareszt/matura_package.py', 'input.jsonl', 'config.json'}
    require(required.issubset(m['files']), 'Unpinned dependency')
    for name, digest in m['files'].items():
        require(sha(safe_file(root, name)) == digest, 'Frozen file changed: ' + name)
    require('hetero-source-run.py' in m['files'] and
            sha(Path(__file__).resolve()) == m['files']['hetero-source-run.py'], 'Unpinned runner')
    r = load('hetero_controller', root / 'hetero-source-controller.py')
    inf = load('hetero_infer', root / 'code/infer.py')
    adapter = load('hetero_adapter', root / 'code/scripts/Bukareszt/matura_package.py')
    classifier = load('hetero_classifier', root / 'code/classifier.py')
    require(m['model_digests'] == r.PINS, 'Model pins changed')
    cfg = inf.load_config(root / 'config.json', False)
    # Every image file must be pinned before load; absolute paths are refused.
    for line in (root / 'input.jsonl').read_text().splitlines():
        for image in json.loads(line).get('images', []):
            require(not Path(image).is_absolute() and image in m['files'], 'Unpinned input image')
            safe_file(root, image)
    cases = inf.load_cases(root / 'input.jsonl', 2 if args.mode == 'smoke' else 6)
    require([c['id'] for c in cases] == m['ids'] and len(set(m['ids'])) == len(m['ids']), 'Input IDs')
    require(len(cases) == (2 if args.mode == 'smoke' else 6), 'Case count')
    cap = 256 if args.mode == 'smoke' else 1024
    max_calls = 2 if args.mode == 'smoke' else 18
    require(m['max_calls'] == max_calls and m['max_requested_output_tokens'] == cap * max_calls,
            'Declared budget mismatch')
    require(cfg['timeout_seconds'] == 420 and cfg['max_output_tokens'] == cap and
            cfg['reasoning_effort'] == 'none' and 'temperature' not in cfg and
            'api_key_env' not in cfg and cfg['endpoint'] == 'http://127.0.0.1:11436/v1/chat/completions',
            'Config mismatch')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), inf.NoRedirect)
    def api(name, payload=None):
        req = urllib.request.Request('http://127.0.0.1:11436/api/' + name,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'})
        with opener.open(req, timeout=10) as response:
            return json.load(response)
    def snapshot():
        return {'version': api('version')['version'], 'tags': api('tags'), 'ps': api('ps')}
    assets, totals = verify_models(host, r.PINS)
    out = root / 'results'
    out.mkdir(); (out / 'requests').mkdir()
    def write(name, value):
        with (out / name).open('x', encoding='utf8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2); f.flush(); os.fsync(f.fileno())
    def guard(expected):
        require((deadline - dt.datetime.now(dt.timezone.utc)).total_seconds() > (425 if expected is None else 0),
                'UTC deadline')
        require(time.monotonic() - started < 1800 - (425 if expected is None else 0), 'Wall deadline')
        require(sha(root / 'launch.json') == launch_hash, 'Launch changed')
        for name, digest in m['files'].items():
            require(sha(safe_file(root, name)) == digest, 'Frozen file changed: ' + name)
        require(sha(host / 'runtime/bin/ollama') == m['runtime_executable_sha256'], 'Runtime binary changed')
        for file, signature in assets.items():
            stat = Path(file).stat()
            require((stat.st_size, stat.st_mtime_ns, stat.st_ino) == signature, 'Native blob changed')
        for model, digest in r.PINS.items():
            name, tag = model.split(':')
            require(sha(host / 'models/manifests/registry.ollama.ai/library' / name / tag) == digest,
                    'Native manifest changed')
        process_guard(host, m['server_pid'], m['server_start_ticks'])
        state = snapshot(); r.check_runtime(state, expected)
        with (out / 'runtime.jsonl').open('a', encoding='utf8') as log:
            log.write(json.dumps({'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                                  'expected_model': expected, 'state': state}) + '\n')
            log.flush(); os.fsync(log.fileno())
        return state
    initial = guard(None)
    write('start.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'runtime': initial,
                        'launch_sha256': launch_hash, 'weight_bytes': totals,
                        'show': {model: api('show', {'model': model}) for model in r.PINS}})
    reservation_count = 0
    active = None
    capture_used = False
    class Capture:
        def open(self, request, timeout):
            nonlocal capture_used
            require(active is not None and not capture_used, 'Unreserved or repeated request')
            require((deadline - dt.datetime.now(dt.timezone.utc)).total_seconds() > 425 and
                    time.monotonic() - started < 1375, 'Dispatch deadline after guards')
            require(request.full_url == cfg['endpoint'] and timeout == 420, 'Endpoint/timeout')
            case, config = active
            check_body(json.loads(request.data), case, config)
            capture_used = True
            with (out / 'requests' / f'{reservation_count:02}.json').open('xb') as f:
                f.write(request.data); f.flush(); os.fsync(f.fileno())
            return opener.open(request, timeout=timeout)
    inf.OPENER = Capture()
    with (out / 'calls.jsonl').open('x', encoding='utf8') as ledger, (out / 'raw.jsonl').open('x', encoding='utf8') as raw:
        def persist(kind, value):
            nonlocal reservation_count
            if kind == 'reservation':
                require(reservation_count < max_calls and value['cap'] == cap, 'Reservation budget')
                reservation_count += 1
                value = dict(value, utc=dt.datetime.now(dt.timezone.utc).isoformat())
            f = ledger if kind == 'reservation' else raw
            f.write(json.dumps(value, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())
        def backend(case, config):
            nonlocal active, capture_used
            active = (case, config); capture_used = False
            row = inf.run_case(case, config)
            require(capture_used, 'No captured request')
            if isinstance(row.get('raw_response'), dict) and row['raw_response'].get('model') != config['model']:
                row['error'] = {'type': 'runtime_model', 'message': 'Response model differs from executing stage'}
            return row
        if args.mode == 'wave':
            summary = r.run(cases, cfg, backend, guard, persist, inf, adapter,
                            classifier.case_local_generation_error)
        else:
            require(cfg['model'] == 'qwen3.5:9b' and cfg['model_revision'] == r.PINS[cfg['model']],
                    'Smoke only Qwen')
            records = []; status = 'complete'
            for case in cases:
                row = None
                try:
                    guard(None)
                    persist('reservation', {'id': case['id'], 'stage': 'smoke', 'cap': cap,
                                             'model': cfg['model'], 'call': reservation_count + 1})
                    row = backend(case, cfg)
                    outcome = r.validate(row, cap, inf, adapter, classifier.case_local_generation_error,
                                         lambda: guard(cfg['model']))
                    record = {'id': case['id'], 'result': row, **outcome}
                    records.append(record); persist('record', record)
                    require(not outcome['case_error'], 'Readiness generation failure; no retry')
                except Exception as exc:
                    status = type(exc).__name__ + ': ' + str(exc)
                    # Preserve failed raw response too when validation itself failed.
                    if reservation_count > len(records):
                        if isinstance(row, dict) and row.get('error') is None:
                            row['error'] = {'type': 'systemic_validation', 'message': status}
                        record = {'id': case['id'], 'answer': '', 'case_error': True,
                                  'systemic_error': status, 'result': row}
                        records.append(record); persist('record', record)
                    break
            summary = {'status': status, 'calls': reservation_count, 'records': records,
                       'requested_tokens': reservation_count * cap,
                       'unsent': [c['id'] for c in cases[reservation_count:]]}
    summary['elapsed_seconds'] = time.monotonic() - started
    summary['utc_end'] = dt.datetime.now(dt.timezone.utc).isoformat()
    summary['raw_sha256'] = sha(out / 'raw.jsonl')
    summary['request_hashes'] = {p.name: sha(p) for p in (out / 'requests').iterdir()}
    write('summary.json', summary)
    print(json.dumps({k: summary[k] for k in ('status', 'calls', 'requested_tokens', 'elapsed_seconds')}))
    return 0 if summary['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
