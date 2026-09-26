"""CPU-only: deterministic essay checks + blinded grading pack with a SEALED arm key (no model calls).

Reads RUN/answers-<ARM>.jsonl. Writes:
- RUN/blind/pack.jsonl: per input, the prompt plus the essays under random labels X/Y(/Z), with deterministic checks.
  It holds no arm, model or file names.
- RUN/blind/SEALED-key.json: label -> arm per input. Graders must NOT see it; only its sha256 is published before grading.
- RUN/blind/deterministic-summary.json: per-arm aggregate checks (unblinded, mechanical only).
Deterministic checks: body word count and the 400-500 band, preamble/meta opening, both-topics heuristic,
markdown/list formatting, and truncation (finish_reason length) or error.
"""
import argparse, hashlib, json, re, secrets
from pathlib import Path

PREAMBLE = re.compile(r'^\s*(oto\b|poniżej\b|jasne\b|oczywiście\b|oto moje\b|wypracowanie\s*:|temat\s*\d|#|\*\*temat|wybieram\b|wybrałem\b|wybrałam\b)', re.I)


def checks(text, finish_reason, error):
    t = text or ''
    words = re.findall(r'\w+(?:[-’\']\w+)*', t, re.U)
    lines = [l for l in t.splitlines() if l.strip()]
    return {
        'word_count': len(words),
        'in_400_500': 400 <= len(words) <= 500,
        'preamble_or_meta_opening': bool(lines and PREAMBLE.match(lines[0])),
        'mentions_both_topics': bool(re.search(r'temat\s*1', t, re.I) and re.search(r'temat\s*2', t, re.I)),
        'markdown_or_list': bool(re.search(r'^\s*(#|[-*•]\s|\d+[.)]\s)', t, re.M)),
        'truncated': finish_reason == 'length',
        'failed': bool(error) or not t.strip(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--arms', nargs='+', required=True)
    a = ap.parse_args()
    out = a.run / 'blind'
    out.mkdir()  # fails if it exists (no stale pack)
    inputs = {r['id']: r for r in (json.loads(l) for l in a.inputs.read_text(encoding='utf-8').splitlines() if l.strip())}
    ans = {}
    for arm in a.arms:
        recs = [json.loads(l) for l in (a.run / f'answers-{arm}.jsonl').read_text(encoding='utf-8').splitlines()]
        ans[arm] = {r['id']: r for r in recs if 'call_number' in r}
    rng = secrets.SystemRandom()
    labels = ['X', 'Y', 'Z'][:len(a.arms)]
    key, pack, summary = {}, [], {arm: {'n': 0, 'in_400_500': 0, 'preamble': 0, 'both_topics': 0, 'markdown': 0, 'truncated': 0, 'failed': 0, 'words': []} for arm in a.arms}
    for iid, row in inputs.items():
        order = list(a.arms); rng.shuffle(order)
        key[iid] = dict(zip(labels, order))
        essays = {}
        for lab, arm in zip(labels, order):
            r = ans[arm].get(iid, {})
            c = checks(r.get('text'), r.get('finish_reason'), r.get('error') if r else 'missing')
            essays[lab] = {'text': r.get('text') or '', 'checks': c}
            s = summary[arm]; s['n'] += 1; s['words'].append(c['word_count'])
            for k, kk in (('in_400_500', 'in_400_500'), ('preamble', 'preamble_or_meta_opening'), ('both_topics', 'mentions_both_topics'),
                          ('markdown', 'markdown_or_list'), ('truncated', 'truncated'), ('failed', 'failed')):
                s[k] += int(c[kk])
        pack.append({'id': iid, 'source_group_id': row['source_group_id'], 'prompt': row['prompt'], 'essays': essays})
    pb = ''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in pack).encode('utf-8')
    (out / 'pack.jsonl').write_bytes(pb)
    kb = json.dumps({'labels_to_arms': key, 'arms': a.arms, 'pack_sha256': hashlib.sha256(pb).hexdigest()}, indent=1).encode()
    (out / 'SEALED-key.json').write_bytes(kb)
    for s in summary.values():
        w = s.pop('words'); s['word_count_min_median_max'] = [min(w), sorted(w)[len(w) // 2], max(w)] if w else None
    (out / 'deterministic-summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps({'pack_sha256': hashlib.sha256(pb).hexdigest(), 'sealed_key_sha256': hashlib.sha256(kb).hexdigest(), 'summary': summary}))


if __name__ == '__main__':
    main()
