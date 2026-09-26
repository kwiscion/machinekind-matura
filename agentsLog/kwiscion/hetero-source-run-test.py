"""Standalone transport tests use the real infer.run_case payload, no network."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import infer
spec = importlib.util.spec_from_file_location('hetero_runner', HERE / 'hetero-source-run.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


class Transport(unittest.TestCase):
    def setUp(self):
        self.case = {'id': 'synthetic', 'content': [
            {'type': 'text', 'text': 'Complete original source\nsecond paragraph'},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AA=='}}]}
        self.cfg = {'model': 'qwen3.5:9b', 'model_revision': 'pin', 'name': 'synthetic',
                    'base_url': 'http://127.0.0.1:11436/v1',
                    'endpoint': 'http://127.0.0.1:11436/v1/chat/completions',
                    'max_output_tokens': 256, 'reasoning_effort': 'none', 'timeout_seconds': 420}

    def test_real_payload_accepted_once_preserving_sources(self):
        owner = self
        seen = []
        class Capture:
            def open(self, request, timeout):
                body = json.loads(request.data)
                r.check_body(body, owner.case, owner.cfg)
                owner.assertNotIn('stream', body)
                owner.assertNotIn('temperature', body)
                owner.assertEqual(timeout, 420)
                seen.append(body)
                return io.BytesIO(json.dumps({'model': 'qwen3.5:9b', 'choices': [
                    {'finish_reason': 'stop', 'message': {'content': 'synthetic'}}],
                    'usage': {'prompt_tokens': 12, 'completion_tokens': 1}}).encode())
        with patch.object(infer, 'OPENER', Capture()):
            result = infer.run_case(self.case, self.cfg)
        self.assertIsNone(result['error'])
        self.assertEqual(len(seen), 1)

    def test_real_request_rejects_modified_source_model_cap_and_sampling(self):
        owner = self
        for change in ('source', 'model', 'cap', 'temperature'):
            with self.subTest(change=change):
                class Capture:
                    def open(self, request, timeout):
                        body = json.loads(request.data)
                        if change == 'source': body['messages'][0]['content'].pop()
                        if change == 'model': body['model'] = 'unknown'
                        if change == 'cap': body['max_tokens'] = 257
                        if change == 'temperature': body['temperature'] = 0
                        r.check_body(body, owner.case, owner.cfg)
                        raise AssertionError('Should not reach transport')
                with patch.object(infer, 'OPENER', Capture()), self.assertRaises(RuntimeError):
                    infer.run_case(self.case, self.cfg)

    def test_path_escape_refused(self):
        with self.assertRaises(RuntimeError):
            r.safe_file(HERE, '../outside-pinned-package')


if __name__ == '__main__': unittest.main()
