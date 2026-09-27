"""CPU-only generic organizer preparation with the exact tested coverage suffix."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PINS = {
    'essay-coverage-prep/coverage_suffix.py': '298d383edcd03cf1cc0a4b6ffaa1d97941b60c0e48090667b7861418ae836bae',
    'qwen-thinking-prep/prepare_qwen_exam.py': 'a3134927353b28d71d75187c5c3820a8b65e77d45b5874568f7ef71fb84c0873',
    'final-package-prep/prepare_recovery_package.py': '0ba54f2301ff5afde296df154f5f963900b6d956e825e247af6348f3362005af',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(args):
    for rel, digest in PINS.items():
        if sha(HERE.parent / rel) != digest:
            raise ValueError('Reviewed preparation dependency changed: ' + rel)
    if args.model not in ('gemma', 'qwen') or args.minutes not in (60, 120):
        raise ValueError('Choose a reviewed model and 60 or 120 minutes')
    shared = load('coverage_shared', HERE.parent / 'final-package-prep/prepare_recovery_package.py')
    suffix = load('coverage_suffix_frozen', HERE.parent / 'essay-coverage-prep/coverage_suffix.py')
    adapter = shared.n.load('coverage_adapter', REPO / 'scripts/Bukareszt/matura_package.py')
    source = args.exam_dir.resolve()
    package = adapter.load_package(source)
    original = json.loads((source / 'exam.json').read_text(encoding='utf-8-sig'))
    ids = [item['id'] for item in original['items']]
    essays = args.essay_id or []
    if (bool(essays) == bool(args.no_essay) or len(essays) != len(set(essays))
            or not set(essays).issubset(ids)):
        raise ValueError('Declare unique existing essay IDs, or explicitly --no-essay')
    target = args.output.resolve()
    derived_root = target.with_name(target.name + '.coverage-source')
    private = (HERE.parent / 'private').resolve()
    if (not target.is_relative_to(private) or target == private or target.exists()
            or derived_root.exists() or target.is_relative_to(source)
            or derived_root.is_relative_to(source)):
        raise ValueError('Fresh project-private output and derived-source paths required')
    inputs = {}
    for path in adapter.package_inputs(package):
        rel = path.relative_to(source).as_posix()
        shared.n.safe_file(source, rel)
        inputs[rel] = sha(path)
    derived = copy.deepcopy(original)
    for item in derived['items']:
        if item['id'] in essays:
            item.update(suffix.append_to_item(item))
    derived_root.mkdir(parents=True)
    for rel, digest in inputs.items():
        dest = derived_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, dest)
        if sha(dest) != digest or sha(source / rel) != digest:
            raise ValueError('Source changed during staging')
    if essays:
        (derived_root / 'exam.json').write_text(shared.n.line(derived), encoding='utf8', newline='\n')
    forwarded = copy.copy(args)
    forwarded.exam_dir = derived_root
    forwarded.inject_faults = False
    if args.model == 'qwen':
        builder = load('coverage_qwen', HERE.parent / 'qwen-thinking-prep/prepare_qwen_exam.py')
    else:
        builder = shared
    manifest = builder.prepare(forwarded)
    provenance = {
        'schema': 'generic_coverage_preparation_v1', 'essay_ids': essays,
        'source_files': inputs,
        'derived_files': {rel: sha(derived_root / rel) for rel in inputs},
        'suffix_sha256': suffix.SUFFIX_SHA256, 'preparation_pins': PINS,
        'changes': 'Only selected item.question receives the exact suffix; no runtime changes.',
    }
    shared.n.write(target / 'coverage-provenance.json', provenance)
    shutil.copyfile(HERE.parent / 'essay-coverage-prep/coverage_suffix.py', target / 'coverage_suffix.py')
    for rel in ('coverage-provenance.json', 'coverage_suffix.py'):
        manifest['files'][rel] = sha(target / rel)
    (target / 'launch.json').write_text(shared.n.line(manifest), encoding='utf8', newline='\n')
    shared.n.load('coverage_final_preflight', target / 'run_recovery_package.py').preflight(target)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exam-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', choices=('gemma', 'qwen'), required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--essay-id', action='append')
    group.add_argument('--no-essay', action='store_true')
    for name in ('cache', 'binary', 'lock'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--minutes', type=int, choices=(60, 120), default=60)
    args = parser.parse_args()
    manifest = prepare(args)
    print(json.dumps({'status': 'PREPARED_NOT_AUTHORIZED', 'model': manifest['model'],
                      'items': len(manifest['ids']), 'max_calls': manifest['max_calls'],
                      'max_requested_tokens': manifest['max_requested_tokens'],
                      'manifest_sha256': sha(args.output / 'launch.json'), 'model_calls': 0}))


if __name__ == '__main__':
    main()
