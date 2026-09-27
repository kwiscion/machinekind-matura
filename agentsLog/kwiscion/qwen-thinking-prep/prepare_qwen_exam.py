"""Prepare any organizer exam with the reviewed closed Qwen profile; no execution."""
import argparse
import importlib.util
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROFILE_SHA = '953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(args):
    shared = load('qwen_exam_prepare', HERE.parent / 'final-package-prep/prepare_recovery_package.py')
    shared.n.need(shared.n.sha(HERE / 'closed_profile.py') == PROFILE_SHA, 'Reviewed Qwen profile changed')
    # The generic preparer owns source copying, ID/template checks and essay mapping.
    args.inject_faults = False
    manifest = shared.prepare(args)
    target = args.output.resolve()
    shutil.copyfile(HERE / 'closed_profile.py', target / 'closed_profile.py')
    manifest.update(model_profile='qwen35_9b_thinking_v1', model='qwen3.5:9b',
                    temperature=1, top_p=0.95, top_k=64)
    manifest['files']['closed_profile.py'] = PROFILE_SHA
    (target / 'launch.json').write_text(shared.n.line(manifest), encoding='utf8', newline='\n')
    packed = load('qwen_exam_preflight', target / 'run_recovery_package.py')
    packed.preflight(target)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exam-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--essay-id', action='append')
    group.add_argument('--no-essay', action='store_true')
    for name in ('cache', 'binary', 'lock'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--minutes', type=int, choices=(60, 120), default=60)
    args = parser.parse_args()
    manifest = prepare(args)
    import hashlib, json
    print(json.dumps({'status': 'PREPARED_NOT_AUTHORIZED', 'model': manifest['model'],
                      'items': len(manifest['ids']), 'max_calls': manifest['max_calls'],
                      'max_requested_tokens': manifest['max_requested_tokens'],
                      'manifest_sha256': hashlib.sha256((args.output / 'launch.json').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
