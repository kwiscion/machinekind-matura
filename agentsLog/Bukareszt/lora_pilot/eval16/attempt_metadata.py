"""Answer-free per-attempt metadata + EOG/stop configuration summary for an eval16 run (CPU, read-only).

Writes RUN/attempt-metadata.json. For each arm/item/attempt it records: call number, request/response sha256,
finish reason, prompt/completion tokens, seconds, error, skip reason, and the final complete/partial/placeholder
label with body word count. It never includes essay text. It also extracts the EOG/EOS/stop-token lines that
llama-server logged for each arm's model.
usage: attempt_metadata.py RUN
"""
import json, re, sys
from pathlib import Path

run = Path(sys.argv[1])
out = {'arms': {}, 'eog_config': {}}
for ans in sorted(run.glob('answers-*.jsonl')):
    arm = ans.stem.split('-')[1]
    rows = [json.loads(l) for l in ans.read_text(encoding='utf-8').splitlines()]
    meta = next((r['meta'] for r in rows if 'meta' in r), {})
    items = []
    for r in rows:
        if not r.get('item'):
            continue
        items.append({'id': r['id'], 'final_status': r['final_status'], 'chosen_call_number': r['chosen_call_number'],
                      'final_finish_reason': r['finish_reason'],
                      'final_body_words': 0 if r['final_status'] == 'placeholder' else len(re.findall(r'\w+', r['text'])),
                      'attempts': [{k: a.get(k) for k in ('attempt', 'call_number', 'max_tokens', 'synthesis_with_draft', 'request_sha256', 'response_sha256',
                                                          'http_status', 'finish_reason', 'seconds', 'error', 'skipped')}
                                   | {'prompt_tokens': (a.get('usage') or {}).get('prompt_tokens'), 'completion_tokens': (a.get('usage') or {}).get('completion_tokens')}
                                   for a in r['attempts']]})
    calls = [a for it in items for a in it['attempts'] if a.get('call_number')]
    out['arms'][arm] = {'model': meta.get('model'), 'model_sha256': meta.get('model_sha256'), 'mmproj_sha256': meta.get('mmproj_sha256'),
                        'server_cmd': meta.get('server_cmd'), 'served_chat_template_sha256': meta.get('served_chat_template_sha256'),
                        'load_seconds': meta.get('load_seconds'),
                        'counts': {s: sum(1 for i in items if i['final_status'] == s) for s in ('complete', 'partial', 'placeholder')},
                        'calls': len(calls), 'requested_tokens': sum(a['max_tokens'] for a in calls),
                        'completion_tokens': sum(a['completion_tokens'] or 0 for a in calls),
                        'length_finishes': sum(1 for a in calls if a['finish_reason'] == 'length'),
                        'generation_seconds': round(sum(a['seconds'] or 0 for a in calls), 1), 'items': items}
    log = run / f'server-arm{arm}.log'
    if log.exists():
        lines = [l.strip() for l in log.read_text(errors='replace').splitlines()
                 if re.search(r'\b(EOG|EOS|EOT|eog|stop|BOS)\b', l) and ('print_info' in l or 'token' in l.lower())]
        out['eog_config'][arm] = lines[:40]
ledger = [json.loads(l) for l in (run / 'call-ledger.jsonl').read_text().splitlines()]
res = [r for r in ledger if r['event'] == 'reserved']
out['wave'] = {'reserved_calls': len(res), 'requested_tokens': sum(r['max_tokens'] for r in res), 'call_cap': 128, 'token_cap': 4718592}
(run / 'attempt-metadata.json').write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps({a: {k: v for k, v in d.items() if k != 'items' and k != 'server_cmd'} for a, d in out['arms'].items()} | {'wave': out['wave']}, indent=1))
