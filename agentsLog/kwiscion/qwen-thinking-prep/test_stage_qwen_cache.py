"""Tiny CPU fixtures only; production profile and pins are never weakened on disk."""
import hashlib
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import stage_qwen_cache as q

class Tests(unittest.TestCase):
    def test_production_profile_rejects_unpinned_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir()
            with self.assertRaises(ValueError):q.stage(source,root/'dest')
            self.assertFalse((root/'dest').exists())

    def test_real_shared_staging_exact_set_extras_freshness_and_byte_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir();rows=[]
            for i in range(5):
                data=('fixture-'+str(i)).encode();name='blobs/'+str(i);p=source/name;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
                rows.append(dict(path=name,purpose='model' if i==0 else 'metadata',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
            (source/'development-extra').write_text('not copied')
            inventory={'schema':'final_weight_inventory_v1','files':rows};real_load=q.load
            def loader(name,path):
                module=real_load(name,path)
                if name=='qwen_stage_profile':
                    def wrap(base):
                        attrs={k:getattr(base,k) for k in dir(base) if not k.startswith('__')};attrs['native_inventory']=lambda *args:inventory
                        return types.SimpleNamespace(**attrs)
                    module.wrap_guard=wrap
                return module
            with patch.object(q,'load',side_effect=loader),patch.object(q,'EXPECTED_BYTES',sum(r['bytes'] for r in rows)):
                result=q.stage(source,root/'dest')
                self.assertEqual(len(result['report']['files']),5)
                self.assertFalse((root/'dest/development-extra').exists())
                for row in rows:self.assertEqual((source/row['path']).read_bytes(),(root/'dest'/row['path']).read_bytes())
                with self.assertRaises(ValueError):q.stage(source,root/'dest')
                with patch.object(q,'EXPECTED_BYTES',1):
                    with self.assertRaisesRegex(ValueError,'five-file'):q.stage(source,root/'wrong-byte-total')
                (source/'blobs/0').write_bytes(b'changed')
                with self.assertRaises(ValueError):q.stage(source,root/'corrupt')

    def test_destination_and_report_cannot_modify_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir()
            with self.assertRaisesRegex(ValueError,'outside source'):q.stage(source,source/'nested')
            with patch('sys.argv',['stage',str(source),str(root/'dest'),'--report',str(source/'report.json')]):
                with self.assertRaisesRegex(ValueError,'outside source'):q.main()
            self.assertEqual(list(source.iterdir()),[])
            self.assertFalse((root/'dest').exists())

    def test_profile_pin_failure_before_staging(self):
        with patch.object(q,'PROFILE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'profile/guard'):q.stage(Path('unused'),Path('unused-destination'))

if __name__=='__main__':unittest.main()
