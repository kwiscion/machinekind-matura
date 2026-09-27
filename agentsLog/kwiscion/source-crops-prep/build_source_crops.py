"""Lossless source-region extraction; no model, PDF rewriting or network calls.

Source packages and output must remain private. The spec and manifest contain
only IDs, coordinates, hashes and QA notes and may be published separately.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def build(source, output, spec_path):
    source, output = source.resolve(), output.resolve()
    private = (REPO / 'agentsLog/kwiscion/private').resolve()
    assert output.is_relative_to(private) and not output.exists(), 'Fresh private output required'
    assert not output.is_relative_to(source), 'Separate output required'
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    assert sha(source / 'exam.json') == spec['source_exam_sha256']
    assert sha(source / 'answers-template.json') == spec['source_template_sha256']
    original = json.loads((source / 'exam.json').read_text(encoding='utf-8'))
    exam = copy.deepcopy(original)
    ids = [x['id'] for x in original['items']]
    assert len(ids) == len(set(ids)) == spec['item_count']
    assert sum(x['max_points'] for x in original['items']) == spec['points']
    before = {p: sha(p) for p in [source / 'exam.json', source / 'answers-template.json']}
    crops, mapped = [], {k: [] for k in ids}
    output.mkdir(parents=True)
    (output / 'images').mkdir()
    for row in spec['crops']:
        parent = source / row['parent_path']
        assert parent.resolve().is_relative_to(source)
        assert sha(parent) == row['parent_sha256']
        before[parent] = row['parent_sha256']
        assert set(row['item_ids']) <= set(ids)
        im = Image.open(parent)
        x0, y0, x1, y1 = row['bbox']
        assert all(type(v) is int for v in row['bbox'])
        assert 0 <= x0 < x1 <= im.width and 0 <= y0 < y1 <= im.height
        crop = im.crop(tuple(row['bbox']))
        target = output / 'images' / (row['id'] + '.png')
        assert not target.exists(), 'Duplicate crop ID'
        crop.save(target, format='PNG', optimize=False, compress_level=9)
        restored = Image.open(target)
        assert restored.mode == im.mode and restored.size == (x1-x0, y1-y0)
        assert restored.tobytes() == im.crop(tuple(row['bbox'])).tobytes(), 'Pixel change'
        rel = target.relative_to(output).as_posix()
        image_ref = {'path': rel, 'source_page': row['source_page'], 'sha256': sha(target)}
        for item_id in row['item_ids']:
            mapped[item_id].append(image_ref.copy())
        crops.append({**row, 'crop_path': rel, 'crop_sha256': sha(target),
                      'crop_size': list(crop.size), 'parent_size': list(im.size),
                      'pixel_exact_check': 'PASS'})
    changes = []
    for old, new in zip(original['items'], exam['items']):
        new['images'] = mapped[new['id']]
        assert {k:v for k,v in old.items() if k != 'images'} == {k:v for k,v in new.items() if k != 'images'}
        assert bool(old['images']) == bool(new['images']), 'Unexpected image-bearing item change'
        changes.append({'id': old['id'], 'old_images': old['images'], 'new_images': new['images']})
    assert {k:v for k,v in original.items() if k != 'items'} == {k:v for k,v in exam.items() if k != 'items'}
    write(output / 'exam.json', exam)
    shutil.copyfile(source / 'answers-template.json', output / 'answers-template.json')
    assert sha(output / 'answers-template.json') == spec['source_template_sha256']
    adapter_path = REPO / 'scripts/Bukareszt/matura_package.py'
    module_spec = importlib.util.spec_from_file_location('crop_package_adapter', adapter_path)
    adapter = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(adapter)
    package = adapter.load_package(output)
    adapter.prepare(package, output / 'runner_input.jsonl')
    # Prompt changes must be confined to the automatically generated image list.
    for old, new in zip(original['items'], exam['items']):
        old_copy, new_copy = copy.deepcopy(old), copy.deepcopy(new)
        old_copy['images'], new_copy['images'] = [], []
        assert adapter.build_prompt(original, old_copy) == adapter.build_prompt(exam, new_copy)
    assert all(sha(p) == digest for p,digest in before.items()), 'Source mutated'
    manifest = {'schema': 'may2024_source_crops_v1', 'status': 'CPU_BUILT_VISUAL_QA_PENDING',
                'source_exam_sha256': spec['source_exam_sha256'],
                'source_template_sha256': spec['source_template_sha256'],
                'crop_spec_sha256': sha(spec_path), 'builder_sha256': sha(Path(__file__)),
                'adapter_sha256': sha(adapter_path), 'summary': package['summary'],
                'non_image_fields_exact': True, 'template_bytes_exact': True,
                'adapter_prompt_except_image_list_exact': True, 'original_files_unchanged': True,
                'crops': crops, 'item_image_mapping': changes, 'model_calls': 0,
                'rights': 'Private evaluation only; crops inherit source rights. No redistribution grant.'}
    write(output / 'crop-manifest.json', manifest)
    # Contact sheets are private QA derivatives only, never model inputs.
    for offset in range(0, len(crops), 6):
        group = crops[offset:offset+6]
        sheet = Image.new('RGB', (1500, 1500), '#dddddd')
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(group):
            im = Image.open(output / row['crop_path']).convert('RGB')
            im.thumbnail((740, 458))
            x, y = (i % 2) * 750, (i // 2) * 500
            draw.text((x+5,y+5), row['id']+' / page '+str(row['source_page'])+' / '+','.join(row['item_ids']), fill='black')
            sheet.paste(im, (x+5, y+28))
        sheet.save(output / f'qa-contact-{offset//6+1:02d}.png')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--spec', type=Path, default=HERE / 'crop-spec-v1.json')
    args = parser.parse_args()
    result = build(args.source, args.output, args.spec)
    print(json.dumps({'status': result['status'], 'summary': result['summary']}, ensure_ascii=False))
