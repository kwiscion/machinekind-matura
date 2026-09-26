"""Network-free tests; no inference or service operations."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('thinking_runner',HERE/'run_gemma_full_thinking.py')
p=module('thinking_prepare',HERE/'prepare.py')
class Native:
    @staticmethod
    def native_source(c):return c['content'],['YWJj']
class Budget:
    def remaining(self):return 1000
def response(**changes):
    d={'model':r.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':100,'eval_count':99,'message':{'content':'Exact answer.','thinking':'Private reasoning.'}}
    d.update(changes);return d
class Tests(unittest.TestCase):
    def test_cold_native_worker_detected(self):
        self.assertTrue(r.competing_native(['/usr/bin/python3','/owned/scripts/reasoning_lab.py','--execute']))
        self.assertFalse(r.competing_native(['bash','-c','python reasoning_lab.py']))
    def test_payload_preserves_source_images_and_caps(self):
        c={'id':'arbitrary','content':'Original sources and all topics'}
        for cap in (10240,20480):
            b=r.payload(c,cap,Native)
            self.assertEqual(b['messages'],[{'role':'user','content':c['content'],'images':['YWJj']}])
            self.assertTrue(b['think']);self.assertFalse(b['truncate']);self.assertFalse(b['shift'])
            self.assertEqual(b['options'],{'num_ctx':32768,'num_predict':cap});self.assertNotIn('temperature',str(b))
    def test_structure_route_not_id_or_score(self):
        self.assertTrue(p.is_essay('Wybierz jeden z tematów. Minimum 300 wyrazów.'))
        self.assertFalse(p.is_essay('Zadanie 26. Podaj datę.'))
        self.assertFalse(p.is_essay('Napisz minimum 300 wyrazów bez wyboru.'))
    def test_complete_exact_answer(self):self.assertEqual(r.validate(response(),10240),('Exact answer.',None))
    def test_case_local_length_empty(self):
        for d in [response(done_reason='length'),response(message={'content':'','thinking':'reason'})]:
            a,e=r.validate(d,10240);self.assertEqual(a,'');self.assertIsNotNone(e)
    def test_systemic_flags_identity_context_usage(self):
        variants=[response(truncated=True),response(context_truncated=True),response(model='wrong'),response(prompt_eval_count=30000),response(eval_count=True),response(done_reason=None),response(message={'content':'answer','thinking':''})]
        for d in variants:
            with self.subTest(d=d),self.assertRaises(RuntimeError):r.validate(d,10240)
    def run_mock(self,replies,guard=lambda loaded:None,budget=None):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);out=Path(tmp.name)
        cases=[{'id':str(i),'content':'source'} for i in range(3)]
        m={'caps':{str(i):10240 for i in range(3)},'timeout_seconds':600,'base_url':'http://127.0.0.1:11436'}
        sent=[]
        def transport(*args):
            ledger=[json.loads(x) for x in (out/'calls.jsonl').read_text().splitlines()]
            self.assertEqual(len(ledger),len(sent)+1) # reservation exists before send
            sent.append(args[2]);return copy.deepcopy(replies[len(sent)-1])
        result=r.run_loop(cases,m,out,transport,guard,Native,budget or Budget())
        return result,sent,out
    def test_case_local_continues_no_retry(self):
        result,sent,out=self.run_mock([response(done_reason='length'),response(),response()])
        self.assertEqual(len(sent),3);self.assertEqual(result['calls'],3);self.assertFalse(result['unsent'])
        self.assertEqual(result['records'][0]['answer'],'');self.assertEqual(result['records'][1]['answer'],'Exact answer.')
    def test_systemic_stops_preserves_raw(self):
        bad=response(context_truncated=True)
        result,sent,out=self.run_mock([bad])
        self.assertEqual(len(sent),1);self.assertEqual(result['unsent'],['1','2'])
        self.assertEqual(result['records'][0]['raw_response'],bad);self.assertEqual(result['records'][0]['answer'],'')
    def test_runtime_failure_blanks_received_answer(self):
        def guard(loaded):
            if loaded:raise RuntimeError('wrong digest')
        result,sent,out=self.run_mock([response()],guard)
        self.assertEqual(len(sent),1);self.assertEqual(result['records'][0]['answer'],'')
    def test_deadline_no_dispatch(self):
        class Short:
            def remaining(self):return 600
        result,sent,out=self.run_mock([],budget=Short())
        self.assertEqual(sent,[]);self.assertEqual(len(result['unsent']),3)
    def test_adapter_retains_all_template_ids(self):
        repo=HERE.resolve().parents[2]
        a=module('adapter_test',repo/'scripts/Bukareszt/matura_package.py')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);outputs=root/'rows.jsonl';outputs.write_text(json.dumps({'id':'a','error':{'type':'length'},'raw_response':{'choices':[{'finish_reason':'stop','message':{'content':'must be blank'}}]}})+'\n')
            # Validate serializer against arbitrary IDs without touching real exam material.
            template={'exam_id':'synthetic','answers':[{'id':'a','answer':''},{'id':'b','answer':''}]}
            encoded=a.encode_submission(template)
            self.assertEqual(a.validate_submission_bytes(encoded,template),[])
            self.assertIsNotNone(a.extract_answer(json.loads(outputs.read_text()))[1])
if __name__=='__main__':unittest.main()
