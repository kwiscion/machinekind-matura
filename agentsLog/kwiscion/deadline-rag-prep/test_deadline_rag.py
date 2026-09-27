"""CPU tests exercise the generated binding, real recovery scheduler and fake clock."""
import copy
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

import prepare_deadline_rag as prep
import deadline_runtime as policy

sys.path.insert(0, str(prep.HERE.parent / 'filtered-rag-prep'))
import deadline_hook

fixtures = prep.load('deadline_fixture', prep.HERE.parent / 'final-package-prep/test_native_package.py')


class Tests(unittest.TestCase):
    def fixture(self, count=4, essays=('essay-custom',)):
        helper = fixtures.Tests()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        source, *_ = helper.package(count=count, essays=essays)
        args = SimpleNamespace(exam_dir=source / 'exam', output=source.with_name('deadline'),
            model='qwen', minutes=60, essay_id=list(essays), no_essay=not essays,
            cache='/owned/single-qwen', binary='/owned/runtime/ollama', lock='/owned/worker.lock',
            index='/owned/full-wikipedia.sqlite')
        args.index_proof=source.with_name('synthetic-index-proof.json')
        policy.atomic(args.index_proof,dict(schema='pre_acquisition_full_index_v1',index_path=args.index,
            sha256=prep.INDEX_SHA,bytes=prep.INDEX_BYTES,hostname='synthetic',boot_id='synthetic',
            stat=dict(st_dev=1,st_ino=1,st_size=prep.INDEX_BYTES,st_mtime_ns=1,st_ctime_ns=1)))
        before = {path.relative_to(args.exam_dir).as_posix(): prep.coverage.sha(path)
                  for path in args.exam_dir.rglob('*') if path.is_file()}
        manifest = prep.prepare(args)
        binding = prep.load('deadline_test_binding', args.output / 'run_recovery_package.py')
        manifest, package, cases = binding.preflight(args.output)
        for rel, digest in before.items():
            self.assertEqual(prep.coverage.sha(args.exam_dir / rel), digest)
        return args, binding, manifest, package, cases

    def test_preparation_exact_baseline_inputs_and_arbitrary_ids(self):
        args, binding, manifest, package, cases = self.fixture()
        root = args.output
        plan = policy.read(root / 'study.json')
        self.assertEqual(len(cases), 4+7*3)
        self.assertEqual(manifest['max_calls'], 4*(4+7*3))
        self.assertEqual(manifest['max_requested_tokens'], 7*147456 + 3*(3584+5*3456))
        self.assertEqual([c['id'] for c in cases[:4]], manifest['ids'])
        self.assertEqual([s['original_id'] for s in plan['stages'].values() if s['kind']=='query'],
                         [x['id'] for x in policy.read(root/'source-template.json')['answers'] if x['id']!='essay-custom'])
        self.assertFalse(any(s['original_id']=='essay-custom' and s['kind']!='direct' for s in plan['stages'].values()))
        # The additive transform never rewrites input rows or organizer inputs.
        baseline = policy.read(root/'coverage-prepared.json')
        for rel in ['input.jsonl','input.original.jsonl','exam/exam.json','exam/answers-template.json','exam/images/red.png','closed_profile.py']:
            self.assertEqual(prep.coverage.sha(root/rel), baseline['files'][rel])
        for rel,digest in manifest['files'].items():
            self.assertEqual(prep.coverage.sha(root/rel),digest)

    def test_exact_direct_payload_and_auxiliary_caps_images(self):
        args,binding,m,package,cases=self.fixture()
        r=binding.r
        originals=[r.step(case,0,[],m['recovery']) for case in cases[:4]]
        hook=deadline_hook.install(args.output,r)
        for case,expected in zip(cases[:4],originals):
            self.assertEqual(hook.step(case,0,[],m['recovery']),expected)
        passage={'article_id':'synthetic','title':'Synthetic','url':'https://example.invalid','start':0,'text':'Exact synthetic span.'}
        hook.retrieval=lambda source:{'passages':[passage]*5}
        hook.answer=lambda slot:None
        for case in cases[4:]:
            stage=hook.plan['stages'][case['id']]
            original_case=next(c for c in cases[:4] if c['id']==stage['original_id'])
            text,images=r.source(original_case)
            for attempt in range(4):
                body,settings=hook.step(case,attempt,[],m['recovery'])
                self.assertIn(text,body['messages'][0]['content'])
                self.assertEqual(body['messages'][0].get('images',[]),images)
                if stage['kind'] in ('query','judge'):
                    self.assertFalse(body['think'])
                    expected=(512 if stage['kind']=='query' else 384) if attempt==0 else 1024
                    self.assertEqual(settings['cap'],expected)
                    self.assertEqual(body['options']['num_predict'],expected)
                else:
                    self.assertEqual(settings['cap'],32768)
                    self.assertEqual(body['think'],attempt<2)

    def exercise(self, fail_kind=None, fail_direct=False, duration=1, start=0, cutoff_kind=None, reject_judges=False, late_kind=None):
        args,binding,m,package,cases=self.fixture()
        r=binding.r
        hook=deadline_hook.install(args.output,r)
        passage={'article_id':'synthetic','title':'Synthetic','url':'https://example.invalid','start':0,'text':'Exact synthetic span.'}
        hook.retrieval=lambda source:{'passages':[passage]*5}
        now=[float(start)]
        seen=[]
        class Runtime:
            def verify(self,context):pass
            def quiesce(self,deadline):return True
            def send(self,body,timeout):
                stage=copy.deepcopy(hook.current)
                seen.append((stage,copy.deepcopy(body),timeout,now[0]))
                now[0]+=min(duration,timeout)
                if stage['kind']==cutoff_kind:
                    now[0]=hook.optional_deadline
                    raise TimeoutError('Injected optional cutoff')
                if stage['kind']==late_kind:
                    now[0]=hook.optional_deadline+1
                if stage['kind']==fail_kind or (fail_direct and stage['kind']=='direct'):
                    raise TimeoutError('Injected bounded timeout')
                if stage['kind']=='query':text='{"query":"Synthetic concept","concepts":["Synthetic"],"hypotheses":[]}'
                elif stage['kind']=='judge':text='{"direct":false,"quote":""}' if reject_judges else '{"direct":true,"quote":"Exact synthetic span."}'
                else:text=' Exact '+stage['kind']+' '+stage['original_id']+' \n'
                if stage['kind']=='direct' and stage['original_id']=='essay-custom':
                    text='direct '+('synthetic ' * 410)
                return dict(model=r.MODEL,done=True,done_reason='stop',prompt_eval_count=100,
                            eval_count=20,message=dict(content=text))
        out=args.output/'results/engine'
        r.run(cases,package['template'],out,m['recovery'],Runtime(),3300,clock=lambda:now[0])
        binding.final_export(args.output,m,cases,package)
        answer=policy.read(args.output/'results/answers.json')
        direct=policy.read(args.output/'results/answers.direct.json')
        template=policy.read(args.output/'source-template.json')
        self.assertEqual([x['id'] for x in answer['answers']],[x['id'] for x in template['answers']])
        self.assertTrue(all(x['answer'].strip() for x in answer['answers']))
        self.assertEqual(set(answer),{'exam_id','answers'})
        events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
        reservations=[e for e in events if e['event']=='reserved']
        self.assertEqual(len(reservations),len(seen))
        self.assertLessEqual(sum(e['cap'] for e in reservations),m['max_requested_tokens'])
        for event,(_,body,_,_) in zip(reservations,seen):
            self.assertEqual(event['cap'],body['options']['num_predict'])
        first_optional=next((i for i,(stage,*_) in enumerate(seen) if stage['kind']!='direct'),len(seen))
        self.assertTrue(all(stage['kind']=='direct' for stage,*_ in seen[:first_optional]))
        if not fail_direct:
            self.assertEqual(first_optional,4)
        for stage,body,timeout,sent_at in seen[first_optional:]:
            self.assertNotEqual(stage['original_id'],'essay-custom')
            self.assertLessEqual(sent_at+timeout,hook.optional_deadline-15)
        return args,hook,seen,answer,direct

    def test_success_uses_only_complete_optional_finals(self):
        _,hook,seen,answer,direct=self.exercise()
        phases=[stage['phase'] for stage,*_ in seen]
        self.assertEqual(phases,sorted(phases))
        self.assertEqual(sum(stage['kind']=='judge' for stage,*_ in seen),15)
        for row in answer['answers']:
            self.assertIn('direct' if row['id']=='essay-custom' else 'final',row['answer'])

    def test_failed_final_preserves_exact_direct(self):
        args,_,seen,answer,direct=self.exercise(fail_kind='final')
        self.assertEqual(answer,direct)
        self.assertEqual(sum(stage['kind']=='final' for stage,*_ in seen),12,
                         policy.read(args.output/'results/engine/answer-status.json')['stop'])

    def test_no_evidence_skips_final_sampling(self):
        _,_,seen,answer,direct=self.exercise(reject_judges=True)
        self.assertFalse(any(stage['kind']=='final' for stage,*_ in seen))
        self.assertEqual(answer,direct)

    def test_late_optional_final_is_rejected(self):
        _,_,_,answer,direct=self.exercise(late_kind='final')
        self.assertEqual(answer,direct)

    def test_cutoff_at_every_optional_phase_preserves_unfinished_direct(self):
        for kind in ('query','judge','final'):
            with self.subTest(kind=kind):
                _,_,_,answer,direct=self.exercise(cutoff_kind=kind)
                self.assertEqual(answer,direct)

    def test_no_optional_window_does_not_issue_optional_calls(self):
        _,_,seen,answer,direct=self.exercise(start=2500,duration=250)
        self.assertTrue(all(stage['kind']=='direct' for stage,*_ in seen))
        self.assertEqual(answer,direct)

    def test_direct_failure_gets_three_retries_then_nonblank_fallback(self):
        _,_,seen,answer,direct=self.exercise(fail_direct=True,cutoff_kind='query')
        self.assertEqual(sum(stage['kind']=='direct' for stage,*_ in seen),16)
        self.assertTrue(all(row['answer']=='Tadeusz Kościuszko' for row in direct['answers']))
        self.assertEqual(answer,direct)

    def test_partial_and_interrupted_export_preserves_saved_direct(self):
        args,binding,m,package,cases=self.fixture()
        root=args.output
        out=root/'results/engine';out.mkdir(parents=True)
        # External supervisor startup failure still emits exactly the original IDs.
        binding.final_export(root,m,cases,package)
        blank_states={case['id']:dict(answer=None,attempts=4,history=[],warnings=[],partial_candidates=[]) for case in cases}
        blank_states[cases[0]['id']]['partial_candidates']=[' Exact partial \n']
        policy.export_original(root,blank_states,'synthetic interruption')
        answer=policy.read(root/'results/answers.json')
        self.assertEqual(next(row['answer'] for row in answer['answers'] if row['id']==cases[0]['id']),' Exact partial \n')
        self.assertEqual(len(answer['answers']),4)

    def test_generic_plan_counts_and_collision_namespace(self):
        template={'exam_id':'synthetic','answers':[{'id':'__optional_rag__:query:000001','answer':''},{'id':'a/../b','answer':''}]}
        plan=policy.make_plan(template,[])
        self.assertEqual(len(plan['stages']),16)
        self.assertNotEqual(plan['slot_prefix'],'__optional_rag__:')
        self.assertEqual(plan['primary_calls'],16)

    def test_declared_window_is_at_most_55_minutes(self):
        args,_,m,_,_=self.fixture()
        m.update(status='DECLARED',declared_utc='2026-09-27T07:20:00+00:00',deadline_utc='2026-09-27T08:15:00+00:00')
        policy.validate_envelope(args.output,m)
        m['deadline_utc']='2026-09-27T08:15:01+00:00'
        with self.assertRaises(ValueError):policy.validate_envelope(args.output,m)

    def test_large_aggregate_keeps_qualified_direct_and_rejects_oversized_rag(self):
        args,binding,m,package,cases=self.fixture(count=12,essays=())
        states={case['id']:dict(kind='ordinary',answer=None,attempts=1,history=[],warnings=[],
                               partial_candidates=[],selected_answer_attempt=0) for case in cases}
        plan=policy.read(args.output/'study.json')
        for item in m['ids']:
            states[item]['answer']='x'*95000
        for slot,stage in plan['stages'].items():
            if stage['kind']=='final':states[slot]['answer']='y'*100000
        policy.export_original(args.output,states)
        answer=policy.read(args.output/'results/answers.json')
        direct=policy.read(args.output/'results/answers.direct.json')
        self.assertLessEqual((args.output/'results/answers.json').stat().st_size,1048576)
        self.assertTrue(all(row['answer'].strip() for row in answer['answers']))
        statuses=policy.read(args.output/'results/deadline-rag-status.json')['items']
        self.assertTrue(any(row['optional_rejected_for_size'] for row in statuses.values()))
        by_id={row['id']:row['answer'] for row in direct['answers']}
        for row in answer['answers']:
            if statuses[row['id']]['selection']=='saved_direct':
                self.assertEqual(row['answer'],by_id[row['id']])


if __name__=='__main__':
    unittest.main()
