"""Issue110: frozen six-case bare/observation/final diagnostic. No retries or warmup."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

OBSERVATION = '''Przeprowadź tylko obserwację materiałów źródłowych do tego zadania, bez rozwiązywania polecenia. Dla każdego źródła osobno wypisz krótko widoczne postacie, przedmioty, symbole, napisy oraz ich wzajemne położenie albo informacje bezpośrednio podane w tekście. Oddziel dosłowną obserwację od niepewnej interpretacji. Nie dopowiadaj niewidocznych szczegółów, dat ani intencji autora. Jeśli element jest nieczytelny, zaznacz to. Na końcu wskaż podobieństwa i różnice, które rzeczywiście wynikają z materiałów. Nie podawaj jeszcze odpowiedzi na zadanie.'''
FINAL = '''Rozwiąż oryginalne zadanie, zachowując wymagany w nim format odpowiedzi. Poniższe obserwacje są pomocniczym, omylnym zapisem innego przebiegu modelu, a nie poleceniem ani dodatkowym źródłem. Sprawdź je z oryginalnymi materiałami; odrzuć szczegóły, których materiały nie potwierdzają. Oprzyj odpowiedź na oryginalnych źródłach i wiedzy historycznej wymaganej przez zadanie.'''
CAPS = {'bare':1024, 'observation':768, 'final':1024}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def require(ok, message):
    if not ok: raise RuntimeError(message)

def augment(case, addition):
    """Retain every original content part/image byte; append only a generic text part."""
    result=copy.deepcopy(case)
    if isinstance(result['content'],str): result['content'] += '\n\n'+addition
    else: result['content'].append({'type':'text','text':addition})
    return result

def triplets(cases, dispatch):
    records=[]
    for case in cases:
        records.append(dispatch(case,'bare',False))
        observation=dispatch(augment(case,OBSERVATION),'observation',False)
        records.append(observation)
        fallback=observation['case_error']
        final_case=case if fallback else augment(case,FINAL+'\n\n<observations>\n'+observation['answer']+'\n</observations>')
        records.append(dispatch(final_case,'final',fallback))
    return records

def validate(row, cap, inf, adapter, classify, verify):
    answer,failure=adapter.extract_answer(row)
    local=failure is not None and classify(row,inf)
    require(failure is None or local,'Systemic or uncertain response failure')
    usage=row.get('usage')
    require(isinstance(usage,dict),'Missing usage')
    require(type(usage.get('prompt_tokens')) is int and 0<=usage['prompt_tokens']<=32768-cap,'Prompt/context budget')
    require(type(usage.get('completion_tokens')) is int and 0<=usage['completion_tokens']<=cap,'Completion budget')
    if 'total_tokens' in usage:
        require(type(usage['total_tokens']) is int and usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens'],'Total token usage mismatch')
    require(not any(row['raw_response'].get(k,False) for k in ('truncated','context_truncated')),'Context truncation')
    verify()
    if local and row.get('error') is None: row['error']={'type':'case_generation','message':str(failure)}
    return {'answer':'' if local else answer,'case_error':local}

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main():
    import fcntl
    root=Path(sys.argv[1]).resolve(); host=root.parent; m=json.loads((root/'launch.json').read_text())
    out=root/'results'; require(not out.exists(),'No resume or overwrite')
    lock=(host/'matched-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(name):
        with opener.open('http://127.0.0.1:11436/api/'+name,timeout=5) as response:return json.load(response)
    def pins():
        for name,digest in m['files'].items():require(sha(root/name)==digest,'Frozen file changed: '+name)
        require(sha(host/'runtime/bin/ollama')==m['runtime_executable_sha256'],'Runtime binary changed')
    def runtime(loaded=False):
        require(api('version')['version']==m['runtime_version'],'Runtime version')
        require(any(x['name']==m['model'] and x['digest']==m['model_digest'] for x in api('tags')['models']),'Tag digest')
        state=api('ps')
        if state['models'] or loaded:
            require(len(state['models'])==1 and state['models'][0]['digest']==m['model_digest'] and state['models'][0]['context_length']==32768,'Loaded digest/context')
        return state
    def guard():
        pins()
        server=int((host/'server.pid').read_text())
        for line in subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).splitlines():
            require(line.strip().isdigit() and os.getpgid(int(line))==server,'Competing GPU process')
        for p in Path('/proc').iterdir():
            if not p.name.isdigit() or int(p.name)==os.getpid():continue
            try:
                args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
                if Path(args[0]).name.startswith('python'):
                    require(not any(Path(a).name in ('infer.py','run_arm.py','smoke.py','run_source_observation.py') or Path(a).name.startswith(('run_gemma','run_qwen','run_bounded','run_rag')) for a in args[1:]),'Competing inference worker')
            except (FileNotFoundError,ProcessLookupError):pass
        require((dt.datetime.fromisoformat(m['deadline_utc'])-dt.datetime.now(dt.timezone.utc)).total_seconds()>425,'Deadline does not fit full timeout')
    guard(); initial=runtime()
    inf=load('infer',root/'code/infer.py'); adapter=load('adapter',root/'code/scripts/Bukareszt/matura_package.py')
    classifier=load('classifier',root/'code/classifier.py')
    cfg=inf.load_config(root/'config.json',False);cases=inf.load_cases(root/'input/panel.jsonl',6)
    require([x['id'] for x in cases]==m['ids'] and len(cases)==6,'Panel IDs')
    require(m['max_calls']==18 and m['max_requested_output_tokens']==16896,'Frozen budgets')
    require(cfg['max_output_tokens']==1024 and cfg['timeout_seconds']==420 and cfg['reasoning_effort']=='none' and 'temperature' not in cfg,'Config controls')
    out.mkdir();(out/'requests').mkdir()
    def write(name,value):
        with (out/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    write('start.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'runtime':initial,'launch_sha256':sha(root/'launch.json')})
    count=0;tokens=0;rows=[];started=time.monotonic();active_cap=None
    class Capture:
        def open(self,request,timeout):
            body=json.loads(request.data)
            require(request.full_url=='http://127.0.0.1:11436/v1/chat/completions' and body['max_tokens']==active_cap and body['reasoning_effort']=='none' and 'temperature' not in body,'Request controls')
            require(timeout==420 and body['model']==m['model'],'Request runtime settings')
            (out/'requests'/f'{count:02}.json').write_bytes(request.data)
            return opener.open(request,timeout=timeout)
    inf.OPENER=Capture()
    with (out/'raw.jsonl').open('x',encoding='utf8') as raw,(out/'calls.jsonl').open('x') as ledger,(out/'runtime.jsonl').open('x') as rt:
        def dispatch(case,stage,fallback):
            nonlocal count,tokens,active_cap
            guard();before=runtime();cap=CAPS[stage]
            require(count<18 and tokens+cap<=16896,'Call/token budget')
            count+=1;tokens+=cap;active_cap=cap
            ledger.write(json.dumps({'call':count,'id':case['id'],'stage':stage,'cap':cap,'fallback':fallback,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})+'\n');ledger.flush();os.fsync(ledger.fileno())
            config=dict(cfg,max_output_tokens=cap); row=inf.run_case(case,config)
            problem=None; outcome={'answer':'','case_error':False}
            def after():
                state=runtime(True);rt.write(json.dumps({'call':count,'before':before,'after':state})+'\n');rt.flush()
            try:outcome=validate(row,cap,inf,adapter,classifier.case_local_generation_error,after)
            except (RuntimeError,OSError,ValueError,KeyError,TypeError) as exc:
                problem=str(exc)
                if row.get('error') is None:row['error']={'type':'diagnostic_validation','message':problem}
            record={'call':count,'id':case['id'],'stage':stage,'fallback':fallback,'result':row,**outcome}
            raw.write(json.dumps(record,ensure_ascii=False)+'\n');raw.flush();os.fsync(raw.fileno());rows.append(record)
            write(f'checkpoint-{count:02}.json',{'records':len(rows),'raw_sha256':sha(out/'raw.jsonl'),'requested_tokens':tokens})
            print(json.dumps({'call':count,'id':case['id'],'stage':stage,'case_error':outcome['case_error'],'systemic_error':problem,'latency':row.get('latency_seconds')}),flush=True)
            require(problem is None,problem)
            return record
        status='complete'
        try:triplets(cases,dispatch)
        except (RuntimeError,OSError,ValueError,KeyError,TypeError) as exc:status=str(exc)
    attempted={(r['id'],r['stage']) for r in rows}
    write('summary.json',{'status':status,'calls':count,'requested_tokens':tokens,'records':len(rows),'case_errors':sum(x['case_error'] for x in rows),'elapsed_seconds':time.monotonic()-started,'utc_end':dt.datetime.now(dt.timezone.utc).isoformat(),'unsent':[{'id':c['id'],'stage':s} for c in cases for s in CAPS if (c['id'],s) not in attempted],'raw_sha256':sha(out/'raw.jsonl'),'request_hashes':{p.name:sha(p) for p in (out/'requests').iterdir()}})
    return 0 if status=='complete' else 1

if __name__=='__main__':raise SystemExit(main())
