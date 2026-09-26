"""Original synthetic CPU tests; no held-out source fixtures or model calls."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import infer
import run_gemma_package
from scripts.Bukareszt import matura_package
spec = importlib.util.spec_from_file_location('hetero', HERE / 'hetero-source-controller.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class Controller(unittest.TestCase):
    def setUp(self):
        self.cases = [{'id': str(i), 'content': [
            {'type': 'text', 'text': 'Original synthetic source\nDo not drop this line.'},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AA=='}},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AQ=='}}]}
            for i in range(6)]
        self.cfg = {'max_output_tokens': 1024, 'timeout_seconds': 420,
                    'reasoning_effort': 'none',
                    'endpoint': 'http://127.0.0.1:11436/v1/chat/completions'}
        self.events, self.requests = [], []

    def row(self, reason='stop', content='Synthetic observation', **extra):
        raw = {'choices': [{'finish_reason': reason, 'message': {'content': content}}], **extra}
        return {'raw_response': raw, 'error': infer.response_error(raw),
                'usage': {'prompt_tokens': 25, 'completion_tokens': 10, 'total_tokens': 35}}

    def execute(self, replacement=None, guard=lambda _: None, clock=lambda: 0):
        def backend(case, cfg):
            self.assertEqual(self.events[-1][0], 'reservation')
            self.requests.append((case, cfg))
            return replacement(len(self.requests)) if replacement else self.row()
        return r.run(self.cases, self.cfg, backend, guard,
                     lambda kind, value: self.events.append((kind, value)),
                     infer, matura_package, run_gemma_package.case_local_generation_error,
                     clock=clock)

    def test_full_sources_models_and_exact_reservations(self):
        original = copy.deepcopy(self.cases)
        result = self.execute()
        self.assertEqual(result['status'], 'complete')
        self.assertEqual((result['calls'], result['requested_tokens']), (18, 18432))
        self.assertEqual(self.cases, original)
        self.assertEqual(len([e for e in self.events if e[0] == 'reservation']), 18)
        for index, (case, cfg) in enumerate(self.requests):
            stage = r.STAGES[index % 3]
            self.assertEqual(cfg['model'], r.MODELS[stage])
            self.assertEqual(case['content'][:3], original[index // 3]['content'])
            self.assertEqual(cfg['max_output_tokens'], 1024)

    def test_failed_observation_partial_never_propagates(self):
        result = self.execute(lambda i: self.row('length', 'DO NOT PROPAGATE') if i == 2 else self.row())
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['records'][1]['answer'], '')
        self.assertTrue(result['records'][2]['fallback'])
        self.assertEqual(self.requests[2][0], self.cases[0])

    def test_empty_observation_is_same_reserved_fallback(self):
        result = self.execute(lambda i: self.row(content='') if i == 2 else self.row())
        self.assertEqual(result['calls'], 18)
        self.assertTrue(result['records'][2]['fallback'])

    def test_systemic_http_parse_provider_tool_and_context_stop(self):
        bad = [
            {'error': {'type': 'http', 'message': '500'}, 'raw_response': None},
            {'error': {'type': 'parse'}, 'raw_response': 'broken'},
            self.row('length', error='provider error'),
            self.row('length', truncated=True),
            self.row('length', context_truncated=True),
        ]
        tool = self.row('length')
        tool['raw_response']['choices'][0]['message']['tool_calls'] = [{'name': 'bad'}]
        bad.append(tool)
        for row in bad:
            with self.subTest(row=row):
                self.events, self.requests = [], []
                result = self.execute(lambda _: row)
                self.assertEqual(result['calls'], 1)
                self.assertEqual(len(result['unsent']), 17)
                self.assertEqual(result['records'][0]['answer'], '')
                self.assertNotEqual(result['status'], 'complete')

    def test_invalid_usage_cannot_be_local_failure(self):
        row = self.row('length')
        row['usage']['completion_tokens'] = 1025
        result = self.execute(lambda _: row)
        self.assertEqual(result['calls'], 1)
        self.assertNotEqual(result['status'], 'complete')

    def test_runtime_pin_failure_after_response_stops(self):
        def guard(model):
            if model:
                raise RuntimeError('Changed pin')
        result = self.execute(guard=guard)
        self.assertEqual(result['calls'], 1)
        self.assertEqual(result['records'][0]['answer'], '')

    def test_deadline_prevents_any_reservation(self):
        ticks = iter([0, 2400])
        result = self.execute(clock=lambda: next(ticks))
        self.assertEqual(result['calls'], 0)
        self.assertEqual(self.events, [])

    def test_duplicate_ids_rejected_before_dispatch(self):
        self.cases[-1]['id'] = '0'
        with self.assertRaises(RuntimeError):
            self.execute()
        self.assertEqual(self.events, [])

    def test_slow_guard_exhaustion_stops_before_reservation(self):
        now = [0]
        result = self.execute(guard=lambda _: now.__setitem__(0, 2400), clock=lambda: now[0])
        self.assertEqual(result['calls'], 0)
        self.assertEqual(self.events, [])

    def test_systemic_failure_marks_underlying_row_errored(self):
        result = self.execute(guard=lambda model: (_ for _ in ()).throw(RuntimeError('pin')) if model else None)
        record = result['records'][0]
        self.assertEqual(record['answer'], '')
        self.assertEqual(record['result']['error']['type'], 'systemic_validation')

    def test_string_input_retained(self):
        for c in self.cases:
            c['content'] = 'Full synthetic input\nsecond paragraph'
        self.execute()
        self.assertEqual(self.requests[0][0]['content'], self.cases[0]['content'])
        self.assertTrue(self.requests[1][0]['content'].startswith(self.cases[0]['content'] + '\n\n'))

    def test_two_pinned_loaded_models_allowed_only_at_expected_context(self):
        snapshot = {'version': '0.34.4', 'tags': {'models': [
            {'name': k, 'digest': v} for k, v in r.PINS.items()]},
            'ps': {'models': [{'digest': v, 'context_length': 32768} for v in r.PINS.values()]}}
        r.check_runtime(snapshot, 'qwen3.5:9b')
        snapshot['ps']['models'][0]['context_length'] = 4096
        with self.assertRaises(RuntimeError):
            r.check_runtime(snapshot)


if __name__ == '__main__':
    unittest.main()
