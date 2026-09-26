"""Small CPU fixtures only; no model allocation, network or inference."""
import copy,hashlib,importlib.util,json,os
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch

s=importlib.util.spec_from_file_location('package_guard',Path(__file__).with_name('guard.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def pin(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'weights';self.root.mkdir()
    def inventory(self,files):
        rows=[]
        for name,data in files.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows.append(dict(path=name,purpose='model',**pin(data)))
        return {'schema':'final_weight_inventory_v1','files':rows}
    def test_exact_inventory_metadata_and_limit(self):
        m=self.inventory({'model.gguf':b'GGUFabc','config.json':b'{}'});m['files'][1]['purpose']='metadata'
        self.assertEqual(g.verify_inventory(self.root,m,9)['counted_bytes'],9)
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m,8)
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m,g.LIMIT+1)
    def test_missing_unlisted_and_changed(self):
        m=self.inventory({'a':b'abc'});(self.root/'extra').write_bytes(b'x')
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
        (self.root/'extra').unlink();(self.root/'a').write_bytes(b'abd')
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
        (self.root/'a').unlink()
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
    def test_invalid_paths_and_duplicates(self):
        for path in ('../a','/a','a/../b','a\\b','C:/a','a//b','a/./b'):
            with self.subTest(path=path),self.assertRaises(ValueError):g.relative(path)
        m=self.inventory({'a':b'a'});m['files'].append(dict(m['files'][0],path='A'))
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
    def test_symlink_file_and_directory_rejected(self):
        m=self.inventory({'a':b'a'});outside=Path(self.temp.name)/'outside';outside.write_bytes(b'a')
        (self.root/'a').unlink()
        try:(self.root/'a').symlink_to(outside)
        except OSError:self.skipTest('Symlink privilege unavailable; run Linux suite')
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
        (self.root/'a').unlink();(self.root/'a').write_bytes(b'a');(self.root/'linked').symlink_to(outside.parent,target_is_directory=True)
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
    def test_hardlinks_count_twice(self):
        m=self.inventory({'a':b'abc'});os.link(self.root/'a',self.root/'b');m['files'].append(dict(m['files'][0],path='b'))
        self.assertEqual(g.verify_inventory(self.root,m)['counted_bytes'],6)
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m,5)
    def test_runtime_binary_not_weight(self):
        for magic in (b'MZanything',b'\x7fELFanything'):
            m=self.inventory({'renamed.gguf':magic})
            with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
    def test_unreadable_directory_fails_closed(self):
        def broken_walk(root, **kwargs):
            kwargs['onerror'](PermissionError('unreadable directory'))
            return iter(())
        with patch.object(g.os,'walk',broken_walk),self.assertRaises(PermissionError):g.files_under(self.root)
    def test_empty_weights_rejected_metadata_allowed(self):
        m=self.inventory({'a':b''})
        with self.assertRaises(ValueError):g.verify_inventory(self.root,m)
        m['files'][0]['purpose']='metadata'
        self.assertEqual(g.verify_inventory(self.root,m)['counted_bytes'],0)
    def test_earlier_file_change_during_later_hash_rejected(self):
        m=self.inventory({'a':b'abc','b':b'def'});original=g.fingerprint
        def mutate(path):
            if path.name=='b':(self.root/'a').write_bytes(b'longer')
            return original(path)
        with patch.object(g,'fingerprint',mutate),self.assertRaises(ValueError):g.verify_inventory(self.root,m)
    def cache(self):
        pins=copy.deepcopy(g.CANONICAL);pins['model_weight']=pin(b'GGUFmodel');pins['projector']=pin(b'GGUFprojector')
        cfg=b'{}';doc={'config':{'mediaType':'application/vnd.docker.container.image.v1+json','digest':'sha256:'+pin(cfg)['sha256'],'size':len(cfg)},'layers':[]}
        for kind,data in [('model',b'GGUFmodel'),('projector',b'GGUFprojector')]:doc['layers'].append({'mediaType':'application/vnd.ollama.image.'+kind,'digest':'sha256:'+pin(data)['sha256'],'size':len(data)})
        blob=json.dumps(doc).encode();pins['native_manifest_sha256']=pin(blob)['sha256']
        files={'manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M':blob}
        for data in (cfg,b'GGUFmodel',b'GGUFprojector'):files['blobs/sha256-'+pin(data)['sha256']]=data
        self.inventory(files);return pins
    def test_gemma_only_native_cache_no_qwen(self):
        pins=self.cache();inv=g.native_inventory(self.root,pins);result=g.verify_inventory(self.root,inv)
        self.assertEqual(len(result['files']),4)
        with self.assertRaises(ValueError):g.native_inventory(self.root,g.CANONICAL)
        (self.root/'blobs/qwen-extra').write_bytes(b'x')
        with self.assertRaises(ValueError):g.verify_inventory(self.root,g.native_inventory(self.root,pins))
    def test_native_wrong_pair_missing_and_changed_blob(self):
        pins=self.cache();bad=copy.deepcopy(pins);bad['projector']=pin(b'other')
        with self.assertRaises(ValueError):g.native_inventory(self.root,bad)
        (self.root/('blobs/sha256-'+pins['projector']['sha256'])).write_bytes(b'changed')
        with self.assertRaises(ValueError):g.verify_inventory(self.root,g.native_inventory(self.root,pins))
    def test_runtime_snapshot_one_gemma_only(self):
        p=g.CANONICAL;model={'name':p['model'],'digest':p['native_manifest_sha256'],'context_length':32768}
        snap={'version':{'version':'0.34.4'},'tags':{'models':[model]},'ps':{'models':[model]}}
        g.verify_snapshot(snap,p,True)
        snap['ps']['models']=[];g.verify_snapshot(snap,p)
        with self.assertRaises(ValueError):g.verify_snapshot(snap,p,True)
        snap['tags']['models'].append(dict(model,name='qwen3.5:9b'))
        with self.assertRaises(ValueError):g.verify_snapshot(snap,p)
    def test_duplicate_json_key_rejected(self):
        p=Path(self.temp.name)/'duplicate.json';p.write_text('{"a":1,"a":2}')
        with self.assertRaises(ValueError):g.read_json(p)
    def test_fingerprint_directory_rejected_before_open(self):
        with patch.object(g.os,'open',side_effect=AssertionError('must not open')),self.assertRaises(ValueError):g.fingerprint(self.root)
if __name__=='__main__':unittest.main()
