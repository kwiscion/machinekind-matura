"""Actual generic adapter/preflight tests with synthetic arbitrary IDs and images."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import prepare_qwen_exam as q

fixture_module = q.load('qwen_fixture', q.HERE.parent / 'final-package-prep/test_native_package.py')


class Tests(unittest.TestCase):
    def fixture(self, count, essays):
        fixture = fixture_module.Tests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        source, _, _, _, _, _ = fixture.package(count=count, essays=essays)
        args = SimpleNamespace(exam_dir=source / 'exam', output=source.with_name('qwen'),
                               essay_id=list(essays), no_essay=not essays, minutes=120,
                               cache='/owned/qwen-only', binary='/owned/runtime/bin/ollama',
                               lock='/owned/worker.lock')
        return source, args

    def test_arbitrary_ids_count_full_sources_images_and_essay(self):
        source, args = self.fixture(4, ('essay-custom',))
        m = q.prepare(args)
        self.assertEqual(m['ids'], ['id/0', 'essay-custom', 'id/2', 'id/3'])
        self.assertEqual((m['max_calls'], m['max_requested_tokens']), (16, 4 * 147456))
        self.assertEqual(m['recovery']['minutes'], 120)
        self.assertEqual(m['faults'], {})
        for rel in ('exam.json', 'answers-template.json', 'images/red.png'):
            self.assertEqual((source / 'exam' / rel).read_bytes(), (args.output / 'exam' / rel).read_bytes())
        packed = q.load('qwen_actual', args.output / 'run_recovery_package.py')
        _, _, cases = packed.preflight(args.output)
        self.assertEqual(cases[1]['kind'], 'essay')
        body, _ = packed.r.step(cases[0], 0, [], packed.r.config(120))
        self.assertEqual(body['model'], 'qwen3.5:9b')
        self.assertEqual({k: body['options'][k] for k in ('temperature', 'top_p', 'top_k')},
                         {'temperature': 1, 'top_p': .95, 'top_k': 64})
        self.assertTrue(cases[0]['content'][1]['image_url']['url'].startswith('data:image/'))
        self.assertEqual(m['status'], 'PREPARED')
        with self.assertRaises(Exception): q.prepare(args)  # Fresh outputs only.

    def test_one_nonessay_and_profile_mutation_fail_closed(self):
        _, args = self.fixture(1, ())
        with patch.object(q, 'PROFILE_SHA', '0' * 64):
            with self.assertRaises(Exception): q.prepare(args)
        self.assertFalse(args.output.exists())
        m = q.prepare(args)
        self.assertEqual(m['ids'], ['id/0']); self.assertTrue(m['no_essay'])
        self.assertEqual(m['max_calls'], 4)


if __name__ == '__main__': unittest.main()
