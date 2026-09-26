"""Validate lineage/quarantine only; does not independently judge historical content."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


originals = {row['id']: row for row in rows(ROOT / 'data/przemeknowak781/train.jsonl')}
candidates = rows(HERE / 'candidates.jsonl')
manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
assert 0 < len(candidates) <= 30
assert len({row['id'] for row in candidates}) == len(candidates)
for name, expected in manifest['files'].items():
    assert hashlib.sha256((HERE / name).read_text(encoding='utf-8').encode()).hexdigest() == expected
for row in candidates:
    old = originals[row['derivation']['original_id']]
    assert row['id'] not in originals
    assert row['split'] == 'TRAIN' and row['audit']['status'] == 'draft'
    assert row['source_group_id'] == old['source_group_id']
    assert row['source_ids'] == old['source_ids']
    assert all(evidence in old['evidence'] for evidence in row['evidence'])
    assert row['derivation']['original_record_sha256'] == hashlib.sha256(
        json.dumps(old, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

sys.path.insert(0, str(ROOT / 'scripts/przemeknowak781'))
from strict_eligibility import eligible_input
try:
    eligible_input(HERE / 'candidates.jsonl')
except ValueError as exc:
    assert 'not the reviewed strict version' in str(exc)
else:
    raise AssertionError('Draft candidates must not be export-eligible')
print(json.dumps({'candidates': len(candidates), 'lineage_valid': True,
                  'drafts_rejected_by_strict_export': True, 'independent_audit': 'pending'}))
