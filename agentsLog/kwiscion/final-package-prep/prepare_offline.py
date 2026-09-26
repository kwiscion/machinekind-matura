"""Build a fresh private portable qualification package; no remote/model operations."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[3]
FILES={'run_gemma_offline.py':'agentsLog/kwiscion/final-package-prep/run_gemma_offline.py','guard.py':'agentsLog/kwiscion/final-package-prep/guard.py','offline_rehearsal.py':'agentsLog/kwiscion/offline_rehearsal.py','infer.py':'infer.py','scripts/Bukareszt/matura_package.py':'scripts/Bukareszt/matura_package.py','agentsLog/Bukareszt/submission/fixtures/tiny-package/images/fixture-red.png':'agentsLog/Bukareszt/submission/fixtures/tiny-package/images/fixture-red.png'}
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--cache',required=True);p.add_argument('--binary',required=True);p.add_argument('--lock',required=True);a=p.parse_args()
 out=a.output.resolve();private=ROOT/'agentsLog/kwiscion/private';assert out.is_relative_to(private.resolve()) and not out.exists();out.mkdir(parents=True)
 hashes={}
 for dst,src in FILES.items():
  target=out/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/src,target);hashes[dst]=hashlib.sha256(target.read_bytes()).hexdigest()
 m={'schema':'final_offline_two_v1','status':'PREPARED','declared_utc':None,'deadline_utc':None,'max_calls':2,'max_output_tokens':20480,'max_seconds':1200,'request_timeout':420,'think':True,'temperature':'omitted','context':32768,'retries':0,'cache':a.cache,'binary':a.binary,'lock':a.lock,'files':hashes}
 (out/'launch.json').write_text(json.dumps(m,indent=2)+'\n');print(out)
if __name__=='__main__':main()
