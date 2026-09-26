"""Prepared fallback for #38: two synthetic tasks, server and runner in one netns.

Nothing starts without --execute. Companion tests use mocked transport, not a model.
"""
import argparse
import datetime as dt
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OWN = ROOT / 'agentsLog/kwiscion'
CACHE = Path('/usr/share/ollama/.ollama/models')
MODEL = 'gemma4:12b-it-q4_K_M'
DIGEST = '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
ASSETS = {
    '1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606': 7381382048,
    '675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842': 175115584,
}
PORT = 11435
ENDPOINT = f'http://127.0.0.1:{PORT}'
SELF = Path(__file__).resolve()
IDS = ['offline-text', 'offline-image']

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def modules():
    return load('offline_infer', ROOT/'infer.py'), load('offline_adapter', ROOT/'scripts/Bukareszt/matura_package.py')

def output_path(value):
    root = (OWN/'private').resolve()
    p = Path(value).resolve()
    require(p.is_relative_to(root) and p != root, 'Output must be inside this owner ignored private directory')
    require(not p.exists(), 'Fresh output directory required; no resume or overwrite')
    return p

def fixture(out, adapter):
    # Reuse an explicitly invented image from the accepted adapter fixtures.
    fixture_image = ROOT/'agentsLog/Bukareszt/submission/fixtures/tiny-package/images/fixture-red.png'
    require(sha(fixture_image) == 'b4467f0dd939cb7b8af870bf39e79c2433610e765485791c8524ca7a245577b8', 'Synthetic fixture changed')
    pkg = out/'package'
    (pkg/'images').mkdir(parents=True)
    (pkg/'images/fixture.png').write_bytes(fixture_image.read_bytes())
    exam = {'exam_id':'kwiscion-offline-synthetic-v1','title':'Synthetic offline transport rehearsal',
        'language':'pl','input_format':'separate-text-and-images-v1','max_points':2,
        'instructions':'To test techniczny na wymyślonych zadaniach. Odpowiedz krótko po polsku.',
        'items':[
            {'id':IDS[0],'group':1,'max_points':1,'question':'Przepisz słowo: gotowe.',
             'source_text':'','images':[],'answer_format':'Jedno słowo.'},
            {'id':IDS[1],'group':2,'max_points':1,'question':'Podaj dominujący kolor kwadratu na obrazie.',
             'source_text':'Wymyślony obraz testowy.','images':[{'path':'images/fixture.png','source_page':1,'sha256':sha(fixture_image)}],
             'answer_format':'Jedno słowo.'}]}
    write(pkg/'exam.json', exam)
    write(pkg/'answers-template.json', {'exam_id':exam['exam_id'],'answers':[{'id':i,'answer':''} for i in IDS]})
    package = adapter.load_package(pkg)
    adapter.prepare(package, out/'input.jsonl')
    config = {'name':'offline-namespace-gemma-two-synthetic','base_url':ENDPOINT+'/v1','model':MODEL,
        'model_revision':DIGEST,'reasoning_effort':'none','max_output_tokens':1024,'timeout_seconds':420}
    write(out/'config.json',config)
    return package

def api(path, port=PORT):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f'http://127.0.0.1:{port}/api/{path}', timeout=3) as response:
        return json.load(response)

def process_snapshot(own_group=None):
    blockers=[]
    names=('infer.py','run_question_policy.py','run_bounded_gemma.py','run_visual_crops.py',
           'run_crop_diagnostic.py','run_source_correction.py','run_local_smoke.py','run_smoke.py')
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():
            continue
        try:
            args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
            exe=Path(args[0]).name if args else ''
            known_backend=exe in ('llama-server','ollama_llama_server') or 'vllm' in exe
            known_runner=exe.startswith('python') and any(Path(a).name in names or Path(a).name.startswith(('run_gemma','run_qwen','run_rag')) for a in args[1:])
            if (known_backend or known_runner) and (own_group is None or os.getpgid(int(p.name))!=own_group):
                blockers.append({'pid':int(p.name),'kind':'model backend' if known_backend else 'inference runner'})
        except (FileNotFoundError, ProcessLookupError):
            pass
    smi=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
    for line in smi.stdout.splitlines():
        require(line.strip().isdigit(), 'Unrecognized GPU process listing; cannot prove exclusive ownership')
        pid=int(line.strip())
        try:
            if own_group is None or os.getpgid(pid)!=own_group:
                blockers.append({'pid':pid,'kind':'GPU compute process'})
        except ProcessLookupError:
            pass
    require(not blockers, 'Competing/resident model worker(s): '+json.dumps(blockers))

