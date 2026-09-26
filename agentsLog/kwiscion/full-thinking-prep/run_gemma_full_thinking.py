"""CPU-prepared native thinking diagnostic. Default is file-only preflight.

No server start/stop, model warmup, retries, or downloads. Explicit --execute and
a reviewed DECLARED manifest are required. Original source packs stay private.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

MODEL='gemma4:12b-it-q4_K_M'
DIGEST='4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
MAX_CALLS,MAX_TOKENS,MAX_SECONDS=40,419840,5400
def require(ok,message):
    if not ok: raise RuntimeError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def competing_native(args):
    return bool(args and Path(args[0]).name.startswith('python') and
                any(Path(x).name=='reasoning_lab.py' for x in args[1:]))
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s)
    sys.modules[name]=m;s.loader.exec_module(m);return m
def append(p,value):
    with p.open('a',encoding='utf8') as f:
        f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
def preflight(root):
    root=root.resolve();mp=root/'launch.json';m=json.loads(mp.read_text(encoding='utf8'))
    require(m['max_calls']==MAX_CALLS and m['max_requested_tokens']==MAX_TOKENS and m['max_wall_seconds']==MAX_SECONDS,'Fixed budgets')
    require(m['model']==MODEL and m['model_digest']==DIGEST and m['context_length']==32768,'Model/context')
    require(m['base_url']=='http://127.0.0.1:11436' and m['think'] is True and m['temperature']=='omitted' and m['retries']==0,'Frozen controls')
    require(type(m['timeout_seconds']) is int and 1<=m['timeout_seconds']<=600,'Timeout')
    require(len(m['ids'])==40 and len(set(m['ids']))==40 and set(m['caps'])==set(m['ids']),'Exact40 unique IDs')
    require(list(m['caps'].values()).count(20480)==1 and list(m['caps'].values()).count(10240)==39 and sum(m['caps'].values())==MAX_TOKENS,'Fixed caps')
    required={'infer.py','runtime_guard.py','run_gemma_full_thinking.py','scripts/ljaniec/reasoning_lab.py','scripts/Bukareszt/matura_package.py','input.jsonl','input.original.jsonl','exam/exam.json','exam/answers-template.json'}
    require(required<=set(m['files']),'Pinned code/input membership')
    for n,h in m['files'].items():
        p=(root/n).resolve();require(p.is_relative_to(root) and p.is_file() and sha(p)==h,'Pin mismatch: '+n)
    require(sha(Path(__file__))==m['files']['run_gemma_full_thinking.py'],'Executing code pin')
    rows=[json.loads(x) for x in (root/'input.jsonl').read_text(encoding='utf8').splitlines()]
    old=[json.loads(x) for x in (root/'input.original.jsonl').read_text(encoding='utf8').splitlines()]
    require([x['id'] for x in rows]==m['ids']==[x['id'] for x in old],'Input order')
    for new,prior in zip(rows,old):
        expect=dict(prior)
        if new['id'] in m['essay_ids']: expect['prompt']+='\n\n'+m['essay_policy']
        require(new==expect,'Unexpected source modification')
        for image in new.get('images',[]):
            p=(root/image).resolve();require(p.is_relative_to(root) and p.is_file(),'Image boundary')
            require(str(p.relative_to(root)).replace('\\','/') in m['files'],'Unpinned image')
    require(not (root/'results').exists(),'Fresh outputs only')
    return m,sha(mp)
def payload(case,cap,native):
    text,images=native.native_source(case)
    message={'role':'user','content':text}
    if images:message['images']=images
    return {'model':MODEL,'stream':False,'think':True,'truncate':False,'shift':False,
            'messages':[message],'options':{'num_ctx':32768,'num_predict':cap}}
def validate(response,cap):
    """Only length/empty-final are case-local after identity/usage validation."""
    require(isinstance(response,dict),'Malformed native response')
    require(response.get('error') is None and response.get('model')==MODEL,'Provider/model failure')
    require(not any(response.get(k) is True for k in ('truncated','context_truncated')),'Explicit truncation')
    p=response.get('prompt_eval_count');n=response.get('eval_count')
    require(type(p) is int and p>=0 and p+cap<=32768,'Prompt reserve/context')
    require(type(n) is int and 0<=n<=cap,'Generated token budget')
    require(response.get('done') is True and response.get('done_reason') in ('stop','length'),'Unknown completion state')
    msg=response.get('message');require(isinstance(msg,dict) and isinstance(msg.get('content'),str) and isinstance(msg.get('thinking',''),str),'Malformed message')
    if response['done_reason']=='length':return '',{'type':'length','message':'Native combined thinking/final cap reached'}
    if not msg['content'].strip():return '',{'type':'empty_final','message':'No complete final answer'}
    require(bool(msg.get('thinking','').strip()),'Missing requested thinking evidence')
    return msg['content'],None
class Budget:
    def __init__(self,m):
        self.m=m;self.started=time.monotonic();self.deadline=dt.datetime.fromisoformat(m['deadline_utc'].replace('Z','+00:00')).timestamp()
    def remaining(self):
        left=min(self.m['max_wall_seconds']-(time.monotonic()-self.started),self.deadline-time.time())
        require(left>0,'Hard deadline');return left
def run_loop(cases,m,out,transport,guard,native,budget):
    records=[];calls=0;tokens=0;status='complete'
    for case in cases:
        cap=m['caps'][case['id']];response=None;reserved=False;started=time.monotonic()
        try:
            guard(False)
            require(budget.remaining()>m['timeout_seconds']+5,'Insufficient full-timeout window')
            require(calls<MAX_CALLS and tokens+cap<=MAX_TOKENS,'Call/token cap')
            body=payload(case,cap,native)
            append(out/'requests.jsonl',{'id':case['id'],'payload':body})
            calls+=1;tokens+=cap;reserved=True
            append(out/'calls.jsonl',{'id':case['id'],'call':calls,'cap':cap,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})
            response=transport(m['base_url'],'/api/chat',body,budget)
            guard(True);budget.remaining()
            answer,error=validate(response,cap)
            record={'id':case['id'],'answer':answer,'error':error,'raw_response':response,'latency_s':time.monotonic()-started}
            records.append(record);append(out/'raw.jsonl',record)
        except Exception as exc:
            status=type(exc).__name__+': '+str(exc)
            if reserved:
                record={'id':case['id'],'answer':'','error':{'type':'systemic','message':status},'raw_response':response,'latency_s':time.monotonic()-started}
                records.append(record);append(out/'raw.jsonl',record)
            break
    return {'status':status,'calls':calls,'requested_tokens':tokens,'records':records,'unsent':[x['id'] for x in cases if x['id'] not in {r['id'] for r in records}]}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('package',type=Path);parser.add_argument('--execute',action='store_true');a=parser.parse_args()
    root=a.package.resolve();m,mhash=preflight(root)
    print(json.dumps({'status':m['status'],'items':40,'max_requested_tokens':MAX_TOKENS,'execute':a.execute}),flush=True)
    if not a.execute:return 0
    require(m['status']=='DECLARED' and m['deadline_utc'] and m['declared_utc'],'Explicit reviewed launch declaration')
    budget=Budget(m);require(budget.remaining()<=MAX_SECONDS,'Deadline bound')
    host=Path(m['host_root']).resolve();require(root.is_relative_to(host),'Owned project package required')
    import fcntl
    lock=(host/'matched-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sys.path.insert(0,str(root))
    inf=load('infer',root/'infer.py');native=load('full_native',root/'scripts/ljaniec/reasoning_lab.py')
    guardmod=load('full_runtime_guard',root/'runtime_guard.py');adapter=load('full_adapter',root/'scripts/Bukareszt/matura_package.py')
    # Full verified model+projector bytes, unchanged parent runtime guard.
    assets,_=guardmod.verify_models(host,m['model_digests'])
    out=root/'results';out.mkdir()
    def hard_stop(*_):raise RuntimeError('Hard wall deadline')
    signal.signal(signal.SIGALRM,hard_stop);signal.setitimer(signal.ITIMER_REAL,budget.remaining())
    def guard(loaded):
        require(sha(root/'launch.json')==mhash,'Manifest changed')
        for n,h in m['files'].items():require(sha(root/n)==h,'File changed: '+n)
        require(sha(host/'runtime/bin/ollama')==m['runtime_executable_sha256'],'Runtime binary changed')
        for n,state in assets.items():
            st=Path(n).stat();require((st.st_size,st.st_mtime_ns,st.st_ino)==state,'Model file changed')
        guardmod.process_guard(host,m['server_pid'],m['server_start_ticks'])
        # The older shared guard predates the native reasoning controller name.
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
            try:
                args=(proc/'cmdline').read_bytes().decode(errors='replace').split('\0')
                require(not competing_native(args),'Competing native reasoning worker')
            except (FileNotFoundError,ProcessLookupError):pass
        snapshot=native.health(m,budget,require_loaded=loaded)
        append(out/'runtime.jsonl',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'snapshot':snapshot})
    try:
        cases=inf.load_cases(root/'input.jsonl',MAX_CALLS)
        result=run_loop(cases,m,out,native.request_json,guard,native,budget)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    # The actual original organizer template is retained, including all unsent IDs.
    package=adapter.load_package(root/'exam');rows=[]
    for r in result['records']:
        rows.append({'id':r['id'],'error':r['error'],'raw_response':{'choices':[{'finish_reason':'stop','message':{'content':r['answer']}}]}})
    normalized=out/'finalizer-input.jsonl';normalized.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf8')
    adapter.finalize(package,[normalized],out/'answers.json',out/'failures.json')
    result['elapsed_seconds']=time.monotonic()-budget.started
    result['raw_sha256']=sha(out/'raw.jsonl') if (out/'raw.jsonl').exists() else None
    result['records']=len(result['records']);result['manifest_sha256']=mhash
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result),flush=True);return 0 if result['status']=='complete' else 1
if __name__=='__main__':raise SystemExit(main())
