"""Thin sequential A/B/referee wave over the frozen owned recovery runtime."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
import policy

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
PREFIX=Path('agentsLog/kwiscion')
PREP=PREFIX/'final-package-prep'
BRANCH=PREFIX/'essay-branching-prep'
WORK=Path('bundle')/PREFIX/'private/branch-wave'
EXAM_SHA='e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6'
PINS={'run_recovery_package.py':'54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392',
      'recovery_harness.py':'628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0',
      'run_native_package.py':'60393fc61705efb8bdeaf8348ac6fd754bc8a4c0ad1efe142b7c6c39846cda6f',
      'closed_profile.py':'953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d'}


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def helper(root):return load('brain_owned_supervisor',root/'bundle'/BRANCH/'staged_wave.py')


def package(root,exam,items,label):
    s=helper(root);b,_=s.modules(root)
    target=root/(label+'-source');target.mkdir()
    b.package(exam,items,root/'original',target/'exam','-brain-'+label)
    return target/'exam'


def prepare_stage(root,source,label,m):
    s=helper(root);p=load('brain_prepare',root/'bundle'/PREP/'prepare_recovery_package.py')
    output=root/WORK/(label+'-runtime')
    sm=p.prepare(SimpleNamespace(exam_dir=source,output=output,essay_id=[],no_essay=True,
        cache=m['execution_root']+'/caches/'+label,binary=m['binary'],lock=m['host_lock']+'.brain-stage',minutes=60,inject_faults=False))
    shutil.copyfile(root/'closed_profile.py',output/'closed_profile.py')
    sm.update(model_profile='qwen35_9b_thinking_v1',model='qwen3.5:9b',temperature=1,top_p=.95,top_k=64)
    sm['files']['closed_profile.py']=s.sha(output/'closed_profile.py')
    (output/'launch.json').write_text(p.n.line(sm),encoding='utf8',newline='\n')
    runner=load('brain_binding',output/'run_recovery_package.py');_,_,cases=runner.preflight(output)
    for case in cases:
        payload,_=runner.r.step(case,0,[],sm['recovery'])
        s.need(payload['model']=='qwen3.5:9b' and payload['options']==dict(num_ctx=65536,num_predict=32768,temperature=1,top_p=.95,top_k=64),'Qwen initial settings')
        s.need(payload['truncate'] is False and payload['shift'] is False,'Complete context required')
    return output


def prepare(reference,root,remote,cache,binary,lock):
    reference=reference.resolve();root=root.resolve()
    repo=HERE.parents[2];s=load('brain_source_supervisor',repo/BRANCH/'staged_wave.py')
    s.need(s.sha(s.__file__)=='a81523fea5798cbf5663e1cadb30cca300d889927728e43a99289271074ae063','Reviewed supervisor pin')
    s.need(not root.exists() and root.resolve().is_relative_to(repo/PREFIX/'private'),'Fresh private output')
    s.need(s.sha(reference/'exam/exam.json')==EXAM_SHA,'Exact corrected original exam')
    for name,digest in PINS.items():s.need(s.sha(reference/name)==digest,'Reference dependency: '+name)
    p=load('brain_source_prepare',repo/PREP/'prepare_recovery_package.py')
    files=set(p.p.SOURCES.values())|{str(PREP/x) for x in ('prepare_recovery_package.py','run_recovery_package.py','recovery_harness.py')}
    files|={str(BRANCH/x) for x in ('branching.py','staged_wave.py')}
    root.mkdir(parents=True)
    for relative in files:
        dest=root/'bundle'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/relative,dest)
    for name in ('wave.py','policy.py'):shutil.copyfile(HERE/name,root/name)
    shutil.copyfile(reference/'closed_profile.py',root/'closed_profile.py')
    shell=(repo/BRANCH/'operator_wave.sh').read_text().replace('staged_wave.py','wave.py')
    (root/'operator_wave.sh').write_text(shell,encoding='utf8',newline='\n')
    shutil.copytree(reference/'exam',root/'original')
    exam=s.read(root/'original/exam.json');items,mapping=policy.drafts(exam)
    m=dict(schema='brainstorm_qwen_v1',status='PREPARED',declared_utc=None,deadline_utc=None,authorization=None,
        execution_root=remote,cache_source=cache,binary=binary,host_lock=lock,max_seconds=3600,max_calls=120,
        max_requested_tokens=4423680,cost_ceiling_usd=3.28,primary_slots=30,selector_reserve_seconds=1200,
        ids=policy.IDS,model='qwen3.5:9b',source_exam_sha256=EXAM_SHA,source_mapping=mapping)
    source=package(root,exam,items,'drafts');stage=prepare_stage(root,source,'drafts',m)
    # Freeze the exact shared dependency closure actually copied into stage1.
    sm=s.read(stage/'launch.json')
    for name,digest in PINS.items():s.need(s.sha(stage/name)==digest,'Prepared closure mismatch: '+name)
    s.need(sm['max_calls']==80 and sm['max_requested_tokens']==2949120,'Draft envelope')
    m['files']={x.relative_to(root).as_posix():s.sha(x) for x in root.rglob('*') if x.is_file()}
    s.write(root/'prepared-wave.json',m);s.write(root/'wave.json',m);verify(root);return m


def verify(root):
    s=helper(root);m=s.read(root/'wave.json');p=s.read(root/'prepared-wave.json')
    s.need({k:v for k,v in m.items() if k not in s.FIELDS}=={k:v for k,v in p.items() if k not in s.FIELDS},'Declaration-only changes')
    s.need(m['schema']=='brainstorm_qwen_v1' and (m['max_seconds'],m['max_calls'],m['max_requested_tokens'])==(3600,120,4423680),'Exact envelope')
    for name,digest in m['files'].items():
        path=root/name;s.need(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink() and s.sha(path)==digest,'Frozen file changed: '+name)
    s.need(s.sha(__file__)==m['files']['wave.py'] and s.sha(policy.__file__)==m['files']['policy.py'],'Executing modules changed')
    return m


def declare_stage(root,stage,m):
    s=helper(root);sm=s.read(stage/'launch.json');s.need(sm['status']=='PREPARED','Fresh stage')
    s.write(stage/'launch.prepared.json',sm)
    sm.update(status='DECLARED',declared_utc=m['declared_utc'],deadline_utc=m['deadline_utc'],authorization=dict(owner='root',reference=m['authorization']['reference'],max_calls=sm['max_calls'],max_requested_tokens=sm['max_requested_tokens'],max_seconds=sm['max_seconds'],above_240k_explicit=True))
    (stage/'launch.json').write_text(json.dumps(sm)+'\n',encoding='utf8',newline='\n')


def qwen_operator(root,m):
    s=helper(root)
    class Operator(s.Operator):
        def stage(self,source,label):
            profile=load('brain_cache_profile',root/'closed_profile.py')
            guard=profile.wrap_guard(load('brain_cache_guard',root/'bundle'/PREP/'guard.py'))
            src=Path(source);inventory=guard.native_inventory(src,guard.CANONICAL)
            dest=root/'caches'/label;dest.mkdir(parents=True,exist_ok=False)
            for row in inventory['files']:
                original=src/row['path'];guard.no_link(original);target=dest/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
                try:os.link(original,target)
                except OSError:shutil.copyfile(original,target)
            result=guard.verify_inventory(dest,inventory)
            s.need(result['counted_bytes']==6594475420 and len(result['files'])==5,'Pinned one-container Qwen')
            s.write(root/(label+'-cache.json'),result)
    return Operator(root,m)


def save_export(root,selected,states,bindings,fallbacks):
    s=helper(root);rows,receipt=policy.export(selected,states,bindings,fallbacks)
    s.write(root/'answers.json',dict(exam_id=s.read(root/'original/exam.json')['exam_id'],answers=rows))
    s.write(root/'selection-receipt.json',receipt)


def recover_drafts(root):
    """CPU-only recovery of durable finals after controller interruption."""
    s=helper(root)
    if (root/'fallbacks.json').exists():return s.read(root/'candidate-bindings.json'),s.read(root/'fallbacks.json')
    first=root/WORK/'drafts-runtime'
    if not (first/'results').exists():return {},{}
    t=s.terminal(first);drafts={x['id']:x['answer'] for x in s.read(t['answers'])['answers']}
    _,bindings,fallbacks=policy.selection_rows(s.read(root/'original/exam.json'),drafts,t['statuses'])
    if not (root/'candidate-bindings.json').exists():s.write(root/'candidate-bindings.json',bindings)
    s.write(root/'fallbacks.json',fallbacks)
    return bindings,fallbacks


def sequence(root,m,operator,clock=time.time):
    s=helper(root);s.write(root/'execution-once.json',dict(started=clock()));fallbacks={};bindings={};outcome='no_terminal_drafts'
    try:
        first=root/WORK/'drafts-runtime';s.need(s.remaining(m,clock())>m['selector_reserve_seconds']+30,'Draft time')
        operator.stage(m['cache_source'],'drafts');declare_stage(root,first,m)
        code=operator.run(first,s.remaining(m,clock())-m['selector_reserve_seconds']);operator.verify_quiet(first)
        t=s.terminal(first);drafts={x['id']:x['answer'] for x in s.read(t['answers'])['answers']}
        s.write(root/'drafts-terminal.json',dict(returncode=code,answers_sha256=s.sha(t['answers']),calls=t['calls'],requested_tokens=t['requested_tokens'],statuses=t['statuses'],stop=t['stop']))
        items,bindings,fallbacks=policy.selection_rows(s.read(root/'original/exam.json'),drafts,t['statuses'])
        s.write(root/'candidate-bindings.json',bindings);s.write(root/'fallbacks.json',fallbacks)
        s.need(code==0 and not t['stop'],'Draft global failure; preserve usable candidates')
        if items:
            s.need(s.remaining(m,clock())>620,'No selector time beyond recovery reserve')
            source=package(root,s.read(root/'original/exam.json'),items,'selector');second=prepare_stage(root,source,'selector',m)
            sm=s.read(second/'launch.json');s.need(t['calls']+sm['max_calls']<=m['max_calls'] and t['requested_tokens']+sm['max_requested_tokens']<=m['max_requested_tokens'],'Combined budget')
            operator.stage(m['cache_source'],'selector');declare_stage(root,second,m)
            s.write(root/'selector-dispatch.json',dict(manifest_sha256=s.sha(second/'launch.json'),candidate_bindings_sha256=s.sha(root/'candidate-bindings.json'),deadline_utc=m['deadline_utc']))
            code=operator.run(second,max(1,s.remaining(m,clock())-20));operator.verify_quiet(second)
            t=s.terminal(second);selected={x['id']:x['answer'] for x in s.read(t['answers'])['answers']}
            s.write(root/'selector-terminal.json',dict(returncode=code,answers_sha256=s.sha(t['answers']),statuses=t['statuses'],stop=t['stop']))
            save_export(root,selected,t['statuses'],bindings,fallbacks);outcome='selected_with_recorded_fallbacks'
        else:save_export(root,{}, {},bindings,fallbacks);outcome='no_eligible_pair_fallbacks'
    except Exception as exc:
        if not fallbacks:
            try:bindings,fallbacks=recover_drafts(root)
            except Exception:pass  # Invalid/missing evidence cannot invent a final.
        if fallbacks and not (root/'answers.json').exists():save_export(root,{}, {},bindings,fallbacks)
        outcome='operational_stop: '+str(exc)
    finally:
        reservations=[]
        for label in ('drafts','selector'):
            ledger=root/WORK/(label+'-runtime/results/engine/events.jsonl')
            if ledger.exists():reservations += [json.loads(x) for x in ledger.read_text().splitlines() if json.loads(x).get('event')=='reserved']
        calls=len(reservations);tokens=sum(x['cap'] for x in reservations)
        s.need(calls<=m['max_calls'] and tokens<=m['max_requested_tokens'],'Executed budget')
        s.write(root/'wave-terminal.json',dict(outcome=outcome,calls=calls,requested_tokens=tokens,deadline_utc=m['deadline_utc'],answers_sha256=s.sha(root/'answers.json') if (root/'answers.json').exists() else None))
    return outcome


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    for name in ('reference','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('execution-root','cache-source','binary','host-lock'):p.add_argument('--'+name,required=True)
    for command in ('check','execute','cleanup','declare'):
        p=sub.add_parser(command);p.add_argument('root',type=Path)
        if command=='execute':p.add_argument('--guarded',action='store_true')
        if command=='declare':
            for name in ('start','deadline','reference'):p.add_argument('--'+name,required=True)
    a=ap.parse_args()
    if a.command=='prepare':
        m=prepare(a.reference,a.output,a.execution_root,a.cache_source,a.binary,a.host_lock);print(json.dumps(dict(status=m['status'],calls=m['max_calls'],tokens=m['max_requested_tokens'])));return
    root=a.root.resolve();s=helper(root)
    if a.command=='cleanup':
        s.cleanup(root)
        # Interrupted controller: use only previously durable saved candidates.
        if not (root/'answers.json').exists() and (root/'execution-once.json').exists():
            bindings,fallbacks=recover_drafts(root)
            if fallbacks:save_export(root,{}, {},bindings,fallbacks)
        return
    m=verify(root)
    if a.command=='check':print('CPU_PREFLIGHT_PASS');return
    if a.command=='declare':
        s.need(m['status']=='PREPARED' and not (root/'execution-once.json').exists(),'Fresh only')
        m.update(status='DECLARED',declared_utc=a.start,deadline_utc=a.deadline,authorization=dict(owner='root',reference=a.reference,max_calls=120,max_requested_tokens=4423680,max_seconds=3600,above_240k_explicit=True))
        s.remaining(m);(root/'wave.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf8',newline='\n');print(s.sha(root/'wave.json'));return
    s.need(os.name=='posix' and str(root)==m['execution_root'],'Exact Linux root');s.remaining(m)
    if not a.guarded:os.execvp('bash',['bash',str(root/'operator_wave.sh'),str(root)])
    parent=Path(f'/proc/{os.getppid()}/cmdline').read_bytes().split(b'\0')
    s.need(Path(os.fsdecode(parent[0])).name=='timeout' and parent[1:3]==[b'--signal=TERM',b'--kill-after=5s'],'Outer guardian')
    s.need(os.fstat(9).st_ino==Path(m['host_lock']).stat().st_ino,'Inherited lock')
    import fcntl
    fcntl.flock(9,fcntl.LOCK_EX|fcntl.LOCK_NB)
    print(sequence(root,m,qwen_operator(root,m)))


if __name__=='__main__':main()
