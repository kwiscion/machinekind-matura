"""Stage only pinned Gemma native cache members; CPU/file operation, no runtime."""
import argparse,importlib.util,os,shutil,json
from pathlib import Path
s=importlib.util.spec_from_file_location('stage_guard',Path(__file__).with_name('guard.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def stage(source,dest):
 source=source.resolve();g.require(not dest.exists() and not dest.is_symlink(),'Fresh destination required')
 # Native manifest digest fixes exact referenced members; development extras in
 # source are never copied. Destination inventory is strict and includes metadata.
 inventory=g.native_inventory(source,g.CANONICAL);dest.mkdir(parents=True)
 for row in inventory['files']:
  original=g.no_link(source/row['path']);target=dest/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
  try:os.link(source/row['path'],target)
  except OSError:shutil.copyfile(source/row['path'],target)
 report=g.verify_inventory(dest,inventory)
 return {'inventory':inventory,'report':report}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 g.require(not a.report.exists() and not a.report.resolve().is_relative_to(a.destination.resolve()),'Fresh report outside cache')
 result=stage(a.source,a.destination)
 with a.report.open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
 print(json.dumps({'status':'PASS','counted_bytes':result['report']['counted_bytes'],'model_calls':0}))
if __name__=='__main__':main()
