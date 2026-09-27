import datetime,hashlib,importlib.util,json,tempfile,time,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
l=load('launcher');r=load('remote_ops')
class Tests(unittest.TestCase):
 def test_zip_traversal_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);z=p/'bad.zip'
   with zipfile.ZipFile(z,'w') as f:f.writestr('../escape','bad')
   with self.assertRaises(ValueError):l.source_directory(z,p)
 def test_nested_zip_exact_template(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);z=p/'good.zip'
   with zipfile.ZipFile(z,'w') as f:
    f.writestr('organizer/exam.json','{}');f.writestr('organizer/answers-template.json','{}')
   self.assertEqual(l.source_directory(z,p).name,'organizer')
 def test_answer_validation_rejects_duplicates_and_blanks(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);t=p/'template';a=p/'answer';template={'exam_id':'x','answers':[{'id':'a','answer':''}]};t.write_text(json.dumps(template))
   for answers in ([{'id':'a','answer':''}],[{'id':'a','answer':'yes'},{'id':'a','answer':'yes'}]):
    a.write_text(json.dumps({'exam_id':'x','answers':answers}))
    with self.assertRaises(ValueError):l.validate_answers(a,t)
 def test_status_ignores_only_partial_trailing_event(self):
  with tempfile.TemporaryDirectory() as d,patch.object(r,'STAGE',Path(d)):
   run='20260927T120000-abcd1234';root=r.root(run);e=root/'package/results/engine/events.jsonl';e.parent.mkdir(parents=True);e.write_text('{"event":"reserved"}\n{"event":')
   self.assertEqual(r.status(run)['reserved'],1)
 def test_dispatch_marker_prevents_duplicate_spawn(self):
  with tempfile.TemporaryDirectory() as d,patch.object(r,'STAGE',Path(d)),patch.object(r.subprocess,'Popen') as popen:
   run='20260927T120000-abcd1234';root=r.root(run);root.mkdir(parents=True);(root/'stage.json').write_text('{}');(root/'dispatch.json').write_text('{"utc":"already"}')
   self.assertEqual(r.start(run)['status'],'ALREADY_DISPATCHED');popen.assert_not_called()
 def test_fetch_small_answers_while_backup_is_still_building_and_resume_never_starts(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);run='20260927T120000-abcd1234';template=out/'package/exam/answers-template.json';template.parent.mkdir(parents=True)
   template.write_text(json.dumps({'exam_id':'x','answers':[{'id':'a','answer':''}]}))
   answer=json.dumps({'exam_id':'x','answers':[{'id':'a','answer':'Complete answer'}]}).encode();calls=[]
   terminal={'answers_present':True,'answers_sha256':hashlib.sha256(answer).hexdigest()}
   status={'status':'FINALIZING_BACKUP','run_id':run,'terminal':terminal,'answer_summary':{'original_items':1,'placeholders':0}}
   state={'run_id':run,'phase':'FETCHED','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_target_utc':datetime.datetime.fromtimestamp(time.time()+3600,datetime.timezone.utc).isoformat()}
   def transfer(src,dest):
    calls.append(src);Path(dest).write_bytes(answer)
   with patch.object(l,'ssh',return_value=status) as ssh,patch.object(l,'transfer',side_effect=transfer),patch.object(l,'wslpath',side_effect=str):
    self.assertEqual(l.workflow(out,state),0)
   self.assertEqual((out/'answers.json').read_bytes(),answer);self.assertEqual(len(calls),1)
   self.assertTrue(all(x.args[0]=='status' for x in ssh.call_args_list));self.assertFalse((out/'terminal.tar.gz').exists())
 def test_failed_spawn_retains_marker_and_reports_failure(self):
  with tempfile.TemporaryDirectory() as d,patch.object(r,'STAGE',Path(d)),patch.object(r.subprocess,'Popen',side_effect=OSError('spawn failed')):
   run='20260927T120000-abcd1234';root=r.root(run);(root/'package').mkdir(parents=True);(root/'stage.json').write_text('{}')
   (root/'package/launch.json').write_text(json.dumps({'deadline_utc':datetime.datetime.fromtimestamp(time.time()+120,datetime.timezone.utc).isoformat()}))
   with self.assertRaises(OSError):r.start(run)
   self.assertTrue((root/'dispatch.json').exists());self.assertEqual(r.status(run)['status'],'FAILED_START')
 def test_explicit_late_resume_fetches_backup_without_dispatch(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);template=out/'package/exam/answers-template.json';template.parent.mkdir(parents=True)
   template.write_text(json.dumps({'exam_id':'x','answers':[{'id':'a','answer':''}]}))
   answer=json.dumps({'exam_id':'x','answers':[{'id':'a','answer':'Complete'}]}).encode();archive=b'backup';calls=[]
   status={'status':'TERMINAL','terminal':{'answers_present':True,'answers_sha256':hashlib.sha256(answer).hexdigest()},'backup':{'sha256':hashlib.sha256(archive).hexdigest()}}
   state={'run_id':'20260927T120000-abcd1234','phase':'FETCHED','started_utc':datetime.datetime.fromtimestamp(time.time()-7200,datetime.timezone.utc).isoformat(),'local_target_utc':datetime.datetime.fromtimestamp(time.time()-3600,datetime.timezone.utc).isoformat()}
   def transfer(src,dest):
    calls.append(src);Path(dest).write_bytes(archive if src.endswith('.tar.gz') else answer)
   with patch.object(l,'ssh',return_value=status) as ssh,patch.object(l,'transfer',side_effect=transfer),patch.object(l,'wslpath',side_effect=str),patch.object(l,'extract_backup') as extract:
    self.assertEqual(l.workflow(out,state,explicit_resume=True),0);extract.assert_called_once()
   self.assertEqual(len(calls),2);self.assertTrue(all(c.args[0]=='status' for c in ssh.call_args_list))
if __name__=='__main__':unittest.main()
