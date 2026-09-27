"""Real adapter/preflight, synthetic arbitrary IDs and the organizer mock; no model."""
import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import prepare_coverage_exam as c

fixture_module = c.load('coverage_fixture', c.HERE.parent / 'final-package-prep/test_native_package.py')


class Tests(unittest.TestCase):
    def fixture(self, model='gemma', essays=('essay-custom',)):
        fixture = fixture_module.Tests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        source, *_ = fixture.package(count=4, essays=essays)
        return SimpleNamespace(exam_dir=source / 'exam', output=source.with_name('coverage'),
                               model=model, essay_id=list(essays), no_essay=not essays,
                               minutes=120, cache='/owned/single-model',
                               binary='/owned/runtime/bin/ollama', lock='/owned/worker.lock')

    def check(self, args):
        old = json.loads((args.exam_dir / 'exam.json').read_text(encoding='utf8'))
        frozen = copy.deepcopy(old)
        suffix = c.load('coverage_test_suffix', c.HERE.parent / 'essay-coverage-prep/coverage_suffix.py')
        m = c.prepare(args)
        new = json.loads((args.output / 'exam/exam.json').read_text(encoding='utf8'))
        for item in frozen['items']:
            if item['id'] in args.essay_id:
                item['question'] += suffix.SUFFIX
        self.assertEqual(new, frozen)
        self.assertEqual(json.loads((args.exam_dir / 'exam.json').read_text(encoding='utf8')), old)
        provenance = json.loads((args.output / 'coverage-provenance.json').read_text())
        for rel, digest in provenance['source_files'].items():
            self.assertEqual(c.sha(args.exam_dir / rel), digest)
            if rel != 'exam.json' or args.no_essay:
                self.assertEqual(c.sha(args.output / 'exam' / rel), digest)
        self.assertEqual(m['max_calls'], len(old['items']) * 4)
        self.assertEqual(m['max_requested_tokens'], len(old['items']) * 147456)
        self.assertEqual(m['faults'], {})
        for rel, digest in m['files'].items():
            self.assertEqual(c.sha(args.output / rel), digest)
        packed = c.load('coverage_test_packed', args.output / 'run_recovery_package.py')
        packed.preflight(args.output)
        return m

    def test_gemma_arbitrary_ids_and_images(self):
        args = self.fixture(); self.check(args)
        with self.assertRaises(ValueError): c.prepare(args)

    def test_qwen_no_essay(self):
        m = self.check(self.fixture('qwen', ()))
        self.assertEqual(m['model'], 'qwen3.5:9b')

    def test_invalid_duplicate_ids_and_pins_before_output(self):
        args = self.fixture()
        for ids in (['missing'], ['essay-custom', 'essay-custom']):
            args.essay_id = ids
            with self.assertRaises(ValueError): c.prepare(args)
            self.assertFalse(args.output.exists())
        args.essay_id = ['essay-custom']
        with patch.dict(c.PINS, {'essay-coverage-prep/coverage_suffix.py': '0' * 64}):
            with self.assertRaises(ValueError): c.prepare(args)
        self.assertFalse(args.output.exists())

    def test_actual_mock37_qwen_explicit_essay(self):
        args = self.fixture('qwen')
        args.exam_dir = c.REPO / 'data/history-2023-mock-v1'
        if not (args.exam_dir / 'exam.json').is_file():
            self.skipTest('Optional local organizer DEV mock is not distributed with code')
        exam = json.loads((args.exam_dir / 'exam.json').read_text(encoding='utf8'))
        # Test fixture metadata, not a production classifier or fixed exam ID.
        essays = [x['id'] for x in exam['items'] if x.get('max_points') == 15]
        self.assertEqual(len(essays), 1)
        args.essay_id = essays; args.minutes = 60
        m = self.check(args)
        self.assertEqual(len(m['ids']), 37)


if __name__ == '__main__': unittest.main()
