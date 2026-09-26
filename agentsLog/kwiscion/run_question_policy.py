"""Bounded Linux/WSL dispatcher. Preparation alone never authorizes --execute."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'agentsLog/kwiscion/private/validation_2024_keyfree'
INPUT = BASE / 'runner_input.v2-question-policy-frozen.jsonl'
CONFIG = ROOT / 'outputs/local-smoke/gemma4-12b-val40-1024.config.json'
INPUT_HASH = '3257dd89909ec1aeea1f85180244e962cc647e4f2b9d37cb24b1907cabfabb92'
CONFIG_HASH = '3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa'
DIGEST = '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
DEADLINE = dt.datetime.fromisoformat('2026-09-26T17:10:00+02:00').timestamp()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infrastructure(row):
    error = row.get('error')
    return bool(error) and (not isinstance(error, dict) or error.get('type') != 'incomplete')


def stop_reason(rows, elapsed, now, competitors=()):
    if competitors:
        return 'competing inference worker'
    if now >= DEADLINE:
        return '17:10 deadline'
    if elapsed >= 3600:
        return '60-minute wall limit'
    if rows:
        last = rows[-1]
        prompt = (last.get('usage') or {}).get('prompt_tokens')
        if not last.get('error') and (type(prompt) is not int or prompt > 2816):
            return 'prompt token count missing or exceeds 2816'
        if type(prompt) is int and prompt > 2816:
            return 'prompt token count exceeds 2816'
        diagnostic = json.dumps(last.get('error'), ensure_ascii=False).lower()
        raw = last.get('raw_response')
        if isinstance(raw, dict):
            diagnostic += json.dumps({k: raw[k] for k in ('error', 'truncated', 'context_truncated') if k in raw}).lower()
        if any(term in diagnostic for term in ('out of memory', 'out_of_memory', 'oom', 'context length', 'context window', 'context_truncated": true', 'truncated": true')):
            return 'OOM or context truncation indicator'
        if len(rows) >= 2 and all(infrastructure(r) for r in rows[-2:]):
            return 'two consecutive infrastructure failures'
        if len(rows) >= 5 and now + elapsed / len(rows) * (40 - len(rows)) > DEADLINE:
            return 'projected completion exceeds 17:10'
    return None


def competing_workers():
    if not Path('/proc').is_dir():
        raise RuntimeError('Execute only in Linux/WSL with /proc worker checks')
    found = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            args = (entry / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if not args or 'python' not in Path(args[0]).name.lower():
                continue
            if any(Path(arg).name in ('infer.py', 'run_question_policy.py') or Path(arg).name.startswith(('run_gemma', 'run_qwen')) for arg in args[1:]):
                found.append(int(entry.name))
        except (OSError, ProcessLookupError):
            continue
    return found


def local_status(path, body=None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request('http://127.0.0.1:11434/api/' + path,
        data=json.dumps(body).encode() if body else None, headers={'Content-Type': 'application/json'})
    with opener.open(request, timeout=10) as response:
        return json.load(response)


def verify_model(tags, ps, name, require_loaded=False):
    installed = next((m for m in tags['models'] if m.get('name') == name), None)
    if not installed or installed.get('digest') != DIGEST:
        raise RuntimeError('Installed model digest mismatch')
    resident = next((m for m in ps['models'] if m.get('name') == name), None)
    if resident is None:
        if require_loaded:
            raise RuntimeError('Model not resident after request; effective context unverified')
        return None
    if resident.get('digest') != DIGEST or resident.get('context_length') != 4096:
        raise RuntimeError('Resident model digest/context mismatch')
    return resident


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Requires separate lead launch authorization')
    parser.add_argument('--output', type=Path, default=ROOT / 'agentsLog/kwiscion/private/question-policy-20260926/raw.jsonl')
    args = parser.parse_args()
    out = args.output.resolve()
    rel = out.relative_to(ROOT)
    if rel.parts[:3] != ('agentsLog', 'kwiscion', 'private'):
        raise ValueError('Private owner output required')
    meta = out.with_name(out.name + '.run.json')
    if out.exists() or meta.exists():
        raise ValueError('Fresh output and metadata required; no resume')
    if sha(INPUT) != INPUT_HASH or sha(CONFIG) != CONFIG_HASH:
        raise ValueError('Frozen input/config drift')
    manifest = json.loads(INPUT.with_name(INPUT.name + '.manifest.json').read_bytes())
    for path, expected in manifest['images'].items():
        if sha(BASE / path) != expected:
            raise ValueError('Image hash drift')
    spec = importlib.util.spec_from_file_location('infer', ROOT / 'infer.py')
    infer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(infer)
    config = infer.load_config(CONFIG, False)
    cases = infer.load_cases(INPUT, 40)
    if len(cases) != 40:
        raise ValueError('Expected exactly 40 cases')
    if not args.execute:
        print('PREPARED ONLY: 40 cases; estimated context fit, no model calls; launch authorization required')
        return
    if competing_workers():
        raise RuntimeError('Competing inference worker; no requests sent')
    tags = local_status('tags')
    model = verify_model(tags, local_status('ps'), config['model'])
    show = local_status('show', {'model': config['model']})
    report = {'input_sha256': sha(INPUT), 'config_sha256': sha(CONFIG), 'script_sha256': sha(Path(__file__)),
        'infer_sha256': sha(ROOT / 'infer.py'), 'model_status': model, 'version': local_status('version'),
        'parameters': show.get('parameters'), 'context_fit': 'estimated, not exact multimodal tokenizer proof',
        'sampling': 'original defaults not fixed; no temperature or seed sent',
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'max_calls': 40,
        'requested_output_token_budget': 40960, 'paid_api_cost_usd': 0}
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.monotonic()
    with meta.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    reason = None
    try:
        with out.open('x', encoding='utf-8') as stream:
            for case in cases:
                reason = stop_reason(rows, time.monotonic() - started, time.time(), competing_workers())
                if reason:
                    break
                row = infer.run_case(case, config)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                rows.append(row)
                print(json.dumps({'recorded': len(rows), 'id': row['id'], 'error': row['error'], 'usage': row['usage']}), flush=True)
                if len(rows) == 1:
                    try:
                        report['model_status_after_first'] = verify_model(
                            local_status('tags'), local_status('ps'), config['model'], require_loaded=True)
                    except Exception as exc:
                        reason = 'post-first runtime verification failed: ' + str(exc)
                        break
    except BaseException as exc:
        reason = 'dispatcher interrupted: ' + type(exc).__name__
        raise
    finally:
        reason = reason or stop_reason(rows, time.monotonic() - started, time.time())
        report.update({'recorded': len(rows), 'unsent_ids': [c['id'] for c in cases[len(rows):]],
            'stop_reason': reason, 'elapsed_seconds': round(time.monotonic() - started, 3),
            'output_sha256': sha(out) if out.exists() else None})
        meta.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
