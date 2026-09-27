"""Prepare one48-stage complete-source full-Wikipedia filtered retrieval study."""
import argparse,copy,importlib.util,json,shutil,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('rag_prepare',HERE.parent/'final-package-prep/prepare_recovery_package.py');n=p.n
INDEX_SHA='5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36'
BINDING_SHA='54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392'

def prepare(a):
 source=a.exam_dir.resolve();out=a.output.resolve();expanded=out.with_name(out.name+'-expanded-source')
 n.need(not expanded.exists() and not out.exists(),'Fresh outputs')
 adapter=n.load('rag_adapter',REPO/'scripts/Bukareszt/matura_package.py');package=adapter.load_package(source)
 n.need(len(package['exam']['items'])==6,'Exactly six declared source items')
 expanded.mkdir(parents=True)
 for file in adapter.package_inputs(package):
  if file.name in ('exam.json','answers-template.json'):continue
  target=expanded/file.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
 original=copy.deepcopy(package['exam']);items={x['id']:x for x in original['items']};stages={};new=[]
 for kind in ('direct','query','judge','final'):
  for source_id,item in items.items():
   for rank in (range(5) if kind=='judge' else [None]):
    id=kind+(':'+str(rank) if rank is not None else '')+':'+source_id
    row=copy.deepcopy(item);row['id']=id;new.append(row)
    stages[id]={'source_id':source_id,'kind':kind,'rank':rank}
 exam=copy.deepcopy(original);exam['items']=new;exam['max_points']=sum(x['max_points'] for x in new)
 n.write(expanded/'exam.json',exam);n.write(expanded/'answers-template.json',{'exam_id':exam['exam_id'],'answers':[{'id':x['id'],'answer':''} for x in new]})
 m=p.prepare(SimpleNamespace(exam_dir=expanded,output=out,essay_id=[],no_essay=True,cache=a.cache,binary=a.binary,lock=a.lock,minutes=60,inject_faults=False))
 n.need(n.sha(out/'run_recovery_package.py')==BINDING_SHA,'Reviewed binding base')
 shutil.copyfile(out/'run_recovery_package.py',out/'run_recovery_package.original.py')
 code=(out/'run_recovery_package.py').read_text(encoding='utf8')
 old=" runtime=OwnedRuntime(root,m,parent,proof)\n try:\n"
 newcode=" runtime=OwnedRuntime(root,m,parent,proof)\n study_hook=load('filtered_rag_hook',root/'study_hook.py');study_hook.install(root,r)\n try:\n"
 n.need(code.count(old)==1,'Exact one hook insertion');code=code.replace(old,newcode)
 (out/'run_recovery_package.py').write_text(code,encoding='utf8',newline='\n')
 for name in ('study_hook.py','prepare.py','export_answers.py'):shutil.copyfile(HERE/name,out/name)
 for name in ('search_query.py','wiki_index.py'):shutil.copyfile(HERE.parent/'full-wikipedia'/name,out/name)
 n.write(out/'source-exam.json',original)
 with (out/'source-original.jsonl').open('x',encoding='utf8',newline='\n') as f:
  for item in original['items']:f.write(n.line({'id':item['id'],'prompt':adapter.build_prompt(original,item),'images':[x['path'] for x in item.get('images',[])]}))
 study={'schema':'direct_filter_query_study_v1','stages':stages,'source_exam_sha256':n.sha(source/'exam.json'),'source_template_sha256':n.sha(source/'answers-template.json'),'index_path':a.index,'index_sha256':INDEX_SHA,'index_bytes':10464555008,'articles':1587721,'passages':2729746,'query_code_sha256':n.sha(out/'search_query.py'),'primary_calls':48,'max_attempts':192,'max_requested_tokens':7077888,'fallback':'invalid query=>original lexical; invalid/reject judge=>no passage; no admitted passages=>bare answer','dependency_policy':'retrieval/admission frozen at first use; later intermediate recovery does not retroactively change final source evidence'}
 n.write(out/'study.json',study)
 m['files']={f.relative_to(out).as_posix():n.sha(f) for f in out.rglob('*') if f.is_file() and f.name!='launch.json'}
 shutil.copyfile(out/'launch.json',out/'recovery-prepared.json')
 m['files']['recovery-prepared.json']=n.sha(out/'recovery-prepared.json')
 (out/'launch.json').write_text(n.line(m),encoding='utf8',newline='\n');runner=n.load('rag_frozen_binding',out/'run_recovery_package.py');runner.preflight(out)
 n.need(m['max_calls']==192 and m['max_requested_tokens']==7077888,'Authorized arithmetic')
 return m

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--exam-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 for name in ('cache','binary','lock','index'):ap.add_argument('--'+name,required=True)
 a=ap.parse_args();m=prepare(a);print(json.dumps({'status':'PREPARED','manifest_sha256':n.sha(a.output/'launch.json'),'calls':m['max_calls'],'tokens':m['max_requested_tokens']}))
