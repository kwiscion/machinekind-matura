"""CPU-only matched six-item packages, one shared absolute deadline at declaration."""
import argparse,hashlib,importlib.util,json,shutil,types
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--runtime-root',required=True);a=ap.parse_args()
 prep=load('shared_prepare',HERE.parent/'final-package-prep/prepare_recovery_package.py');source=ROOT/'agentsLog/kwiscion/private/qwen-thinking-six-20260927/package-v6'
 assert prep.n.sha(source/'launch.json')=='9bcca4c5d3b0955fa13e7240d4c0aa94b85e4001ea5d786e0d9c632d562f53c4'
 a.output=a.output.resolve();assert not a.output.exists();a.output.mkdir(parents=True)
 receipts=[]
 for arm in ('gemma','qwen'):
  dest=a.output/arm
  host=str(PurePosixPath(a.runtime_root).parent)
  args=types.SimpleNamespace(exam_dir=source/'exam',output=dest,essay_id=[],no_essay=True,cache=a.runtime_root+'/'+arm+'-models',binary=host+'/runtime/bin/ollama',lock=host+'/matched-worker.lock',minutes=60,inject_faults=False)
  m=prep.prepare(args)
  if arm=='qwen':
   shutil.copyfile(HERE/'closed_profile.py',dest/'closed_profile.py')
   m.update(model_profile='qwen35_9b_thinking_v1',model='qwen3.5:9b',temperature=1,top_p=0.95,top_k=64)
   m['files']['closed_profile.py']=prep.n.sha(dest/'closed_profile.py')
   (dest/'launch.json').write_text(prep.n.line(m),encoding='utf8')
  runner=load('pair_'+arm,dest/'run_recovery_package.py');runner.preflight(dest)
  receipts.append({'arm':arm,'manifest_sha256':prep.n.sha(dest/'launch.json'),'calls':m['max_calls'],'tokens':m['max_requested_tokens']})
 (a.output/'pair.json').write_text(json.dumps({'status':'PREPARED_NOT_AUTHORIZED','shared_deadline_required':True,'max_seconds':3600,'max_calls':48,'max_requested_tokens':1769472,'arms':receipts},indent=2)+'\n')
 print(json.dumps(receipts))
if __name__=='__main__':main()
