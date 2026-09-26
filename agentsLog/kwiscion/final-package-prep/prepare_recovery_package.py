"""Prepare the reusable champion recovery package; no execution or network."""
import argparse,json,shutil,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepare_native',HERE/'prepare_native_package.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
n=p.runner

def prepare(a):
 # Reuse actual organizer adapter and complete source staging before changing the
 # execution envelope. The original prepared manifest remains explicit evidence.
 m=p.prepare(a.exam_dir,a.output,essay_ids=a.essay_id or [],no_essay=a.no_essay,cache=a.cache,binary=a.binary,lock=a.lock,max_seconds=a.minutes*60,request_timeout=420)
 root=a.output.resolve();shutil.copyfile(root/'launch.json',root/'native-prepared.json')
 for name in ('run_recovery_package.py','recovery_harness.py','prepare_recovery_package.py'):
  shutil.copyfile(HERE/name,root/name)
 guardian=p.guardian(a.minutes*60).replace('operator_native.sh','operator_recovery.sh').replace('run_native_package.py','run_recovery_package.py')
 (root/'operator_recovery.sh').write_text(guardian,encoding='utf8',newline='\n')
 module=n.load('prepared_recovery',root/'recovery_harness.py');rows=n.rows(root/'input.original.jsonl')
 faults={}
 if a.inject_faults:
  eligible=sorted((x for x in rows if x['id'] not in m['essay_ids']),key=lambda x:(len(x['prompt']),x['id']))
  n.need(len(eligible)>=2,'Two ordinary items needed for injection');faults={eligible[0]['id']:'timeout',eligible[1]['id']:'length'}
 m.update(schema='champion_recovery_v1',context=65536,retries=3,max_calls=len(rows)*4,max_requested_tokens=len(rows)*(32768*3+49152),recovery=module.config(a.minutes),faults=faults)
 m['files']={path.relative_to(root).as_posix():n.sha(path) for path in root.rglob('*') if path.is_file() and path.name!='launch.json'}
 (root/'launch.json').write_text(n.line(m),encoding='utf8',newline='\n')
 runner=n.load('prepared_recovery_binding',root/'run_recovery_package.py');runner.preflight(root)
 return m

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--exam-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 group=ap.add_mutually_exclusive_group(required=True);group.add_argument('--essay-id',action='append');group.add_argument('--no-essay',action='store_true')
 for k in ('cache','binary','lock'):ap.add_argument('--'+k,required=True)
 ap.add_argument('--minutes',type=int,choices=(60,120),default=60);ap.add_argument('--inject-faults',action='store_true')
 a=ap.parse_args();m=prepare(a);print(json.dumps({'status':'PREPARED','calls':m['max_calls'],'tokens':m['max_requested_tokens'],'faults':m['faults'],'manifest_sha256':n.sha(a.output/'launch.json')}))
if __name__=='__main__':main()
