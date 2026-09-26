"""Two synthetic native calls in a dedicated network namespace; dry preflight default."""
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os,re,signal,subprocess,sys,time,urllib.request
from pathlib import Path
MODEL='gemma4:12b-it-q4_K_M'
DIGEST='4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c'
GUARD='8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473'
CAP=10240
ENDPOINT='http://127.0.0.1:11435'
def need(x,msg):
    if not x:raise RuntimeError(msg)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(8*1024*1024),b''):h.update(x)
    return h.hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def write(p,x):
    with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def append(p,x):
    with p.open('a',encoding='utf8') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
def preflight(root):
    m=json.loads((root/'launch.json').read_text());need(m['schema']=='final_offline_two_v1','Schema')
    need((m['max_calls'],m['max_output_tokens'],m['max_seconds'],m['request_timeout'])==(2,20480,1200,420),'Budgets')
    need(m['think'] is True and m['temperature']=='omitted' and m['context']==32768 and m['retries']==0,'Controls')
    required={'run_gemma_offline.py','guard.py','offline_rehearsal.py','infer.py','scripts/Bukareszt/matura_package.py','agentsLog/Bukareszt/submission/fixtures/tiny-package/images/fixture-red.png'}
    need(set(m['files'])==required,'Exact dependency membership')
    for n,h in m['files'].items():
        p=root/n;need(not p.is_symlink() and p.resolve().is_relative_to(root) and sha(p)==h,'Code/fixture pin: '+n)
    need(m['files']['guard.py']==GUARD and sha(Path(__file__))==m['files']['run_gemma_offline.py'],'Guard/executing pin')
    need(not (root/'results').exists(),'Fresh results required')
    return m

def payload(case):
    c=case['content'];images=[]
    if isinstance(c,str):text=c
    else:
        text=c[0]['text']
        for part in c[1:]:
            prefix,data=part['image_url']['url'].split(',',1);need(prefix.startswith('data:image/') and prefix.endswith(';base64'),'Local image only');base64.b64decode(data,validate=True);images.append(data)
    msg={'role':'user','content':text}
    if images:msg['images']=images
    return {'model':MODEL,'stream':False,'think':True,'truncate':False,'shift':False,'messages':[msg],'options':{'num_ctx':32768,'num_predict':CAP}}
def answer(response):
    need(response.get('model')==MODEL and response.get('error') is None,'Model/provider')
    need(not any(response.get(k) is True for k in ('truncated','context_truncated')),'Truncated context')
    p=response.get('prompt_eval_count');n=response.get('eval_count')
    need(type(p) is int and p>=0 and p+CAP<=32768 and type(n) is int and 0<=n<=CAP,'Usage/context')
    need(response.get('done') is True and response.get('done_reason')=='stop','Incomplete final')
    msg=response.get('message',{});need(isinstance(msg.get('content'),str) and msg['content'].strip(),'Empty final')
    need(isinstance(msg.get('thinking'),str) and msg['thinking'].strip(),'Missing requested thinking')
    return msg['content']
def correct(id,text):
    normalized=text.strip().casefold().strip(' .!\n\t')
    return normalized in ({'gotowe'} if id=='offline-text' else {'czerwony','czerwona','czerwone','red'})
def ticks(pid):return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
def cleanup(record):
    """Only recorded group members with namespace and start-time evidence."""
    matched=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            pid=int(p.name)
            if os.getpgid(pid)==record['pid'] and os.readlink(p/'ns/net')==record['namespace'] and int(ticks(pid))>=int(record['ticks']):matched.append(pid)
        except (FileNotFoundError,ProcessLookupError):pass
    if matched:
        if Path(f"/proc/{record['pid']}").exists():need(ticks(record['pid'])==record['ticks'],'PID reuse')
        try:os.killpg(record['pid'],signal.SIGKILL)
        except ProcessLookupError:pass
    return matched

def namespace_cleanup(proof,binary):
    """Fallback for death after spawn but before the PID receipt is durable."""
    namespace=proof['isolated_namespace'];need(namespace!=os.readlink('/proc/self/ns/net'),'Never clean host namespace')
    killed=[];runtime=Path(binary).resolve().parent.parent
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if p.stat().st_uid!=os.getuid():continue
            if os.readlink(p/'ns/net')==namespace and (p/'exe').resolve().is_relative_to(runtime):
                pid=int(p.name);start=ticks(pid)
                need(os.readlink(p/'ns/net')==namespace and ticks(pid)==start,'Cleanup identity changed')
                os.kill(pid,signal.SIGKILL);killed.append(pid)
        except (FileNotFoundError,ProcessLookupError):pass
    return killed

