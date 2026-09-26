import json
import pathlib
import tempfile
import unittest

from audit_smoke_outputs import audit


class AuditTests(unittest.TestCase):
    def fixture(self, directory, rows, name='raw.jsonl'):
        path = pathlib.Path(directory) / name
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        return path

    def test_empty_unreported_error_duplicates_and_even_median(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = [{'id': 'a', 'raw_response': '', 'error': None, 'latency_s': 2, 'usage': {'completion_tokens': 200}},
                    {'id': 'a', 'raw_response': 'answer', 'error': None, 'latency_s': 4}]
            result = audit(self.fixture(directory, rows), 200)
            self.assertEqual(result['empty_response_without_reported_error_count'], 1)
            self.assertEqual(result['duplicate_id_record_count'], 1)
            self.assertEqual(result['latency']['median_seconds'], 3)
            self.assertEqual(result['completion_tokens']['records_at_or_above_budget'], 1)
            self.assertEqual(result['completion_tokens']['denominator_records_with_token_count'], 1)

    def test_comparison_and_aggregate_output_do_not_expose_text(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = [{'id': 'a', 'prompt': 'PRIVATE PROMPT', 'raw_response': 'PRIVATE ANSWER', 'wall_s': 1}]
            raw = self.fixture(directory, rows)
            before = raw.read_bytes()
            catalog = self.fixture(directory, [{'id': 'a', 'prompt': 'PRIVATE PROMPT'}], 'input.jsonl')
            result = audit(raw, 200, catalog, 'synthetic-smoke')
            self.assertTrue(result['input_comparison']['all_record_prompts_match_by_id'])
            self.assertNotIn('PRIVATE', json.dumps(result))
            self.assertEqual(raw.read_bytes(), before)
            rows[0]['prompt'] = 'mismatch'
            self.assertFalse(audit(self.fixture(directory, rows), 200, catalog)['input_comparison']['all_record_prompts_match_by_id'])

    def test_malformed_records_fail_closed_without_content(self):
        invalid = [[], {'id': 3}, {'id': 'a'}, {'id': 'a', 'raw_response': ['PRIVATE']},
                   {'id': 'a', 'raw_response': '', 'latency_s': float('nan')},
                   {'id': 'a', 'raw_response': '', 'completion_tokens': True},
                   {'id': 'a', 'raw_response': '', 'usage': ['PRIVATE']},
                   {'id': 'a', 'raw_response': '', 'error': False}]
        with tempfile.TemporaryDirectory() as directory:
            for row in invalid:
                with self.subTest(row=row), self.assertRaises(ValueError) as caught:
                    audit(self.fixture(directory, [row]), 200)
                self.assertNotIn('PRIVATE', str(caught.exception))
            broken = pathlib.Path(directory) / 'broken.jsonl'
            broken.write_text('{"PRIVATE":')
            with self.assertRaisesRegex(ValueError, 'Invalid JSON at line 1'):
                audit(broken, 200)

    def test_reported_error_with_nonempty_response_is_still_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = [{'id': 'a', 'raw_response': 'partial answer', 'error': 'timeout'},
                    {'id': 'b', 'raw_response': None, 'error': ''}]
            result = audit(self.fixture(directory, rows), 200)
            self.assertEqual(result['reported_error_count'], 2)
            self.assertEqual(result['response_nonempty_count'], 1)
            self.assertEqual(result['reported_error_or_empty_response_count'], 2)
            self.assertEqual(result['empty_response_without_reported_error_count'], 0)
            self.assertEqual(result['latency']['denominator_records_with_latency'], 0)
            self.assertIsNone(result['latency']['mean_seconds'])


if __name__ == '__main__':
    unittest.main()
