import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import matched_pair as m

fixtures=m.load('pair_fixtures',m.REPO/m.PREFIX/'essay-branching-prep/test_staged_wave.py')


class Tests(unittest.TestCase):
    def fixture(self):
        (m.REPO/m.PREFIX/'private').mkdir(parents=True,exist_ok=True)
        tmp=tempfile.TemporaryDirectory(dir=m.REPO/m.PREFIX/'private',prefix='coverage-test-');self.addCleanup(tmp.cleanup)
        base=Path(tmp.name);src,item=fixtures.fixtures.Tests().fixture(base);root=base/'pair'
        manifest=m.prepare(src,item['id'],root,'/synthetic/pair','/synthetic/cache','/synthetic/bin','/synthetic/lock')
        manifest.update(status='DECLARED',declared_utc='1970-01-01T00:01:40+00:00',deadline_utc='1970-01-01T01:01:40+00:00',authorization=dict(owner='root',reference='CPU-only synthetic test',max_calls=8,max_requested_tokens=294912,max_seconds=3600,above_240k_explicit=True))
        (root/'wave.json').write_text(json.dumps(manifest));return root,manifest,item

    def test_complete_source_same_id_and_sequence_no_replay(self):
        root,manifest,item=self.fixture();s=m.helper(root);clock=[100.]
        control=s.read(root/'control-source/exam/exam.json')['items'][0]
        candidate=s.read(root/'candidate-source/exam/exam.json')['items'][0]
        self.assertEqual(control,item)
        self.assertTrue(candidate['question'].startswith(item['question']))
        self.assertEqual({k:v for k,v in candidate.items() if k!='question'},{k:v for k,v in item.items() if k!='question'})
        self.assertEqual((root/'candidate-source/exam/images/x.png').read_bytes(),fixtures.fixtures.PNG)
        op=fixtures.FakeOperator(root,clock)
        with patch('time.time',side_effect=lambda:clock[0]):results=m.sequence(root,manifest,op,clock=lambda:clock[0])
        self.assertEqual([x['arm'] for x in results],['control','candidate'])
        self.assertEqual([x[1] for x in op.events if x[0]=='run'],['control-runtime','candidate-runtime'])
        self.assertLess(op.events[1][2],1800)
        for label in ('control','candidate'):
            self.assertEqual(s.read(root/s.WORK/(label+'-runtime/launch.json'))['deadline_utc'],manifest['deadline_utc'])
        with self.assertRaises(FileExistsError):m.sequence(root,manifest,op)

    def test_cleanup_failure_stops_next_arm_and_preserves_accounting(self):
        root,manifest,item=self.fixture();clock=[100.];op=fixtures.FakeOperator(root,clock)
        def bad(package):raise ValueError('synthetic ownership failure')
        op.verify_quiet=bad
        with patch('time.time',side_effect=lambda:clock[0]),self.assertRaisesRegex(ValueError,'ownership'):
            m.sequence(root,manifest,op,clock=lambda:clock[0])
        self.assertEqual([x[1] for x in op.events if x[0]=='run'],['control-runtime'])
        self.assertGreater(json.loads((root/'pair-terminal.json').read_text())['calls'],0)


if __name__=='__main__':unittest.main()