def workers(allowed,server_group=None):
    blockers=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) in allowed:continue
        try:
            args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0');exe=Path(args[0]).name
            if exe.startswith('python') and any(Path(a).name.startswith(('run_','hetero-source')) or Path(a).name in ('infer.py','reasoning_lab.py','smoke.py') for a in args[1:]):blockers.append(int(p.name))
        except (FileNotFoundError,ProcessLookupError):pass
    gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True)
    for row in gpu.splitlines():
        need(row.strip().isdigit(),'GPU process parse');pid=int(row)
        need(server_group is not None and os.getpgid(pid)==server_group,'Foreign GPU process')
    need(not blockers,'Competing inference worker')
    return {'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'workers':blockers,'gpu_pids':gpu.splitlines()}

def remaining(m):
    seconds=dt.datetime.fromisoformat(m['deadline_utc']).timestamp()-time.time();need(0<seconds<=1200,'Absolute deadline');return seconds

def dispatch(cases,m,out,send,check):
    rows=[];reserved=0
    for case in cases:
        need(remaining(m)>425,'Insufficient complete request window');check(bool(reserved))
        body=payload(case);need(reserved<2,'Call cap')
        append(out/'requests.jsonl',{'id':case['id'],'payload':body});reserved+=1
        append(out/'reservations.jsonl',{'call':reserved,'id':case['id'],'cap':CAP,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})
        response=None;row={'id':case['id'],'error':None};started=time.monotonic()
        try:
            response=send(body)
            check(True);remaining(m);text=answer(response)
            row['raw_response']={'choices':[{'finish_reason':'stop','message':{'content':text}}]}
        except Exception as exc:row['error']={'type':type(exc).__name__,'message':str(exc)}
        append(out/'native-raw.jsonl',{'id':case['id'],'response':response,'error':row['error'],'latency_s':time.monotonic()-started});append(out/'finalizer-input.jsonl',row);rows.append(row)
        if row['error'] is not None:break
    return rows,reserved

def inside(root,m,host_net,parent):
    r=load('rehearsal',root/'offline_rehearsal.py');r.ROOT=root
    g=load('weights',root/'guard.py');adapter=load('adapter',root/'scripts/Bukareszt/matura_package.py');inf=load('inference',root/'infer.py')
    out=root/'results';proof=r.network_proof(host_net);write(out/'network-proof.json',proof)
    package=r.fixture(out,adapter);(out/'config.json').write_text(json.dumps({'transport':'native','think':True,'num_ctx':32768,'num_predict':CAP,'temperature':'omitted'}));cases=inf.load_cases(out/'input.jsonl',2);need([x['id'] for x in cases]==r.IDS,'Two fixed items')
    write(out/'pre-process.json',workers({os.getpid(),parent}))
    home=out/'server-home';home.mkdir();env={'PATH':os.environ['PATH'],'HOME':str(home),'OLLAMA_MODELS':m['cache'],'OLLAMA_HOST':'127.0.0.1:11435','OLLAMA_CONTEXT_LENGTH':'32768','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_NO_CLOUD':'1','OLLAMA_KEEP_ALIVE':'5m'}
    server=None;record=None;rows=[];error=None;opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));reserved=0
    def snapshot(loaded):
        need(server.poll() is None,'Owned server exited');need(ticks(server.pid)==record['ticks'],'Server identity changed')
        need(os.readlink(f'/proc/{server.pid}/ns/net')==proof['isolated_namespace'],'Server namespace')
        need(Path(f'/proc/{server.pid}/exe').resolve()==Path(m['binary']),'Server executable')
        env_actual=dict(x.split('=',1) for x in Path(f'/proc/{server.pid}/environ').read_bytes().decode().split('\0') if '=' in x)
        need(all(env_actual.get(k)==v for k,v in env.items()),'Server environment')
        snap={k:r.api(k) for k in ('version','tags','ps')};g.verify_snapshot(snap,g.CANONICAL,loaded)
        append(out/'runtime.jsonl',snap);workers({os.getpid(),parent},server.pid)
    try:
        with (out/'server.log').open('xb') as log:server=subprocess.Popen([m['binary'],'serve'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        record={'pid':server.pid,'ticks':ticks(server.pid),'namespace':os.readlink(f'/proc/{server.pid}/ns/net')};write(out/'server-identity.json',record)
        until=time.monotonic()+45
        while True:
            try:snapshot(False);break
            except OSError:
                need(time.monotonic()<until and server.poll() is None,'Readiness failure');time.sleep(.25)
        def send(body):
            req=urllib.request.Request(ENDPOINT+'/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with opener.open(req,timeout=420) as reply:return json.load(reply)
        rows,reserved=dispatch(cases,m,out,send,snapshot)
        need(len(rows)==2 and all(x['error'] is None for x in rows),'Incomplete qualification')
        report=adapter.finalize(package,[out/'finalizer-input.jsonl'],out/'answers.json',out/'failures.json',out/'input.jsonl.manifest.json')
        need(not report['failures'],'Adapter failures')
        need(adapter.main(['validate',str(out/'answers.json'),'--exam-dir',str(out/'package')])==0,'Template validation')
        actual=json.loads((out/'answers.json').read_text())['answers'];need(all(correct(x['id'],x['answer']) for x in actual),'Synthetic answer meaning failed')
        write(out/'success.json',{'calls':reserved,'requested_tokens':reserved*CAP,'answers_sha256':sha(out/'answers.json'),'synthetic_checks':'exact gotowe; dominant red','scope':'two synthetic organizer items only'})
    except Exception as exc:error=str(exc);raise
    finally:
        if record:
            killed=cleanup(record);server.wait(timeout=5);write(out/'cleanup.json',{'owned':record,'matched_pids':killed,'returncode':server.returncode})
        if not (out/'answers.json').exists():
            p=out/'finalizer-input.jsonl'
            if not p.exists():p.write_text('')
            adapter.finalize(package,[p],out/'answers.json',out/'failures.json',out/'input.jsonl.manifest.json')
        reserved=len((out/'reservations.jsonl').read_text().splitlines()) if (out/'reservations.jsonl').exists() else 0
        rows=[json.loads(x) for x in (out/'finalizer-input.jsonl').read_text().splitlines()]
        write(out/'terminal.json',{'calls':reserved,'requested_tokens':reserved*CAP,'error':error,'unsent_ids':[x['id'] for x in cases[len(rows):]]})

def execute(root,m):
    import fcntl
    need(sys.platform=='linux' and m['status']=='DECLARED','Explicit declaration required');left=remaining(m)
    declared=dt.datetime.fromisoformat(m['declared_utc']).timestamp();need(0<=time.time()-declared<=1200 and dt.datetime.fromisoformat(m['deadline_utc']).timestamp()-declared<=1200,'Declaration bound')
    lock=Path(m['lock']).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    g=load('weights',root/'guard.py');need(g.fingerprint(Path(m['binary']))['sha256']==g.CANONICAL['runtime_binary_sha256'],'Runtime binary')
    verified=g.verify_inventory(m['cache'],g.native_inventory(m['cache'],g.CANONICAL));workers({os.getpid()})
    r=load('rehearsal',root/'offline_rehearsal.py');r.isolation_probe();need(not r.api('ps',11436)['models'],'Existing host model resident; do not unload automatically')
    out=root/'results';out.mkdir();write(out/'weights.json',verified);write(out/'launch.json',m)
    command=['unshare','-rn','--',sys.executable,'-B',str(Path(__file__).resolve()),str(root),'--execute','--inside','--host-net',os.readlink('/proc/self/ns/net'),'--parent',str(os.getpid())]
    p=subprocess.Popen(command,start_new_session=True)
    try:return p.wait(timeout=max(1,remaining(m)-10))
    finally:
        if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
        record=out/'server-identity.json'
        if record.exists():
            try:cleanup(json.loads(record.read_text()))
            except (ValueError,KeyError):pass
        proof=out/'network-proof.json'
        if proof.exists():namespace_cleanup(json.loads(proof.read_text()),m['binary'])
        write(out/'post-process.json',workers({os.getpid()}))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);ap.add_argument('--execute',action='store_true');ap.add_argument('--cleanup',action='store_true');ap.add_argument('--inside',action='store_true');ap.add_argument('--host-net');ap.add_argument('--parent',type=int);a=ap.parse_args();root=a.package.resolve()
    if a.cleanup:
        m=json.loads((root/'results/launch.json').read_text());need(m==json.loads((root/'launch.json').read_text()),'Cleanup declaration changed')
        for n,h in m['files'].items():need(sha(root/n)==h,'Cleanup code pin')
        proof=root/'results/network-proof.json'
        if proof.exists():namespace_cleanup(json.loads(proof.read_text()),m['binary'])
        return 0
    if a.inside:
        need(a.execute and a.parent and a.host_net,'Internal execution arguments');m=json.loads((root/'results/launch.json').read_text());need(m==json.loads((root/'launch.json').read_text()) and m['status']=='DECLARED','Frozen declaration');remaining(m)
        for n,h in m['files'].items():need(sha(root/n)==h,'Internal dependency pin')
        inside(root,m,a.host_net,a.parent);return 0
    m=preflight(root)
    if not a.execute:print('PASS: file-only preflight; no server or model started');return 0
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(RuntimeError('Whole-operation deadline')))
    signal.setitimer(signal.ITIMER_REAL,max(1,remaining(m)-10))
    try:return execute(root,m)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':raise SystemExit(main())
