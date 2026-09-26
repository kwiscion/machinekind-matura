#!/usr/bin/env python3
"""Explicit source-only v2 repair of the pinned key-free validation input.

No downloads, key access, model calls, or mutation of the v1 input. Outputs must
be fresh siblings of the input so existing relative page paths keep resolving.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

V1_SHA256 = 'f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7'
ITEM_ID = 'val2024-hist-z13'
ASSET = 'pages/page-16.png'
ROOT = Path(__file__).resolve().parents[3]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_png(data):
    """Check PNG structure/CRCs without decoding or modifying the image."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Required asset is not a PNG')
    offset, chunks, dimensions = 8, [], None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('Truncated PNG data')
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', data[offset + 8 + length:end])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        if not chunks:
            if kind != b'IHDR' or length != 13:
                raise ValueError('Invalid PNG header')
            dimensions = struct.unpack('>II', payload[:8])
            if min(dimensions) <= 0:
                raise ValueError('Invalid PNG dimensions')
        chunks.append(kind)
        offset = end
        if kind == b'IEND':
            if length or offset != len(data):
                raise ValueError('Invalid PNG end')
            break
    if not chunks or chunks[-1] != b'IEND' or b'IDAT' not in chunks:
        raise ValueError('Incomplete PNG')
    return dimensions


def repair(input_path, output_path=None, affected_path=None, manifest_path=None):
    source = Path(input_path).resolve()
    output = Path(output_path).resolve() if output_path else source.with_name('runner_input.v2.jsonl')
    affected = Path(affected_path).resolve() if affected_path else source.with_name('runner_input.v2-affected.jsonl')
    manifest = Path(manifest_path).resolve() if manifest_path else source.with_name('source-repair-v2.json')
    destinations = [output, affected, manifest]
    try:
        relative = source.relative_to(ROOT)
    except ValueError:
        raise ValueError('Input must stay under this repository agentsLog/<owner>/private/') from None
    if len(relative.parts) < 4 or relative.parts[0] != 'agentsLog' or relative.parts[2] != 'private':
        raise ValueError('Input must stay under this repository agentsLog/<owner>/private/')
    if len(set([source, *destinations])) != 4:
        raise ValueError('Input and output paths must be distinct')
    if any(p.parent != source.parent for p in destinations):
        raise ValueError('Outputs must be siblings of input to preserve image paths')
    if any(p.exists() for p in destinations):
        raise ValueError('Refusing to overwrite an existing output')
    original = source.read_bytes()
    if digest(original) != V1_SHA256:
        raise ValueError('Input is not the exact frozen v1 hash')
    asset_path = source.parent / ASSET
    asset_bytes = asset_path.read_bytes()
    width, height = validate_png(asset_bytes)
    bootstrap_path = source.parent / 'bootstrap_verification.json'
    bootstrap_bytes = bootstrap_path.read_bytes()
    bootstrap = json.loads(bootstrap_bytes)
    if bootstrap.get('input_sha256') != V1_SHA256:
        raise ValueError('Local bootstrap manifest does not match frozen v1 input')
    expected_asset_hash = bootstrap.get('images', {}).get(ASSET)
    if expected_asset_hash != digest(asset_bytes):
        raise ValueError('Required asset does not match local bootstrap image manifest')
    lines = original.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    if len(rows) != 40 or len({row['id'] for row in rows}) != 40:
        raise ValueError('Expected 40 unique input rows')
    matches = [i for i, row in enumerate(rows) if row['id'] == ITEM_ID]
    if len(matches) != 1:
        raise ValueError('Expected exactly one affected item')
    index = matches[0]
    old = rows[index]
    if old.get('images') != []:
        raise ValueError('Affected v1 row must have an empty images array')
    new = dict(old, images=[ASSET])
    if 'modality' in new:
        new['modality'] = 'image'
    replacement = (json.dumps(new, ensure_ascii=False) + '\n').encode('utf-8')
    new_lines = list(lines)
    new_lines[index] = replacement
    payload = b''.join(new_lines)
    final_rows = [json.loads(line) for line in payload.splitlines()]
    if sum(bool(row['images']) for row in final_rows) != 30:
        raise ValueError('Expected 30 image-labelled rows in v2')
    if any(not (source.parent / image).is_file() for row in final_rows for image in row['images']):
        raise ValueError('A referenced image is missing')
    changed_fields = [key for key in new if new[key] != old.get(key)]
    report = {
        'repair': 'source-completeness-v2', 'input_file': source.name,
        'output_file': output.name, 'affected_only_file': affected.name,
        'v1_sha256': digest(original), 'v2_sha256': digest(payload),
        'affected_only_sha256': digest(replacement), 'items': 40,
        'image_items': 30, 'text_items': 10,
        'unique_pages': len({image for row in final_rows for image in row['images']}),
        'delta': [{'id': ITEM_ID, 'fields': {key: {'before': old.get(key), 'after': new[key]} for key in changed_fields}}],
        'unchanged_other_rows_byte_identical': all(lines[i] == new_lines[i] for i in range(40) if i != index),
        'all_prompt_strings_unchanged': all(a['prompt'] == b['prompt'] for a, b in zip(rows, final_rows)),
        'asset': {'path': ASSET, 'sha256': digest(asset_bytes), 'width': width, 'height': height},
        'bootstrap_manifest': {'path': bootstrap_path.name, 'sha256': digest(bootstrap_bytes),
                               'asset_hash_verified': True},
        'answer_key_access': False, 'model_calls': 0,
    }
    # Exclusive creation also protects against an output appearing after checks.
    # If a later write fails, preserve partial outputs as failed-attempt evidence.
    for path, data in [(output, payload), (affected, replacement),
                       (manifest, (json.dumps(report, indent=2) + '\n').encode('utf-8'))]:
        with path.open('xb') as stream:
            stream.write(data)
    if source.read_bytes() != original:
        raise ValueError('Input changed concurrently; preserve outputs and investigate')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Exact frozen v1 runner_input.jsonl')
    parser.add_argument('--output', type=Path, help='Fresh sibling v2 JSONL')
    parser.add_argument('--affected-output', type=Path, help='Fresh sibling one-item JSONL')
    parser.add_argument('--manifest', type=Path, help='Fresh sibling repair manifest')
    args = parser.parse_args()
    report = repair(args.input, args.output, args.affected_output, args.manifest)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        sys.exit('Repair refused: ' + str(exc))
