"""Prepare a private paired recovery package from the frozen terminal run; no network."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_SOURCE = REPO/'agentsLog/kwiscion/private/full-thinking-20260926/recovered/full-thinking-20260926'
DEFAULT_DEST = REPO/'agentsLog/kwiscion/private/answer-recovery-20260926/package-v2'
RAW_SHA = '8b814e4f0cd9d35a7b0635d0b62c81ef16d2694b3743373cc68af8d504e4ab78'
LAUNCH_SHA = '2c17a930e89d0f7eb0e4f18b068aa0faf5167e72893116807869d6c8bcf0e4d5'
spec = importlib.util.spec_from_file_location('recovery_prepare_runner', HERE/'run_gemma_answer_recovery.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)

def prepare(source, dest):
    source, dest = source.resolve(), dest.resolve()
    r.require(not dest.exists(), 'Fresh destination required')
    r.require(r.sha(source/'results/raw.jsonl') == RAW_SHA and r.sha(source/'launch.json') == LAUNCH_SHA, 'Terminal provenance')
    old = json.loads((source/'launch.json').read_text(encoding='utf8'))
    for name, digest in old['files'].items():
        path = (source/name).resolve()
        r.require(path.is_relative_to(source) and r.sha(path) == digest, 'Parent pin: '+name)
    inputs, records = r.read_rows(source/'input.jsonl'), r.read_rows(source/'results/raw.jsonl')
    selected = r.select_failures(inputs, records)
    r.require(len(selected) == 3, 'This declaration expects exactly three actual eligible failures')
    dest.mkdir(parents=True)
    shutil.copytree(source/'exam', dest/'exam')
    copies = {'infer.py': source/'infer.py', 'runtime_guard.py': source/'runtime_guard.py',
              'control.py': source/'run_gemma_full_thinking.py',
              'scripts/ljaniec/reasoning_lab.py': source/'scripts/ljaniec/reasoning_lab.py',
              'scripts/Bukareszt/matura_package.py': source/'scripts/Bukareszt/matura_package.py',
              'run_gemma_answer_recovery.py': HERE/'run_gemma_answer_recovery.py',
              'parent/input.jsonl': source/'input.jsonl', 'parent/raw.jsonl': source/'results/raw.jsonl',
              'parent/launch.json': source/'launch.json'}
    for name, path in copies.items():
        target = dest/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
    (dest/'input.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in selected), encoding='utf8', newline='\n')
    by_id = {row['id']: row for row in records}
    notes = []
    for row in selected:
        record = by_id[row['id']]
        note = record.get('raw_response', {}).get('message', {}).get('thinking')
        notes.append({'id': row['id'], 'thinking': note, 'preflight_error': r.note_error(record)})
        for image in row['images']:
            r.require((dest/image).read_bytes() == (source/image).read_bytes(), 'Image preservation')
    (dest/'notes.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in notes), encoding='utf8', newline='\n')
    manifest = dict(status='PREPARED_NOT_AUTHORIZED', declared_utc=None, deadline_utc=None,
        max_calls=6, max_requested_tokens=12288, max_wall_seconds=1200, timeout_seconds=180,
        model=r.MODEL, model_digest=r.DIGEST, runtime_version='0.34.4', context_length=32768,
        think=False, temperature='omitted', retries=0, smokes=0, num_predict=2048,
        base_url='http://127.0.0.1:11436', ids=[row['id'] for row in selected],
        planned_items_per_arm=3, dispatch_order='input order, A then B for each selected item',
        selection='actual terminal error.type in {length, empty_final}; no keys, scores, content or fixed ID filters',
        parent_raw_sha256=RAW_SHA, parent_launch_sha256=LAUNCH_SHA,
        note_policy=r.NOTE_POLICY, notes_screening='original prompt_eval_count + eval_count + 2048 + 256 <= 32768; estimate only; never clip',
        context_acceptance='truncate:false, shift:false; reject either true truncation flag; actual returned prompt_eval_count + 2048 <= 32768',
        submission_weight_bytes=r.WEIGHTS, aggregate_weight_limit_bytes=r.WEIGHT_LIMIT,
        estimated_cost_usd=1.10, cost_basis='20 minutes at reported $3.28/hour, rounded; not measured billing',
        runtime_executable_sha256=old['runtime_executable_sha256'], host_root=None, server_pid=None, server_start_ticks=None,
        files={p.relative_to(dest).as_posix():r.sha(p) for p in dest.rglob('*') if p.is_file()})
    (dest/'launch.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')
    public = {k:v for k,v in manifest.items() if k not in ('files','host_root','server_pid','server_start_ticks')}
    public['private_manifest_sha256'] = r.sha(dest/'launch.json')
    public['runner_sha256'] = r.sha(dest/'run_gemma_answer_recovery.py')
    public['input_sha256'] = r.sha(dest/'input.jsonl')
    public['notes_sha256'] = r.sha(dest/'notes.jsonl')
    public['source_preservation_verified'] = True
    public['notes_status'] = [{'id':x['id'],'error':x['preflight_error']} for x in notes]
    (HERE/'candidate-public.json').write_text(json.dumps(public, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')
    print(json.dumps({'status':manifest['status'],'items_per_arm':3,'manifest_sha256':public['private_manifest_sha256'],'notes_status':public['notes_status']}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--dest', type=Path, default=DEFAULT_DEST)
    args=parser.parse_args(); prepare(args.source, args.dest)