def verify_assets():
    manifest=CACHE/'manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M'
    require(sha(manifest)==DIGEST,'Installed model manifest digest mismatch')
    layers=json.loads(manifest.read_text())['layers']
    for digest,size in ASSETS.items():
        require(any(x['digest']=='sha256:'+digest and x['size']==size for x in layers),'Manifest asset mismatch')
        p=CACHE/'blobs'/('sha256-'+digest)
        require(p.stat().st_size==size and sha(p)==digest,'Model/projector bytes mismatch')
    require(sum(ASSETS.values())<=8000000000,'Weight limit exceeded')

def network_proof(host_net):
    net=os.readlink('/proc/self/ns/net')
    require(net!=host_net,'Runner is still in the host network namespace')
    subprocess.run(['ip','link','set','lo','up'],check=True)
    links=json.loads(subprocess.check_output(['ip','-j','link'],text=True))
    require([x['ifname'] for x in links]==['lo'],'Non-loopback interface exists')
    for family in ('-4','-6'):
        routes=json.loads(subprocess.check_output(['ip',family,'-j','route','show','table','main'],text=True))
        require(not routes,'External route exists')
    failures=[]
    for family,addr in [(socket.AF_INET,('1.1.1.1',443)),(socket.AF_INET6,('2001:4860:4860::8888',443,0,0))]:
        with socket.socket(family,socket.SOCK_STREAM) as s:
            s.settimeout(2)
            try:
                s.connect(addr)
            except OSError as e:
                require(e.errno in (errno.ENETUNREACH,errno.EHOSTUNREACH,errno.EADDRNOTAVAIL),'Unexpected external probe failure')
                failures.append({'family':family.name,'errno':e.errno})
            else:
                raise RuntimeError('External connection unexpectedly succeeded')
    return {'host_namespace':host_net,'isolated_namespace':net,'interfaces':['lo'],'external_connect_failures':failures}

def verify_model(resident=False):
    tags=api('tags')['models']
    require(any(m.get('name')==MODEL and m.get('digest')==DIGEST for m in tags),'Namespace model tag mismatch')
    if resident:
        models=api('ps')['models']
        require(len(models)==1 and models[0].get('digest')==DIGEST and models[0].get('context_length')==4096,'Resident digest/context mismatch')

