#!/usr/bin/env python3
"""Reproduce frozen May 2024 runner input from the question PDF only.

No answer PDF, answer card, evaluator keys, model call, or training data is used.
Requires existing Poppler pdftotext/pdftoppm; generated artifacts stay private.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / 'agentsLog/Pewciu6/harness/build_validation_2024.py'
BUILDER_SHA256_LF = '7dd1f3368cd406a4bf34d1065b3957595b53b40f043cf07abf9d9e2bd3739531'
QUESTION_SHA256 = 'ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21'
INPUT_SHA256 = 'f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7'
QUESTION_URL = ('https://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2023/'
                'Arkusze_egzaminacyjne/2024/Historia/MHIP-R0-100-A-2405-arkusz.pdf')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def question_builder():
    if digest(BUILDER.read_text(encoding='utf-8').encode('utf-8')) != BUILDER_SHA256_LF:
        raise ValueError('Shared builder revision changed; review before rebuilding')
    spec = importlib.util.spec_from_file_location('validation_question_parser', BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Definitions only; never call its key-reading main().
    return module


def runner_bytes(text, builder):
    items = builder.parse_arkusz(text)
    # The essay is identified from points printed on the question sheet itself.
    essays = set()
    for line in text.splitlines():
        match = builder.SHEET_HDR.match(line)
        if match and match.group(3) and int(re.split('[–-]', match.group(3))[-1]) >= 10:
            essays.add(match.group(1) + ('.' + match.group(2) if match.group(2) else ''))
    rows = []
    for number in sorted(items, key=lambda value: tuple(map(int, value.split('.')))):
        sheet = items[number]
        image = builder.modality(sheet['text'])[0] == 'image' and number not in essays
        rows.append({'id': 'val2024-hist-z' + number,
                     'prompt': builder.PROMPT_HEADER + sheet['text'],
                     'images': ['pages/page-%02d.png' % page for page in sheet['pages']] if image else []})
    payload = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows).encode('utf-8')
    if len(rows) != 40 or sum(bool(row['images']) for row in rows) != 29 or len(essays) != 1:
        raise ValueError('Unexpected question extraction counts; no runner input written')
    if digest(payload) != INPUT_SHA256:
        raise ValueError('Frozen input hash mismatch (got %s); no runner input written' % digest(payload))
    return rows, payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question-pdf', type=Path, help='Reuse a local pinned question PDF instead of downloading')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'agentsLog/kwiscion/private/validation_2024_keyfree')
    parser.add_argument('--poppler-bin', type=Path, help='Directory containing existing pdftotext and pdftoppm')
    args = parser.parse_args(argv)
    out = args.output_dir.resolve()
    relative = out.relative_to(ROOT.resolve())
    if relative.parts[0] != 'agentsLog' or 'private' not in relative.parts:
        raise ValueError('Output must be under this repository agentsLog/<owner>/private/')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory is not empty; select a fresh directory')
    commands = {}
    for name in ('pdftotext', 'pdftoppm'):
        executable = shutil.which(name, path=str(args.poppler_bin) if args.poppler_bin else None)
        if not executable:
            raise ValueError('Missing existing Poppler tool: ' + name)
        commands[name] = executable
    builder = question_builder()
    if args.question_pdf:
        pdf_bytes = args.question_pdf.read_bytes()
    else:
        request = urllib.request.Request(QUESTION_URL, headers={'User-Agent': 'Mozilla/5.0 (matura-keyfree-bootstrap)'})
        with urllib.request.urlopen(request, timeout=60) as response:
            pdf_bytes = response.read(20_000_001)
    if digest(pdf_bytes) != QUESTION_SHA256:
        raise ValueError('Question PDF hash mismatch; refusing changed source')
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / 'MHIP-R0-100-A-2405-arkusz.pdf'
    pdf.write_bytes(pdf_bytes)
    text = subprocess.run([commands['pdftotext'], str(pdf), '-'], check=True,
                          stdout=subprocess.PIPE).stdout.decode('utf-8')
    rows, payload = runner_bytes(text, builder)
    pages = sorted({image for row in rows for image in row['images']})
    if len(pages) != 21:
        raise ValueError('Expected 21 referenced pages')
    (out / 'pages').mkdir()
    for image in pages:
        page = str(int(Path(image).stem.split('-')[1]))
        subprocess.run([commands['pdftoppm'], '-r', '110', '-png', '-f', page, '-l', page,
                        '-singlefile', str(pdf), str((out / image).with_suffix(''))], check=True)
        if not (out / image).is_file() or (out / image).stat().st_size == 0:
            raise ValueError('Missing or empty rendered page: ' + image)
    # Publish the local entry point only after every referenced image is available.
    (out / 'runner_input.jsonl').write_bytes(payload)
    report = {'input_sha256': digest(payload), 'question_sha256': digest(pdf_bytes),
              'builder_sha256_lf': BUILDER_SHA256_LF, 'items': len(rows),
              'image_items': 29, 'text_items': 11, 'rendered_pages': len(pages), 'dpi': 110,
              'question_url': QUESTION_URL, 'answer_key_access': False,
              'images': {image: digest((out / image).read_bytes()) for image in pages}}
    (out / 'bootstrap_verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'images'}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit('Bootstrap refused: ' + str(exc))
