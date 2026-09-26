"""Reconstruct eligibility from the pinned, already-committed round-1 evidence."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('data/przemeknowak781')
TRAIN = str(BASE / 'train.jsonl').replace('\\', '/')
LENSES = ['agentsLog/przemeknowak781/strict/r1_S.jsonl',
          'agentsLog/przemeknowak781/strict/r1_Q.jsonl']


def read_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate IDs in {path}')
    return rows


def reviewed_records(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / BASE / 'strict_provenance.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((root / name).read_text(encoding='utf-8').encode('utf-8')).hexdigest() != expected:
            raise ValueError(f'Reviewed evidence changed: {name}; independent re-review required')
    lenses = [{row['id']: row for row in read_rows(root / name)} for name in LENSES]
    result = []
    for original in read_rows(root / TRAIN):
        if not all(lens.get(original['id'], {}).get('pass') is True for lens in lenses):
            continue
        if original['split'] != 'TRAIN' or original['rights_status'] != 'clear':
            raise ValueError(f'Ineligible split/rights: {original["id"]}')
        row = copy.deepcopy(original)
        row['legacy_audit'] = row.pop('audit')
        row['audit'] = {'status': 'verified', 'reviewer': manifest['reviewer'],
                        'notes': 'r1: both committed lenses passed; provisional; no new judging',
                        'source_commit': manifest['source_commit'], 'rubric': manifest['rubric']}
        result.append(row)
    if not result:
        raise ValueError('No reviewed dual-pass records')
    return result


def eligible_input(path, root=ROOT):
    expected = {row['id']: row for row in reviewed_records(root)}
    rows = read_rows(path)
    if not rows:
        raise ValueError('No eligible input records')
    for row in rows:
        if row != expected.get(row['id']):
            raise ValueError(f'Record is not the reviewed strict version: {row["id"]}')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify committed strict artifact without writing')
    args = parser.parse_args()
    target = ROOT / BASE / 'train_strict.jsonl'
    expected = reviewed_records()
    if args.check:
        if read_rows(target) != expected:
            raise ValueError('Strict artifact differs from reviewed evidence')
    else:
        target.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in expected), encoding='utf-8')
    print(json.dumps({'strict_dual_pass': len(expected), 'provisional': True}))


if __name__ == '__main__':
    main()
