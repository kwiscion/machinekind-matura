"""Generic optional RAG scheduling and exact original-template answer export.

No exam-specific eligibility, model weights, network or model dispatch here.
"""
import copy
import hashlib
import json
from pathlib import Path

_BASELINE_EXPORTS = {}

SCHEMA = 'generic_deadline_rag_v1'
OPTIONAL_SECONDS = 1200
RESERVE_SECONDS = 600
ANSWER_TOKENS = 32768 * 3 + 49152
QUERY_TOKENS = 512 + 1024 * 3
JUDGE_TOKENS = 384 + 1024 * 3


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def atomic(path, value):
    import os
    import time
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf8')
    if path.exists() and path.read_bytes() == encoded:
        return
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('wb') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    for retry in range(6):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if os.name != 'nt' or retry == 5:
                raise
            time.sleep(.02)


def make_plan(template, essay_ids):
    ids = [row['id'] for row in template['answers']]
    if not ids or len(ids) != len(set(ids)) or not set(essay_ids).issubset(ids):
        raise ValueError('Exact original template and explicit essay IDs required')
    prefix = '__optional_rag__:'
    while any(item.startswith(prefix) for item in ids):
        prefix = '_' + prefix
    stages = {}
    sources = {}
    phase = 1
    for number, original_id in enumerate(ids):
        key = f'{number:06d}'
        sources[key] = original_id
        stages[original_id] = dict(source_id=key, original_id=original_id,
                                   kind='direct', rank=None, phase=0)
    for key, original_id in sources.items():
        if original_id in essay_ids:
            continue
        for kind, ranks in [('query', [None]), ('judge', range(5)), ('final', [None])]:
            for rank in ranks:
                slot = prefix + kind + (':' + str(rank) if rank is not None else '') + ':' + key
                stages[slot] = dict(source_id=key, original_id=original_id,
                                    kind=kind, rank=rank, phase=phase)
            phase += 1
    eligible = len(ids) - len(essay_ids)
    return dict(schema=SCHEMA, stages=stages, sources=sources, slot_prefix=prefix,
                original_ids=ids, essay_ids=list(essay_ids), eligible_count=eligible,
                eligibility='Every explicitly nonessay item, in original template order',
                optional_seconds=OPTIONAL_SECONDS, reserve_seconds=RESERVE_SECONDS,
                maximum_declared_seconds=3300,
                primary_calls=len(ids) + 7 * eligible,
                max_calls=4 * (len(ids) + 7 * eligible),
                max_requested_tokens=(len(ids) + eligible) * ANSWER_TOKENS
                    + eligible * (QUERY_TOKENS + 5 * JUDGE_TOKENS))


def validate_envelope(root, manifest):
    plan = read(root / 'study.json')
    template = read(root / 'source-template.json')
    expected = make_plan(template, manifest['essay_ids'])
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ValueError('Generic frozen stage plan changed: ' + key)
    if manifest['recovery']['minutes'] != 60 or manifest['max_seconds'] != 3600:
        raise ValueError('Exactly 60-minute guardian required')
    if manifest['status'] == 'DECLARED':
        import datetime
        start = datetime.datetime.fromisoformat(manifest['declared_utc'])
        end = datetime.datetime.fromisoformat(manifest['deadline_utc'])
        if not 0 < (end - start).total_seconds() <= expected['maximum_declared_seconds']:
            raise ValueError('Final actual declaration must be at most 55 minutes')
    if (manifest['max_calls'] != expected['max_calls']
            or manifest['max_requested_tokens'] != expected['max_requested_tokens']):
        raise ValueError('Exact short auxiliary call/token envelope required')
    if set(manifest['ids']) != set(expected['original_ids']):
        raise ValueError('Original ID set changed')
    return plan


def expand(root, package, cases, manifest):
    plan = validate_envelope(root, manifest)
    if read(root / 'source-template.json') != package['template']:
        raise ValueError('Original template changed')
    by_id = {case['id']: case for case in cases}
    expanded = []
    # Preserve the original direct scheduler order and each complete payload.
    for case in cases:
        expanded.append(copy.deepcopy(case))
    for slot, stage in plan['stages'].items():
        if stage['kind'] == 'direct':
            continue
        case = copy.deepcopy(by_id[stage['original_id']])
        case['id'] = slot
        case['kind'] = 'ordinary'
        expanded.append(case)
    result = copy.deepcopy(package)
    result['template'] = dict(exam_id=package['template']['exam_id'],
        answers=[dict(id=case['id'], answer='') for case in expanded])
    return result, expanded


def export_original(root, states, stop=None):
    plan = read(root / 'study.json')
    template = read(root / 'source-template.json')
    # Reuse the preserved baseline's qualified aggregate-size and partial policy.
    # Raw complete strings remain in engine states/events; this is the exact
    # artifact the original-only baseline exporter would have produced.
    baseline_path = root / 'recovery_harness.py.baseline'
    if baseline_path not in _BASELINE_EXPORTS:
        import importlib.util
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader('deadline_saved_baseline', str(baseline_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        _BASELINE_EXPORTS[baseline_path] = module.export
    baseline_out = root / 'results/direct-baseline'
    baseline_out.mkdir(parents=True, exist_ok=True)
    direct_result = _BASELINE_EXPORTS[baseline_path](baseline_out, template,
        {item: states[item] for item in plan['original_ids']}, stop)
    direct_status = read(baseline_out / 'answer-status.json')['items']
    result = copy.deepcopy(direct_result)
    metadata = {}
    final_slots = {stage['original_id']: slot for slot, stage in plan['stages'].items()
                   if stage['kind'] == 'final'}
    for row, direct_row in zip(result['answers'], direct_result['answers']):
        item = row['id']
        direct = states[item]
        complete = direct['answer']
        partial = max(direct['partial_candidates'], key=len, default=None)
        baseline = direct_row['answer']
        slot = final_slots.get(item)
        final = states.get(slot, {})
        selected = final.get('answer')
        # Optional incomplete outputs never displace a usable direct candidate.
        use_final = isinstance(selected, str) and bool(selected.strip()) and len(selected) <= 100000 and not final.get('warnings')
        row['answer'] = selected if use_final else baseline
        overflow = len((json.dumps(result, ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf8')) > 1048576
        if overflow:
            row['answer'] = baseline
            use_final = False
        metadata[item] = dict(selection='rag_complete_final' if use_final else 'saved_direct',
            direct_sha256=hashlib.sha256(baseline.encode('utf8')).hexdigest(),
            direct_placeholder=complete is None and partial is None,
            direct_incomplete_partial=complete is None and partial is not None,
            direct_attempts=direct['attempts'], optional_final_slot=slot,
            optional_final_attempts=final.get('attempts', 0),
            optional_rejected_for_size=overflow, direct_export_status=direct_status[item],
            mandatory_attempts_unfulfilled=max(0, 4-direct['attempts']) if complete is None else 0)
    for doc in (result, direct_result):
        if any(not isinstance(row['answer'], str) or not row['answer'].strip()
               or len(row['answer']) > 100000 for row in doc['answers']):
            raise ValueError('Exact export contains invalid answer')
        if len((json.dumps(doc, ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf8')) > 1048576:
            raise ValueError('Exact original-template export exceeds organizer byte cap; originals preserved')
    atomic(root / 'results/answers.direct.json', direct_result)
    atomic(root / 'results/answers.json', result)
    atomic(root / 'results/deadline-rag-status.json', dict(stop=stop, items=metadata,
        placeholder_is_not_successful_recovery=True, exact_direct_fallback=True))
    return result
