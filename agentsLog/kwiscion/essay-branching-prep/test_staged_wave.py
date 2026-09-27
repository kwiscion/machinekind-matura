import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('staged_wave_test',HERE/'staged_wave.py')
fixtures=load('branch_fixture',HERE/'test_branching.py')


class FakeOperator:
    def __init__(self,root,clock,fail=None,partial=False):
        self.root=root;self.clock=clock;self.fail=fail;self.partial=partial;self.events=[];self.live=False
    def stage(self,source,label):
        assert not self.live
        self.events.append(('cache',label))
    def verify_quiet(self,package):
        assert not self.live
        self.events.append(('quiet',package.name))
    def run(self,package,limit):
        assert not self.live
        self.live=True;self.events.append(('run',package.name,limit))
        runner=w.load('fake_packed_runtime',package/'run_recovery_package.py')
        m,p,cases=runner.preflight(package)
        out=package/'results';out.mkdir()
        parent=self
        class CPU:
            def verify(self,context):assert context==65536
            def quiesce(self,deadline):return True
            def send(self,body,timeout):
                assert body['truncate'] is False and body['shift'] is False
                parent.clock[0]+=1
                label='selected' if package.name.startswith('selector') else 'draft'
                return dict(model=runner.r.MODEL,done=True,done_reason='length' if parent.partial and label=='selected' else 'stop',
                    prompt_eval_count=1000,eval_count=500,message={'content':label+' '+('word '*399).strip()})
        runner.r.run(cases,p['template'],out/'engine',m['recovery'],CPU(),dt.datetime.fromisoformat(m['deadline_utc']).timestamp(),clock=lambda:self.clock[0])
        runner.final_export(package,m,cases,p)
        self.live=False
        if self.fail==package.name:return 2
        return 0


