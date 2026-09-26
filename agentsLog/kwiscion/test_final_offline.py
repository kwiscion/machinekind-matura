"""Invented package/mocked transport only: no server, namespace or GPU launch."""
import argparse
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import run_gemma_package as f


class FinalOffline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=f.r.OWN/'private', prefix='final-launch-test-')
        self.root = Path(self.tmp.name)
        self.inf, self.adapter = f.r.modules()
        fixture = f.r.ROOT/'agentsLog/Bukareszt/submission/fixtures/tiny-package'
        import shutil
        self.pkg = self.root/'package'
        shutil.copytree(fixture,self.pkg)
        exam = json.loads((self.pkg/'exam.json').read_text())
        # Arbitrary IDs and a third unsent item, independent of validation exam IDs.
        exam['items'] = [dict(exam['items'][0], id='alpha'),dict(exam['items'][1], id='B/2'),dict(exam['items'][0], id='last')]
        exam['max_points'] = sum(x['max_points'] for x in exam['items'])
        (self.pkg/'exam.json').write_text(json.dumps(exam),encoding='utf-8')
        (self.pkg/'answers-template.json').write_text(json.dumps({'exam_id':exam['exam_id'],
            'answers':[{'id':i['id'],'answer':''} for i in exam['items']]}),encoding='utf-8')
        self.args = argparse.Namespace(output=self.root/'new-run', exam_dir=self.pkg,
            config=f.r.ROOT/'outputs/local-smoke/gemma4-12b-val40-1024.config.json',
            max_calls=3,max_output_tokens_total=3072,wall_seconds=1800)

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_preflight_preserves_ids_and_never_calls_runtime(self):
        with patch('socket.socket',side_effect=AssertionError('network')), patch.object(f.subprocess,'Popen',side_effect=AssertionError('process')):
            out,pkg,cfg,record = f.preflight(self.args)
        self.assertEqual(record['ids'],['alpha','B/2','last'])
        self.assertFalse(out.exists())
        self.assertEqual(cfg['max_output_tokens'],1024)
        self.assertTrue(any(p.endswith('.png') for p in record['package_files']))

    def test_wrong_pin_budget_and_fresh_output_refused(self):
        with patch.object(f.r,'sha',return_value='bad'):
            with self.assertRaisesRegex(RuntimeError,'hash mismatch'): f.preflight(self.args)
        self.args.max_output_tokens_total=9999
        with self.assertRaisesRegex(RuntimeError,'budget'): f.preflight(self.args)
        self.args.max_output_tokens_total=3072
        self.args.output.mkdir()
        with self.assertRaisesRegex(RuntimeError,'Fresh'): f.preflight(self.args)

    def prepared(self):
        out,package,config,_=f.preflight(self.args)
        out.mkdir()
        self.adapter.prepare(package,out/'input.jsonl')
        return out,package,config,self.inf.load_cases(out/'input.jsonl',3)

    def test_failure_and_unsent_ids_finalize_as_blanks(self):
        out,package,config,cases=self.prepared()
        self.assertTrue(any(isinstance(c['content'],list) for c in cases))
        ok={'id':'alpha','error':None,'usage':{'prompt_tokens':20,'completion_tokens':2},
            'raw_response':{'choices':[{'finish_reason':'stop','message':{'content':'Exact answer'}}]}}
        failed={'id':'B/2','error':{'type':'incomplete','message':'length'},'raw_response':{}}
        with patch.object(self.inf,'run_case',side_effect=[ok,failed]) as call:
            result=f.request_loop(cases,config,out,3,time.monotonic()+1800,lambda:None,lambda:None,self.inf)
        self.assertEqual(call.call_count,2)
        self.assertEqual(result['unsent_ids'],['last'])
        report=f.finalize(out,package)
        answers=json.loads((out/'answers.json').read_text())['answers']
        self.assertEqual(answers,[{'id':'alpha','answer':'Exact answer'},{'id':'B/2','answer':''},{'id':'last','answer':''}])
        self.assertEqual(report['empty'],2)

    def test_worker_refusal_and_wall_bound_send_nothing(self):
        out,package,config,cases=self.prepared()
        def blocked(): raise RuntimeError('competing worker')
        with patch.object(self.inf,'run_case',side_effect=AssertionError('no inference')):
            result=f.request_loop(cases,config,out,3,time.monotonic()+1800,blocked,lambda:None,self.inf)
        self.assertEqual(result['unsent_ids'],['alpha','B/2','last'])
        self.assertEqual(f.finalize(out,package)['empty'],3)
        other=self.root/'short'; other.mkdir()
        with patch.object(self.inf,'run_case',side_effect=AssertionError('no inference')):
            result=f.request_loop(cases,config,other,3,time.monotonic()+10,lambda:None,lambda:None,self.inf)
        self.assertIn('wall budget',result['stop_reason'])

    def test_changed_frozen_file_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Frozen file changed'):
            f.verify_pins({str(self.pkg/'exam.json'):'0'*64})

    def test_launcher_validation_failures_stop_and_export_blanks(self):
        import copy
        for kind in ('missing_usage','runtime_mismatch','unknown_finish'):
            with self.subTest(kind=kind):
                self.args.output=self.root/kind
                out,package,config,cases=self.prepared()
                row={'id':'alpha','error':None,'usage':{'prompt_tokens':20,'completion_tokens':2},
                     'raw_response':{'choices':[{'finish_reason':'stop','message':{'content':'Preserve raw'}}]}}
                if kind=='missing_usage': row.pop('usage')
                if kind=='unknown_finish': row['raw_response']['choices'][0]['finish_reason']='unknown'
                original=copy.deepcopy(row['raw_response'])
                def verify():
                    if kind=='runtime_mismatch': raise RuntimeError('wrong runtime')
                with patch.object(self.inf,'run_case',return_value=row) as call:
                    result=f.request_loop(cases,config,out,3,time.monotonic()+1800,lambda:None,verify,self.inf)
                self.assertEqual(call.call_count,1)
                saved=json.loads((out/'raw.jsonl').read_text())
                self.assertEqual(saved['raw_response'],original)
                self.assertIsNotNone(saved['error'])
                self.assertEqual(result['unsent_ids'],['B/2','last'])
                self.assertEqual(f.finalize(out,package)['empty'],3)

    def test_core_call_limit_is_not_bypassed(self):
        self.args.max_calls=101
        self.args.max_output_tokens_total=101*1024
        with self.assertRaisesRegex(RuntimeError,'maximum calls'): f.preflight(self.args)

    def test_guard_allows_exact_supervisor_but_blocks_other_cold_launcher(self):
        proc=self.root/'proc'; (proc/'999991').mkdir(parents=True)
        (proc/'999991/cmdline').write_bytes(b'python3\0/repo/run_gemma_package.py\0--execute\0')
        with patch.object(f,'Path',side_effect=lambda x:proc if x=='/proc' else Path(x)), \
             patch.object(f.subprocess,'run',return_value=f.subprocess.CompletedProcess([],0,stdout='')):
            f.worker_guard(parent_pid=999991)
            with self.assertRaisesRegex(RuntimeError,'Competing inference'):
                f.worker_guard(parent_pid=999992)

    def test_cleanup_requires_matching_group_and_namespace(self):
        out=self.root/'cleanup'; out.mkdir()
        f.r.write(out/'server-pid.json',{'process_group':123,'namespace':'net:[owned]'})
        proc=self.root/'proc'; (proc/'123').mkdir(parents=True)
        for namespace,expected in [('net:[other]',False),('net:[owned]',True)]:
            with patch.object(f,'Path',side_effect=lambda x:proc if x=='/proc' else Path(x)), \
                 patch.object(f.os,'getpgid',return_value=123,create=True), patch.object(f.os,'readlink',return_value=namespace), \
                 patch.object(f.os,'killpg',create=True) as kill, patch.object(f.signal,'SIGKILL',9,create=True):
                f.cleanup_owned(out)
                self.assertEqual(kill.called,expected)


if __name__=='__main__': unittest.main()
