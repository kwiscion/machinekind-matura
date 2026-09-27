"""CPU-only corrected-input Qwen40 preparation using the reviewed shared runner.

No execution, network, cache staging or authorization timestamps are added.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'agentsLog/kwiscion/private/may2024-source-crops-v1/package-v1'
EXAM_SHA = 'e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6'
TEMPLATE_SHA = 'aa4451a853063e3f67d1b9d281ac063ee48c112e01c3cb8712ded433253b865f'
PINS = {
    'recovery_harness.py': '628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0',
    'run_native_package.py': '60393fc61705efb8bdeaf8348ac6fd754bc8a4c0ad1efe142b7c6c39846cda6f',
    'run_recovery_package.py': '54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392',
    'closed_profile.py': '953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d',
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(output, runtime_root):
    assert sha(SOURCE/'exam.json') == EXAM_SHA
    assert sha(SOURCE/'answers-template.json') == TEMPLATE_SHA
    for name, digest in PINS.items():
        parent = HERE if name == 'closed_profile.py' else HERE.parent/'final-package-prep'
        assert sha(parent/name) == digest, 'Reviewed dependency changed: '+name
    output = output.resolve()
    assert not output.exists(), 'Fresh private output required'
    remote = PurePosixPath(runtime_root)
    assert remote.is_absolute() and '..' not in remote.parts
    host = remote.parent
    prep = load('qwen_full40_prepare', HERE.parent/'final-package-prep/prepare_recovery_package.py')
    args = SimpleNamespace(exam_dir=SOURCE, output=output, essay_id=['26'], no_essay=False,
                           cache=str(remote/'models'), binary=str(host/'runtime/bin/ollama'),
                           lock=str(host/'matched-worker.lock'), minutes=60, inject_faults=False)
    manifest = prep.prepare(args)
    shutil.copyfile(HERE/'closed_profile.py', output/'closed_profile.py')
    manifest.update(model_profile='qwen35_9b_thinking_v1', model='qwen3.5:9b',
                    temperature=1, top_p=0.95, top_k=64)
    manifest['files']['closed_profile.py'] = PINS['closed_profile.py']
    (output/'launch.json').write_bytes(prep.n.line(manifest).encode('utf8'))
    runner = load('qwen_full40_binding', output/'run_recovery_package.py')
    m, package, cases = runner.preflight(output)
    assert len(cases) == 40 and package['summary']['points'] == 60
    assert package['summary']['unique_image_files'] == 21 and package['summary']['image_references'] == 32
    assert m['max_calls'] == 160 and m['max_requested_tokens'] == 5898240 and not m['faults']
    assert m['essay_ids'] == ['26'] and not m['no_essay']
    assert m['status'] == 'PREPARED' and all(m[k] is None for k in ('declared_utc','deadline_utc','authorization'))
    original = json.loads((SOURCE/'exam.json').read_text(encoding='utf8'))
    assert package['exam'] == original
    assert (output/'exam/answers-template.json').read_bytes() == (SOURCE/'answers-template.json').read_bytes()
    checks = []
    for case, item in zip(cases, original['items']):
        assert case['id'] == item['id']
        assert case['kind'] == ('essay' if item['id'] == '26' else 'ordinary')
        text, images = runner.r.source(case)
        for field in ('question','source_text','answer_format'):
            assert item[field] in text
        assert original['instructions'] in text
        assert len(images) == len(item['images'])
        for encoded, ref in zip(images, item['images']):
            data = base64.b64decode(encoded, validate=True)
            assert data == (SOURCE/ref['path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == ref['sha256']
        payload, settings = runner.r.step(case, 0, [], m['recovery'])
        assert payload['model'] == 'qwen3.5:9b' and payload['think'] is True
        assert payload['truncate'] is False and payload['shift'] is False
        assert payload['options'] == {'num_ctx':65536,'num_predict':32768,'temperature':1,'top_p':0.95,'top_k':64}
        assert payload['messages'][0]['content'] == text
        assert payload['messages'][0].get('images',[]) == images
        checks.append({'id':case['id'],'kind':case['kind'],'image_references':len(images),
                       'initial_payload_sha256':runner.r.digest(payload),'initial_payload_profile':'PASS'})
    # Synthetic metadata only tests the configured ladder, not measured context fit.
    essay = next(x for x in cases if x['kind']=='essay')
    history = [{'raw':{'prompt_eval_count':100,'message':{'thinking':''}}}]
    retry_controls = []
    for attempt in (1,2,3):
        body, settings = runner.r.step(essay, attempt, history, m['recovery'])
        assert body['model']=='qwen3.5:9b'
        assert {k:body['options'][k] for k in ('temperature','top_p','top_k')} == {'temperature':1,'top_p':0.95,'top_k':64}
        assert body['think'] is (attempt==1)
        retry_controls.append({'attempt':attempt,'think':body['think'],'cap':settings['cap']})
    proof = {'status':'PREPARED_NOT_AUTHORIZED','model_calls':0,'remote_operations':0,
             'prepared_manifest_sha256':sha(output/'launch.json'),'exam_sha256':EXAM_SHA,
             'template_sha256':TEMPLATE_SHA,'items':40,'points':60,'unique_pngs':21,'image_references':32,
             'copied_file_pins':m['files'],'max_calls':160,'max_requested_output_tokens':5898240,
             'max_seconds':3600,'cost_ceiling_estimate_usd':3.28,'cache_expected_counted_bytes':6594475420,
             'native_digest':runner.ACTIVE_PROFILE.DIGEST,'single_container_weight_bytes':6594462816,
             'cache_status':'NOT_STAGED_OR_VERIFIED_BY_THIS_PREPARATION','faults':{},
             'complete_input_checks':checks,'synthetic_history_retry_controls':retry_controls,
             'context_note':'Initial controls verified on CPU; real prompt usage/loaded context remain runtime checks.',
             'profile_source_sha256':PINS['closed_profile.py'],'preparer_sha256':sha(Path(__file__))}
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime-root',required=True)
    args = parser.parse_args()
    proof = prepare(args.output,args.runtime_root)
    target = args.output.parent/'preparation-proof.json'
    assert not target.exists(), 'Preserve prior proof'
    target.write_bytes((json.dumps(proof,indent=2)+'\n').encode('utf8'))
    print(json.dumps({k:proof[k] for k in ('status','prepared_manifest_sha256','items','max_calls','max_requested_output_tokens')}))
