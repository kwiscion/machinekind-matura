"""Issue #72: optional explicit temperature in infer.py. No network, no model calls."""

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import infer

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "agentsLog/kwiscion/gemma4-12b-val40-1024.config.json"
CANDIDATE = ROOT / "scripts/Bukareszt/configs/gemma4-12b-val40-1024-temp0.2.experimental.json"
# Request body the pre-#72 runner (origin/main 7eada40) sends for the baseline config and case below.
BASELINE_BODY = (
    b'{"model": "gemma4:12b-it-q4_K_M", "messages": [{"role": "user", "content": "Pytanie"}], '
    b'"max_tokens": 1024, "reasoning_effort": "none"}'
)


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return b'{"choices":[{"message":{"content":"OK"},"finish_reason":"stop"}]}'


def request_body(config):
    captured = []

    def respond(request, timeout):
        captured.append(request.data)
        return FakeResponse()

    with patch.object(infer.OPENER, "open", side_effect=respond):
        result = infer.run_case({"id": "q", "content": "Pytanie"}, config)
    assert result["error"] is None, result["error"]
    return captured[0]


def load(data):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(data) if isinstance(data, dict) else data, encoding="utf-8")
        return infer.load_config(path, False)


class TemperatureTests(unittest.TestCase):
    def test_omitted_temperature_keeps_baseline_request_bytes(self):
        config = infer.load_config(BASELINE, False)
        self.assertNotIn("temperature", config)
        self.assertEqual(request_body(config), BASELINE_BODY)

    def test_candidate_differs_from_baseline_only_by_temperature(self):
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(candidate.pop("temperature"), 0.2)
        self.assertTrue(candidate.pop("name").endswith("-experimental"))
        baseline.pop("name")
        self.assertEqual(candidate, baseline)
        body = request_body(infer.load_config(CANDIDATE, False))
        self.assertEqual(body, BASELINE_BODY[:-1] + b', "temperature": 0.2}')
        without = json.loads(body)
        self.assertEqual(without.pop("temperature"), 0.2)
        self.assertEqual(without, json.loads(BASELINE_BODY))

    def test_supplied_values_are_forwarded_unchanged(self):
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        for value in (0, 0.0, 0.2, 1, 1.5, 2, 2.0):
            with self.subTest(value=value):
                sent = json.loads(request_body(load({**base, "temperature": value})))
                self.assertEqual(sent["temperature"], value)
                self.assertIs(type(sent["temperature"]), type(value))

    def test_invalid_values_are_rejected(self):
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        for value in (True, False, None, "0.2", [0.2], {"value": 0.2}, -0.01, 2.01, 100, 10**400, -(10**400)):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "temperature"):
                    load({**base, "temperature": value})
        text = json.dumps(base)[:-1]
        for token in ("NaN", "Infinity", "-Infinity", "1e999", "1" + "0" * 400):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ValueError, "temperature"):
                    load(text + ', "temperature": ' + token + "}")
        self.assertTrue(math.isinf(json.loads("1e999")))


if __name__ == "__main__":
    unittest.main()
