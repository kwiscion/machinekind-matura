"""Prepare a frozen known-validation reasoning subset without keys or HTTP.

The IDs identify this development panel; they are not a deployment router.
Input/output question text and image bytes remain in the owned private folder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "agentsLog/ljaniec/private"
SOURCE_SHA = "6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4"
PANEL_SHA = "393d4b70ec748a899605cfbc52f4cf3301fb288f0e59ec16401fd42df88063b2"
STRUCTURES = {
    "z1": "decision/source comparison", "z2": "decision/source comparison",
    "z7": "chronology/decision", "z10": "closed/graph", "z14.2": "closed/map",
    "z19.1": "PF/chronology/visual", "z20.1": "decision/text comparison",
    "z20.2": "PF/text", "z24": "decision/source comparison",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(source, output, include_readiness=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    source.relative_to(PRIVATE.resolve())
    output.relative_to(PRIVATE.resolve())
    if source.parent != output.parent:
        raise ValueError("Keep panel beside canonical input to preserve relative image paths")
    data = source.read_bytes()
    if digest(data) != SOURCE_SHA:
        raise ValueError("Question-only source-v2 input changed")
    rows, metadata, hashes = [], [], {}
    original = [json.loads(line) for line in data.decode().splitlines()]
    if len(original) != 40 or len({r['id'] for r in original}) != 40:
        raise ValueError("Require all 40 unique source-v2 IDs")
    for row in original:
        short = row['id'].removeprefix('val2024-hist-')
        if short not in STRUCTURES:
            continue
        if set(row) != {'id', 'prompt', 'images'}:
            raise ValueError("Require canonical question-only row")
        case = dict(row)
        case['families'] = [{'name': name} for name in ['baseline', 'thinking', 'critic']]
        if short in ['z19.1', 'z20.2']:
            task = row['prompt'].split('Zadanie ' + short.removeprefix('z') + '.')[-1]
            tail = task.split('prawdziwe, albo F – jeśli jest fałszywe.', 1)[1]
            statements = []
            for block in re.split(r'\nP\s*\n\s*F\s*(?:\n|$)', tail):
                text = re.sub(r'^0–1–2\s*', '', ' '.join(block.strip().split()))
                if text:
                    statements.append({'id': str(len(statements) + 1), 'text': text})
            if len(statements) != 3 or any(s['text'] not in ' '.join(row['prompt'].split()) for s in statements):
                raise ValueError("Reviewed PF statement layout changed")
            case['families'].append({'name': 'pf_statementwise', 'statements': statements})
        rows.append(case)
        images = []
        for path in row['images']:
            image = (source.parent / path).resolve()
            image.relative_to(source.parent)
            sha = digest(image.read_bytes())
            hashes[path] = sha
            images.append({'path': path, 'sha256': sha})
        metadata.append({'id': row['id'], 'structure': STRUCTURES[short],
                         'prompt_sha256': digest(row['prompt'].encode()), 'images': images,
                         'families': [f['name'] for f in case['families']]})
    payload = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode()
    if len(rows) != 9 or digest(payload) != PANEL_SHA:
        raise ValueError("Frozen panel construction changed")
    if include_readiness:
        image_bytes = (ROOT / 'agentsLog/ljaniec/fixtures/reasoning-digit7.png').read_bytes()
        image = source.parent / 'readiness-digit7.png'
        if image.exists():
            if image.read_bytes() != image_bytes:
                raise ValueError('Existing readiness image differs')
        else:
            with image.open('xb') as handle:
                handle.write(image_bytes)
        hashes[image.name] = digest(image_bytes)
        readiness = [
            {'id': 'ljaniec-ready-text-v1', 'prompt': 'Oblicz 2+3. Zwróć wyłącznie jedną cyfrę.',
             'images': [], 'families': [{'name': 'baseline'}], 'readiness': True,
             'readiness_expected_answer': '5'},
            {'id': 'ljaniec-ready-image-v1',
             'prompt': 'Odczytaj jedną cyfrę widoczną na obrazie. Zwróć tylko tę cyfrę, bez innych znaków.',
             'images': [image.name], 'families': [{'name': 'baseline'}], 'readiness': True,
             'readiness_expected_answer': '7'},
        ]
        rows = readiness + rows
        payload = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode()
    with output.open('xb') as handle:
        handle.write(payload)
    return {'source_v2_sha256': SOURCE_SHA, 'panel_sha256': digest(payload),
            'evaluation_panel_sha256': PANEL_SHA, 'items': metadata,
            'image_hashes': hashes, 'planned_calls_without_readiness': 42,
            'readiness_calls': 2 if include_readiness else 0,
            'planned_calls': 44 if include_readiness else 42,
            'planned_requested_tokens_at_2048': 90112 if include_readiness else 86016,
            'http_requests': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-readiness', action='store_true',
                        help='Prepend two original text/image qualification calls inside the same wave')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, args.include_readiness), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
