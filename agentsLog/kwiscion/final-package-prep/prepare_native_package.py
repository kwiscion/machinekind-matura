"""Prepare an arbitrary organizer package without network, model or server work."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('native_prepare_contract', HERE / 'run_native_package.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
SOURCES = {
    'run_native_package.py': 'agentsLog/kwiscion/final-package-prep/run_native_package.py',
    'prepare_native_package.py': 'agentsLog/kwiscion/final-package-prep/prepare_native_package.py',
    'run_gemma_offline.py': 'agentsLog/kwiscion/final-package-prep/run_gemma_offline.py',
    'guard.py': 'agentsLog/kwiscion/final-package-prep/guard.py',
    'offline_rehearsal.py': 'agentsLog/kwiscion/offline_rehearsal.py',
    'infer.py': 'infer.py',
    'scripts/Bukareszt/matura_package.py': 'scripts/Bukareszt/matura_package.py',
}


def guardian(seconds):
    # Generated as a pinned package file. No mutation of the live two-item wrapper.
    return '''#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 2 ] || [ "$2" != --execute ]; then
  echo 'Usage: bash operator_native.sh /absolute/private/package --execute' >&2
  exit 2
fi
package=$(realpath -- "$1")
cleanup() {
  if [ -f "$package/results/network-proof.json" ]; then
    timeout --signal=KILL 5s python3 -B "$package/run_native_package.py" "$package" --cleanup
  fi
}
trap cleanup EXIT
budget=$(python3 -B -c 'import datetime,json,math,sys,time; m=json.load(open(sys.argv[1],encoding="utf8")); end=datetime.datetime.fromisoformat(m["deadline_utc"]); assert m["status"]=="DECLARED" and end.utcoffset()==datetime.timedelta(0); n=math.floor(min(m["max_seconds"],end.timestamp()-time.time()))-10; assert n>0; print(n)' "$package/launch.json")
timeout --signal=TERM --kill-after=5s "${budget}s" python3 -B "$package/run_native_package.py" "$package" --execute --guarded
'''


def prepare(exam, output, *, essay_ids, no_essay, cache, binary, lock, max_seconds, request_timeout):
    output = output.resolve()
    private = (REPO / 'agentsLog/kwiscion/private').resolve()
    runner.need(output.is_relative_to(private) and output != private and not output.exists(),
                'Fresh project-private output required')
    for name, digest in runner.PINS.items():
        runner.need(runner.sha(REPO / SOURCES[name]) == digest, 'Reviewed dependency changed: ' + name)
    adapter = runner.load('prepare_native_adapter', REPO / SOURCES['scripts/Bukareszt/matura_package.py'])
    exam = exam.resolve()
    package = adapter.load_package(exam)
    # Copy only actual required package files, never keys, unrelated files or caches.
    source_hashes = {}
    for source in adapter.package_inputs(package):
        relative = source.relative_to(exam).as_posix()
        runner.safe_file(exam, relative)
        source_hashes[relative] = runner.sha(source)
    runner.need(not output.is_relative_to(exam), 'Output must be separate from source package')
    output.mkdir(parents=True)
    for dst, src in SOURCES.items():
        target = output / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / src, target)
    for relative, digest in source_hashes.items():
        target = output / 'exam' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(exam / relative, target)
        runner.need(runner.sha(target) == digest == runner.sha(exam / relative), 'Source changed while copying')
    copied = adapter.load_package(output / 'exam')
    adapter.prepare(copied, output / 'input.original.jsonl')
    original = runner.rows(output / 'input.original.jsonl')
    routed, routes = runner.build_routes(original, essay_ids, no_essay)
    with (output / 'input.jsonl').open('x', encoding='utf8', newline='\n') as f:
        for row in routed:
            f.write(runner.line(row))
    runner.write(output / 'routes.json', routes)
    (output / 'operator_native.sh').write_text(guardian(max_seconds), encoding='utf8', newline='\n')
    files = {p.relative_to(output).as_posix(): runner.sha(p) for p in output.rglob('*') if p.is_file()}
    manifest = {
        'schema': 'native_organizer_package_v1', 'status': 'PREPARED',
        'declared_utc': None, 'deadline_utc': None, 'authorization': None,
        'model': runner.MODEL, 'think': True, 'temperature': 'omitted', 'context': 32768,
        'truncate': False, 'shift': False, 'retries': 0,
        'max_calls': len(routes), 'max_requested_tokens': sum(r['cap'] for r in routes),
        'max_seconds': max_seconds, 'request_timeout': request_timeout,
        'ids': [r['id'] for r in original], 'essay_ids': essay_ids, 'no_essay': no_essay,
        'essay_policy_sha256': runner.textsha(runner.ESSAY_POLICY),
        'routes_sha256': runner.sha(output / 'routes.json'),
        'cache': cache, 'binary': binary, 'lock': lock, 'files': files,
    }
    runner.write(output / 'launch.json', manifest)
    # Load the actual portable runner so its executing-file hash is checked too.
    packed = runner.load('packed_native_preflight', output / 'run_native_package.py')
    packed.preflight(output)
    return manifest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exam-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--essay-id', action='append', help='Actual received item ID; repeat for multiple essays')
    group.add_argument('--no-essay', action='store_true', help='Explicitly declare no essay items')
    for name in ('cache', 'binary', 'lock'):
        p.add_argument('--' + name, required=True, help='Absolute Linux execution path')
    p.add_argument('--max-seconds', type=int, required=True)
    p.add_argument('--request-timeout', type=int, default=600)
    a = p.parse_args(argv)
    m = prepare(a.exam_dir, a.output, essay_ids=a.essay_id or [], no_essay=a.no_essay,
                cache=a.cache, binary=a.binary, lock=a.lock,
                max_seconds=a.max_seconds, request_timeout=a.request_timeout)
    print(json.dumps({'status': m['status'], 'items': m['max_calls'],
                      'requested_tokens': m['max_requested_tokens'], 'manifest_sha256': runner.sha(a.output / 'launch.json'),
                      'model_calls': 0}))


if __name__ == '__main__':
    main()
