"""Frozen-manifest Gemma dispatcher; dry preflight unless --execute is explicit."""
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('policy_limits', Path(__file__).with_name('run_question_policy.py'))
limits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(limits)


def private_path(value):
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    rel = path.relative_to(ROOT)
    if len(rel.parts) < 4 or rel.parts[:3] != ('agentsLog', 'kwiscion', 'private'):
        raise ValueError('Path must remain in repository agentsLog/kwiscion/private/')
    return path


def preflight(manifest):
    fixed = {'max_calls': 40, 'max_requested_output_tokens': 40960, 'max_output_tokens': 1024,
             'timeout_seconds': 420, 'context_tokens': 4096, 'paid_api_budget_usd': 0}
    for key, expected in fixed.items():
        if type(manifest.get(key)) is not int or manifest[key] != expected:
            raise ValueError('Invalid fixed bound: ' + key)
    wall = manifest.get('max_elapsed_seconds')
    if type(wall) is not int or not 1 <= wall <= 3600:
        raise ValueError('Elapsed budget must be 1-3600 seconds')
    deadline = dt.datetime.fromisoformat(manifest['deadline'])
    if deadline.utcoffset() is None:
        raise ValueError('Deadline requires explicit timezone')
    if manifest.get('model_digest') != limits.DIGEST:
        raise ValueError('Full Gemma digest mismatch')
    inp = private_path(manifest['input'])
    out = private_path(manifest['output'])
    meta = out.with_name(out.name + '.run.json')
    if out.exists() or meta.exists() or out == inp:
        raise ValueError('Fresh output and metadata required; no resume')
    config_path = (ROOT / manifest['config']).resolve()
    config_path.relative_to(ROOT)
    if limits.sha(config_path) != limits.CONFIG_HASH or manifest.get('config_sha256') != limits.CONFIG_HASH:
        raise ValueError('Original config pin mismatch')
    if limits.sha(inp) != manifest.get('input_sha256'):
        raise ValueError('Input pin mismatch')
    rows = [json.loads(line) for line in inp.read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = manifest.get('expected_ids')
    if not isinstance(ids, list) or len(ids) != 40 or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != 40:
        raise ValueError('Exactly 40 unique expected IDs required')
    if [row['id'] for row in rows] != ids:
        raise ValueError('Input order/IDs mismatch')
    images = manifest.get('images')
    if not isinstance(images, dict):
        raise ValueError('Images hash map required, keyed by input image string')
    referenced = {p for row in rows for p in row.get('images', [])}
    if referenced != set(images):
        raise ValueError('Images map must cover exactly all references')
    for image, expected in images.items():
        path = private_path(str(inp.parent / image))
        if limits.sha(path) != expected:
            raise ValueError('Image pin mismatch')
    spec = importlib.util.spec_from_file_location('infer', ROOT / 'infer.py')
    infer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(infer)
    config = infer.load_config(config_path, False)
    cases = infer.load_cases(inp, 40)
    return inp, out, meta, config, cases, infer, deadline.timestamp()


def competing_workers():
    found = limits.competing_workers()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            argv = (entry / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if argv and 'python' in Path(argv[0]).name.lower() and any(Path(a).name == 'run_bounded_gemma.py' for a in argv[1:]):
                found.append(int(entry.name))
        except OSError:
            continue
    return sorted(set(found))


def stop(rows, elapsed, now, manifest, workers=()):
    if elapsed >= manifest['max_elapsed_seconds']:
        return 'declared elapsed-time limit'
    # Reuse reviewed stop logic with this arm's explicitly declared deadline.
    limits.DEADLINE = dt.datetime.fromisoformat(manifest['deadline']).timestamp()
    reason = limits.stop_reason(rows, elapsed, now, workers)
    return reason.replace('17:10', 'declared deadline') if reason else None


def execute(manifest, manifest_hash):
    inp, out, meta, config, cases, infer, deadline = preflight(manifest)
    if competing_workers() or time.time() >= deadline:
        raise RuntimeError('Competing worker or passed deadline; no inference')
    model = limits.verify_model(limits.local_status('tags'), limits.local_status('ps'), config['model'])
    show = limits.local_status('show', {'model': config['model']})
    report = {'manifest': manifest, 'manifest_sha256': manifest_hash,
        'git_revision': subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT), 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'script_sha256': limits.sha(Path(__file__)), 'stop_logic_sha256': limits.sha(Path(limits.__file__)),
        'infer_sha256': limits.sha(ROOT / 'infer.py'), 'model_status': model,
        'version': limits.local_status('version'), 'parameters': show.get('parameters'),
        'sampling': 'original defaults not fixed; no temperature/seed sent',
        'context_fit': 'estimated; returned prompt usage must be <=2816; silent truncation unproven',
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'paid_api_cost_usd': 0}
    out.parent.mkdir(parents=True, exist_ok=True)
    with meta.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    rows, reason, started = [], None, time.monotonic()
    try:
        with out.open('x', encoding='utf-8') as stream:
            for case in cases:
                reason = stop(rows, time.monotonic() - started, time.time(), manifest, competing_workers())
                if reason:
                    break
                row = infer.run_case(case, config)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                rows.append(row)
                print(json.dumps({'recorded': len(rows), 'id': row['id'], 'error': row['error'], 'usage': row['usage']}), flush=True)
                if len(rows) == 1:
                    try:
                        report['model_status_after_first'] = limits.verify_model(
                            limits.local_status('tags'), limits.local_status('ps'), config['model'], require_loaded=True)
                    except Exception as exc:
                        reason = 'post-first runtime verification failed: ' + str(exc)
                        break
    except BaseException as exc:
        reason = 'dispatcher interrupted: ' + type(exc).__name__
        raise
    finally:
        report.update({'recorded': len(rows), 'unsent_ids': [c['id'] for c in cases[len(rows):]],
            'stop_reason': reason or stop(rows, time.monotonic() - started, time.time(), manifest),
            'elapsed_seconds': round(time.monotonic() - started, 3), 'output_sha256': limits.sha(out) if out.exists() else None})
        meta.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    manifest_path = private_path(str(args.manifest))
    manifest = json.loads(manifest_path.read_bytes())
    if args.execute:
        execute(manifest, limits.sha(manifest_path))
    else:
        preflight(manifest)
        print('PREPARED ONLY: 40 cases, no model/status calls; separate launch authorization required')
