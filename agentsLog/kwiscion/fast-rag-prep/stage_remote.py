"""Stage fresh pinned Qwen-only development cache; never starts a service."""
import datetime,hashlib,importlib.util,json,subprocess,sys,tarfile
from pathlib import Path
BASE=Path('/home/shadeform/machinekind-matura-pawel-20260927')
TARGET=BASE/'fast-qwen-rag-v1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 archive=BASE/'fast-qwen-rag-v1.tar.gz';assert sha(archive)==sys.argv[1]
 assert not TARGET.exists()
 gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True);assert not gpu.strip(),gpu
 processes=subprocess.check_output(['ps','-eo','pid,comm,args'],text=True)
 workers=[x for x in processes.splitlines() if len(x.split())>2 and x.split()[1].startswith('python') and any(Path(a).name in ('run_recovery_package.py','run_gemma_package.py','infer.py') for a in x.split()[2:])];assert not workers,workers
 TARGET.mkdir()
 with tarfile.open(archive) as t:
  for member in t.getmembers():
   p=Path(member.name);assert not p.is_absolute() and '..' not in p.parts and not member.issym() and not member.islnk() and (member.isfile() or member.isdir())
  t.extractall(TARGET)
 p=TARGET/'package-v1';assert sha(p/'launch.json')=='6f8f146da995c9bc82190c17e2a7939e42fc1482e6e405095ac4575aebf87889'
 stage=load('qwen_stage',TARGET/'qwen-thinking-prep/stage_qwen_cache.py')
 report=stage.stage(BASE/'models-stage',TARGET/'qwen-cache')
 assert sha(BASE/'runtime/bin/ollama')=='ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4'
 preflight=subprocess.run(['python3','-B',str(p/'run_recovery_package.py'),str(p)],capture_output=True,text=True);assert preflight.returncode==0,preflight.stderr
 receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='microseconds'),'archive_sha256':sha(archive),'manifest_sha256':sha(p/'launch.json'),'cache':report,'gpu_before':gpu,'workers_before':workers,'preflight':preflight.stdout,'model_calls':0,'services_started':0}
 (TARGET/'stage-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':main()