def inside(args):
    out=Path(args.output).resolve()
    require((out/'launch.json').is_file(),'Missing parent launch record')
    proof=network_proof(args.host_net)
    write(out/'network-proof.json',proof)
    inf,adapter=modules()
    package=fixture(out,adapter)
    cases=inf.load_cases(out/'input.jsonl',2)
    require([x['id'] for x in cases]==IDS,'Exactly two synthetic tasks required')
    config=inf.load_config(out/'config.json',False)
    inf.OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),inf.NoRedirect)
    process_snapshot()
    home=out/'server-home'
    home.mkdir()
    env={'PATH':'/usr/local/bin:/usr/bin:/bin:/usr/sbin:/usr/lib/wsl/lib','HOME':str(home),
        'OLLAMA_HOST':f'127.0.0.1:{PORT}','OLLAMA_MODELS':str(CACHE),'OLLAMA_CONTEXT_LENGTH':'4096',
        'OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_NO_CLOUD':'1','OLLAMA_KEEP_ALIVE':'5m'}
    server=None
    rows=[]
    started=time.monotonic()
    try:
        with (out/'server.log').open('xb') as log:
            server=subprocess.Popen(['/usr/local/bin/ollama','serve'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        server_net=os.readlink(f'/proc/{server.pid}/ns/net')
        require(server_net==proof['isolated_namespace'],'Server and runner namespaces differ')
        write(out/'server-pid.json',{'pid':server.pid,'process_group':server.pid,'port':PORT,'namespace':server_net})
        deadline=time.monotonic()+45
        while True:
            require(server.poll() is None,'Namespace server exited before readiness')
            try:
                version=api('version')
                require(version.get('version')=='0.30.7','Ollama runtime version changed')
                verify_model()
                break
            except (OSError, ValueError):
                require(time.monotonic()<deadline,'Server readiness deadline exceeded')
                time.sleep(.5)
        write(out/'readiness.json',{'server_ready':True,'model_loaded_by_readiness':False,'version':version,'digest':DIGEST})
        with (out/'raw.jsonl').open('x',encoding='utf-8') as raw, (out/'call-reservations.jsonl').open('x',encoding='utf-8') as calls:
            for index,case in enumerate(cases):
                require(index<2,'Call budget exhausted')
                require(time.monotonic()-started+420<950,'Insufficient wall-clock budget for one bounded request')
                process_snapshot(server.pid)
                calls.write(json.dumps({'call':index+1,'id':case['id'],'max_output_tokens':1024})+'\n'); calls.flush(); os.fsync(calls.fileno())
                result=inf.run_case(case,config)
                raw.write(json.dumps(result,ensure_ascii=False)+'\n'); raw.flush(); os.fsync(raw.fileno())
                rows.append(result)
                require(not result.get('error'),'Model request failed; no retry or second request')
                usage=result.get('usage') or {}
                require(type(usage.get('prompt_tokens')) is int and usage['prompt_tokens']<=2816,'Missing/excess prompt usage')
                require(type(usage.get('completion_tokens')) is int and usage['completion_tokens']<=1024,'Missing/excess completion usage')
                verify_model(resident=True)
        report=adapter.finalize(package,[out/'raw.jsonl'],out/'answers.json',out/'failures.json',out/'input.jsonl.manifest.json')
        require(not report['failures'],'Adapter reported failed answers')
        require(adapter.main(['validate',str(out/'answers.json'),'--exam-dir',str(out/'package')])==0,'answers.json validation failed')
        write(out/'success.json',{'model_calls':len(rows),'estimated_cost_usd':0,'actual_cost_usd':0,'output_token_cap_total':2048,
            'completion_tokens':sum(r['usage']['completion_tokens'] for r in rows),'elapsed_seconds':time.monotonic()-started,
            'answers_sha256':sha(out/'answers.json'),'submission_performed':False,'synthetic_only':True})
    finally:
        if server is not None:
            # Kill only the new server process group, never the host daemon or a named process globally.
            try:
                os.killpg(server.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid,signal.SIGKILL); server.wait(timeout=5)
            # A child backend may outlive a quickly exiting parent but stays in this owned group.
            try:
                os.killpg(server.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            write(out/'cleanup.json',{'owned_server_pid':server.pid,'owned_process_group':server.pid,
                'server_returncode':server.returncode,'termination_signals_confined_to_owned_group':True,
                'host_daemon_stopped':False,'host_firewall_changed':False})

def execute(args):
    require(sys.platform=='linux','Execute only under WSL/Linux')
    import fcntl
    out=output_path(args.output)
    lock=(OWN/'private/offline-rehearsal.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not api('ps',11434)['models'],'Host model must be explicitly unloaded by the lead first')
    process_snapshot()
    verify_assets()
    out.mkdir(parents=True)
    write(out/'launch.json',{'prepared_recipe':'kwiscion fallback for ljaniec issue #38','authorized_by_lead_argument':True,
        'max_model_calls':2,'max_output_tokens_total':2048,'retries':0,'estimated_cost_usd':0,
        'model_digest':DIGEST,'model_cache':str(CACHE),'weight_bytes':sum(ASSETS.values()),
        'script_sha256':sha(SELF),'infer_sha256':sha(ROOT/'infer.py'),'adapter_sha256':sha(ROOT/'scripts/Bukareszt/matura_package.py')})
    command=['unshare','-rn','--',sys.executable,'-B',str(SELF),'--inside','--host-net',os.readlink('/proc/self/ns/net'),'--output',str(out)]
    p=subprocess.Popen(command,start_new_session=True)
    try:
        return p.wait(timeout=980)
    except (subprocess.TimeoutExpired,KeyboardInterrupt):
        os.killpg(p.pid,signal.SIGTERM)
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); p.wait()
        raise RuntimeError('Rehearsal exceeded 980-second wall limit or was interrupted')
    finally:
        # Parent safety net if the inner Python process cannot execute its finally block.
        record=out/'server-pid.json'
        if record.is_file():
            owned=json.loads(record.read_text())
            matching=False
            for proc in Path('/proc').iterdir():
                if not proc.name.isdigit():
                    continue
                try:
                    if os.getpgid(int(proc.name))==owned['process_group'] and os.readlink(proc/'ns/net')==owned['namespace']:
                        matching=True
                except (OSError,ProcessLookupError):
                    continue
            if matching:
                try:
                    os.killpg(owned['process_group'],signal.SIGKILL)
                except ProcessLookupError:
                    pass

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--execute',action='store_true',help='Lead-only: launches server and at most two model calls')
    mode.add_argument('--inside',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--host-net',default='')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.inside:
        signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
        inside(a)
        return 0
    return execute(a)

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError,OSError,ValueError) as exc:
        print('STOP: '+str(exc),file=sys.stderr)
        raise SystemExit(2)
