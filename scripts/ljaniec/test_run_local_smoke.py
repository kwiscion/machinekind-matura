"""Failure-path checks using invented prompts and fake weight files only."""
import io
import json
import pathlib
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import run_local_smoke as smoke


def reply(body):
    return io.BytesIO(json.dumps(body).encode())


class SmokeFailureTests(unittest.TestCase):
    def test_malformed_json_shapes_are_item_errors_with_raw_evidence(self):
        bodies = [None, [1], {"choices": []}, {"choices": [None]},
                  {"choices": [{"message": []}]},
                  {"choices": [{"message": {"content": ["not text"]}}]}]
        for body in bodies:
            with self.subTest(body=body), patch.object(smoke.LOCAL_OPENER, "open", return_value=reply(body)):
                result = smoke.request("http://127.0.0.1:8080/v1/chat/completions", "fixture", "Invented prompt", 1, 16, 42)
                self.assertIsInstance(result["error"], str)
                self.assertEqual(result["raw_api_response"], body)

    def test_empty_and_truncated_answers_are_errors(self):
        for content, reason in [("", "stop"), ("partial answer", "length")]:
            body = {"choices": [{"message": {"content": content}, "finish_reason": reason}]}
            with self.subTest(reason=reason), patch.object(smoke.LOCAL_OPENER, "open", return_value=reply(body)):
                result = smoke.request("http://127.0.0.1:8080/v1/chat/completions", "fixture", "Invented prompt", 1, 16, 42)
                self.assertIsNotNone(result["error"])
                self.assertEqual(result["raw_response"], content)

    def test_redirect_is_not_followed(self):
        visits = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                visits.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/redirected")
                self.end_headers()

            def do_GET(self):
                visits.append(self.path)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
            result = smoke.request(url, "fixture", "Invented prompt", 2, 16, 42)
            self.assertIsNotNone(result["error"])
            self.assertEqual(visits, ["/v1/chat/completions"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_interrupted_run_retains_manifest_and_actual_output_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            weight = root / "fake.gguf"
            weight.write_bytes(b"fixture, not a model")
            inputs = root / "input.jsonl"
            inputs.write_text('\n'.join(json.dumps({"id": str(i), "prompt": "Invented prompt"}) for i in range(2)) + '\n')
            output, manifest = root / "output.jsonl", root / "manifest.json"
            argv = ["run_local_smoke.py", "--input", str(inputs), "--output", str(output),
                    "--manifest", str(manifest), "--model-file", str(weight), "--model-repo", "fixture",
                    "--revision", "fixture-revision", "--license", "fixture", "--quantization", "fixture",
                    "--template", "fixture", "--model-id", "fixture", "--split", "DEV",
                    "--server-command", "fixture-server", "--run-id", "interrupted-fixture"]
            calls = 0

            def interrupted_request(*args):
                nonlocal calls
                self.assertEqual(json.loads(manifest.read_text())["status"], "running")
                calls += 1
                if calls == 2:
                    raise RuntimeError("invented interruption")
                return {"usage": {}, "latency_s": 0.1, "error": None, "raw_response": "fixture answer"}

            with patch("sys.argv", argv), patch.object(smoke, "gpu_used_bytes", return_value=None), patch.object(smoke, "request", side_effect=interrupted_request):
                with self.assertRaisesRegex(RuntimeError, "invented interruption"):
                    smoke.main()
            recorded = json.loads(manifest.read_text())
            self.assertEqual(recorded["status"], "failed")
            self.assertEqual(recorded["output_count"], 1)
            self.assertEqual(recorded["input_count"], 2)
            self.assertEqual(recorded["run_failure"]["type"], "RuntimeError")
            self.assertEqual(recorded["output_sha256"], smoke.sha256(output))
            self.assertEqual(len(output.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
