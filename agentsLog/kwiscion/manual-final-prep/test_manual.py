import importlib.util,json,tempfile,unittest,zipfile
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
if __name__=='__main__':unittest.main()
