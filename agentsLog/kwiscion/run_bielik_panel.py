"""Dry-default, frozen nine-item/two-model text comparison. No server management."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request

PINS = {
    'bielik11b-v3-q5:latest': '771843b8f249eae2f2faad7d0f0aabe33e22b00c90332976f9eba1608ca1d28a',
    'gemma4:12b-it-q4_K_M': '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c',
}
PANEL_SHA = '213197cc40570123d52d90e3c5609675f4d2f36f050704a042475bba418614d0'
RUNTIME_SHA = 'ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4'
IDS = ['val2024-hist-z'+x for x in ('3.1','3.2','7','15.1','15.2','20.1','20.2','22.1','22.2')]
ENDPOINT = 'http://127.0.0.1:11436/v1/chat/completions'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def preflight(root):
    """Only local files: no network, imports of pinned code, or output mutation."""
    root = Path(root).resolve()
    m = json.loads((root/'launch.json').read_text())
    require(m['max_calls'] == 18 and m['max_requested_output_tokens'] == 18432, 'Budget')
    require(m['context'] == 32768 and m['output_cap'] == 1024 and m['timeout'] == 420, 'Settings')
    require(m['models'] == PINS and m['runtime_sha256'] == RUNTIME_SHA, 'Runtime/model pins')
    require(m['files'].get('panel.jsonl') == PANEL_SHA, 'Panel pin')
    require({'panel.jsonl','infer.py','run_bielik_panel.py'} <= m['files'].keys(), 'Required pins')
    for name, digest in m['files'].items():
        p = (root/name).resolve()
        require(p.is_relative_to(root) and sha(p) == digest, 'Frozen file: '+name)
    require(sha(Path(__file__)) == m['files']['run_bielik_panel.py'], 'Running controller pin')
    rows = [json.loads(x) for x in (root/'panel.jsonl').read_text(encoding='utf8').splitlines()]
    require([r['id'] for r in rows] == IDS, 'Panel IDs/order')
    require(all(not r.get('images') and isinstance(r.get('prompt'),str) for r in rows), 'Text-only sources')
    require(not (root/'results').exists(), 'Fresh output required')
    deadline = dt.datetime.fromisoformat(m['deadline_utc'])
    require(deadline.tzinfo is not None, 'UTC deadline required')
    require(425 < (deadline-dt.datetime.now(dt.timezone.utc)).total_seconds() <= 2700, '45-minute deadline')
    return m, rows, deadline


def check_runtime(snapshot, expected=None):
    require(snapshot['version']['version'] == '0.34.4', 'Runtime version')
    for name, digest in PINS.items():
        require(any(x['name'] == name and x['digest'] == digest for x in snapshot['tags']['models']), 'Tag pin')
    loaded = snapshot['ps']['models']
    require(len(loaded) <= 1, 'Unexpected loaded count')
    for item in loaded:
        require(item['digest'] in PINS.values() and item['context_length'] == 32768, 'Loaded identity/context')
    if expected:
        require(len(loaded) == 1 and loaded[0]['digest'] == PINS[expected], 'Requested model not loaded')


def validate(row, model, inf):
    """Only length/empty-final may continue, after all systemic checks pass."""
    raw = row.get('raw_response')
    require(isinstance(raw,dict) and raw.get('error') is None, 'Transport/provider response')
    require(raw.get('model') == model, 'Response identity')
    require(not any(raw.get(k,False) for k in ('truncated','context_truncated')), 'Context truncation')
    usage = row.get('usage')
    require(isinstance(usage,dict), 'Missing usage')
    require(type(usage.get('prompt_tokens')) is int and 0 <= usage['prompt_tokens'] <= 31744, 'Prompt budget')
    require(type(usage.get('completion_tokens')) is int and 0 <= usage['completion_tokens'] <= 1024, 'Output budget')
    if 'total_tokens' in usage:
        require(type(usage['total_tokens']) is int and usage['total_tokens'] == usage['prompt_tokens']+usage['completion_tokens'], 'Usage total')
    choices = raw.get('choices')
    require(isinstance(choices,list) and len(choices) == 1 and isinstance(choices[0],dict), 'Choices')
    choice = choices[0]; message = choice.get('message')
    require(isinstance(message,dict) and 'content' in message, 'Message')
    require(not any(message.get(k) for k in ('refusal','tool_calls','function_call')), 'Refusal/tools')
    answer = message['content']
    require(answer is None or isinstance(answer,str), 'Content shape')
    require(choice.get('finish_reason') in ('stop','length'), 'Finish reason')
    local = choice['finish_reason'] == 'length' or not (answer or '').strip()
    error = row.get('error')
    require(error is None or (local and error == inf.response_error(raw) and error.get('type') == 'incomplete'), 'Runner error')
    if local:
        row['error'] = error or {'type':'case_generation','message':'Length or empty final'}
    return '' if local else answer


def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('--execute',action='store_true')
    a=parser.parse_args();root=a.root.resolve();m,rows,deadline=preflight(root)
    if not a.execute:
        print(json.dumps({'status':'dry_preflight_pass','items':len(rows),'calls':18,'tokens':18432}));return 0
    import fcntl
    host=root.parent
    require(sha(host/'runtime/bin/ollama') == RUNTIME_SHA, 'Runtime executable pin')
    lock=(host/'paired-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    started=time.monotonic();wall=min(2700,(deadline-dt.datetime.now(dt.timezone.utc)).total_seconds())
    def timeout(*_): raise RuntimeError('Hard wall deadline')
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,wall)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def snapshot():
        result={}
        for name in ('version','tags','ps'):
            with opener.open('http://127.0.0.1:11436/api/'+name,timeout=5) as r:result[name]=json.load(r)
        return result
    def guard():
        require((deadline-dt.datetime.now(dt.timezone.utc)).total_seconds()>425 and time.monotonic()-started+425<wall,'Dispatch deadline')
        for name,digest in m['files'].items():require(sha(root/name)==digest,'Frozen file changed')
        require(sha(host/'runtime/bin/ollama')==RUNTIME_SHA,'Runtime changed')
        server=int((host/'server.pid').read_text())
        for line in subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).splitlines():
            require(line.strip().isdigit() and os.getpgid(int(line))==server,'Competing GPU worker')
        for p in Path('/proc').iterdir():
            if not p.name.isdigit() or int(p.name)==os.getpid():continue
            try:
                args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
                if Path(args[0]).name.startswith('python'):
                    require(not any(Path(x).name.startswith(('run_','hetero-source')) or Path(x).name in ('infer.py','smoke.py') for x in args[1:]),'Competing inference worker')
            except (FileNotFoundError,ProcessLookupError):pass
    guard();check_runtime(snapshot())
    spec=importlib.util.spec_from_file_location('infer',root/'infer.py');inf=importlib.util.module_from_spec(spec);spec.loader.exec_module(inf)
    cases=inf.load_cases(root/'panel.jsonl',9)
    out=root/'results';out.mkdir();(out/'requests').mkdir()
    def append(f,value):f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    count=0;records=[];active=None
    class Capture:
        def open(self,request,timeout):
            guard();data=json.loads(request.data)
            require(request.full_url==ENDPOINT and timeout==420,'Transport controls')
            require(data==active,'Exact original request changed')
            (out/'requests'/f'{count:02}.json').write_bytes(request.data)
            return opener.open(request,timeout=timeout)
    inf.OPENER=Capture();status='complete'
    with (out/'calls.jsonl').open('x') as ledger,(out/'raw.jsonl').open('x',encoding='utf8') as raw,(out/'runtime.jsonl').open('x') as runtime:
        try:
            for model,digest in PINS.items():
                config={'name':'paired-text-panel','base_url':ENDPOINT.rsplit('/',2)[0],'endpoint':ENDPOINT,'model':model,'model_revision':digest,'max_output_tokens':1024,'timeout_seconds':420}
                if model.startswith('gemma'):config['reasoning_effort']='none'
                for case in cases:
                    guard();before=snapshot();check_runtime(before);guard()
                    require(count<18,'Call cap');count+=1
                    active={'model':model,'messages':[{'role':'user','content':case['content']}],'max_tokens':1024}
                    if model.startswith('gemma'):active['reasoning_effort']='none'
                    append(ledger,{'call':count,'model':model,'id':case['id'],'cap':1024,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})
                    row=inf.run_case(case,config);answer='';problem=None
                    try:
                        after=snapshot();append(runtime,{'call':count,'before':before,'after':after});check_runtime(after,model)
                        answer=validate(row,model,inf)
                    except Exception as exc:
                        problem=str(exc);row['error']=row.get('error') or {'type':'panel_validation','message':problem}
                    record={'call':count,'model':model,'id':case['id'],'answer':answer,'result':row}
                    append(raw,record);records.append(record)
                    require(problem is None,problem)
        except Exception as exc:status=str(exc)
    signal.setitimer(signal.ITIMER_REAL,0)
    attempted={(r['model'],r['id']) for r in records}
    summary={'status':status,'calls_reserved':count,'records':len(records),'requested_output_tokens':count*1024,'elapsed_seconds':time.monotonic()-started,'unsent':[{'model':model,'id':case['id']} for model in PINS for case in cases if (model,case['id']) not in attempted],'raw_sha256':sha(out/'raw.jsonl')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
    return 0 if status=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
