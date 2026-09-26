"""CPU/socket-free preparation checks. These never launch Ollama or unshare."""
import io
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
import offline_rehearsal as r

class Preparation(unittest.TestCase):
    def test_waiting_bounded_dispatcher_blocks_even_with_empty_gpu_list(self):
        with tempfile.TemporaryDirectory(dir=r.OWN/'private',prefix='offline-process-test-') as tmp:
            proc=Path(tmp)
            (proc/'999999').mkdir()
            (proc/'999999/cmdline').write_bytes(b'/usr/bin/python3\0/repo/agentsLog/kwiscion/run_bounded_gemma.py\0--execute\0')
            with patch.object(r,'Path',side_effect=lambda value: proc if value=='/proc' else Path(value)), patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='',stderr='')):
                with self.assertRaisesRegex(RuntimeError,'inference runner'):
                    r.process_snapshot()

    def test_other_inference_helpers_block_but_rag_preparation_does_not(self):
        runners=('run_source_correction.py','run_local_smoke.py','run_smoke.py',
                 'run_gemma_source_crops.py','run_rag.py','run_rag_candidate.py')
        preparation=('prepare_rag.py','prepare_bounded_rag.py')
        with tempfile.TemporaryDirectory(dir=r.OWN/'private',prefix='offline-helper-test-') as tmp:
            proc=Path(tmp)
            (proc/'999999').mkdir()
            for name in runners+preparation:
                with self.subTest(helper=name):
                    (proc/'999999/cmdline').write_bytes(
                        ('/usr/bin/python3\0/repo/'+name+'\0').encode())
                    with patch.object(r,'Path',side_effect=lambda value: proc if value=='/proc' else Path(value)), patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='',stderr='')):
                        if name in runners:
                            with self.assertRaisesRegex(RuntimeError,'inference runner'):
                                r.process_snapshot()
                        else:
                            r.process_snapshot()

    def test_synthetic_adapter_and_two_mocked_transports(self):
        with tempfile.TemporaryDirectory(dir=r.OWN/'private',prefix='offline-fixture-test-') as tmp:
            out=Path(tmp)
            inf,adapter=r.modules()
            with patch('socket.socket',side_effect=AssertionError('network forbidden')):
                package=r.fixture(out,adapter)
                cases=inf.load_cases(out/'input.jsonl',2)
                config=inf.load_config(out/'config.json',False)
                self.assertEqual([c['id'] for c in cases],r.IDS)
                self.assertIsInstance(cases[0]['content'],str)
                self.assertTrue(cases[1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
                self.assertEqual(config['reasoning_effort'],'none')
                self.assertEqual(config['max_output_tokens'],1024)
                sent=[]
                class Transport:
                    def open(self,req,timeout):
                        sent.append(json.loads(req.data))
                        self_url=req.full_url
                        if self_url!=r.ENDPOINT+'/v1/chat/completions':
                            raise AssertionError('wrong endpoint')
                        answer={'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'synthetic-mock-answer'}}],
                                'usage':{'prompt_tokens':30,'completion_tokens':4}}
                        return io.BytesIO(json.dumps(answer).encode())
                inf.OPENER=Transport()
                rows=[inf.run_case(case,config) for case in cases]
                self.assertEqual(len(sent),2)
                self.assertEqual(sum(x['max_tokens'] for x in sent),2048)
                self.assertTrue(all(x['reasoning_effort']=='none' for x in sent))
                raw=out/'raw.jsonl'
                raw.write_text(''.join(json.dumps(x)+'\n' for x in rows))
                report=adapter.finalize(package,[raw],out/'answers.json',out/'failures.json',out/'input.jsonl.manifest.json')
                self.assertEqual(report['failures'],[])
                self.assertEqual(adapter.main(['validate',str(out/'answers.json'),'--exam-dir',str(out/'package')]),0)
                self.assertEqual([x['id'] for x in json.loads((out/'answers.json').read_text())['answers']],r.IDS)
                with self.assertRaises(ValueError):
                    inf.load_cases(out/'input.jsonl',1)

    def test_output_boundary_and_overwrite_refusal(self):
        with self.assertRaises(RuntimeError):
            r.output_path(r.ROOT/'private/not-ignored')
        with self.assertRaises(RuntimeError):
            r.output_path(r.OWN/'private')
        with tempfile.TemporaryDirectory(dir=r.OWN/'private',prefix='offline-boundary-test-') as tmp:
            with self.assertRaises(RuntimeError):
                r.output_path(tmp)

    def test_network_gate_refuses_host_namespace_before_ip_change(self):
        with patch.object(r.os,'readlink',return_value='net:[123]'),patch.object(r.subprocess,'run') as run:
            with self.assertRaises(RuntimeError):
                r.network_proof('net:[123]')
            run.assert_not_called()

    def test_no_argument_never_starts_process(self):
        with patch.object(r.sys,'argv',['offline_rehearsal.py']),patch.object(r.subprocess,'Popen') as popen:
            with self.assertRaises(SystemExit):
                r.main()
            popen.assert_not_called()

if __name__=='__main__':
    unittest.main()
