"""Synthetic-only gate tests; no historical dataset or model execution."""
import copy,json,tempfile,unittest
from pathlib import Path
import prepare as p

class ToyTokenizer:
    """One-character toy vocabulary plus a terminator; never a Gemma tokenizer."""
    def apply_chat_template(self,messages,**kwargs):return '<bos><|turn>user\n'+messages[-1]['content']+'<turn|>\n<|turn>model\n<|channel>thought\n<channel|>'
    def __call__(self,text,**kwargs):
        if text=='<turn|>':return {'input_ids':[999]}
        return {'input_ids':[ord(x) for x in text[:-7]]+[999] if text.endswith('<turn|>') else [ord(x) for x in text]}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.rows={s:[dict(id=s,task_type='essay',split=s,status='accepted',source_group_id=s,source_ids=[s],prompt='SYNTHETIC TEST ONLY',response=' '.join([s]*410))] for s in ('train','holdout')}
    def tearDown(self):self.tmp.cleanup()
    def bundle(self):
        files={s:self.root/(s+'.jsonl') for s in self.rows}
        for s,path in files.items():path.write_text(json.dumps(self.rows[s][0])+'\n',encoding='utf-8')
        clear=dict(schema='essay_lora_clearance_v1',checks={k:True for k in p.CHECKS},files={s:{'sha256':p.sha(path.read_bytes())} for s,path in files.items()},canonical_group_map={'train':'A','holdout':'B'},accepted_records={r['id']:{'status':'accepted','record_sha256':p.sha(p.canonical(r)),'independent_review_reference':'synthetic-review-fixture'} for rows in self.rows.values() for r in rows})
        return clear,files
    def run_check(self,c=None,f=None):
        if c is None:c,f=self.bundle()
        return p.validate_data(self.rows['train'],self.rows['holdout'],c,f)
    def test_valid(self):self.assertEqual(self.run_check()['max_optimizer_steps'],3)
    def test_draft(self):
        self.rows['train'][0]['status']='synthetic_draft_pending_independent_review'
        with self.assertRaisesRegex(ValueError,'DRAFT'):self.run_check()
    def test_missing_clearance(self):
        c,f=self.bundle();c['checks']['rights_export_review']=False
        with self.assertRaisesRegex(ValueError,'gates'):self.run_check(c,f)
    def test_stale_file(self):
        c,f=self.bundle();f['train'].write_text('changed')
        with self.assertRaisesRegex(ValueError,'bind'):self.run_check(c,f)
    def test_stale_record(self):
        c,f=self.bundle();self.rows['train'][0]['prompt']='MUTATED'
        with self.assertRaisesRegex(ValueError,'binding'):self.run_check(c,f)
    def test_alias_leak(self):
        c,f=self.bundle();c['canonical_group_map']['holdout']='A'
        with self.assertRaisesRegex(ValueError,'component'):self.run_check(c,f)
    def test_multitopic_leak(self):
        self.rows['train'][0]['additional_source_group_dependencies']=['holdout']
        with self.assertRaisesRegex(ValueError,'component'):self.run_check()
    def test_unmapped_dependency(self):
        self.rows['train'][0]['additional_source_group_dependencies']=['unknown']
        with self.assertRaisesRegex(ValueError,'Unmapped'):self.run_check()
    def test_same_source(self):
        self.rows['holdout'][0]['source_ids']=['train']
        with self.assertRaisesRegex(ValueError,'Same source'):self.run_check()
    def test_same_response(self):
        self.rows['holdout'][0]['response']=self.rows['train'][0]['response']
        with self.assertRaisesRegex(ValueError,'Same target'):self.run_check()
    def test_reserved(self):
        self.rows['train'][0]['prompt']+='<|turn>'
        with self.assertRaisesRegex(ValueError,'Reserved'):self.run_check()
    def test_assistant_loss(self):
        row=p.tokenized_record(self.rows['train'][0],ToyTokenizer(),10000)
        n=row['prompt_tokens'];self.assertTrue(all(x==-100 for x in row['labels'][:n]));self.assertEqual(row['labels'][n:],row['input_ids'][n:]);self.assertEqual(row['labels'][-1],999)
    def test_no_truncation(self):
        with self.assertRaisesRegex(ValueError,'Oversized'):p.tokenized_record(self.rows['train'][0],ToyTokenizer(),10)
    def test_bad_prefix(self):
        t=ToyTokenizer();t.apply_chat_template=lambda *a,**k:'wrong'
        with self.assertRaisesRegex(ValueError,'prefix'):p.tokenized_record(self.rows['train'][0],t,10000)
    def test_boundary_change(self):
        class Bad(ToyTokenizer):
            def __call__(self,text,**kwargs):
                r=super().__call__(text,**kwargs)
                if text.endswith('<turn|>') and len(text)>7:r['input_ids'][0]=0
                return r
        with self.assertRaisesRegex(ValueError,'boundary'):p.tokenized_record(self.rows['train'][0],Bad(),10000)
    def test_size(self):
        files=[self.root/'a.gguf',self.root/'p.gguf']
        for x in files:x.write_bytes(b'GGUF0000')
        self.assertEqual(p.check_artifacts(files)['total_bytes'],16)
        with self.assertRaisesRegex(ValueError,'exceed'):p.check_artifacts(files,15)
    def test_bad_magic(self):
        files=[self.root/'a.gguf',self.root/'p.gguf']
        for x in files:x.write_bytes(b'FAIL')
        with self.assertRaisesRegex(ValueError,'Not a GGUF'):p.check_artifacts(files)
    def test_aggregate_all_routes_and_adapter(self):
        files=[self.root/'base.gguf',self.root/'projector.gguf',self.root/'adapter.safetensors']
        for x in files:x.write_bytes(b'GGUF0000')
        self.assertEqual(p.check_artifacts(files,24)['remaining_bytes'],0)
        with self.assertRaisesRegex(ValueError,'Aggregate'):p.check_artifacts(files,23)
        self.assertEqual(p.check_artifacts(files)['limit_bytes'],8_800_000_000)
    def test_inventory_empty_missing_directory_or_duplicate(self):
        with self.assertRaisesRegex(ValueError,'Nonempty'):p.check_artifacts([])
        with self.assertRaises(FileNotFoundError):p.check_artifacts([self.root/'missing'])
        with self.assertRaisesRegex(ValueError,'regular'):p.check_artifacts([self.root])
        empty=self.root/'empty.bin';empty.write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'Nonempty'):p.check_artifacts([empty])
        weight=self.root/'weight.bin';weight.write_bytes(b'weights')
        with self.assertRaisesRegex(ValueError,'Duplicate'):p.check_artifacts([weight,weight])
    def test_hardlink_cannot_duplicate_inventory(self):
        weight=self.root/'weight.bin';weight.write_bytes(b'weights')
        alias=self.root/'alias.bin';alias.hardlink_to(weight)
        with self.assertRaisesRegex(ValueError,'Duplicate'):p.check_artifacts([weight,alias])
    def test_limit_cannot_be_relaxed(self):
        with self.assertRaisesRegex(ValueError,'Invalid aggregate'):p.check_artifacts([],8_800_000_001)
    def eval_bundle(self):
        c,f=self.bundle();c['accepted_records'].pop('holdout');c['files'].pop('holdout');f.pop('holdout')
        inputs=[{'id':'eval-only','prompt':'SYNTHETIC EVALUATION INPUT','source_group_id':'holdout'}]
        path=self.root/'eval.jsonl';path.write_text(json.dumps(inputs[0])+'\n');f['eval_inputs']=path;c['files']['eval_inputs']={'sha256':p.sha(path.read_bytes())};c['checks']['evaluation_inputs_group_audit']=True
        return c,f,inputs
    def test_eval_input_only(self):
        c,f,e=self.eval_bundle();r=p.validate_data(self.rows['train'],[],c,f,eval_inputs=e)
        self.assertFalse(r['evaluation_loss_enabled']);self.assertEqual(r['external_eval_input_count'],1)
    def test_eval_input_leak(self):
        c,f,e=self.eval_bundle();c['canonical_group_map']['holdout']='A'
        with self.assertRaisesRegex(ValueError,'overlaps'):p.validate_data(self.rows['train'],[],c,f,eval_inputs=e)
    def test_eval_requires_audit(self):
        c,f,e=self.eval_bundle();c['checks']['evaluation_inputs_group_audit']=False
        with self.assertRaisesRegex(ValueError,'audit'):p.validate_data(self.rows['train'],[],c,f,eval_inputs=e)
    def test_eval_rejects_target(self):
        c,f,e=self.eval_bundle();e[0]['response']='SYNTHETIC'
        with self.assertRaisesRegex(ValueError,'target fields'):p.validate_data(self.rows['train'],[],c,f,eval_inputs=e)

if __name__=='__main__':unittest.main()
