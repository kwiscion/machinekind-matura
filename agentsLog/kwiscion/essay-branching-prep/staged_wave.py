"""Two sequential immutable recovery packages; dry preparation unless --execute.

This controller owns no model transport. The frozen recovery CLI owns each
namespace, server, retry ledger and cleanup. All outputs are diagnostic only.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREFIX = Path('agentsLog/kwiscion')
PREP = PREFIX/'final-package-prep'
BRANCH = PREFIX/'essay-branching-prep'
WORK = Path('bundle')/PREFIX/'private/branch-wave'
FIELDS = {'status', 'declared_utc', 'deadline_utc', 'authorization'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def need(ok, reason):
    if not ok: raise ValueError(reason)


def write(path, value):
    # Exclusive creates are the durable no-replay boundary.
    with Path(path).open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
        f.flush(); os.fsync(f.fileno())


def modules(root):
    bundle = root/'bundle'
    b = load('wave_builder', bundle/BRANCH/'branching.py')
    p = load('wave_prepare', bundle/PREP/'prepare_recovery_package.py')
    return b, p


def prepare_stage(root, source, label, m):
    b, p = modules(root)
    ids = [x['id'] for x in b.adapter.load_package(source/'exam')['exam']['items']]
    output = root/WORK/(label+'-runtime')
    args = SimpleNamespace(exam_dir=source/'exam', output=output, essay_id=ids,
        no_essay=False, cache=m['execution_root']+'/caches/'+label,
        binary=m['binary'], lock=m['host_lock']+'.branch-stage', minutes=60,
        inject_faults=False)
    p.prepare(args)
    return output


def prepare(exam, item, output, execution_root, cache_source, binary, host_lock):
    repo = HERE.parents[2]
    need(not output.exists(), 'Fresh wave directory required')
    need(output.resolve().is_relative_to(repo/PREFIX/'private'), 'Private output required')
    for value in (execution_root, cache_source, binary, host_lock):
        need(isinstance(value, str) and value.startswith('/') and '\n' not in value,
             'Absolute Linux execution paths required')
    source_p = load('wave_source_prepare', repo/PREP/'prepare_recovery_package.py')
    files = set(source_p.p.SOURCES.values()) | {
        str(PREP/x) for x in ('prepare_recovery_package.py', 'run_recovery_package.py',
                              'recovery_harness.py', 'stage_recovery_cache.py')}
    files |= {str(BRANCH/'branching.py')}
    output.mkdir(parents=True)
    for relative in files:
        target = output/'bundle'/relative; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo/relative, target)
    shutil.copyfile(__file__, output/'staged_wave.py')
    shutil.copyfile(HERE/'operator_wave.sh', output/'operator_wave.sh')
    b, _ = modules(output)
    first = b.stage1(exam, item, output/'drafts-source')
    m = dict(schema='essay_branching_wave_v1', status='PREPARED', declared_utc=None,
        deadline_utc=None, authorization=None, execution_root=execution_root,
        cache_source=cache_source, binary=binary, host_lock=host_lock,
        max_seconds=3600, max_calls=first['max_attempts_entire_wave'],
        max_requested_tokens=first['max_requested_tokens_entire_wave'],
        primary_slots=first['primary_calls_entire_wave'], cost_ceiling_usd=3.28,
        selector_reserve_seconds=900, stage1_manifest_sha256=sha(output/'drafts-source/branching-manifest.json'))
    prepare_stage(output, output/'drafts-source', 'drafts', m)
    m['files'] = {x.relative_to(output).as_posix(): sha(x) for x in output.rglob('*') if x.is_file()}
    write(output/'prepared-wave.json', m); write(output/'wave.json', m)
    verify(output)
    return m


def verify(root):
    m = read(root/'wave.json'); prepared = read(root/'prepared-wave.json')
    need({k:v for k,v in m.items() if k not in FIELDS} ==
         {k:v for k,v in prepared.items() if k not in FIELDS}, 'Only declaration fields may change')
    need(m['schema']=='essay_branching_wave_v1' and m['max_seconds']==3600, 'Wave contract')
    for relative, digest in m['files'].items():
        target = root/relative
        need(target.resolve().is_relative_to(root.resolve()) and not target.is_symlink() and sha(target)==digest,
             'Frozen wave file changed: '+relative)
    need(sha(__file__)==m['files']['staged_wave.py'], 'Executing controller changed')
    b, _ = modules(root); first = b.verify(root/'drafts-source')
    need(m['max_calls']==first['max_attempts_entire_wave'] and
         m['max_requested_tokens']==first['max_requested_tokens_entire_wave'], 'Exact total envelope')
    return m


def remaining(m, now=None):
    now = time.time() if now is None else now
    for key in ('declared_utc','deadline_utc'):
        need(isinstance(m.get(key),str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00',m[key]),
             'UTC +00:00 timestamps with at most six fractional digits required for Python3.10')
    start = dt.datetime.fromisoformat(m['declared_utc']); end = dt.datetime.fromisoformat(m['deadline_utc'])
    need(start.utcoffset()==end.utcoffset()==dt.timedelta(0), 'Aware UTC required')
    need(m['status']=='DECLARED' and start.timestamp()<=now<end.timestamp() and
         0<(end-start).total_seconds()<=3600, 'Live common declaration required')
    a=m['authorization']
    need(isinstance(a,dict) and a.get('owner')=='root' and a.get('reference') and
         all(a.get(k)==m[k] for k in ('max_calls','max_requested_tokens','max_seconds')) and
         a.get('above_240k_explicit') is True, 'Exact root authorization required')
    return end.timestamp()-now


def declare_stage(root, stage, m):
    sm=read(stage/'launch.json')
    need(sm['status']=='PREPARED', 'Stage already declared')
    sm.update(status='DECLARED',declared_utc=m['declared_utc'],deadline_utc=m['deadline_utc'],
        authorization=dict(owner='root',reference=m['authorization']['reference'],
            max_calls=sm['max_calls'],max_requested_tokens=sm['max_requested_tokens'],
            max_seconds=sm['max_seconds'],above_240k_explicit=True))
    b,_=modules(root);b.common_deadline(m,sm)
    # Prepared copy is preserved. The only stage mutation is declaration fields.
    write(stage/'launch.prepared.json',read(stage/'launch.json'))
    (stage/'launch.json').write_text(json.dumps(sm,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    return sm


def terminal(stage):
    m=read(stage/'launch.json'); out=stage/'results'
    runner=load('wave_terminal',stage/'run_recovery_package.py')
    runner.verify(stage,m)
    # Recover durable engine candidates after an interrupted stage supervisor.
    # This is the existing CPU export path, never a model call or new answer.
    if out.exists():
        package=runner.modules(stage)[3].load_package(stage/'exam')
        cases=runner.modules(stage)[4].load_cases(stage/'input.jsonl',len(m['ids']))
        for case in cases:case['kind']='essay' if case['id'] in m['essay_ids'] else 'ordinary'
        runner.final_export(stage,m,cases,package)
    doc=runner.validate_final(out/'answers.json',read(stage/'exam/answers-template.json'))
    status=read(out/'engine/answer-status.json'); receipt=read(out/'terminal.json')
    events=[json.loads(x) for x in (out/'engine/events.jsonl').read_text(encoding='utf8').splitlines()] if (out/'engine/events.jsonl').exists() else []
    reserved=[x for x in events if x['event']=='reserved']
    need(receipt['answers_sha256']==sha(out/'answers.json') and receipt['calls']==len(reserved) and
         receipt['requested_tokens']==sum(x['cap'] for x in reserved), 'Terminal/ledger mismatch')
    need(receipt['calls']<=m['max_calls'] and receipt['requested_tokens']<=m['max_requested_tokens'], 'Stage budget exceeded')
    need(set(status['items'])=={x['id'] for x in doc['answers']}, 'Exact status IDs')
    return dict(answers=out/'answers.json', statuses=status['items'], stop=status.get('stop'),
                calls=receipt['calls'], requested_tokens=receipt['requested_tokens'])


def ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]


def stop_group(record):
    try:
        need(ticks(record['pid'])==record['ticks'] and os.getpgid(record['pid'])==record['pid'], 'Owned stage group identity')
        os.killpg(record['pid'],signal.SIGKILL)
    except (FileNotFoundError,ProcessLookupError): pass


def cleanup(root):
    # Called by both the controller and outer guardian, including hard interruption.
    receipt=root/'active-stage.json'
    if not receipt.exists(): return
    record=read(receipt); stage=root/record['relative']
    need(stage.resolve().is_relative_to((root/WORK).resolve()), 'Owned stage path')
    if record.get('pid') is not None:stop_group(record)
    # The reviewed runner creates a separate session for its namespace child.
    # Stop only this exact immutable package's execute controllers before asking
    # its existing helper to stop the recorded server/backend. No /proc exe/ns
    # reads across user namespaces and no broad same-user runtime sweep.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid(): continue
        try:
            if proc.stat().st_uid!=os.getuid(): continue
            args=(proc/'cmdline').read_bytes().split(b'\0')
            if os.fsencode(str(stage/'run_recovery_package.py')) in args and b'--execute' in args:
                pid=int(proc.name); stamp=ticks(pid)
                need(ticks(pid)==stamp,'Stage controller identity changed')
                os.kill(pid,signal.SIGKILL)
        except (FileNotFoundError,ProcessLookupError): pass
    if (stage/'results/network-proof.json').exists():
        subprocess.run([sys.executable,'-B',str(stage/'run_recovery_package.py'),str(stage),'--cleanup'],
                       check=True,timeout=7)


class Operator:
    def __init__(self,root,m): self.root=root;self.m=m
    def stage(self,source,label):
        stage=load('wave_cache',self.root/'bundle'/PREP/'stage_recovery_cache.py')
        result=stage.stage(Path(source),self.root/'caches'/label)
        write(self.root/(label+'-cache.json'),result)
    def run(self,package,limit):
        child=None
        try:
            # Durable intent precedes spawn, closing the interruption gap before
            # PID/start-ticks capture. Cleanup can match the exact package argv.
            active=self.root/'active-stage.json';tmp=self.root/'active-stage.next.json'
            write(tmp,dict(pid=None,ticks=None,relative=package.relative_to(self.root).as_posix()))
            os.replace(tmp,active)
            with (self.root/(package.name+'.log')).open('xb') as log:
                child=subprocess.Popen([sys.executable,'-B',str(package/'run_recovery_package.py'),str(package),'--execute'],
                                       stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                record=dict(pid=child.pid,ticks=ticks(child.pid),relative=package.relative_to(self.root).as_posix())
                # Previous terminal receipt stays in the per-stage dispatch evidence.
                write(tmp,record);os.replace(tmp,active)
                try: code=child.wait(timeout=limit)
                except subprocess.TimeoutExpired: code=124
        finally:
            try:
                if child is not None and child.poll() is None:
                    # Still our unreaped Popen child even if PID receipt failed.
                    os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
            finally:cleanup(self.root)
        return code
    def verify_quiet(self,package):
        # Same reviewed recorded-identity cleanup; no new inference/service probe.
        cleanup(self.root)


def sequence(root,m,operator,clock=time.time):
    """Inject only a CPU fake operator in tests; production always uses Operator."""
    write(root/'execution-once.json',dict(wave_sha256=sha(root/'wave.json'),started_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    b,_=modules(root); first=root/'drafts-source'; one=root/WORK/'drafts-runtime'
    used_calls=used_tokens=0; control=None; outcome=None
    try:
        remaining(m,clock());operator.stage(m['cache_source'],'drafts')
        declare_stage(root,one,m)
        write(root/'drafts-dispatch.json',dict(manifest_sha256=sha(one/'launch.json'),deadline_utc=m['deadline_utc']))
        limit=remaining(m,clock())-m['selector_reserve_seconds']
        need(limit>0,'No draft window after selector reserve')
        code=operator.run(one,limit);operator.verify_quiet(one)
        t=terminal(one);control=t;used_calls+=t['calls'];used_tokens+=t['requested_tokens']
        write(root/'drafts-terminal.json',dict(returncode=code,calls=t['calls'],requested_tokens=t['requested_tokens'],answers_sha256=sha(t['answers']),statuses=t['statuses']))
        need(code==0 and not t['stop'],'Draft stage failed; retain baseline')
        need(remaining(m,clock())>600,'No selection initial window beyond recovery reserve')
        two_source=root/'selector-source'
        b.selector(first,t['answers'],sha(t['answers']),two_source,statuses=t['statuses'])
        two=prepare_stage(root,two_source,'selector',m)
        # Fresh metadata view after verified prior cleanup; identical pinned weight set.
        operator.stage(m['cache_source'],'selector');declare_stage(root,two,m)
        sm=read(two/'launch.json')
        need(used_calls+sm['max_calls']<=m['max_calls'] and used_tokens+sm['max_requested_tokens']<=m['max_requested_tokens'],'Aggregate remaining budget')
        write(root/'selector-dispatch.json',dict(manifest_sha256=sha(two/'launch.json'),deadline_utc=m['deadline_utc'],source_manifest_sha256=sha(two_source/'branching-manifest.json')))
        code=operator.run(two,max(1,remaining(m,clock())-20));operator.verify_quiet(two)
        t=terminal(two);used_calls+=t['calls'];used_tokens+=t['requested_tokens']
        write(root/'selector-terminal.json',dict(returncode=code,calls=t['calls'],requested_tokens=t['requested_tokens'],answers_sha256=sha(t['answers']),statuses=t['statuses']))
        state=t['statuses'][b.verify(first)['original_item_id']]
        need(code==0 and not t['stop'] and not state['placeholder'] and not state['incomplete_partial'],'Selector incomplete/failed; retain baseline')
        b.export_final(first,two_source,t['answers'],sha(t['answers']),root/'answers.json')
        outcome=dict(mode='same_model_selected',submitted_status=state)
    except Exception as exc:
        if control is None and (one/'results').exists():
            try:control=terminal(one)
            except Exception:pass  # Missing or invalid evidence cannot become an answer.
        if control is not None:
            b.baseline_fallback(first,control['answers'],sha(control['answers']),root/'answers.json','selector_runtime_failed')
            outcome=dict(mode='direct_baseline_fallback',submitted_status=control['statuses']['branch-control'],reason=str(exc))
        else: outcome=dict(mode='no_terminal_control',reason=str(exc))
    finally:
        # Recount durable reservations even when cleanup or terminal validation
        # interrupted a stage before its receipt could be consumed.
        reservations=[]
        for label in ('drafts','selector'):
            ledger=root/WORK/(label+'-runtime')/'results/engine/events.jsonl'
            if ledger.exists():
                reservations += [json.loads(x) for x in ledger.read_text(encoding='utf8').splitlines() if json.loads(x).get('event')=='reserved']
        used_calls=len(reservations);used_tokens=sum(x['cap'] for x in reservations)
        need(used_calls<=m['max_calls'] and used_tokens<=m['max_requested_tokens'],'Aggregate executed budget')
        write(root/'wave-terminal.json',dict(outcome=outcome,calls=used_calls,requested_tokens=used_tokens,
            deadline_utc=m['deadline_utc'],answers_sha256=sha(root/'answers.json') if (root/'answers.json').exists() else None))
    return outcome


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    for k in ('exam-dir','output'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('item-id','execution-root','cache-source','binary','host-lock'):p.add_argument('--'+k,required=True)
    for command in ('check','execute','cleanup'):
        p=sub.add_parser(command);p.add_argument('root',type=Path)
        if command=='execute':p.add_argument('--guarded',action='store_true')
    p=sub.add_parser('declare');p.add_argument('root',type=Path)
    for k in ('reference','start','deadline'):p.add_argument('--'+k,required=True)
    a=ap.parse_args()
    if a.command=='prepare':
        m=prepare(a.exam_dir,a.item_id,a.output,a.execution_root,a.cache_source,a.binary,a.host_lock)
        print(json.dumps(dict(status='PREPARED',max_calls=m['max_calls'],max_requested_tokens=m['max_requested_tokens'])));return
    root=a.root.resolve()
    if a.command=='cleanup':
        cleanup(root)
        if (root/'execution-once.json').exists() and not (root/'wave-terminal.json').exists() and not (root/'guardian-terminal.json').exists():
            b,_=modules(root);one=root/WORK/'drafts-runtime';outcome={'mode':'no_terminal_control','reason':'Outer guardian interruption'}
            try:
                t=terminal(one)
                if not (root/'answers.json').exists():
                    b.baseline_fallback(root/'drafts-source',t['answers'],sha(t['answers']),root/'answers.json','budget_exhausted')
                    outcome=dict(mode='direct_baseline_fallback',reason='Outer guardian interruption',submitted_status=t['statuses']['branch-control'])
                else:
                    outcome=dict(mode='existing_export_preserved',reason='Interrupted between answer export and wave receipt; no new selection claim')
            except Exception as exc:outcome['evidence_error']=str(exc)
            write(root/'guardian-terminal.json',dict(outcome=outcome,answers_sha256=sha(root/'answers.json') if (root/'answers.json').exists() else None,
                accounting='Per-stage durable reservation ledgers remain authoritative; wave supervisor interrupted'))
        return
    m=verify(root)
    if a.command=='check':print(json.dumps(dict(status='CPU_PREFLIGHT_PASS',model_calls=0)));return
    if a.command=='declare':
        need(m['status']=='PREPARED' and not (root/'execution-once.json').exists(),'Fresh prepared wave only')
        m.update(status='DECLARED',declared_utc=a.start,deadline_utc=a.deadline,
            authorization=dict(owner='root',reference=a.reference,max_calls=m['max_calls'],
                max_requested_tokens=m['max_requested_tokens'],max_seconds=m['max_seconds'],above_240k_explicit=True))
        remaining(m)
        (root/'wave.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
        print(json.dumps(dict(status='DECLARED_NOT_EXECUTED',wave_sha256=sha(root/'wave.json'))));return
    need(os.name=='posix' and str(root)==m['execution_root'],'Exact Linux execution root')
    remaining(m)
    if not a.guarded:os.execvp('bash',['bash',str(root/'operator_wave.sh'),str(root)])
    parent=Path(f'/proc/{os.getppid()}/cmdline').read_bytes().split(b'\0')
    need(Path(os.fsdecode(parent[0])).name=='timeout' and parent[1:3]==[b'--signal=TERM',b'--kill-after=5s'],'Outer guardian required')
    # The shell owns the shared host flock on inherited FD9 throughout both stages.
    need(os.fstat(9).st_ino==Path(m['host_lock']).stat().st_ino,'Inherited host lock')
    import fcntl
    fcntl.flock(9,fcntl.LOCK_EX|fcntl.LOCK_NB)
    outcome=sequence(root,m,Operator(root,m))
    print(json.dumps(outcome));return 0 if outcome['mode']=='same_model_selected' else 2


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('STOP: '+str(exc),file=sys.stderr);sys.exit(2)
