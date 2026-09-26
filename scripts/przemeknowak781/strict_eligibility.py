"""Reconstruct eligibility from pinned, already-committed verification evidence.

Round 1: base records whose committed S and Q verdicts are both true.
Round B: round-1 repairs and generated essay plans, exactly as judged (payload_rB), passing both lenses.
Round C: round-B repairs, exactly as judged (payload_rC), passing both lenses.
Round D: the context audit covers exactly the accepted set (payload_rD); records with a
         confirmed defect are excluded.
No model is called here: membership and text follow only from the pinned files.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('data/przemeknowak781')
TRAIN = str(BASE / 'train.jsonl').replace('\\', '/')
STRICT = 'agentsLog/przemeknowak781/strict'
LENSES = [f'{STRICT}/r1_S.jsonl', f'{STRICT}/r1_Q.jsonl']
PAYLOAD_KEYS = ('task_type', 'era', 'prompt', 'answer')


def read_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate IDs in {path}')
    return rows


def by_id(root, name):
    return {row['id']: row for row in read_rows(root / name)}


def passes(lenses, rid):
    return all(lens.get(rid, {}).get('pass') is True for lens in lenses)


def repaired(row, repair):
    if not repair or repair.get('action') != 'repair' or not repair.get('prompt') or not repair.get('answer'):
        return None
    row = copy.deepcopy(row)
    row['prompt'], row['answer'] = repair['prompt'], repair['answer']
    row['generator']['prompt_revision'] += '+repair_v2'
    return row


def as_judged(candidates, payload_name, root):
    """Keep the candidates that were judged, and prove the judged text equals the reconstruction."""
    judged = []
    for item in read_rows(root / payload_name):
        row = candidates.get(item['id'])
        if row is None:
            raise ValueError(f'{payload_name}: judged id not reconstructible: {item["id"]}')
        claims = [{'locator': e['locator'], 'claim': e['claim']} for e in row['evidence']]
        if any(item.get(k) != row.get(k) for k in PAYLOAD_KEYS) or item['evidence'] != claims:
            raise ValueError(f'{payload_name}: judged text differs from reconstruction: {item["id"]}')
        judged.append(row)
    return judged


def verified(row, manifest, rnd):
    row = copy.deepcopy(row)
    row['legacy_audit'] = row.pop('audit')
    row['audit'] = {'status': 'verified', 'reviewer': manifest['reviewer'],
                    'notes': f'{rnd}: both committed lenses passed; context_audit_v1: no confirmed defect; '
                             'provisional; no new judging',
                    'source_commit': manifest['source_commits'][rnd], 'rubric': manifest['rubrics'][rnd]}
    return row


def reviewed_records(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / BASE / 'strict_provenance.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((root / name).read_text(encoding='utf-8').encode('utf-8')).hexdigest() != expected:
            raise ValueError(f'Reviewed evidence changed: {name}; independent re-review required')

    base = read_rows(root / TRAIN)
    for row in base:
        if row['split'] != 'TRAIN' or row['rights_status'] != 'clear':
            raise ValueError(f'Ineligible split/rights: {row["id"]}')

    lenses_1 = [by_id(root, name) for name in LENSES]
    accepted = [(r, 'r1') for r in base if passes(lenses_1, r['id'])]
    repairs_1 = by_id(root, f'{STRICT}/r1_repairs.jsonl')
    cand_b = {}
    for r in base:
        if not passes(lenses_1, r['id']):
            fixed = repaired(r, repairs_1.get(r['id']))
            if fixed:
                cand_b[fixed['id']] = fixed
    for name in manifest['essay_files']:
        for r in read_rows(root / name):
            if r['id'] in cand_b:
                raise ValueError(f'Duplicate candidate id: {r["id"]}')
            cand_b[r['id']] = r
    judged_b = as_judged(cand_b, f'{STRICT}/payload_rB.jsonl', root)

    lenses_b = [by_id(root, f'{STRICT}/rB_S.jsonl'), by_id(root, f'{STRICT}/rB_Q.jsonl')]
    accepted += [(r, 'rB') for r in judged_b if passes(lenses_b, r['id'])]
    repairs_b = by_id(root, f'{STRICT}/rB_repairs.jsonl')
    cand_c = {}
    for r in judged_b:
        if not passes(lenses_b, r['id']):
            fixed = repaired(r, repairs_b.get(r['id']))
            if fixed:
                cand_c[fixed['id']] = fixed
    judged_c = as_judged(cand_c, f'{STRICT}/payload_rC.jsonl', root)
    lenses_c = [by_id(root, f'{STRICT}/rC_S.jsonl'), by_id(root, f'{STRICT}/rC_Q.jsonl')]
    accepted += [(r, 'rC') for r in judged_c if passes(lenses_c, r['id'])]

    audited = as_judged({r['id']: r for r, _ in accepted}, f'{STRICT}/payload_rD.jsonl', root)
    if {r['id'] for r in audited} != {r['id'] for r, _ in accepted}:
        raise ValueError('Context audit did not cover exactly the accepted set')
    audit = by_id(root, f'{STRICT}/rD_context_audit.jsonl')
    if set(audit) != {r['id'] for r, _ in accepted}:
        raise ValueError('Context audit results do not match the accepted set')
    confirmed = {cid for cid, c in by_id(root, f'{STRICT}/rD_context_confirm.jsonl').items()
                 if c.get('confirmed') is True and audit[cid].get('flag') is True}

    result = [verified(r, manifest, rnd) for r, rnd in accepted if r['id'] not in confirmed]
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
    rounds = {}
    for row in expected:
        rounds[row['audit']['notes'].split(':')[0]] = rounds.get(row['audit']['notes'].split(':')[0], 0) + 1
    print(json.dumps({'strict_dual_pass': len(expected), 'by_round': rounds, 'provisional': True}))


if __name__ == '__main__':
    main()
