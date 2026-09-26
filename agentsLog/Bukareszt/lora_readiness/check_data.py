"""Canonical-bytes and attribution check for the cleared #117 export_v1 (no model use).

Extracts the train/eval/attribution files from a Git revision (never the working
tree, which may carry CRLF on Windows), asserts the root-cleared train SHA-256,
checks id alignment, and writes a training attribution sidecar that carries the
reference-only fields from root's PR131 clearance addendum. Frozen exports are
not modified.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

EXPORT = 'agentsLog/Bukareszt/essay_corpus/export_v1'
TRAIN_SHA = '83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5'
CLEARANCE = 'agentsLog/kwiscion/2026-09-26-pr131-data-clearance.json'


def blob(rev, path):
    return subprocess.check_output(['git', 'show', f'{rev}:{path}'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rev', default='origin/main')
    ap.add_argument('--out-dir', type=Path, required=True)
    a = ap.parse_args()
    train_b = blob(a.rev, f'{EXPORT}/train_sft.jsonl')
    eval_b = blob(a.rev, f'{EXPORT}/eval16_input.jsonl')
    attr_b = blob(a.rev, f'{EXPORT}/attribution.jsonl')
    clearance = json.loads(blob(a.rev, CLEARANCE))
    sha = hashlib.sha256(train_b).hexdigest()
    assert sha == TRAIN_SHA, ('train hash mismatch', sha)
    assert b'\r' not in train_b, 'CRLF in canonical train bytes'
    train = [json.loads(l) for l in train_b.decode('utf-8').splitlines()]
    attr = [json.loads(l) for l in attr_b.decode('utf-8').splitlines()]
    evals = [json.loads(l) for l in eval_b.decode('utf-8').splitlines()]
    assert len(train) == 90 and len(evals) == 16, (len(train), len(evals))
    assert [r['id'] for r in train] == [r['id'] for r in attr], 'attribution id order/coverage mismatch'
    ref = clearance['reference_only']
    ref_ids = set(ref['source_ids'])
    assert ref['source_text_exported'] is False
    sidecar, ref_rows = [], 0
    for r in attr:
        srcs = []
        for s in r['sources']:
            s = dict(s)
            if s['source_id'] in ref_ids:
                s['allowed_use'] = ref['allowed_use']
                s['source_text_exported'] = False
                ref_rows += 1
            srcs.append(s)
        sidecar.append({**r, 'sources': srcs})
    types = {}
    for r in train:
        types[r.get('task_type')] = types.get(r.get('task_type'), 0) + 1
    a.out_dir.mkdir(parents=True, exist_ok=True)
    side_bytes = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in sidecar).encode('utf-8')
    (a.out_dir / 'training_attribution.jsonl').write_bytes(side_bytes)
    report = {
        'status': 'PASS', 'rev': subprocess.check_output(['git', 'rev-parse', a.rev], text=True).strip(),
        'train_sha256': sha, 'train_git_blob': subprocess.check_output(['git', 'rev-parse', f'{a.rev}:{EXPORT}/train_sft.jsonl'], text=True).strip(),
        'eval16_sha256': hashlib.sha256(eval_b).hexdigest(), 'attribution_sha256': hashlib.sha256(attr_b).hexdigest(),
        'rows': len(train), 'task_types': types, 'eval_inputs': len(evals),
        'reference_only_source_ids': sorted(ref_ids), 'reference_only_source_entries_marked': ref_rows,
        'training_attribution_sidecar_sha256': hashlib.sha256(side_bytes).hexdigest(),
        'clearance_file': CLEARANCE,
    }
    (a.out_dir / 'data_check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    sys.exit(main())
