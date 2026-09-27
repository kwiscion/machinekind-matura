"""Fresh derivative of the exact preserved V2 package; no remote execution."""
import argparse,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
V2_MANIFEST='be90e608eb10965f657c1e350bce6c1570265d03da71a8b23b6d772e02a6e53d'
PROFILE='953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(source,out):
 assert sha(source/'launch.json')==V2_MANIFEST
 assert not out.exists();out.mkdir(parents=True)
 m=json.loads((source/'launch.json').read_text())
 for name,digest in m['files'].items():
  assert sha(source/name)==digest,name
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dest)
 shutil.copyfile(source/'launch.json',out/'v2-prepared.json')
 profile=HERE.parent/'qwen-thinking-prep/closed_profile.py';assert sha(profile)==PROFILE
 for src in (profile,HERE/'fast_hook.py',HERE/'prepare.py'):
  shutil.copyfile(src,out/src.name)
 binding=out/'run_recovery_package.py';code=binding.read_text(encoding='utf8')
 old="study_hook=load('filtered_rag_hook_v2',root/'study_hook_v2.py')"
 assert code.count(old)==1
 binding.write_text(code.replace(old,"study_hook=load('fast_rag_hook',root/'fast_hook.py')"),encoding='utf8',newline='\n')
 m.update(model_profile='qwen35_9b_thinking_v1',model='qwen3.5:9b',temperature=1,top_p=0.95,top_k=64,
          cache='/home/shadeform/machinekind-matura-pawel-20260927/fast-qwen-rag-v1/qwen-cache')
 m['auxiliary_budget']={'query_initial':512,'judge_initial':384,'retry':1024,'think':False,
   'actual_max_requested_tokens':12*(32768*3+49152)+8*(512+3*1024)+32*(384+3*1024),
   'primary_slots':52,'max_attempts':208,'absolute_terminal_utc':'2026-09-27T07:05:00.000000+00:00'}
 m['files']={f.relative_to(out).as_posix():sha(f) for f in out.rglob('*') if f.is_file()}
 (out/'launch.json').write_text(json.dumps(m,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
 sys.path.insert(0,str(out));sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('fast_preflight',binding);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.preflight(out)
 return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 m=prepare(a.source.resolve(),a.output.resolve());print(json.dumps({'status':'PREPARED_NOT_DISPATCHED','sha256':sha(a.output/'launch.json'),'budget':m['auxiliary_budget']}))
