import importlib.util,json,tempfile,unittest,copy
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('binding',HERE.parent/'final-package-prep/run_recovery_package.py');q=load('profile',HERE/'closed_profile.py');g=load('guard',HERE.parent/'final-package-prep/guard.py')
class Tests(unittest.TestCase):
 def tearDown(self):b.configure_profile(HERE,{'model':b.n.MODEL,'temperature':'omitted'})
 def test_default_exact_and_reset(self):
  case={'content':'source','kind':'ordinary'};c=b.r.config();before=b.r.step(case,0,[],c)
  q.install(b.r,b.ORIGINAL_STEP);body,_=b.r.step(case,0,[],c);self.assertEqual(body['model'],q.MODEL);self.assertEqual({k:body['options'][k] for k in q.SAMPLING},q.SAMPLING)
  b.configure_profile(HERE,{'model':b.n.MODEL,'temperature':'omitted'});self.assertEqual(before,b.r.step(case,0,[],c))
 def test_closed_profile_and_pin(self):
  with self.assertRaises(Exception):b.configure_profile(HERE,{'model_profile':'arbitrary'})
  with self.assertRaises(Exception):b.configure_profile(HERE,{'model_profile':q.PROFILE,'files':{'closed_profile.py':'0'*64}})
 def test_response_identity(self):
  q.install(b.r,b.ORIGINAL_STEP)
  with self.assertRaises(b.r.Fatal):b.r.accepted({'model':b.n.MODEL},32768,65536)
 def test_snapshot(self):
  guard=q.wrap_guard(g);s={'version':{'version':'0.34.4'},'tags':{'models':[{'name':q.MODEL,'digest':q.DIGEST}]},'ps':{'models':[{'name':q.MODEL,'digest':q.DIGEST,'context_length':65536}]}}
  guard.verify_snapshot(s,guard.CANONICAL,True)
  for field,value in [('context_length',32768),('digest','0'*64),('name',b.n.MODEL)]:
   bad=copy.deepcopy(s);bad['ps']['models'][0][field]=value
   with self.assertRaises(ValueError):guard.verify_snapshot(bad,guard.CANONICAL,True)
 def test_exact_single_container(self):
  evidence=json.loads((HERE/'qwen-native-manifest-evidence.json').read_text())['manifest']
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);f=root/'manifests/registry.ollama.ai/library/qwen3.5/9b';f.parent.mkdir(parents=True);f.write_text(json.dumps(evidence))
   with patch.object(g,'fingerprint',return_value={'bytes':100,'sha256':q.DIGEST}):
    inv=q.wrap_guard(g).native_inventory(root,{})
    self.assertEqual(len(inv['files']),5);self.assertEqual(sum(x['bytes'] for x in inv['files'] if x['purpose']=='model'),6594462816)
    for badlayer in [dict(q.WEIGHT,mediaType='application/vnd.ollama.image.projector'),q.WEIGHT]:
     bad=copy.deepcopy(evidence);bad['layers'].append(badlayer);f.write_text(json.dumps(bad))
     with self.assertRaises(ValueError):q.wrap_guard(g).native_inventory(root,{})
if __name__=='__main__':unittest.main()
