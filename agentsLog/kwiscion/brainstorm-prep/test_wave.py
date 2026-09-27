import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave as wave_module


class FakeHelper:
    def __init__(self,root,fail_second=False):self.root=root;self.fail_second=fail_second
    def read(self,p):return json.loads(Path(p).read_text())
    def write(self,p,v):
        Path(p).parent.mkdir(parents=True,exist_ok=True)
        with Path(p).open('x') as f:json.dump(v,f)
    def sha(self,p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    def need(self,x,reason):
        if not x:raise ValueError(reason)
    def remaining(self,m,now):return 3500-now
    def terminal(self,stage):
        selected=stage.name.startswith('selector')
        if selected and self.fail_second:raise ValueError('Simulated terminal failure')
        rows=[dict(id='x',answer='invalid selection')] if selected else [dict(id='x--A',answer='A exact \n'),dict(id='x--B',answer='B exact')]
        p=stage/'results/answers.json';self.write(p,dict(answers=rows))
        return dict(answers=p,statuses={x['id']:dict(placeholder=False,incomplete_partial=False) for x in rows},stop=None,calls=len(rows),requested_tokens=len(rows)*32768)


class FakeOperator:
    def __init__(self):self.events=[]
    def stage(self,source,label):self.events.append(('stage',label))
    def run(self,package,limit):self.events.append(('run',package.name,limit));return 0
    def verify_quiet(self,package):self.events.append(('quiet',package.name))


class WaveTests(unittest.TestCase):
    def run_case(self,root,failed=False):
        s=FakeHelper(root,failed);op=FakeOperator()
        s.write(root/'original/exam.json',dict(exam_id='synthetic',items=[dict(id='x',question='Original',images=[],source_text='All evidence',answer_format='Answer')]))
        def stage(root,source,label,m):
            p=root/wave_module.WORK/(label+'-runtime');s.write(p/'launch.json',dict(max_calls=4,max_requested_tokens=147456));return p
        m=dict(cache_source='/existing',selector_reserve_seconds=1200,max_calls=120,max_requested_tokens=4423680,deadline_utc='2026-09-27T04:00:00.000000+00:00')
        original=wave_module.policy.selection_rows
        with patch.object(wave_module,'helper',return_value=s),patch.object(wave_module,'declare_stage'),patch.object(wave_module,'package',return_value=root/'source'),patch.object(wave_module,'prepare_stage',side_effect=stage),patch.object(wave_module.policy,'selection_rows',side_effect=lambda e,a,t:original(e,a,t,['x'])):
            result=wave_module.sequence(root,m,op,clock=lambda:0)
        return s,op,result

    def test_sequential_cleanup_and_invalid_selection_retains_exact_a(self):
        with tempfile.TemporaryDirectory() as d:
            s,op,result=self.run_case(Path(d))
            self.assertEqual([e[0] for e in op.events],['stage','run','quiet','stage','run','quiet'])
            self.assertEqual(s.read(Path(d)/'answers.json')['answers'][0]['answer'],'A exact \n')
            self.assertEqual(s.read(Path(d)/'selection-receipt.json')[0]['mode'],'operational_fallback')
            self.assertEqual(op.events[1][2],2300)

    def test_selector_failure_preserves_durable_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            s,op,result=self.run_case(Path(d),True)
            self.assertTrue(result.startswith('operational_stop'))
            self.assertEqual(s.read(Path(d)/'answers.json')['answers'][0]['answer'],'A exact \n')
            self.assertTrue((Path(d)/'candidate-bindings.json').exists())


if __name__=='__main__':unittest.main()
