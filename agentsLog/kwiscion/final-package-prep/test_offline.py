import base64,copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('offline',Path(__file__).with_name('run_gemma_offline.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def response(self):return {'model':m.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':30,'eval_count':40,'message':{'content':'gotowe','thinking':'Check exact word.'}}
 def test_native_payload_full_images(self):
  data=b'complete-image-bytes';case={'content':[{'text':'original prompt'},{'image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}}]};p=m.payload(case)
  self.assertEqual(base64.b64decode(p['messages'][0]['images'][0]),data);self.assertEqual(p['messages'][0]['content'],'original prompt');self.assertTrue(p['think']);self.assertFalse(p['truncate']);self.assertFalse(p['shift']);self.assertEqual(p['options'],{'num_ctx':32768,'num_predict':10240});self.assertNotIn('temperature',p['options'])
 def test_transport_failures(self):
  for key,value in [('context_truncated',True),('truncated',True),('done_reason','length'),('model','other'),('prompt_eval_count',None),('eval_count',10241),('prompt_eval_count',30000),('error','bad')]:
   r=self.response();r[key]=value
   with self.subTest(key=key),self.assertRaises(RuntimeError):m.answer(r)
 def test_final_and_thinking_required(self):
  self.assertEqual(m.answer(self.response()),'gotowe')
  for key in ('content','thinking'):
   r=self.response();r['message'][key]=''
   with self.assertRaises(RuntimeError):m.answer(r)
 def test_semantics(self):
  self.assertTrue(m.correct('offline-text','Gotowe.'));self.assertTrue(m.correct('offline-image','czerwony'));self.assertFalse(m.correct('offline-image','niebieski'));self.assertFalse(m.correct('offline-text','something nonempty'))
 def test_deadline(self):
  with patch.object(m.time,'time',return_value=100):
   self.assertEqual(m.remaining({'deadline_utc':'1970-01-01T00:02:00+00:00'}),20)
   for d in ('1970-01-01T00:00:00+00:00','1970-01-01T01:00:00+00:00'):
    with self.assertRaises(RuntimeError):m.remaining({'deadline_utc':d})
 def test_no_matching_cleanup_no_signal(self):
  with patch.object(m.Path,'iterdir',return_value=[]),patch.object(m.os,'killpg',create=True) as kill:
   self.assertEqual(m.cleanup({'pid':123,'ticks':'1','namespace':'net:test'}),[]);kill.assert_not_called()
 def test_empty_wrong_template_not_semantic_success(self):
  self.assertFalse(m.correct('offline-image',''));self.assertFalse(m.correct('offline-text','gotowy'))
 def test_missing_receipt_namespace_fallback(self):
  proc=Path('/proc/42');proof={'isolated_namespace':'net:child'}
  def link(path):return 'net:host' if str(path)=='/proc/self/ns/net' else 'net:child'
  with patch.object(m.Path,'iterdir',return_value=[proc]),patch.object(m.Path,'stat',return_value=SimpleNamespace(st_uid=123)),patch.object(m.os,'getuid',return_value=123,create=True),patch.object(m.os,'readlink',side_effect=link),patch.object(m.Path,'resolve',return_value=Path('/owned/runtime/bin/ollama')),patch.object(m,'ticks',return_value='123'),patch.object(m.os,'kill') as kill,patch.object(m.signal,'SIGKILL',9,create=True):
   self.assertEqual(m.namespace_cleanup(proof,'/owned/runtime/bin/ollama'),[42]);kill.assert_called_once_with(42,m.signal.SIGKILL)
 def test_foreign_proc_not_inspected_during_cleanup(self):
  def link(path):
   if str(path)=='/proc/1/ns/net':raise PermissionError('foreign')
   return 'net:host' if str(path)=='/proc/self/ns/net' else 'net:child'
  def st(path,*args,**kwargs):return SimpleNamespace(st_uid=0 if path.name=='1' else 123)
  with patch.object(m.Path,'iterdir',return_value=[Path('/proc/1'),Path('/proc/42')]),patch.object(m.Path,'stat',st),patch.object(m.os,'getuid',return_value=123,create=True),patch.object(m.os,'readlink',side_effect=link),patch.object(m.Path,'resolve',return_value=Path('/owned/runtime/bin/ollama')),patch.object(m,'ticks',return_value='123'),patch.object(m.os,'kill') as kill,patch.object(m.signal,'SIGKILL',9,create=True):
   self.assertEqual(m.namespace_cleanup({'isolated_namespace':'net:child'},'/owned/runtime/bin/ollama'),[42]);kill.assert_called_once()
 def test_cleanup_refuses_host_namespace(self):
  with patch.object(m.os,'readlink',return_value='net:host'),self.assertRaises(RuntimeError):m.namespace_cleanup({'isolated_namespace':'net:host'},'/owned/runtime/bin/ollama')
 def test_real_adapter_mocked_two_calls_and_no_retry(self):
  repo=Path(__file__).resolve().parents[3]
  adapter=m.load('test_adapter',repo/'scripts/Bukareszt/matura_package.py');r=m.load('test_rehearsal',repo/'agentsLog/kwiscion/offline_rehearsal.py');inf=m.load('test_infer',repo/'infer.py')
  for broken in (False,True):
   with tempfile.TemporaryDirectory() as td:
    out=Path(td);pkg=r.fixture(out,adapter);cases=inf.load_cases(out/'input.jsonl',2);sent=[]
    def send(body):
     ledger=[json.loads(x) for x in (out/'reservations.jsonl').read_text().splitlines()]
     self.assertEqual(len(ledger),len(sent)+1);self.assertLessEqual(sum(x['cap'] for x in ledger),20480);sent.append(body)
     response=self.response();response['message']['content']='gotowe' if len(sent)==1 else 'niebieski'
     if broken:response['context_truncated']=True
     return response
    with patch.object(m,'remaining',return_value=900):rows,count=m.dispatch(cases,{},out,send,lambda loaded:None)
    self.assertEqual(count,1 if broken else 2)
    report=adapter.finalize(pkg,[out/'finalizer-input.jsonl'],out/'answers.json',out/'failures.json',out/'input.jsonl.manifest.json')
    actual=json.loads((out/'answers.json').read_text())['answers'];self.assertEqual([x['id'] for x in actual],['offline-text','offline-image'])
    if broken:self.assertEqual([x['answer'] for x in actual],['',''])
    else:self.assertEqual(actual[0]['answer'],'gotowe');self.assertFalse(m.correct(actual[1]['id'],actual[1]['answer']))
if __name__=='__main__':unittest.main()