class Tests(unittest.TestCase):
    def fixture(self):
        private=HERE.parents[2]/'agentsLog/kwiscion/private';private.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(prefix='branch-cpu-',dir=private);self.addCleanup(temp.cleanup)
        base=Path(temp.name);source,item=fixtures.Tests().fixture(base)
        root=base/'wave'
        lock=str(base/'host.lock') if os.name=='posix' else '/synthetic/host.lock'
        m=w.prepare(source,item['id'],root,'/synthetic/remote/wave','/synthetic/cache','/synthetic/bin/ollama',lock)
        clock=[100.]
        m.update(status='DECLARED',declared_utc='1970-01-01T00:01:40+00:00',deadline_utc='1970-01-01T01:01:40+00:00',
          authorization=dict(owner='root',reference='CPU fixture only; not generation authorization',
            max_calls=m['max_calls'],max_requested_tokens=m['max_requested_tokens'],max_seconds=3600,above_240k_explicit=True))
        (root/'wave.json').write_text(json.dumps(m),encoding='utf8')
        return root,m,clock

    def run_sequence(self,root,m,clock,op):
        # Runtime preflight validates the same declaration with real wallclock;
        # isolate only that clock check in fake-provider tests.
        from unittest.mock import patch
        with patch('time.time',side_effect=lambda:clock[0]):return w.sequence(root,m,op,clock=lambda:clock[0])

    def test_sequence_deadline_source_preservation_and_no_replay(self):
        root,m,clock=self.fixture();op=FakeOperator(root,clock)
        outcome=self.run_sequence(root,m,clock,op)
        self.assertEqual(outcome['mode'],'same_model_selected')
        self.assertEqual([x[:2] for x in op.events],[('cache','drafts'),('run','drafts-runtime'),('quiet','drafts-runtime'),('cache','selector'),('run','selector-runtime'),('quiet','selector-runtime')])
        for label in ('drafts','selector'):
            stage=root/w.WORK/(label+'-runtime');sm=w.read(stage/'launch.json')
            self.assertEqual(sm['declared_utc'],m['declared_utc']);self.assertEqual(sm['deadline_utc'],m['deadline_utc'])
        receipt=w.read(root/'wave-terminal.json');self.assertEqual(receipt['calls'],5)
        self.assertEqual(receipt['requested_tokens'],5*32768)
        raw=root/'selector-source/raw-candidates.answers.json'
        self.assertEqual(raw.read_bytes(),(root/w.WORK/'drafts-runtime/results/answers.json').read_bytes())
        selected=w.read(root/'answers.json');self.assertEqual(set(selected),{'exam_id','answers'});self.assertEqual(selected['answers'][0]['id'],'actual-essay')
        source=w.read(root/'selector-source/exam/exam.json')['items'][0]
        self.assertIn('Pełne źródło',source['source_text']);self.assertEqual(len(source['images']),1)
        self.assertIn('incomplete_partial',source['question'])
        with self.assertRaises(FileExistsError):self.run_sequence(root,m,clock,FakeOperator(root,clock))

    def test_failed_draft_stage_preserves_control_without_selector(self):
        root,m,clock=self.fixture();op=FakeOperator(root,clock,fail='drafts-runtime')
        result=self.run_sequence(root,m,clock,op)
        self.assertEqual(result['mode'],'direct_baseline_fallback');self.assertFalse((root/'selector-source').exists())
        raw=w.read(root/w.WORK/'drafts-runtime/results/answers.json')['answers'][0]['answer']
        self.assertEqual(w.read(root/'answers.json')['answers'][0]['answer'],raw)

    def test_partial_selector_is_not_promoted_over_complete_control(self):
        root,m,clock=self.fixture();op=FakeOperator(root,clock,partial=True)
        result=self.run_sequence(root,m,clock,op)
        self.assertEqual(result['mode'],'direct_baseline_fallback')
        self.assertFalse(result['submitted_status']['incomplete_partial'])
        self.assertTrue(w.read(root/'selector-terminal.json')['statuses']['actual-essay']['incomplete_partial'])
        self.assertEqual(w.read(root/'wave-terminal.json')['calls'],8)

    def test_deadline_does_not_reset_or_dispatch_when_draft_window_gone(self):
        root,m,clock=self.fixture();clock[0]=3150;op=FakeOperator(root,clock)
        result=self.run_sequence(root,m,clock,op)
        self.assertEqual(result['mode'],'no_terminal_control')
        self.assertFalse(any(x[0]=='run' for x in op.events))
        self.assertEqual(w.read(root/'wave-terminal.json')['calls'],0)
        changed=dict(m,deadline_utc='1970-01-01T02:01:40+00:00')
        with self.assertRaises(ValueError):w.remaining(changed,100)
        with self.assertRaises(ValueError):w.remaining(dict(m,deadline_utc='1970-01-01T01:01:40.1234567+00:00'),100)
        self.assertGreater(w.remaining(dict(m,deadline_utc='1970-01-01T01:01:39.123456+00:00'),100),3599)

    def test_stage_intent_is_durable_before_spawn_can_be_interrupted(self):
        from unittest.mock import patch
        root,m,_=self.fixture();package=root/w.WORK/'drafts-runtime';observed=[]
        def interrupted(*args,**kwargs):
            record=w.read(root/'active-stage.json');observed.append(record)
            self.assertIsNone(record['pid']);self.assertEqual(record['relative'],package.relative_to(root).as_posix())
            raise KeyboardInterrupt('synthetic death before PID receipt')
        with patch.object(w.subprocess,'Popen',side_effect=interrupted),patch.object(w,'cleanup') as cleanup:
            with self.assertRaises(KeyboardInterrupt):w.Operator(root,m).run(package,30)
            cleanup.assert_called_once_with(root)
        self.assertEqual(len(observed),1)

    @unittest.skipUnless(os.name=='posix','POSIX owned-child interruption fixture')
    def test_missing_pid_receipt_still_kills_actual_owned_cpu_child(self):
        from unittest.mock import patch
        root,m,_=self.fixture();package=root/w.WORK/'drafts-runtime';children=[]
        popen=subprocess.Popen
        def interrupted(*args,**kwargs):
            child=popen([sys.executable,'-c','import time;time.sleep(60)',str(package/'run_recovery_package.py'),'--execute'],start_new_session=True)
            children.append(child)
            raise KeyboardInterrupt('synthetic death after spawn before PID capture')
        try:
            with patch.object(w.subprocess,'Popen',side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt):w.Operator(root,m).run(package,30)
            self.assertEqual(children[0].wait(timeout=5),-9)
            self.assertIsNone(w.read(root/'active-stage.json')['pid'])
        finally:
            for child in children:
                if child.poll() is None:child.kill();child.wait(timeout=5)

    def test_cleanup_uncertainty_blocks_selector_but_preserves_durable_control(self):
        root,m,clock=self.fixture();op=FakeOperator(root,clock)
        def uncertain(package):raise ValueError('Synthetic cleanup uncertainty')
        op.verify_quiet=uncertain
        result=self.run_sequence(root,m,clock,op)
        self.assertEqual(result['mode'],'direct_baseline_fallback')
        self.assertFalse((root/'selector-source').exists())
        self.assertEqual(w.read(root/'wave-terminal.json')['calls'],4)
        self.assertIn('cleanup uncertainty',result['reason'])

    def test_guardian_preserves_already_exported_answer_without_false_baseline_claim(self):
        from unittest.mock import patch
        root,m,clock=self.fixture();self.run_sequence(root,m,clock,FakeOperator(root,clock))
        answer=(root/'answers.json').read_bytes();(root/'wave-terminal.json').unlink()
        with patch.object(w,'cleanup'),patch('sys.argv',['staged_wave.py','cleanup',str(root)]):
            w.main();w.main()
        self.assertEqual((root/'answers.json').read_bytes(),answer)
        self.assertEqual(w.read(root/'guardian-terminal.json')['outcome']['mode'],'existing_export_preserved')

    @unittest.skipUnless(os.name=='posix','POSIX host-lock fixture')
    def test_second_host_lock_is_refused(self):
        import fcntl
        root,m,_=self.fixture()
        with Path(m['host_lock']).open('a') as one:
            fcntl.flock(one,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=subprocess.run(['bash',str(root/'operator_wave.sh'),str(root)],capture_output=True,timeout=20)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'CPU_PREFLIGHT_PASS',result.stdout)
        self.assertFalse((root/'execution-once.json').exists())


if __name__=='__main__':unittest.main()
