"""CPU-only actual adapter preparation and mocked ownership/recovery binding."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
HERE=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('binding_test',HERE/'run_recovery_package.py');prep=load('binding_prepare',HERE/'prepare_recovery_package.py')
old=load('native_fixture',HERE/'test_native_package.py')
class Tests(unittest.TestCase):
 def test_actual_adapter_fresh_preparation_and_source_mutation(self):
  fixture=old.Tests();fixture.setUp();self.addCleanup(fixture.doCleanups)
  parent,_,_,_,_,_=fixture.package()
  args=SimpleNamespace(exam_dir=parent/'exam',output=parent.with_name('recovery'),essay_id=['essay-custom'],no_essay=False,cache='/owned/fresh/models',binary='/owned/runtime/bin/ollama',lock='/owned/offline.lock',minutes=60,inject_faults=True)
  m=prep.prepare(args);packed=load('packed_binding',args.output/'run_recovery_package.py');actual,package,cases=packed.preflight(args.output)
  self.assertEqual(m['max_calls'],12);self.assertEqual(m['max_requested_tokens'],3*147456);self.assertEqual(len(m['faults']),2)
  self.assertTrue(cases[0]['content'][1]['image_url']['url'].startswith('data:image/'));self.assertEqual(cases[1]['kind'],'essay')
  self.assertNotIn('unrelated-private-key.txt',m['files'])
  (args.output/'input.jsonl').write_text('changed')
  with self.assertRaises(Exception):packed.preflight(args.output)
 def test_context_drift_converted_to_global_fatal(self):
  runtime=object.__new__(b.OwnedRuntime);runtime._verify=Mock(side_effect=ValueError('wrong context'))
  with self.assertRaises(b.r.Fatal):runtime.verify(65536)
 def test_post_send_context_drift_never_retries(self):
  runtime=object.__new__(b.OwnedRuntime);runtime.loaded=True;runtime._verify=Mock(side_effect=[None,None,ValueError('context drift')]);runtime.quiesce=Mock(return_value=True)
  runtime.send=Mock(return_value={'model':b.r.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':10,'eval_count':2,'message':{'content':'answer'}})
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'run';cases=[{'id':'x','content':'original'}];template={'exam_id':'x','answers':[{'id':'x','answer':''}]}
   b.r.run(cases,template,out,b.r.config(),runtime,3700,clock=lambda:100)
   self.assertEqual(runtime.send.call_count,1);self.assertIn('context drift',json.loads((out/'answer-status.json').read_text())['stop'])
 def test_cold_allowance_is_finite_and_warm_allocation_unchanged(self):
  runtime=object.__new__(b.OwnedRuntime);runtime.loaded=False
  self.assertEqual(runtime.timeout_for(75,0),240)
  runtime.loaded=True;self.assertEqual(runtime.timeout_for(75,0),75)
 def test_durable_identity_precedes_broad_namespace_fallback(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'results';out.mkdir();record={'pid':123,'ticks':'1','namespace':'net:owned'}
   b.r.atomic(out/'server-identity.json',record);b.r.atomic(out/'network-proof.json',{'isolated_namespace':'net:owned'})
   helper=Mock();helper.cleanup.return_value=[123,124];helper.process_absent.return_value=True
   with patch.object(b.os,'readlink',return_value='net:host'):
    result=b.recover_owned(root,{'binary':'/owned/ollama'},helper)
   self.assertEqual(result['mode'],'recorded_identity_group');helper.cleanup_from_receipts.assert_not_called()
 def test_timeout_kills_http_child_then_requires_owned_cleanup(self):
  runtime=object.__new__(b.OwnedRuntime);runtime.server=Mock();runtime.m={'max_calls':4,'max_requested_tokens':147456};runtime.out=Path('synthetic');runtime.response_terminal=False
  runtime.verify=Mock();runtime.remaining=Mock(return_value=100);runtime.fault='timeout';runtime.loaded=False
  child=Mock();child.communicate.side_effect=[b.subprocess.TimeoutExpired('http',.25),(b'',b'')]
  with patch.object(b.n,'rows',return_value=[{'event':'reserved','cap':32768}]),patch.object(b.n,'append'),patch.object(b.subprocess,'Popen',return_value=child):
   with self.assertRaises(TimeoutError):runtime.send({'messages':[]},10)
  child.kill.assert_called_once();self.assertFalse(runtime.response_terminal)
 def test_owned_quiescence_reaps_and_checks_no_gpu_before_return(self):
  runtime=object.__new__(b.OwnedRuntime);runtime.response_terminal=False;runtime.server=Mock(pid=123,returncode=-9);runtime.record={'pid':123,'ticks':'1','namespace':'net:owned'}
  runtime.helper=Mock();runtime.helper.cleanup.return_value=[123,124];runtime.helper.process_absent.return_value=True;runtime.out=Path('synthetic');runtime.parent=11
  with patch.object(b.r,'atomic'),patch.object(b.n,'append'):self.assertTrue(runtime.quiesce(999))
  runtime.helper.cleanup.assert_called_once_with(runtime.record);runtime.helper.workers.assert_called_once();self.assertIsNone(runtime.server)
 def test_exact_site_schema_not_legacy_utf16(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'answers.json';template={'exam_id':'x','answers':[{'id':'a','answer':''}]}
   b.r.atomic(path,{'exam_id':'x','answers':[{'id':'a','answer':'\U0001f600'*100000}]});b.validate_final(path,template)
   b.r.atomic(path,{'exam_id':'x','answers':[{'id':'a','answer':' '}]})
   with self.assertRaises(Exception):b.validate_final(path,template)
if __name__=='__main__':unittest.main()
