"""Export only actual direct/final study slots; never query/judgment JSON."""
import argparse,json,hashlib
from pathlib import Path
def export(root):
 plan=json.loads((root/'study.json').read_text(encoding='utf8'));source=json.loads((root/'source-exam.json').read_text(encoding='utf8'))
 doc=json.loads((root/'results/answers.json').read_text(encoding='utf8'))
 assert set(doc)=={'exam_id','answers'} and doc['exam_id']==source['exam_id']
 assert all(set(x)=={'id','answer'} and isinstance(x['id'],str) and isinstance(x['answer'],str) for x in doc['answers'])
 answers={x['id']:x['answer'] for x in doc['answers']}
 assert len(answers)==len(doc['answers']) and set(answers)==set(plan['stages'])
 source_ids=[x['id'] for x in source['items']];assert len(set(source_ids))==len(source_ids)
 status=json.loads((root/'results/engine/answer-status.json').read_text(encoding='utf8'))['items']
 assert set(status)==set(answers)
 def complete(id):return status[id].get('selection')=='complete_final' and not status[id].get('placeholder') and not status[id].get('incomplete_partial') and bool(answers[id].strip())
 output={};fallbacks=[]
 for arm,kind in [('direct','direct'),('filtered','final')]:
  rows=[]
  for item in source['items']:
   id=item['id'];selected=kind+':'+id
   if kind=='final' and not complete(selected) and complete('direct:'+id):
    fallbacks.append({'id':id,'failed_final_id':selected,'failed_final_sha256':hashlib.sha256(answers[selected].encode()).hexdigest(),'selected_id':'direct:'+id,'reason':'Incomplete filtered final; preserve complete matched direct control'})
    selected='direct:'+id
   rows.append({'id':id,'answer':answers[selected]})
  value={'exam_id':source['exam_id'],'answers':rows};path=root/'results'/('answers.'+arm+'.json')
  assert not path.exists()
  path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8',newline='\n')
  output[arm]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'items':len(rows),'blank':sum(not x['answer'].strip() for x in rows)}
 receipt=root/'results/export-fallbacks.json';assert not receipt.exists()
 receipt.write_text(json.dumps({'fallbacks':fallbacks,'original_stage_answers_sha256':hashlib.sha256((root/'results/answers.json').read_bytes()).hexdigest(),'raw_stage_answers_preserved':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
 return output
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(export(a.root)))
