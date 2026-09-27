"""Exercise real scheduler reservations and source-preserving hook composition."""
import copy,importlib.util,json,sys,tempfile,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'filtered-rag-prep'))
import test_v2,fast_hook

class Tests(test_v2.Tests):
 def hook(self,r,out):
  profile_path=HERE.parent/'qwen-thinking-prep/closed_profile.py'
  spec=importlib.util.spec_from_file_location('fast_profile',profile_path);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.install(r,r.step)
  hook=super().hook(r,out);hook.__class__=fast_hook.Hook;r.step=hook.step
  return hook
 def test_auxiliary_caps_and_unchanged_final(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=test_v2.engine();hook=self.hook(r,Path(tmp));case={'content':[{'type':'text','text':'full'},{'type':'image_url','image_url':{'url':'data:image/png;base64,YWJj'}}]}
   for id in hook.plan['stages']:
    case['id']=id
    for attempt in range(4):
     baseline,old=test_v2.h.Hook.step(hook,case,attempt,[],r.config())
     body,new=hook.step(case,attempt,[],r.config())
     if hook.current['kind'] in ('query','judge'):
      cap=1024 if attempt else 512 if hook.current['kind']=='query' else 384
      self.assertFalse(body['think']);self.assertEqual(body['options']['num_predict'],cap);self.assertEqual(new['cap'],cap)
      self.assertEqual(body['messages'],baseline['messages']);self.assertEqual(body['format'],baseline['format'])
     else:self.assertEqual(body,baseline);self.assertEqual(new,old)
     self.assertEqual(body['options']['temperature'],1);self.assertEqual(body['model'],'qwen3.5:9b')
 def test_ledger_records_exact_requested_caps(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=test_v2.engine();hook=self.hook(r,Path(tmp)/'study');cases=[{'id':id,'content':'full'} for id in hook.plan['stages']];template={'exam_id':'synthetic','answers':[{'id':x['id'],'answer':''} for x in cases]};seen=[]
   class Runtime:
    def verify(self,c):pass
    def quiesce(self,d):return True
    def send(self,body,timeout):
     seen.append(copy.deepcopy(body));kind=hook.current['kind']
     text='invalid' if len(seen)==1 else '{"query":"Aster source","concepts":["Aster"],"hypotheses":[]}' if kind=='query' else '{"direct":false,"quote":""}' if kind=='judge' else 'Final'
     return {'model':r.MODEL,'done':True,'done_reason':'stop','message':{'content':text},'prompt_eval_count':100,'eval_count':20}
   out=Path(tmp)/'engine';r.run(cases,template,out,r.config(),Runtime(),time.time()+3500)
   events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()];reserved=[x for x in events if x['event']=='reserved']
   self.assertEqual([x['cap'] for x in reserved],[x['options']['num_predict'] for x in seen])
   self.assertIn(1024,[x['cap'] for x in reserved]);self.assertIsNone(json.loads((out/'answer-status.json').read_text())['stop'])
if __name__=='__main__':unittest.main()
