"""CPU-only frozen organizer-package preparation; never opens evaluation keys."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / 'agentsLog/kwiscion/private/organizer-control-20260926'
DEST = REPO / 'agentsLog/kwiscion/private/full-thinking-20260926/package'
ESSAY_POLICY = ('Wybierz dokładnie jeden z podanych tematów. Napisz wyłącznie gotowe '
                'wypracowanie na ten temat, 400–500 słów ciągłego tekstu. Uwzględnij wszystkie '
                'wymagane aspekty i materiały wybranego tematu. Bez planu, komentarzy o pisaniu, '
                'liczniku słów ani drugiego wypracowania. Pozostałych tematów nie opracowuj.')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m
def is_essay(question):
    q = re.sub(r'\s+', ' ', question).casefold()
    return ('wybierz jeden' in q and 'temat' in q and
            bool(re.search(r'minimum\s+300\s+(?:wyrazów|słów)', q)))
def main():
    assert not DEST.exists(), 'Fresh private destination required'
    assert sha(SOURCE/'package/exam.json') == '907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471'
    assert sha(SOURCE/'package/answers-template.json') == 'aa4451a853063e3f67d1b9d281ac063ee48c112e01c3cb8712ded433253b865f'
    DEST.mkdir(parents=True)
    shutil.copytree(SOURCE/'package', DEST/'exam')
    files = {
        'infer.py': 'infer.py',
        'scripts/Bukareszt/matura_package.py': 'scripts/Bukareszt/matura_package.py',
        'scripts/ljaniec/reasoning_lab.py': 'scripts/ljaniec/reasoning_lab.py',
        'runtime_guard.py': 'agentsLog/kwiscion/hetero-replication-run.py',
        'run_gemma_full_thinking.py': 'agentsLog/kwiscion/full-thinking-prep/run_gemma_full_thinking.py',
    }
    for dst, src in files.items():
        p=DEST/dst; p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(REPO/src,p)
    adapter=load('full_thinking_adapter_prepare',DEST/'scripts/Bukareszt/matura_package.py')
    package=adapter.load_package(DEST/'exam')
    adapter.prepare(package,DEST/'input.original.jsonl')
    original=[json.loads(x) for x in (DEST/'input.original.jsonl').read_text(encoding='utf8').splitlines()]
    prior_path=SOURCE/'prepared/input.jsonl'
    prior=[json.loads(x) for x in prior_path.read_text(encoding='utf8').splitlines()]
    assert len(prior)==len(original)==40
    for before,after in zip(prior,original):
        assert before['id']==after['id'] and before['prompt']==after['prompt']
        assert len(before['images'])==len(after['images'])
        for a,b in zip(before['images'],after['images']):
            assert (prior_path.parent/a).read_bytes()==(DEST/b).read_bytes()
    items=package['exam']['items']; assert len(original)==len(items)==40
    caps={}; essay_ids=[]
    modified=[]
    for row,item in zip(original,items):
        assert row['id']==item['id']
        fresh=dict(row)
        essay=is_essay(item['question']); caps[row['id']]=20480 if essay else 10240
        if essay:
            essay_ids.append(row['id']); fresh['prompt']+='\n\n'+ESSAY_POLICY
        assert fresh.get('images')==row.get('images')
        modified.append(fresh)
    assert len(essay_ids)==1 and sum(caps.values())==419840
    (DEST/'input.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in modified),encoding='utf8',newline='\n')
    manifest=dict(status='PREPARED_NOT_AUTHORIZED',deadline_utc=None,declared_utc=None,
        max_calls=40,max_requested_tokens=419840,max_wall_seconds=5400,timeout_seconds=600,
        model='gemma4:12b-it-q4_K_M',model_digest='4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c',
        runtime_version='0.34.4',context_length=32768,think=True,temperature='omitted',retries=0,
        base_url='http://127.0.0.1:11436',caps=caps,ids=[x['id'] for x in original],essay_ids=essay_ids,
        essay_policy=ESSAY_POLICY,essay_route='question contains choose-one-topic + minimum300 words; no ID/score routing',
        runtime_executable_sha256='ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4',
        host_root=None,server_pid=None,server_start_ticks=None,
        model_digests={'gemma4:12b-it-q4_K_M':'4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c','qwen3.5:9b':'6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7'},
        files={str(p.relative_to(DEST)).replace('\\','/'):sha(p) for p in DEST.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    (DEST/'launch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'items':40,'essay_ids':essay_ids,'input_sha256':sha(DEST/'input.jsonl'),'manifest_sha256':sha(DEST/'launch.json'),'images':package['summary']['image_references'],'status':manifest['status']}))
if __name__=='__main__': main()
