import json
import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import infer


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "name": "local",
            "base_url": "http://127.0.0.1:11434/v1",
            "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
            "model": "gemma2:9b",
            "max_output_tokens": 64,
            "timeout_seconds": 5,
        }

    def test_text_and_image_serialization_and_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tiny.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            (root / "cases.jsonl").write_text(
                json.dumps({"id": "c1", "prompt": "Describe this", "images": ["tiny.png"]}) + "\n",
                encoding="utf-8",
            )
            case = infer.load_cases(root / "cases.jsonl", 1)[0]
            captured = {}

            def respond(request, timeout):
                captured["url"] = request.full_url
                captured["body"] = json.loads(request.data)
                captured["timeout"] = timeout
                return FakeResponse(b'{"id":"response-1","model":"served-revision","choices":[{"message":{"content":"ok"}}],"usage":{"total_tokens":7}}')

            with patch.object(infer.OPENER, "open", side_effect=respond):
                result = infer.run_case(case, self.config)
            self.assertEqual(captured["url"], self.config["endpoint"])
            self.assertEqual(captured["body"]["max_tokens"], 64)
            content = captured["body"]["messages"][0]["content"]
            self.assertEqual(content[0], {"type": "text", "text": "Describe this"})
            self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/png;base64,"))
            self.assertEqual(result["usage"]["total_tokens"], 7)
            self.assertEqual(result["raw_response"]["choices"][0]["message"]["content"], "ok")
            self.assertEqual(result["backend"]["response_model"], "served-revision")
            self.assertEqual(result["backend"]["response_id"], "response-1")
            self.assertIsNone(result["error"])

    def test_only_prompt_and_images_reach_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.jsonl"
            path.write_text(json.dumps({"id": "q1", "prompt": "Question", "answer": "secret", "rubric": "private", "split": "VALIDATION"}) + "\n", encoding="utf-8")
            case = infer.load_cases(path, 1)[0]
            self.assertEqual(case, {"id": "q1", "content": "Question"})
            with patch.object(infer.OPENER, "open", return_value=FakeResponse(b'{"choices":[]}')) as opened:
                infer.run_case(case, self.config)
            body = json.loads(opened.call_args.args[0].data)
            self.assertEqual(body["messages"], [{"role": "user", "content": "Question"}])

    def test_http_error_is_recorded(self):
        error = urllib.error.HTTPError(self.config["endpoint"], 429, "rate limit", {}, io.BytesIO(b"too many requests"))
        with patch.object(infer.OPENER, "open", side_effect=error):
            result = infer.run_case({"id": "c2", "content": "question"}, self.config)
        self.assertEqual(result["error"]["status"], 429)
        self.assertIn("too many requests", result["error"]["message"])
        self.assertEqual(result["raw_response"], "too many requests")

    def test_reasoning_effort_is_optional_and_passed_through(self):
        case = {"id": "q", "content": "Reply OK"}
        captured = []

        def respond(request, timeout):
            captured.append(json.loads(request.data))
            return FakeResponse(b'{"choices":[{"message":{"content":"OK"}}]}')

        with patch.object(infer.OPENER, "open", side_effect=respond):
            infer.run_case(case, self.config)
            infer.run_case(case, {**self.config, "reasoning_effort": "none"})
        self.assertNotIn("reasoning_effort", captured[0])
        self.assertEqual(captured[1]["reasoning_effort"], "none")
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({**self.config, "reasoning_effort": "invalid"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reasoning_effort"):
                infer.load_config(config_path, False)

    def test_unusable_200_responses_are_errors_with_raw_body(self):
        bodies = [
            ({"error": {"message": "model not available"}}, "provider"),
            ({"choices": []}, "invalid_response"),
            ({"choices": [{"message": {"content": "", "reasoning_content": "internal reasoning"}, "finish_reason": "length"}]}, "incomplete"),
            ({"choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}, "incomplete"),
            (["not a chat completion"], "invalid_response"),
        ]
        for body, expected_type in bodies:
            with self.subTest(body=body):
                with patch.object(infer.OPENER, "open", return_value=FakeResponse(json.dumps(body).encode("utf-8"))):
                    result = infer.run_case({"id": "bad", "content": "question"}, self.config)
                self.assertEqual(result["error"]["type"], expected_type)
                self.assertEqual(result["raw_response"], body)

    def test_malformed_json_is_kept_for_diagnosis(self):
        with patch.object(infer.OPENER, "open", return_value=FakeResponse(b"not-json")):
            result = infer.run_case({"id": "bad", "content": "question"}, self.config)
        self.assertEqual(result["raw_response"], "not-json")
        self.assertIsNotNone(result["error"])

    def test_remote_guard_and_token_bounds(self):
        with self.assertRaisesRegex(ValueError, "Remote endpoint refused"):
            infer.endpoint_url("https://example.org/v1", False)
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            infer.endpoint_url("http://example.org/v1", True)
        self.assertEqual(infer.endpoint_url("https://example.org/v1", True), "https://example.org/v1/chat/completions")
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({**self.config, "max_output_tokens": 5000}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "max_output_tokens"):
                infer.load_config(config_path, False)

    def test_preflight_rejects_excess_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.jsonl"
            path.write_text('{"id":"one","prompt":"a"}\n{"id":"two","prompt":"b"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exceeds --max-calls"):
                infer.load_cases(path, 1)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            cases = root / "cases.jsonl"
            output = root / "results.jsonl"
            config.write_text(json.dumps(self.config), encoding="utf-8")
            cases.write_text('{"id":"q1","prompt":"test"}\n', encoding="utf-8")
            output.write_text("keep this", encoding="utf-8")
            with patch.object(infer.OPENER, "open") as opened:
                status = infer.main(["--config", str(config), "--input", str(cases), "--output", str(output)])
            self.assertEqual(status, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep this")
            opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
