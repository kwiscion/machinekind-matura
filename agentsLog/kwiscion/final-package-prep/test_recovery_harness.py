import importlib.util,json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
s=importlib.util.spec_from_file_location('recovery',Path(__file__).with_name('recovery_harness.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def good(text='answer',**kwargs):
 x={'model':r.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':100,'eval_count':50,'message':{'content':text,'thinking':'fallible notes'}};x.update(kwargs);return x
class Runtime:
 def __init__(self,responses,clock):self.responses=list(responses);self.clock=clock;self.calls=[];self.active=False;self.stops=0;self.fail_stop=False
 def verify(self,context):assert context==65536
 def send(self,body,timeout):
  assert not self.active;self.active=True;self.calls.append((body,timeout));self.clock[0]+=min(timeout,.1)
  x=self.responses.pop(0)
  if isinstance(x,BaseException):raise x
  return x
 def quiesce(self,deadline):self.stops+=1;self.active=False;return not self.fail_stop
class Tests(unittest.TestCase):
 def setup_run(self,responses,cases=None):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);out=Path(tmp.name)/'run';clock=[100.];cases=cases or [{'id':'x','content':'complete original source'}];template={'exam_id':'synthetic','answers':[{'id':x['id'],'answer':''} for x in cases]};runtime=Runtime(responses,clock);return out,clock,cases,template,runtime
 def run_it(self,pack,**kwargs):
  out,clock,cases,template,runtime=pack;return r.run(cases,template,out,r.config(),runtime,3700,clock=lambda:clock[0],**kwargs)
 def test_four_attempts_and_placeholder_not_success(self):
  p=self.setup_run([good('',done_reason='length'),None,TimeoutError('forced'),good('')]);actual=self.run_it(p);self.assertEqual(len(p[4].calls),4);self.assertEqual(actual['answers'][0]['answer'],r.PLACEHOLDER)
  state=json.loads((p[0]/'answer-status.json').read_text())['items']['x'];self.assertTrue(state['placeholder']);self.assertFalse(state['successful_recovery']);self.assertEqual(state['mandatory_attempts_unfulfilled'],0)
  payloads=[x[0] for x in p[4].calls];self.assertEqual([x['think'] for x in payloads],[True,True,False,False]);self.assertEqual(payloads[1]['options']['num_predict'],49152)
 def test_timeout_quiescence_before_retry(self):
  p=self.setup_run([TimeoutError('forced timeout'),good()]);self.run_it(p);self.assertEqual(len(p[4].calls),2);self.assertGreaterEqual(p[4].stops,3)
 def test_breadth_first_fairness(self):
  p=self.setup_run([good('',done_reason='length'),good('second'),good('first')],[{'id':'a','content':'a'},{'id':'b','content':'b'}]);actual=self.run_it(p);self.assertEqual([x[0]['messages'][0]['content'] for x in p[4].calls],['a','b','a']);self.assertEqual([x['answer'] for x in actual['answers']],['first','second'])
 def test_preserves_usable_essay_on_failed_repairs(self):
  p=self.setup_run([good('A useful short final.'),None,None,None],[{'id':'essay','content':'original','kind':'essay'}]);actual=self.run_it(p);self.assertEqual(actual['answers'][0]['answer'],'A useful short final.');self.assertEqual(len(p[4].calls),4)
  self.assertFalse(json.loads((p[0]/'answer-status.json').read_text())['items']['essay']['successful_recovery'])
 def test_truncation_is_global_fatal(self):
  p=self.setup_run([good(truncated=True)]);self.run_it(p);self.assertEqual(len(p[4].calls),1);self.assertIn('Source/context truncation',(p[0]/'answer-status.json').read_text())
 def test_resume_orphan_consumes_attempt_without_resending(self):
  p=self.setup_run([KeyboardInterrupt()])
  with self.assertRaises(KeyboardInterrupt):self.run_it(p)
  self.assertTrue((p[0]/'answers.json').exists());p[4].responses=[good('resumed')];actual=self.run_it(p,resume=True);self.assertEqual(actual['answers'][0]['answer'],'resumed');self.assertEqual(len(p[4].calls),2)
  ledger=[json.loads(x) for x in (p[0]/'events.jsonl').read_text().splitlines() if json.loads(x)['event']=='reserved'];self.assertEqual([x['attempt'] for x in ledger],[0,1])
 def test_resume_source_mutation_rejected(self):
  p=self.setup_run([good()]);self.run_it(p);p[2][0]['content']='changed'
  with self.assertRaises(r.Fatal):self.run_it(p,resume=True)
 def test_deadline_and_unverified_stop_preserve_placeholders(self):
  p=self.setup_run([]);p[1][0]=3699;self.run_it(p);self.assertFalse(p[4].calls);self.assertIn('Hard wallclock',(p[0]/'answer-status.json').read_text())
  q=self.setup_run([]);q[4].fail_stop=True;self.run_it(q);self.assertFalse(q[4].calls)
 def test_full_image_and_source_not_truncated(self):
  case={'id':'x','content':[{'text':'full source'},{'image_url':{'url':'data:image/png;base64,YWJj'}}]};body,meta=r.step(case,3,[{'raw':good()}],r.config());self.assertTrue(body['messages'][0]['content'].startswith('full source'));self.assertEqual(body['messages'][0]['images'],['YWJj']);self.assertFalse(body['truncate']);self.assertFalse(body['shift'])
 def test_configuration_and_answer_length(self):
  self.assertEqual(r.config(120)['minutes'],120)
  with self.assertRaises(ValueError):r.config(90)
  with self.assertRaises(r.Failed):r.accepted(good('x'*100001),32768,65536)
 def test_parent_identity_uses_live_start_argv_not_protected_exe(self):
  spec=importlib.util.spec_from_file_location('generic_identity',Path(__file__).with_name('run_native_package.py'));generic=importlib.util.module_from_spec(spec);spec.loader.exec_module(generic)
  receipt={'pid':123,'ticks':'456','argv':['python3','runner.py'],'executable':'/usr/bin/python3','namespace':'net:parent'}
  fields=['S']+['0']*18+['456']
  with patch.object(generic.Path,'read_text',return_value='123 (python) '+' '.join(fields)),patch.object(generic.Path,'read_bytes',return_value=b'python3\0runner.py\0'),patch.object(generic.Path,'resolve',side_effect=PermissionError('protected exe')):
   self.assertEqual(generic.inherited_parent_identity(123,receipt),receipt)
   with self.assertRaises(generic.GlobalStop):generic.inherited_parent_identity(123,dict(receipt,ticks='999'))
 def test_final_utf8_size_and_placeholder_metadata(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td);template={'exam_id':'synthetic','answers':[{'id':str(i),'answer':''} for i in range(12)]}
   states={str(i):{'answer':'x'*100000,'attempts':1,'warnings':[],'history':[],'partial_candidates':[]} for i in range(12)}
   result=r.export(out,template,states);self.assertLessEqual((out/'answers.json').stat().st_size,1048576);self.assertTrue(all(x['answer'] for x in result['answers']))
   metadata=json.loads((out/'answer-status.json').read_text())['items'];self.assertTrue(any(x.get('schema_size_replaced') for x in metadata.values()))
   self.assertTrue(any(x['selection']=='size_bounded_partial' for x in metadata.values()))
 def test_partial_final_preserved_without_success_claim(self):
  p=self.setup_run([good('usable partial',done_reason='length'),None,None,None]);actual=self.run_it(p)
  self.assertEqual(actual['answers'][0]['answer'],'usable partial')
  state=json.loads((p[0]/'answer-status.json').read_text())['items']['x']
  self.assertTrue(state['incomplete_partial']);self.assertFalse(state['successful_recovery']);self.assertFalse(state['placeholder'])
 def test_exact_placeholder_and_bad_unicode_retries(self):
  self.assertEqual(r.PLACEHOLDER,'Tadeusz Ko\u015bciuszko')
  p=self.setup_run([good('\ud800'),good('valid')]);actual=self.run_it(p)
  self.assertEqual(actual['answers'][0]['answer'],'valid');self.assertEqual(len(p[4].calls),2)
  self.assertIsNone(r.usable_partial(good('\ud800',done_reason='length'),32768,65536))
 def test_initial_allocation_does_not_divide_by_all_future_retries(self):
  cases=[{'id':str(i),'content':'original'} for i in range(40)]
  p=self.setup_run([good() for _ in cases],cases);self.run_it(p)
  self.assertEqual(p[4].calls[0][1],75);self.assertGreater(p[4].calls[1][1],75)
 def test_plan_hook_cannot_be_submitted_as_final(self):
  def route(*args):return {'name':'plan','suffix':'make plan','cap':8192,'think':True}
  route.provenance_sha256='synthetic'
  p=self.setup_run([]);self.run_it(p,route=route);self.assertFalse(p[4].calls)
  self.assertIn('stage-result protocol',(p[0]/'answer-status.json').read_text())
if __name__=='__main__':unittest.main()
