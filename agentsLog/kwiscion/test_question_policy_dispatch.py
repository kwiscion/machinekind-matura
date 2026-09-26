import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('dispatch', Path(__file__).with_name('run_question_policy.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class StopTests(unittest.TestCase):
    def test_installed_loaded_and_unloaded_identity(self):
        name = 'gemma'
        tags = {'models': [{'name': name, 'digest': d.DIGEST}]}
        unloaded = {'models': []}
        loaded = {'models': [{'name': name, 'digest': d.DIGEST, 'context_length': 4096}]}
        self.assertIsNone(d.verify_model(tags, unloaded, name))
        self.assertEqual(d.verify_model(tags, loaded, name)['context_length'], 4096)
        with self.assertRaisesRegex(RuntimeError, 'not resident'):
            d.verify_model(tags, unloaded, name, require_loaded=True)
        with self.assertRaisesRegex(RuntimeError, 'Installed'):
            d.verify_model({'models': [{'name': name, 'digest': 'wrong'}]}, unloaded, name)
        for field, value in (('digest', 'wrong'), ('context_length', 8192)):
            bad = {'models': [dict(loaded['models'][0], **{field: value})]}
            with self.assertRaisesRegex(RuntimeError, 'Resident'):
                d.verify_model(tags, bad, name)

    def test_time_projection_and_competition(self):
        good = {'error': None, 'usage': {'prompt_tokens': 2000}}
        now = d.DEADLINE - 1000
        self.assertIsNone(d.stop_reason([good] * 4, 500, now))
        self.assertIn('projected', d.stop_reason([good] * 5, 500, now))
        self.assertIn('deadline', d.stop_reason([], 0, d.DEADLINE))
        self.assertIn('60-minute', d.stop_reason([], 3600, now))
        self.assertIn('competing', d.stop_reason([], 0, now, [123]))

    def test_context_and_missing_usage(self):
        now = d.DEADLINE - 3600
        for count in (2817, None):
            self.assertIn('token count', d.stop_reason([{'error': None, 'usage': {'prompt_tokens': count}}], 1, now))
        self.assertIsNone(d.stop_reason([{'error': None, 'usage': {'prompt_tokens': 2816}}], 1, now))
        self.assertIn('context truncation', d.stop_reason([{'error': {'message': 'CUDA out of memory'}}], 1, now))
        self.assertIn('context truncation', d.stop_reason([{'error': None, 'usage': {'prompt_tokens': 100}, 'raw_response': {'context_truncated': True}}], 1, now))

    def test_infrastructure_streak_not_answer_incompleteness(self):
        now = d.DEADLINE - 3600
        failed = {'error': {'type': 'URLError'}}
        incomplete = {'error': {'type': 'incomplete'}, 'usage': {'prompt_tokens': 100}}
        self.assertIsNone(d.stop_reason([failed], 1, now))
        self.assertIn('two consecutive', d.stop_reason([failed, failed], 2, now))
        self.assertIsNone(d.stop_reason([failed, incomplete], 2, now))


if __name__ == '__main__':
    unittest.main()
