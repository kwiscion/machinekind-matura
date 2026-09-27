"""Pre-acquisition dedicated five-member cache and full immutable DB staging."""
import hashlib,importlib.util,json,os,shutil,subprocess,datetime,socket
from pathlib import Path
B=Path('/home/shadeform/machinekind-matura-pawel-20260927');OUT=B/'manual-final-stage'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True);assert not gpu.strip(),gpu
 assert not OUT.exists(),'Fresh staged root required';OUT.mkdir()
 src=B/'fast-qwen-rag-v1'
 stage=load('manual_qwen_stage',src/'qwen-thinking-prep/stage_qwen_cache.py')
 weights=stage.stage(B/'models-stage',OUT/'models-base')
 index=OUT/'wiki/passages.sqlite';index.parent.mkdir();shutil.copyfile(B/'full-wikipedia/corpus/passages.sqlite',index)
 assert index.stat().st_size==10464555008 and sha(index)=='5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36'
 index.chmod(0o444);s=index.stat()
 proof=dict(schema='pre_acquisition_full_index_v1',index_path=str(index),sha256=sha(index),bytes=s.st_size,
  stat={k:getattr(s,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')},hostname=socket.gethostname(),
  boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  immutable_assumption='Dedicated copied read-only DB; all final retrieval must use mode=ro&immutable=1; no writers or replacements')
 (OUT/'index-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
 (OUT/'weights-proof.json').write_text(json.dumps(weights,indent=2)+'\n')
 print(json.dumps({'status':'STAGED','index':proof,'model_bytes':weights['report']['counted_bytes'],'gpu_before':gpu,'model_calls':0}))
if __name__=='__main__':main()
