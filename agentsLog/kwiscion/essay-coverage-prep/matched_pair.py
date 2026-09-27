"""Two source-complete immutable arms using the reviewed recovery CLI and guardian."""
import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sys
import time
import importlib.util

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREFIX = Path('agentsLog/kwiscion')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def helper(root):
    return load('pair_wave', root/'bundle'/PREFIX/'essay-branching-prep/staged_wave.py')


def prepare(exam, item, root, remote, cache, binary, lock):
    exam=exam.resolve();root=root.resolve()
    s = load('pair_source_wave', REPO/PREFIX/'essay-branching-prep/staged_wave.py')
    c = load('pair_suffix', HERE/'coverage_suffix.py')
    s.need(not root.exists(), 'Fresh pair required')
    s.need(root.resolve().is_relative_to(REPO/PREFIX/'private'), 'Private output only')
    p = load('pair_prepare', REPO/s.PREP/'prepare_recovery_package.py')
    files = set(p.p.SOURCES.values()) | {str(s.PREP/x) for x in
        ('prepare_recovery_package.py','run_recovery_package.py','recovery_harness.py','stage_recovery_cache.py')}
    files |= {str(s.BRANCH/x) for x in ('branching.py','staged_wave.py')}
    root.mkdir(parents=True)
    for f in files:
        target=root/'bundle'/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/f,target)
    shutil.copyfile(__file__,root/'matched_pair.py')
    shutil.copyfile(HERE/'coverage_suffix.py',root/'coverage_suffix.py')
    shell=(REPO/s.BRANCH/'operator_wave.sh').read_text().replace('staged_wave.py','matched_pair.py')
    (root/'operator_pair.sh').write_text(shell,encoding='utf8',newline='\n')
    b,_=s.modules(root); original=b.adapter.load_package(exam)
    matches=[x for x in original['exam']['items'] if x['id']==item]
    s.need(len(matches)==1 and len(original['exam']['items'])==1,'Exact single-item original source required')
    m=dict(schema='coverage_matched_pair_v1',status='PREPARED',declared_utc=None,deadline_utc=None,
        authorization=None,execution_root=remote,cache_source=cache,binary=binary,host_lock=lock,
        max_seconds=3600,max_calls=8,max_requested_tokens=294912,cost_ceiling_usd=3.28,
        original_item_id=item,suffix_sha256=c.SUFFIX_SHA256)
    for label in ('control','candidate'):
        target=root/(label+'-source')/'exam';target.mkdir(parents=True)
        for source in b.adapter.package_inputs(original):
            dest=target/source.relative_to(exam);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        if label=='candidate':
            doc=s.read(target/'exam.json');doc['items']=[c.append_to_item(doc['items'][0])]
            (target/'exam.json').write_text(json.dumps(doc,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
        s.prepare_stage(root,target.parent,label,m)
    stages=[root/s.WORK/(x+'-runtime') for x in ('control','candidate')]
    a,brows=[s.read(x/'launch.json') for x in stages]
    s.need(a['ids']==brows['ids']==[item] and a['max_calls']==brows['max_calls']==4,'Matched IDs/budgets')
    for key in ('model','context','think','temperature','recovery','essay_policy_sha256'):
        s.need(a[key]==brows[key], 'Settings differ: '+key)
    m['files']={x.relative_to(root).as_posix():s.sha(x) for x in root.rglob('*') if x.is_file()}
    s.write(root/'prepared-wave.json',m);s.write(root/'wave.json',m);verify(root);return m


def verify(root):
    s=helper(root);m=s.read(root/'wave.json');p=s.read(root/'prepared-wave.json')
    s.need({k:v for k,v in m.items() if k not in s.FIELDS}=={k:v for k,v in p.items() if k not in s.FIELDS},'Declaration-only changes')
    s.need(m['schema']=='coverage_matched_pair_v1' and (m['max_seconds'],m['max_calls'],m['max_requested_tokens'])==(3600,8,294912),'Pair envelope')
    for name,digest in m['files'].items():
        path=root/name;s.need(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink() and s.sha(path)==digest,'Frozen file changed: '+name)
    s.need(s.sha(__file__)==m['files']['matched_pair.py'],'Executing controller changed')
    return m


def sequence(root,m,operator,clock=time.time):
    s=helper(root);s.write(root/'execution-once.json',{'started':clock()});results=[]
    try:
        for index,label in enumerate(('control','candidate')):
            stage=root/s.WORK/(label+'-runtime')
            s.need(s.remaining(m,clock())>620,'No initial window beyond recovery reserve')
            operator.stage(m['cache_source'],label);s.declare_stage(root,stage,m)
            budget=s.remaining(m,clock())-20
            # The first arm cannot consume the second arm's entire window.
            if index==0:budget=min(budget,budget/2)
            code=operator.run(stage,max(1,budget));operator.verify_quiet(stage)
            result=s.terminal(stage)
            results.append(dict(arm=label,returncode=code,calls=result['calls'],requested_tokens=result['requested_tokens'],answers_sha256=s.sha(result['answers']),statuses=result['statuses'],stop=result['stop']))
            s.write(root/(label+'-terminal.json'),results[-1])
            # Ownership/integrity failures raise; ordinary model errors remain
            # per-answer evidence and do not invent a successful candidate.
    finally:
        reservations=[]
        for label in ('control','candidate'):
            p=root/s.WORK/(label+'-runtime/results/engine/events.jsonl')
            if p.exists():reservations += [json.loads(x) for x in p.read_text().splitlines() if json.loads(x).get('event')=='reserved']
        calls=len(reservations);tokens=sum(x['cap'] for x in reservations)
        s.need(calls<=8 and tokens<=294912,'Executed aggregate budget')
        s.write(root/'pair-terminal.json',dict(stages=results,calls=calls,requested_tokens=tokens,deadline_utc=m['deadline_utc']))
    return results


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    for name in ('exam-dir','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('item-id','execution-root','cache-source','binary','host-lock'):p.add_argument('--'+name,required=True)
    for command in ('check','execute','cleanup','declare'):
        p=sub.add_parser(command);p.add_argument('root',type=Path)
        if command=='execute':p.add_argument('--guarded',action='store_true')
        if command=='declare':
            for name in ('start','deadline','reference'):p.add_argument('--'+name,required=True)
    a=ap.parse_args()
    if a.command=='prepare':
        prepare(a.exam_dir,a.item_id,a.output,a.execution_root,a.cache_source,a.binary,a.host_lock);print('PREPARED');return
    root=a.root.resolve();s=helper(root)
    if a.command=='cleanup':s.cleanup(root);return
    m=verify(root)
    if a.command=='check':print('CPU_PREFLIGHT_PASS');return
    if a.command=='declare':
        s.need(m['status']=='PREPARED' and not (root/'execution-once.json').exists(),'Fresh only')
        m.update(status='DECLARED',declared_utc=a.start,deadline_utc=a.deadline,authorization=dict(owner='root',reference=a.reference,max_calls=8,max_requested_tokens=294912,max_seconds=3600,above_240k_explicit=True))
        s.remaining(m);(root/'wave.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf8',newline='\n');print(s.sha(root/'wave.json'));return
    s.need(os.name=='posix' and str(root)==m['execution_root'],'Exact Linux root');s.remaining(m)
    if not a.guarded:os.execvp('bash',['bash',str(root/'operator_pair.sh'),str(root)])
    parent=Path(f'/proc/{os.getppid()}/cmdline').read_bytes().split(b'\0')
    s.need(Path(os.fsdecode(parent[0])).name=='timeout' and parent[1:3]==[b'--signal=TERM',b'--kill-after=5s'],'Outer guardian required')
    s.need(os.fstat(9).st_ino==Path(m['host_lock']).stat().st_ino,'Inherited lock')
    import fcntl
    fcntl.flock(9,fcntl.LOCK_EX|fcntl.LOCK_NB)
    print(json.dumps(sequence(root,m,s.Operator(root,m))))


if __name__=='__main__':main()
