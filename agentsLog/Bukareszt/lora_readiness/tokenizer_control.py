"""Tokenizer control on the pinned local base: no model weights loaded, no generation.

Part A (synthetic): runs root's UNCHANGED prepare.py `data --local-base` end-to-end on
two synthetic 400-word records with a SYNTHETIC clearance sidecar (clearly labelled;
not real accepted history data).
Part B (real rows, tokenization only): applies prepare.tokenized_record to the 90
canonical export_v1 rows to measure prompt/completion token lengths, boundary
stability and the 4096-token cap. No prepared training output is written for
real rows and no clearance sidecar is fabricated; issuing that sidecar stays with root.
"""
import argparse, hashlib, json, subprocess, sys, tempfile
from pathlib import Path


def sha(b): return hashlib.sha256(b).hexdigest()


def synthetic_rows():
    rows = []
    for i, grp in enumerate(('SYN-A', 'SYN-B')):
        words = ' '.join([f'Synteza{i}'] + ['zdanie' if i == 0 else 'wyraz'] * 419) + '.'
        rows.append({'id': f'synthetic-{i}', 'task_type': 'essay', 'source_group_id': grp, 'source_ids': [f'synthetic-src-{i}'],
                     'messages': [{'role': 'user', 'content': f'Syntetyczne polecenie kontrolne {i}.'},
                                  {'role': 'assistant', 'content': words}]})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--probe-dir', type=Path, required=True, help='dir with root prepare.py/candidate.json/evidence-manifest.json')
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--train', type=Path, required=True, help='canonical export_v1/train_sft.jsonl bytes')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.probe_dir))
    import prepare
    report = {'prepare_py_sha256': sha((a.probe_dir / 'prepare.py').read_bytes()),
              'train_sha256': sha(a.train.read_bytes())}
    assert report['train_sha256'] == '83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5'
    # Part A: synthetic end-to-end through prepare.py CLI
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rows = synthetic_rows()
        train = td / 'train.jsonl'; train.write_text(json.dumps(rows[0], ensure_ascii=False) + '\n', encoding='utf-8')
        hold = td / 'holdout.jsonl'; hold.write_text(json.dumps(rows[1], ensure_ascii=False) + '\n', encoding='utf-8')
        clear = {'schema': 'essay_lora_clearance_v1', 'SYNTHETIC_CONTROL_NOT_REAL_CLEARANCE': True,
                 'checks': {k: True for k in prepare.CHECKS},
                 'files': {'train': {'sha256': sha(train.read_bytes())}, 'holdout': {'sha256': sha(hold.read_bytes())}},
                 'canonical_group_map': {'SYN-A': 'SYN-A', 'SYN-B': 'SYN-B'},
                 'accepted_records': {r['id']: {'status': 'accepted', 'record_sha256': sha(prepare.canonical(r)),
                                                'independent_review_reference': 'SYNTHETIC_CONTROL'} for r in rows}}
        cp = td / 'clearance.json'; cp.write_text(json.dumps(clear), encoding='utf-8')
        done = subprocess.run([sys.executable, str(a.probe_dir / 'prepare.py'), 'data', '--train', str(train), '--holdout', str(hold),
                               '--clearance', str(cp), '--local-base', str(a.base), '--output', str(td / 'prepared')],
                              capture_output=True, text=True, timeout=300, env={'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PATH': '/usr/bin:/bin'})
        report['synthetic_prepare'] = {'returncode': done.returncode, 'stdout_tail': done.stdout[-3000:], 'stderr_tail': done.stderr[-2000:]}
        if done.returncode == 0:
            prepped = [json.loads(l) for l in (td / 'prepared' / 'train.jsonl').read_text().splitlines()]
            p = prepped[0]
            report['synthetic_prepare']['record'] = {'prompt_tokens': p['prompt_tokens'], 'completion_tokens': p['completion_tokens'],
                                                     'masked_labels': sum(1 for x in p['labels'] if x == -100),
                                                     'first_ids': p['input_ids'][:4], 'last_ids': p['input_ids'][-3:]}
    # Part B: real rows, tokenization only
    prepare.verify_metadata(a.base, json.loads((a.probe_dir / 'candidate.json').read_text()))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(a.base), local_files_only=True, trust_remote_code=False)
    rows = [json.loads(l) for l in a.train.read_text(encoding='utf-8').splitlines() if l.strip()]
    lens, fails = [], []
    for r in rows:
        try:
            t = prepare.tokenized_record(r, tok, 4096)
            lens.append((r['id'], r['task_type'], t['prompt_tokens'], t['completion_tokens']))
        except Exception as e:  # record, don't hide
            fails.append({'id': r['id'], 'error': str(e)[:300]})
    tot = [p + c for _, _, p, c in lens]
    report['real_rows_tokenization_only'] = {
        'rows': len(rows), 'pass': len(lens), 'fail': fails,
        'max_total_tokens': max(tot) if tot else None, 'mean_total_tokens': round(sum(tot) / len(tot), 1) if tot else None,
        'max_prompt_tokens': max(p for _, _, p, _ in lens) if lens else None,
        'completion_tokens_min_max': [min(c for *_, c in lens), max(c for *_, c in lens)] if lens else None,
        'supervised_completion_tokens_total': sum(c for *_, c in lens),
        'cap': 4096, 'written_training_output': False}
    report['tokenizer'] = {'class': type(tok).__name__, 'vocab_size': tok.vocab_size, 'len': len(tok),
                           'turn_end_ids': tok('<turn|>', add_special_tokens=False)['input_ids']}
    report['status'] = 'PASS' if report['synthetic_prepare']['returncode'] == 0 and not fails else 'FAIL'
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
