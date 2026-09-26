"""Synthetic CPU checks only. No exam keys, inference, services or network."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path); obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj
r=module('recovery_test',HERE/'run_gemma_answer_recovery.py')
c=module('control_test',HERE.parent/'full-thinking-prep/run_gemma_full_thinking.py')
a=module('adapter_recovery_test',REPO/'scripts/Bukareszt/matura_package.py')

def prior(i='arbitrary', error='length', note='All notes\nincluding a false claim and final fragment.'):
    return {'id':i,'error':{'type':error} if error else None,'raw_response':{'prompt_eval_count':1000,'eval_count':10240,'message':{'thinking':note,'content':'partial final ignored'}}}
def response(**updates):
    obj={'model':r.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':1000,'eval_count':30,
         'message':{'content':'  Exact final.\n'}}
    obj.update(updates);return obj
class Native:
    @staticmethod
    def native_source(case):return case['content'],['original-encoded-image-one','original-encoded-image-two']
class Budget:
    def remaining(self):return 1000

class Tests(unittest.TestCase):
    def test_error_only_selection_and_exact_preservation(self):
        inputs=[{'id':i,'prompt':'opaque unchanged source\n'+i,'images':['same.png']} for i in ['random-9','unrelated','empty','systemic']]
        records=[prior('empty','empty_final'),prior('systemic','systemic'),prior('unrelated',None),prior('random-9')]
        chosen=r.select_failures(inputs,records)
        self.assertEqual(chosen,[inputs[0],inputs[2]])
        changed=[dict(row,prompt='different topic',score=0) for row in inputs]
        self.assertEqual([x['id'] for x in r.select_failures(changed,records)],['random-9','empty'])
    def test_duplicates_and_incomplete_terminal_rejected(self):
        for inputs,records in [([{'id':'x'},{'id':'x'}],[prior('x'),prior('x')]),([{'id':'x'}],[])]:
            with self.assertRaises(RuntimeError):r.select_failures(inputs,records)
    def test_payload_original_message_and_full_fallible_notes(self):
        case={'id':'arbitrary','content':'ORIGINAL\nUnicode źródło; do not modify.'}; old=prior()
        bare=r.payload(case,'A',old,Native); notes=r.payload(case,'B',old,Native)
        self.assertEqual(bare['messages'][0],notes['messages'][0])
        self.assertEqual(bare['messages'][0]['content'],case['content'])
        self.assertEqual(len(bare['messages']),1)
        encoded=notes['messages'][1]['content'].split('\n',1)[1]
        self.assertEqual(json.loads(encoded)['fallible_interrupted_notes'],old['raw_response']['message']['thinking'])
        self.assertNotIn('partial final ignored',encoded)
        for body in (bare,notes):
            self.assertEqual(body['options'],{'num_ctx':32768,'num_predict':2048})
            for field in ('think','truncate','shift'):self.assertIs(body[field],False)
            self.assertNotIn('temperature',body['options'])
    def test_malformed_notes_no_fallback_or_clipping(self):
        for note in (None,[],{},'', '  ', 'nul\x00text','bad\ud800'):
            self.assertEqual(r.note_error(prior(note=note))['type'],'malformed_notes')
        old=prior();old['raw_response']['eval_count']=30000
        self.assertEqual(r.note_error(old)['type'],'notes_context_budget')
        old=prior();old['raw_response']['prompt_eval_count']=True
        self.assertEqual(r.note_error(old)['type'],'malformed_notes')
    def test_nonthinking_success_exact_final(self):
        self.assertEqual(r.validate(response()),('  Exact final.\n',None))
        self.assertEqual(r.validate(response(message={'content':'ok','thinking':''})),('ok',None))
    def test_actual_context_boundaries_and_usage(self):
        self.assertIsNone(r.validate(response(prompt_eval_count=30720))[1])
        for update in ({'prompt_eval_count':30721},{'eval_count':2049},{'eval_count':True},{'model':'other'},
                       {'truncated':True},{'context_truncated':True},{'truncated':'false'},{'done':False}):
            with self.subTest(update=update),self.assertRaises(RuntimeError):r.validate(response(**update))
    def mocked(self,replies,budget=None,records=None):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);out=Path(tmp.name)
        cases=[{'id':str(i),'content':'all sources'} for i in range(3)]
        sent=[]; m={'timeout_seconds':180,'base_url':'http://127.0.0.1:11436'}
        def transport(base,route,body,b):
            ledger=r.read_rows(out/'calls.jsonl')
            self.assertEqual(len(ledger),len(sent)+1)
            self.assertEqual(ledger[-1]['cumulative_requested_tokens'],len(ledger)*2048)
            self.assertEqual(ledger[-1]['arm'],('A','B')[len(sent)%2] if not records else ledger[-1]['arm'])
            sent.append(body)
            value=replies[len(sent)-1]
            if isinstance(value,Exception):raise value
            return copy.deepcopy(value)
        result=r.run_loop(cases,records or [prior(str(i)) for i in range(3)],m,out,transport,lambda loaded:None,Native,budget or Budget(),c.append)
        return result,sent,out
    def test_all_six_durable_caps_no_retries(self):
        result,sent,out=self.mocked([response()]*6)
        self.assertEqual((result['calls'],result['requested_tokens'],len(sent)),(6,12288,6));self.assertEqual(result['unsent'],[])
        self.assertEqual(len(r.read_rows(out/'requests.jsonl')),6)
    def test_failed_then_valid_and_transport_stop(self):
        result,sent,_=self.mocked([response(done_reason='length'),response(message={'content':''}),response(),RuntimeError('transport')])
        self.assertEqual(len(sent),4);self.assertEqual(len(result['unsent']),2)
        self.assertEqual([x['answer'] for x in result['records'][:2]],['',''])
        self.assertEqual(result['records'][-1]['error']['type'],'systemic')
    def test_context_rejection_blanks_and_stops(self):
        result,sent,_=self.mocked([response(),response(prompt_eval_count=32000)])
        self.assertEqual(len(sent),2);self.assertEqual(result['records'][-1]['answer'],'');self.assertEqual(len(result['unsent']),4)
    def test_unexpected_thinking_is_systemic_not_a_success(self):
        result,sent,_=self.mocked([response(message={'content':'apparently valid','thinking':'unexpected reasoning'})])
        self.assertEqual(len(sent),1);self.assertEqual(result['records'][0]['answer'],'')
        self.assertEqual(result['records'][0]['error']['type'],'systemic');self.assertEqual(len(result['unsent']),5)
    def test_invalid_notes_keep_denominator_without_call(self):
        result,sent,_=self.mocked([response()]*3,records=[prior(str(i),note=None) for i in range(3)])
        self.assertEqual(len(sent),3);self.assertEqual(len(result['records']),6);self.assertEqual(result['unsent'],[])
        self.assertEqual([x['error']['type'] for x in result['records'] if x['arm']=='B'],['malformed_notes']*3)
    def test_deadline_no_dispatch(self):
        class Short:
            def remaining(self):return 185
        result,sent,_=self.mocked([],budget=Short())
        self.assertEqual(sent,[]);self.assertEqual(len(result['unsent']),6)
    def test_real_adapter_preserves_template_failed_and_unsent_blanks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);exam=root/'exam';exam.mkdir();out=root/'results';out.mkdir()
            ids=['0','1','2','not-selected']
            doc={'exam_id':'synthetic','instructions':'Original instructions','items':[
                {'id':i,'question':'Synthetic question','source_text':'Synthetic source','answer_format':'text','max_points':1,'images':[]} for i in ids]}
            template={'exam_id':'synthetic','answers':[{'id':i,'answer':''} for i in ids]}
            (exam/'exam.json').write_text(json.dumps(doc));(exam/'answers-template.json').write_text(json.dumps(template))
            result={'records':[{'id':'0','arm':'A','answer':'exact answer','error':None},
                               {'id':'1','arm':'A','answer':'not allowed through','error':{'type':'length'}}]}
            r.finalize(root,result,a,out,ids[:3])
            for arm in ('A','B'):
                blob=(out/arm/'answers.json').read_bytes()
                self.assertEqual(a.validate_submission_bytes(blob,template),[])
                vals={x['id']:x['answer'] for x in json.loads(blob)['answers']}
                self.assertEqual(list(vals),ids)
                self.assertEqual(vals['1'],'');self.assertEqual(vals['2'],'');self.assertEqual(vals['not-selected'],'')
                self.assertEqual(len(r.read_rows(out/arm/'selected-answers.jsonl')),3)
            self.assertEqual(json.loads((out/'A/answers.json').read_text())['answers'][0]['answer'],'exact answer')

if __name__=='__main__':unittest.main()
