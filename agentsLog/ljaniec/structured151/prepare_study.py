"""Freeze the existing four-case handoff into a private shared-runtime package."""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SHARED = REPO / 'agentsLog/kwiscion/final-package-prep'
ROUTES = REPO / 'agentsLog/kwiscion/essay-planning-prep'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(output, cache, binary, lock):
    native = load('study_prepare_native', SHARED / 'run_native_package.py')
    prep = load('study_prepare_helpers', SHARED / 'prepare_native_package.py')
    output = output.resolve()
    private = (REPO / 'agentsLog/ljaniec/private').resolve()
    native.need(output.is_relative_to(private) and output != private and not output.exists(),
                'Fresh owned private package required')
    sys.path.insert(0, str(ROUTES))
    import study_driver
    cases, budget = study_driver.load_cases(REPO)
    output.mkdir(parents=True)
    for destination, source in prep.SOURCES.items():
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / source, target)
    for name in ('run_recovery_package.py', 'recovery_harness.py'):
        shutil.copyfile(SHARED / name, output / name)
    for name in ('study_binding.py', 'stage_session.py', 'prepare_study.py'):
        target = output / 'study' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / name, target)
    inventory = native.read(ROUTES / 'PUBLICATION_INVENTORY.json')
    for row in inventory['files']:
        source = native.safe_file(ROUTES, row['path'])
        native.need(native.sha(source) == row['sha256'], 'Frozen route dependency: ' + row['path'])
        target = output / 'study/routes' / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    native.write(output / 'cases.json', cases)
    guardian = prep.guardian(3600).replace('operator_native.sh', 'operator_recovery.sh').replace(
        'run_native_package.py', 'run_recovery_package.py')
    (output / 'operator_recovery.sh').write_text(guardian, encoding='utf8', newline='\n')
    files = {p.relative_to(output).as_posix(): native.sha(p) for p in output.rglob('*') if p.is_file()}
    m = {'schema': 'typed_stage_study_v1', 'status': 'PREPARED',
         'declared_utc': None, 'deadline_utc': None, 'authorization': None,
         'model': native.MODEL, 'context': 65536, 'temperature': 'omitted',
         'truncate': False, 'shift': False, 'max_calls': 64,
         'max_requested_tokens': 1409024, 'max_seconds': 3600,
         'ids': [c['id'] for c in cases], 'binary': binary, 'cache': cache, 'lock': lock,
         'original_service_policy': 'absent_or_verified_idle',
         'budget_sha256': native.sha(output / 'study/routes/prompt-study-budget-v2.json'),
         'files': files}
    native.write(output / 'launch.json', m)
    binding = load('prepared_study_binding', output / 'run_recovery_package.py')
    binding.preflight(output)
    return {'status': 'PREPARED', 'model_calls': 0, 'max_calls': 64,
            'max_requested_tokens': 1409024, 'manifest_sha256': native.sha(output / 'launch.json'),
            'cases_sha256': native.sha(output / 'cases.json'), 'files': len(files)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    for name in ('cache', 'binary', 'lock'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, args.cache, args.binary, args.lock)))
