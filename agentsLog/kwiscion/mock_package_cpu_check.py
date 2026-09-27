"""CPU-only exact organizer-package plumbing; outputs are unmistakably synthetic."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def check(exam_dir, output):
    prep = load('mock_cpu_prepare', HERE/'final-package-prep/prepare_recovery_package.py')
    manifest = prep.prepare(SimpleNamespace(exam_dir=exam_dir, output=output, essay_id=['26'], no_essay=False,
                          cache='/cpu-placeholder/fresh/models', binary='/cpu-placeholder/runtime/bin/ollama',
                          lock='/cpu-placeholder/offline.lock', minutes=60, inject_faults=False))
    runner = load('mock_cpu_packed', output/'run_recovery_package.py')
    m, package, cases = runner.preflight(output)
    adapter = runner.modules(output)[3]
    original = adapter.load_package(exam_dir)
    rows = runner.n.rows(output/'input.original.jsonl')
    assert len(cases) == len(original['exam']['items']) == 37
    assert [x['id'] for x in rows] == [x['id'] for x in original['exam']['items']]
    assert m['max_calls'] == 148 and m['max_requested_tokens'] == 5455872
    for row, item, case in zip(rows, original['exam']['items'], cases):
        assert row['prompt'] == adapter.build_prompt(original['exam'], item)
        assert item['question'] in row['prompt']
        if item['source_text'].strip(): assert item['source_text'] in row['prompt']
        assert item['answer_format'] in row['prompt']
        text, images = runner.r.source(case)
        assert text.startswith(row['prompt'])
        assert len(images) == len(item['images'])
        for encoded, im in zip(images, item['images']):
            raw = base64.b64decode(encoded, validate=True)
            assert raw == (exam_dir/im['path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == im['sha256']

    class FakeProvider:
        def __init__(self): self.calls = 0; self.active = False
        def verify(self, context): assert context == 65536
        def quiesce(self, deadline): self.active = False; return True
        def send(self, body, timeout):
            assert not self.active; self.active = True
            case = cases[self.calls]
            text, images = runner.r.source(case)
            assert body['messages'][0]['content'] == text
            assert body['messages'][0].get('images', []) == images
            assert body['truncate'] is False and body['shift'] is False
            assert body['think'] is True and body['options']['num_ctx'] == 65536
            assert 'temperature' not in body['options']
            self.calls += 1
            answer = ('Temat 2.\n\n' + 'SYNTHETIC_FIXTURE_NOT_A_HISTORICAL_ANSWER ' * 400) if case['kind'] == 'essay' else 'SYNTHETIC_CPU_FIXTURE_NOT_A_HISTORICAL_ANSWER_' + case['id']
            return {'model': runner.r.MODEL, 'done': True, 'done_reason':'stop', 'prompt_eval_count':100,
                    'eval_count':450 if case['kind']=='essay' else 20, 'message':{'content':answer, 'thinking':'SYNTHETIC FIXTURE; no model reasoning'}}

    results = output/'results'; results.mkdir()
    provider = FakeProvider()
    runner.r.run(cases, package['template'], results/'engine', m['recovery'], provider, 3700, clock=lambda:100)
    assert provider.calls == 37
    runner.final_export(output, m, cases, package)
    final = runner.validate_final(results/'answers.json', package['template'])
    assert not adapter.validate_submission_bytes((results/'answers.json').read_bytes(), package['template'])
    assert final['exam_id'] == original['exam']['exam_id']
    assert [x['id'] for x in final['answers']] == [x['id'] for x in original['template']['answers']]
    for row in final['answers']: assert row['answer'].strip() and 'SYNTHETIC' in row['answer']
    essay = next(x['answer'] for x in final['answers'] if x['id']=='26')
    assert essay.startswith('Temat 2.\n\n') and runner.r.essay_body_words(essay)==400
    status = runner.n.read(results/'engine/answer-status.json')
    assert status['items']['26']['format_contract_satisfied'] and not status['items']['26']['warnings']
    summary = {'status':'CPU_SYNTHETIC_PROVIDER_PASS_NOT_INFERENCE', 'real_model_calls':0, 'synthetic_provider_replies':37,
               'package':original['summary'], 'input_files_sha256':{p.relative_to(exam_dir).as_posix():runner.n.sha(p) for p in adapter.package_inputs(original)},
               'prepared_manifest_sha256':runner.n.sha(output/'launch.json'), 'prepared_calls_ceiling':m['max_calls'],
               'prepared_tokens_ceiling':m['max_requested_tokens'], 'fake_answers_sha256':runner.n.sha(results/'answers.json'),
               'fake_answer_file_bytes':(results/'answers.json').stat().st_size, 'essay_body_words':400,
               'chosen_topic_number_preserved':True, 'all_original_prompts_and_29_image_references_verified':True,
               'runtime_files_sha256':{n:runner.n.sha(output/n) for n in ('recovery_harness.py','run_native_package.py','run_recovery_package.py')},
               'no_namespace_gpu_or_runtime_claim':True}
    runner.r.atomic(output/'cpu-check-summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exam-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();check(args.exam_dir.resolve(),args.output.resolve())
