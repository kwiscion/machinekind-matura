"""Export reviewed strict dual-pass records to chat-format SFT files for LoRA training.

Writes two variants to data/przemeknowak781/sft/:
  closed_book_{train,holdout}.jsonl  user = question only
  grounded_{train,holdout}.jsonl     user = question + source passages (the record's claims
                                     plus distractor claims from other topics, shuffled)
The holdout is chosen by source_group_id so no topic appears in both parts. It is an internal
overfitting check only, not an exam split.

Usage: python scripts/przemeknowak781/export_sft.py [--input PATH] [--holdout 0.1] [--distractors 2] [--seed 13]
"""
import argparse
import hashlib
import json
import random
import sys

try:
    from .strict_eligibility import eligible_input
except ImportError:
    from strict_eligibility import eligible_input
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "data/przemeknowak781"
SYSTEM = ("Jesteś asystentem przygotowującym do matury z historii Polski. Odpowiadasz po polsku, "
          "zwięźle i precyzyjnie, w stylu odpowiedzi maturalnej. Podajesz tylko fakty, które wynikają "
          "z wiedzy historycznej lub z podanych fragmentów; nie dopisujesz dat, nazwisk ani ocen bez podstaw.")
GROUNDED_HINT = "Odpowiedz na podstawie fragmentów źródeł; nie wszystkie muszą dotyczyć pytania."


def in_holdout(group, fraction, seed):
    h = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(), 16)
    return (h % 10_000) / 10_000 < fraction


def render_exports(rows, fraction=0.1, distractors=2, seed=13):
    if not 0 < fraction < 1 or distractors < 0:
        raise ValueError('holdout must be between 0 and 1; distractors must be nonnegative')
    partition = lambda group: 'holdout' if in_holdout(group, fraction, seed) else 'train'
    pools = {part: [] for part in ('train', 'holdout')}
    for row in rows:
        part = partition(row['source_group_id'])
        pools[part].extend((row['source_group_id'], e['claim']) for e in row['evidence'])
    rng = random.Random(seed)
    outputs = {f'{variant}_{part}': [] for variant in ('closed_book', 'grounded')
               for part in ('train', 'holdout')}
    for row in rows:
        group = row['source_group_id']
        part = partition(group)
        meta = {key: row.get(key) for key in ('id', 'task_type', 'era', 'source_group_id', 'source_ids')}
        meta['audit'] = row['audit']
        closed = {'messages': [{'role': 'system', 'content': SYSTEM},
                               {'role': 'user', 'content': row['prompt']},
                               {'role': 'assistant', 'content': row['answer']}], **meta}
        others = [(g, claim) for g, claim in pools[part] if g != group]
        selected = [(group, e['claim']) for e in row['evidence']]
        selected += rng.sample(others, min(distractors, len(others)))
        rng.shuffle(selected)
        context = '\n'.join(f'[{i + 1}] {claim}' for i, (_, claim) in enumerate(selected))
        grounded = {'messages': [{'role': 'system', 'content': SYSTEM},
                                  {'role': 'user', 'content': f'{GROUNDED_HINT}\n\nFragmenty źródeł:\n{context}\n\nPytanie: {row["prompt"]}'},
                                  {'role': 'assistant', 'content': row['answer']}],
                    **meta, 'context_source_group_ids': [g for g, _ in selected]}
        if any(partition(g) != part for g in grounded['context_source_group_ids']):
            raise ValueError('Cross-partition context detected')
        outputs[f'closed_book_{part}'].append(closed)
        outputs[f'grounded_{part}'].append(grounded)
    return outputs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, default=BASE / 'train_strict.jsonl',
                    help='Reviewed strict artifact or exact subset; legacy verified labels are insufficient')
    ap.add_argument('--output-dir', type=Path, default=BASE / 'sft')
    ap.add_argument('--holdout', type=float, default=0.1)
    ap.add_argument('--distractors', type=int, default=2)
    ap.add_argument('--seed', type=int, default=13)
    args = ap.parse_args(argv)
    try:
        rows = eligible_input(args.input)
        outputs = render_exports(rows, args.holdout, args.distractors, args.seed)
        # Preflight every target before creating any output. Never overwrite prior evidence.
        targets = {key: args.output_dir / f'{key}.jsonl' for key in outputs}
        if any(path.exists() for path in targets.values()):
            raise ValueError('Export files already exist; select a fresh --output-dir')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for key, records in outputs.items():
            with targets[key].open('x', encoding='utf-8', newline='\n') as stream:
                for record in records:
                    stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(json.dumps({'strict_input': len(rows), **{key: len(value) for key, value in outputs.items()}}))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f'Export refused: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
