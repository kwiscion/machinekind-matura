import copy,importlib.util,json,tempfile,time,unittest
from pathlib import Path
import study_hook_v2 as h
HERE=Path(__file__).resolve().parent

def engine():
 path=HERE.parent/'final-package-prep/recovery_harness.py'
 spec=importlib.util.spec_from_file_location('v2_test_engine',path);r=importlib.util.module_from_spec(spec)
 code=path.read_text(encoding='utf8').replace('   if not unresolved:break','   unresolved=stage_barrier(unresolved,states)\n   if not unresolved:break')
 exec(compile(code,str(path),'exec'),r.__dict__);return r

class Tests(unittest.TestCase):
 def hook(self,r,out):
  hook=object.__new__(h.Hook);hook.engine=r;hook.original=r.step;hook.original_accepted=r.accepted;hook.original_partial=r.usable_partial;hook.base_out=out;hook.scope='main';hook.current=None
  hook.rows={'x':{'prompt':'FULL ORIGINAL\nAnswer only the year.\nŹródło retained.'},'y':{'prompt':'SECOND ORIGINAL'}}
  hook.plan={'stages':{}}
  for kind,phase,probe in [('query',0,True),('judge',1,True),('direct',2,False),('query',3,False),('judge',4,False),('final',5,False)]:
   for source in (['x','y'] if probe else ['x']):
    id=('probe:' if probe else '')+kind+(':0' if kind=='judge' else '')+':'+source
    hook.plan['stages'][id]={'source_id':source,'kind':kind,'rank':0 if kind=='judge' else None,'phase':phase,'probe':probe}
  hook.retrieval=lambda source:{'passages':[{'article_id':'1','title':'Aster','url':'u','start':0,'text':'Exact supporting text.'}]}
  hook.answer=lambda id:None
  r.step=hook.step;r.accepted=hook.accepted;r.usable_partial=hook.partial;r.stage_barrier=hook.barrier
  return hook
 def test_frame_schema_full_original_and_images(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=engine();hook=self.hook(r,Path(tmp));case={'id':'probe:query:x','content':[{'type':'text','text':'synthetic'},{'type':'image_url','image_url':{'url':'data:image/png;base64,YWJj'}}]};before=copy.deepcopy(case)
   for attempt in range(4):
    body,_=hook.step(case,attempt,[],r.config());self.assertEqual(body['format'],h.QUERY_SCHEMA);self.assertTrue(body['messages'][0]['content'].startswith(h.FRAME));self.assertIn(hook.rows['x']['prompt'],body['messages'][0]['content']);self.assertEqual(body['messages'][0]['images'],['YWJj'])
   self.assertEqual(case,before)
 def test_verbatim_negative_duplicate_contract(self):
  p={'article_id':'a','title':'t','url':'u','start':0,'text':'Exact span'}
  self.assertFalse(h.parse_judge('{"direct":false,"quote":""}',p)['direct'])
  self.assertTrue(h.parse_judge('```json\n{"direct":true,"quote":"Exact span"}\n```',p)['direct'])
  for text in ['{"direct":true,"quote":"invented"}','{"direct":false,"quote":"x"}','{"direct":false,"direct":true,"quote":"Exact span"}','1848']:
   with self.assertRaises((ValueError,TypeError)):h.parse_judge(text,p)
 def exercise(self,fail_probe=False):
  with tempfile.TemporaryDirectory() as tmp:
   r=engine();hook=self.hook(r,Path(tmp)/'study');cases=[{'id':id,'content':'FULL'} for id in hook.plan['stages']];template={'exam_id':'synthetic','answers':[{'id':x['id'],'answer':''} for x in cases]};seen=[];counts={}
   class Runtime:
    def verify(self,context):pass
    def quiesce(self,deadline):return True
    def send(self,body,timeout):
     stage=copy.deepcopy(hook.current);key=(stage['phase'],stage['source_id']);counts[key]=counts.get(key,0)+1;seen.append((stage['phase'],stage['source_id'],counts[key]))
     if stage['kind']=='query':text='1848' if (stage.get('probe') and stage['source_id']=='x' and (fail_probe or counts[key]==1)) else '{"query":"Aster source","concepts":["Aster"],"hypotheses":[]}'
     elif stage['kind']=='judge':text='{"direct":false,"quote":""}'
     else:text='Final answer'
     return {'model':r.MODEL,'done':True,'done_reason':'stop','message':{'content':text},'prompt_eval_count':100,'eval_count':20}
   out=Path(tmp)/'engine';r.run(cases,template,out,r.config(),Runtime(),time.time()+3500)
   status=json.loads((out/'answer-status.json').read_text());events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
   self.assertEqual(len([x for x in events if x['event']=='reserved']),len(seen))
   self.assertEqual(seen[0][0],0)
   if fail_probe:
    self.assertIn('qualification failed',status['stop']);self.assertFalse(any(phase>=2 for phase,_,_ in seen));self.assertEqual(counts[(0,'x')],4)
   else:
    self.assertIsNone(status['stop']);self.assertEqual(counts[(0,'x')],2);self.assertEqual([x[0] for x in seen],sorted(x[0] for x in seen));self.assertTrue(json.loads((Path(tmp)/'study/probe-gate.json').read_text())['passed'])
 def test_real_scheduler_recovers_before_dependency_and_keeps_ledger(self):self.exercise()
 def test_invalid_probe_blocks_every_main_call(self):self.exercise(True)

if __name__=='__main__':unittest.main()
