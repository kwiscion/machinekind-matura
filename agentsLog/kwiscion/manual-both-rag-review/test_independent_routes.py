"""Independent synthetic review of both manual RAG routes; no model calls."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

OWNER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OWNER / 'deadline-rag-prep'))
import test_deadline_rag as existing
import deadline_hook
import deadline_runtime as policy
import essay_support


class IndependentRoutes(unittest.TestCase):
    def exercise(self, failed_essay_judge=False, essay_cutoff=False, invalid_plan=False, late_essay=False, global_cutoff=False):
        fixture = existing.Tests()
        self.addCleanup(fixture.doCleanups)
        args, binding, manifest, package, cases = fixture.fixture(count=2)
        engine = binding.r
        hook = deadline_hook.install(args.output, engine)
        passage = dict(article_id='synthetic', title='Synthetic', url='https://example.invalid',
                       start=0, end=20, text='Exact synthetic span', query_index=0, rank=1,
                       text_sha256=essay_support.builder.tsha('Exact synthetic span'))
        hook.retrieval = lambda source: {'passages': [passage] * 5}
        hook.essay.retrieval = lambda source: {'passages': [passage, dict(passage, article_id='second')]}
        now = [0.0]
        seen = []

        class Runtime:
            def verify(self, context): pass
            def quiesce(self, deadline): return True
            def send(self, body, timeout):
                stage = copy.deepcopy(hook.current)
                seen.append((stage, copy.deepcopy(body), timeout, now[0]))
                now[0] += 1
                kind = stage['kind']
                if global_cutoff:
                    now[0] = 3301
                if kind == 'essay_final' and essay_cutoff:
                    now[0] = hook.essay_deadline
                    raise TimeoutError('Synthetic safely quiesced essay route cutoff')
                if kind == 'essay_final' and late_essay:
                    now[0] = hook.essay_deadline + 1
                if kind == 'essay_query':
                    text = 'invalid' if invalid_plan else json.dumps(dict(topic_id=1, queries=['one','two','three','four','five','six']))
                elif kind == 'essay_judge':
                    if failed_essay_judge and stage['rank'] == 0:
                        text = 'invalid'
                    else:
                        text = json.dumps(dict(relevant=True, quote=passage['text']))
                elif kind == 'query':
                    text = json.dumps(dict(query='Synthetic', concepts=['Synthetic'], hypotheses=[]))
                elif kind == 'judge':
                    text = json.dumps(dict(direct=True, quote=passage['text']))
                elif kind == 'essay_final':
                    text = 'Temat 1\n' + 'RAG synthetic ' * 210
                elif kind == 'direct' and stage['original_id'] == 'essay-custom':
                    text = 'Temat 1\n' + 'Direct synthetic ' * 210
                else:
                    text = kind + ' original answer'
                return dict(model=engine.MODEL, done=True, done_reason='stop',
                            prompt_eval_count=100, eval_count=20, message=dict(content=text))

        out = args.output / 'results/engine'
        engine.run(cases, package['template'], out, manifest['recovery'], Runtime(), 3300,
                   clock=lambda: now[0])
        binding.final_export(args.output, manifest, cases, package)
        result = policy.read(args.output / 'results/answers.json')
        direct = policy.read(args.output / 'results/answers.direct.json')
        self.assertEqual([x['id'] for x in result['answers']], ['essay-custom', 'id/0'])
        self.assertTrue(all(x['answer'].strip() for x in result['answers']))
        self.assertLessEqual((args.output / 'results/answers.json').stat().st_size, 1048576)
        reservations = [json.loads(line) for line in (out / 'events.jsonl').read_text().splitlines()
                        if json.loads(line)['event'] == 'reserved']
        self.assertEqual(len(reservations), len(seen))
        self.assertLessEqual(sum(x['cap'] for x in reservations), manifest['max_requested_tokens'])
        for reserved, (_, body, _, _) in zip(reservations, seen):
            self.assertEqual(reserved['cap'], body['options']['num_predict'])
        if not global_cutoff:
            self.assertTrue(any(stage['kind'] == 'final' for stage, *_ in seen), 'Ordinary RAG must remain reachable')
        self.assertNotIn('__optional_rag__:', json.dumps(result))
        return seen, result, direct

    def test_positive_essay_then_positive_ordinary(self):
        seen, result, _ = self.exercise()
        kinds = [stage['kind'] for stage, *_ in seen]
        self.assertLess(kinds.index('essay_final'), kinds.index('query'))
        self.assertTrue(result['answers'][0]['answer'].startswith('Temat 1\nRAG'))

    def test_failed_one_essay_judge_preserves_other_positive_evidence(self):
        seen, result, _ = self.exercise(failed_essay_judge=True)
        self.assertEqual(sum(stage['kind'] == 'essay_judge' and stage['rank'] == 0 for stage, *_ in seen), 4)
        self.assertTrue(result['answers'][0]['answer'].startswith('Temat 1\nRAG'))

    def test_invalid_essay_plan_skips_to_ordinary(self):
        seen, result, direct = self.exercise(invalid_plan=True)
        self.assertEqual(sum(stage['kind'] == 'essay_query' for stage, *_ in seen), 4)
        self.assertEqual(result['answers'][0], direct['answers'][0])

    def test_essay_cutoff_preserves_direct_and_runs_ordinary(self):
        _, result, direct = self.exercise(essay_cutoff=True)
        self.assertEqual(result['answers'][0], direct['answers'][0])

    def test_late_completed_essay_is_not_selected_and_ordinary_runs(self):
        _, result, direct = self.exercise(late_essay=True)
        self.assertEqual(result['answers'][0], direct['answers'][0])

    def test_global_cutoff_still_exports_exact_nonblank_template(self):
        seen, result, direct = self.exercise(global_cutoff=True)
        self.assertEqual(len(seen), 1)
        self.assertEqual(result, direct)
        self.assertTrue(all(x['answer'] == 'Tadeusz Kościuszko' for x in result['answers']))

    def test_numbered_requirements_are_not_alternative_topics(self):
        item = {'kind': 'essay', 'question': 'Write one essay.\n1. Discuss politics.\n2. Discuss culture.\n3. Discuss trade.'}
        self.assertEqual(essay_support.offered_topics(item), [1])

    def test_actual_dev_essay_is_detected(self):
        source = OWNER / 'private/manual-both-rag-review-20260927/dev-mixed-input/exam.json'
        item = next(x for x in json.loads(source.read_text(encoding='utf8'))['items'] if x['id'] == '26')
        self.assertTrue(essay_support.is_essay(item))
        self.assertEqual(essay_support.offered_topics(item), [1, 2, 3])

    def test_generated_cleanup_skips_unreadable_unrelated_process(self):
        fixture = existing.Tests()
        self.addCleanup(fixture.doCleanups)
        args, binding, _, _, _ = fixture.fixture(count=2)
        helper = existing.prep.load('independent_cleanup', args.output / 'run_gemma_offline.py')
        with patch.object(helper.Path, 'iterdir', return_value=iter([Path('/proc/999')])), \
             patch.object(helper.os, 'getpgid', side_effect=PermissionError('unrelated protected process'), create=True), \
             patch.object(helper.os, 'killpg', create=True) as kill:
            self.assertEqual(helper.cleanup(dict(pid=123, ticks='1', namespace='isolated')), [])
            kill.assert_not_called()


if __name__ == '__main__':
    unittest.main()
