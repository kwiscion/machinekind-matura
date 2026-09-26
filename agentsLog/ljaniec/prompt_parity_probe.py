#!/usr/bin/env python3
"""CPU-only original-fixture renderer/payload audit. No network or model calls."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import infer


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Definitions only; never key-reading builder main.
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Capture:
    def __init__(self):
        self.payloads = []

    def open(self, request, timeout):
        self.payloads.append(json.loads(request.data))
        return io.BytesIO(b'{"choices":[{"message":{"content":"fixture"},"finish_reason":"stop"}]}')


def main():
    adapter = load('parity_adapter', 'scripts/Bukareszt/matura_package.py')
    builder = load('parity_question_builder', 'agentsLog/Pewciu6/harness/build_validation_2024.py')
    text = ('Zadanie 1.\nSOURCE_SHARED mapa fixture\n'
            'Zadanie 1.1. (0–1)\nQUESTION_A\n'
            'Zadanie 1.2. (0–1)\nQUESTION_B\fCONTINUATION_B\n'
            'Zadanie 2. (0–1)\nQUESTION_C\n'
            'Zadanie 3. (0–15)\nESSAY_REQUIREMENT_A\nESSAY_REQUIREMENT_B\n')
    parsed = builder.parse_arkusz(text)
    expected = ['1.1', '1.2', '2', '3']
    assert sorted(parsed, key=lambda n: tuple(map(int, n.split('.')))) == expected
    assert all('SOURCE_SHARED' in parsed[n]['text'] for n in expected[:2])
    assert 'QUESTION_B' not in parsed['1.1']['text']
    assert 'QUESTION_A' not in parsed['1.2']['text']
    assert parsed['1.2']['pages'] == [1, 2]
    capture = Capture()
    old_opener, old_socket = infer.OPENER, socket.socket

    def forbidden(*args, **kwargs):
        raise AssertionError('Network socket creation forbidden in parity probe')

    try:
        infer.OPENER, socket.socket = capture, forbidden
        with tempfile.TemporaryDirectory(prefix='ljaniec-parity-') as tmp:
            folder = Path(tmp)
            (folder / 'images').mkdir()
            fixtures = ROOT / 'agentsLog/Bukareszt/submission/fixtures/tiny-package/images'
            for number, name in [(1, 'fixture-red.png'), (2, 'fixture-blue.png')]:
                shutil.copyfile(fixtures / name, folder / f'images/page-{number:02d}.png')
            items, bare = [], []
            for number in expected:
                sheet = parsed[number]
                image_pages = sheet['pages'] if number.startswith('1.') else []
                images = [{'path': f'images/page-{page:02d}.png',
                           'sha256': sha((folder / f'images/page-{page:02d}.png').read_bytes()),
                           'source_page': page} for page in image_pages]
                # Identical task/source text supplied as one question field isolates wrapping.
                items.append({'id': number, 'group': number.split('.')[0],
                              'max_points': 15 if number == '3' else 1,
                              'question': sheet['text'], 'source_text': '',
                              'images': images, 'answer_format': 'SYNTHETIC_FORMAT'})
                bare.append({'id': number, 'prompt': builder.PROMPT_HEADER + sheet['text'],
                             'images': [im['path'] for im in images]})
            exam = {'exam_id': 'ljaniec-original-parity-fixture',
                    'instructions': 'SYNTHETIC_EXAM_INSTRUCTION', 'items': items}
            (folder / 'exam.json').write_text(json.dumps(exam))
            (folder / 'answers-template.json').write_text(json.dumps({
                'exam_id': exam['exam_id'], 'answers': [{'id': n, 'answer': ''} for n in expected]}))
            package = adapter.load_package(folder)
            adapter.prepare(package, folder / 'organizer.jsonl')
            (folder / 'bare.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in bare))
            config_path = ROOT / 'agentsLog/kwiscion/gemma4-12b-val40-1024.config.json'
            config = infer.load_config(config_path, False)
            rows = []
            for mode in ['bare', 'organizer']:
                for case in infer.load_cases(folder / f'{mode}.jsonl', 4):
                    result = infer.run_case(case, config)
                    assert result['error'] is None
            for index, number in enumerate(expected):
                before, after = capture.payloads[index], capture.payloads[index + 4]
                b, a = before['messages'][0]['content'], after['messages'][0]['content']
                bt = b if isinstance(b, str) else b[0]['text']
                at = a if isinstance(a, str) else a[0]['text']
                bi = [] if isinstance(b, str) else [v['image_url']['url'] for v in b[1:]]
                ai = [] if isinstance(a, str) else [v['image_url']['url'] for v in a[1:]]
                assert bt != at and bi == ai
                assert parsed[number]['text'] in bt and parsed[number]['text'] in at
                assert {k: v for k, v in before.items() if k != 'messages'} == {
                    k: v for k, v in after.items() if k != 'messages'}
                assert [v['role'] for v in before['messages']] == ['user']
                assert [v['role'] for v in after['messages']] == ['user']
                rows.append({'fixture_id': number, 'bare_text_sha256': sha(bt.encode()),
                             'organizer_text_sha256': sha(at.encode()), 'prompt_equal': False,
                             'source_text_preserved': True, 'image_bytes_and_order_equal': True,
                             'image_count': len(ai), 'settings_equal': True})
            result = {'scope': 'Original synthetic parser/renderer fixtures; no accuracy evidence',
                      'model_calls': 0, 'network_calls': 0, 'captured_stub_requests': len(capture.payloads),
                      'shared_source_repeated': True, 'neighbor_text_excluded': True,
                      'source_and_subtask_pages_ascending': True, 'single_user_message': True,
                      'thinking': config['reasoning_effort'], 'output_cap': config['max_output_tokens'],
                      'temperature_omitted': 'temperature' not in capture.payloads[0], 'fixtures': rows,
                      'config_sha256_lf': sha(config_path.read_bytes()),
                      'config_sha256_crlf': sha(config_path.read_bytes().replace(b'\n', b'\r\n')),
                      'code_sha256': {str(p): sha((ROOT / p).read_bytes()) for p in [
                          Path('infer.py'), Path('scripts/Bukareszt/matura_package.py'),
                          Path('agentsLog/Pewciu6/harness/build_validation_2024.py'),
                          Path('agentsLog/kwiscion/run_gemma_package.py')]}}
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        infer.OPENER, socket.socket = old_opener, old_socket


if __name__ == '__main__':
    main()
