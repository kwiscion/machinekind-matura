"""Prepare a full40 Qwen confirmation with only the generic essay coverage suffix."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
EXAM_SHA = 'e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6'
PINS = {
    'prepare_recovery_package.py': '0ba54f2301ff5afde296df154f5f963900b6d956e825e247af6348f3362005af',
    'prepare_native_package.py': '94c5cec3fd8d166543374c499c6fa60ca9ecbad41a6ff21bf03dd0e6a3979ad3',
    'recovery_harness.py': '628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0',
    'run_native_package.py': '60393fc61705efb8bdeaf8348ac6fd754bc8a4c0ad1efe142b7c6c39846cda6f',
    'run_recovery_package.py': '54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392',
    'closed_profile.py': '953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d',
}
COVERAGE_SHA = '298d383edcd03cf1cc0a4b6ffaa1d97941b60c0e48090667b7861418ae836bae'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_exam(exam, item_id, suffix):
    """Preserve all original items/IDs; append only the approved essay policy."""
    derived = copy.deepcopy(exam)
    assert len(derived['items']) == 40 and derived['max_points'] == 60
    selected = [x for x in derived['items'] if x['id'] == item_id]
    assert len(selected) == 1
    selected[0]['question'] += suffix
    template = {'exam_id': derived['exam_id'], 'answers': [{'id': x['id'], 'answer': ''} for x in derived['items']]}
    return derived, template, [{'id': x['id'], 'source_item_id': x['id'], 'coverage': x['id'] == item_id} for x in derived['items']]


def prepare(reference, output, runtime_root):
    reference, output = reference.resolve(), output.resolve()
    assert not output.exists(), 'Fresh output required; previous attempts are immutable'
    assert sha(reference/'exam/exam.json') == EXAM_SHA
    assert sha(HERE/'coverage_suffix.py') == COVERAGE_SHA
    for name, digest in PINS.items():
        assert sha(reference/name) == digest, 'Changed reviewed dependency: '+name
    policy = load('coverage_policy', HERE/'coverage_suffix.py')
    source = json.loads((reference/'exam/exam.json').read_text(encoding='utf8'))
    exam, template, mappings = derive_exam(source, '26', policy.SUFFIX)
    output.mkdir(parents=True)
    inputs = output/'source-private'
    inputs.mkdir()
    for name, value in [('exam.json', exam), ('answers-template.json', template)]:
        (inputs/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')
    shutil.copyfile(reference/'exam/answers-template.json', inputs/'answers-template.json')
    for item in exam['items']:
        for image in item.get('images', []):
            rel = Path(image['path'])
            assert not rel.is_absolute() and '..' not in rel.parts
            dest = inputs/rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copyfile(reference/'exam'/rel, dest)
            assert sha(dest) == image['sha256']
    remote = PurePosixPath(runtime_root)
    assert remote.is_absolute() and '..' not in remote.parts
    # The preparer intentionally resolves repository-private output from its
    # canonical location. Verify the live copy matches the reviewed archive
    # before using it; imported archived paths would derive the wrong REPO.
    public_runtime = HERE.parent/'final-package-prep'
    for name, digest in PINS.items():
        if name != 'closed_profile.py':
            assert sha(public_runtime/name) == digest, 'Changed canonical preparer closure: '+name
    shared = load('frozen_coverage_prepare', public_runtime/'prepare_recovery_package.py')
    for name, source_path in shared.p.SOURCES.items():
        assert sha(shared.p.REPO/source_path) == sha(reference/name), 'Changed archive/runtime dependency: '+name
    package = output/'package-v1'
    ids = ['26']
    args = SimpleNamespace(exam_dir=inputs, output=package, essay_id=ids, no_essay=False,
                           cache=str(remote/'models'), binary=str(remote.parent/'runtime/bin/ollama'),
                           lock=str(remote.parent/'matched-worker.lock'), minutes=60, inject_faults=False)
    manifest = shared.prepare(args)
    shutil.copyfile(reference/'closed_profile.py', package/'closed_profile.py')
    manifest.update(model_profile='qwen35_9b_thinking_v1', model='qwen3.5:9b', temperature=1, top_p=.95, top_k=64)
    manifest['files']['closed_profile.py'] = PINS['closed_profile.py']
    (package/'launch.json').write_text(shared.n.line(manifest), encoding='utf8', newline='\n')
    runner = load('coverage_qwen_binding', package/'run_recovery_package.py')
    m, prepared, cases = runner.preflight(package)
    assert len(cases) == 40 and m['max_calls'] == 160 and m['max_requested_tokens'] == 5898240
    assert m['essay_ids'] == ids and not m['faults']
    assert m['status'] == 'PREPARED' and all(m[k] is None for k in ('declared_utc','deadline_utc','authorization'))
    originals = {x['id']: x for x in source['items']}
    checks = []
    for case, derived in zip(cases, exam['items']):
        original = originals[case['id']]
        assert case['kind'] == ('essay' if case['id'] == '26' else 'ordinary')
        assert derived['question'] == original['question'] + (policy.SUFFIX if case['id'] == '26' else '')
        assert {k:v for k,v in derived.items() if k not in ('id','question')} == {k:v for k,v in original.items() if k not in ('id','question')}
        text, images = runner.r.source(case)
        for field in ('question','source_text','answer_format'):
            assert original[field] in text
        assert source['instructions'] in text
        payload, settings = runner.r.step(case, 0, [], m['recovery'])
        assert payload['model']=='qwen3.5:9b' and payload['think'] is True
        assert payload['truncate'] is False and payload['shift'] is False
        assert payload['options']=={'num_ctx':65536,'num_predict':32768,'temperature':1,'top_p':.95,'top_k':64}
        assert payload['messages'][0]['content'] == text
        checks.append({'id':case['id'],'source_preserved':True,'initial_payload_sha256':runner.r.digest(payload)})
    proof = {'status':'PREPARED_NOT_AUTHORIZED','source_exam_sha256':EXAM_SHA,
             'source_item_id':'26','model_calls':0,'remote_operations':0,
             'prepared_manifest_sha256':sha(package/'launch.json'),'derived_exam_sha256':sha(inputs/'exam.json'),
             'coverage_module_sha256':COVERAGE_SHA,'coverage_suffix_sha256':policy.SUFFIX_SHA256,
             'builder_sha256':sha(Path(__file__)),'copied_file_pins':m['files'], 'mappings':mappings,
             'checks':checks,'max_calls':160,'max_requested_output_tokens':5898240,'max_seconds':3600,
             'cost_ceiling_estimate_usd':3.28,'cache_counted_bytes':6594475420,
             'cache_status':'FRESH_STAGE_REQUIRED; prior served cache has runtime sidecars',
             'scope':'Full40/60 confirmation: unchanged direct nonessay; one autonomous essay with generic coverage suffix. No posthoc composition.',
             'no_selector':True,'no_fault_injection':True}
    (output/'preparation-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8',newline='\n')
    return proof


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime-root',required=True)
    args=parser.parse_args()
    proof=prepare(args.reference,args.output,args.runtime_root)
    print(json.dumps({k:proof[k] for k in ('status','prepared_manifest_sha256','max_calls','max_requested_output_tokens')}))
