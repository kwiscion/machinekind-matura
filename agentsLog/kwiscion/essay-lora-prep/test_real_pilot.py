"""Pure CPU contracts; imports no model library and performs no optimizer step."""
import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('run_real_pilot.py');s=importlib.util.spec_from_file_location('pilot',p);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Test(unittest.TestCase):
    def test_empty_multimodal_inventory_rejected(self):
        with self.assertRaises(ValueError):r.require_multimodal_inventory({})
        r.require_multimodal_inventory({'model.embed_vision.weight':'frozen-hash'})
    def manifest(self,mode='history'):
        m=dict(mode=mode,max_optimizer_steps=36 if mode=='history' else 1,max_seconds=1500 if mode=='history' else 600,base_weight_sha256=r.BASE_SHA,inference_calls=0,train_records=90,
          files={str(r.ROOT/n):'pinned' for n in ('run_real_pilot.py','prepare.py','candidate.json','evidence-manifest.json')})
        for k in ('train','eval_inputs','clearance','control_serving_report','synthetic_probe_report'):m[k]=k;m['files'][k]='pinned'
        return m
    def test_exact_three_epochs_and_partial_accumulation(self):
        groups=r.groups(90);self.assertEqual(len(groups),36);self.assertEqual(sum(map(len,groups)),270)
        self.assertEqual([len(g) for g in groups].count(2),3)
        self.assertTrue(all(sum(i in g for g in groups)==3 for i in range(90)))
    def test_synthetic_has_separate_one_step_bound(self):r.validate_manifest(self.manifest('synthetic_probe'))
    def test_pilot_not120_step_override(self):
        m=self.manifest();m['max_optimizer_steps']=120
        with self.assertRaises(ValueError):r.validate_manifest(m)
    def test_missing_clearance_or_probe_pin_rejected(self):
        for key in ('clearance','synthetic_probe_report','control_serving_report'):
            m=self.manifest();del m['files'][key]
            with self.assertRaises(ValueError):r.validate_manifest(m)
    def test_no_inference_and_no_unbounded_time(self):
        for key,value in [('inference_calls',1),('max_seconds',3601),('train_records',91),('base_weight_sha256','changed')]:
            m=self.manifest();m[key]=value
            with self.assertRaises(ValueError):r.validate_manifest(m)
if __name__=='__main__':unittest.main()
