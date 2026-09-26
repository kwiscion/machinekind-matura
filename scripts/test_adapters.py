import json
import tempfile
import unittest
from pathlib import Path

from scripts import normalize_outputs, prepare_rag


class AdapterTests(unittest.TestCase):
    def test_prepare_and_normalize_synthetic_case(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chunks = [{"chunk_id": "ref-1#0000", "source_id": "ref-1", "title": "Synthetic article",
                       "section": "Overview", "locator": "Overview [part 1]",
                       "text": "The synthetic event occurred in 1410."}]
            index = root / "index.json"
            index.write_text(json.dumps(prepare_rag.retrieval.BM25Index(chunks).to_json()), encoding="utf-8")
            input_path = root / "input.jsonl"
            input_path.write_text(json.dumps({"id": "demo", "prompt": "When did the synthetic event occur?",
                                              "images": ["figure.png"], "answer": "private key"}) + "\n", encoding="utf-8")
            prepared = root / "prepared.jsonl"
            trace = root / "trace.jsonl"
            corpus = root / "corpus.jsonl"
            self.assertEqual(prepare_rag.main(["--input", str(input_path), "--output", str(prepared),
                                               "--trace", str(trace), "--corpus", str(corpus),
                                               "--index", str(index), "--mode", "bm25", "--k", "1"]), 0)
            row = prepare_rag.read_jsonl(prepared)[0]
            self.assertNotIn("private key", row["prompt"])
            self.assertIn("[[ref-1#ref-1#0000]]", row["prompt"])
            self.assertEqual(row["images"], [str((root / "figure.png").resolve())])
            self.assertEqual(prepare_rag.read_jsonl(corpus)[0]["locator"], "ref-1#0000")
            self.assertEqual(prepare_rag.read_jsonl(trace)[0]["retrieved_evidence"][0]["source_id"], "ref-1")

            raw = root / "raw.jsonl"
            raw.write_text(json.dumps({"id": "demo", "backend": {"name": "local", "model": "test-model",
                                                             "response_model": "served-model", "model_revision": "abc"},
                                       "raw_response": {"choices": [{"message": {"content": "1410 [[ref-1#ref-1#0000]]"}}]},
                                       "latency_seconds": 0.1, "usage": {"total_tokens": 3}, "error": None}) + "\n", encoding="utf-8")
            normalized = root / "normalized.jsonl"
            self.assertEqual(normalize_outputs.main(["--input", str(raw), "--output", str(normalized), "--trace", str(trace)]), 0)
            result = normalize_outputs.read_jsonl(normalized)[0]
            self.assertEqual(result["raw_response"], "1410 [[ref-1#ref-1#0000]]")
            self.assertEqual(result["model"], "served-model")
            self.assertIsNone(result["error"])
            self.assertEqual(result["retrieval_evidence"][0]["chunk_id"], "ref-1#0000")
            self.assertEqual(result["provider_raw_response"], json.loads(raw.read_text())["raw_response"])

    def test_failed_inference_remains_excluded(self):
        row = normalize_outputs.normalize({"id": "bad", "backend": {"name": "local", "model": "m"},
                                           "raw_response": {"error": "failed"}, "error": {"type": "provider", "message": "failed"}})
        self.assertIn("provider", row["error"])
        self.assertEqual(row["raw_response"], "")
        self.assertNotIn("model_revision", row)
        self.assertNotIn("usage", row)
        self.assertNotIn("latency_s", row)

    def test_trace_id_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw.jsonl"
            trace = root / "trace.jsonl"
            raw.write_text('{"id":"one","raw_response":{"choices":[{"message":{"content":"ok"}}]}}\n', encoding="utf-8")
            trace.write_text('{"id":"other","retrieved_evidence":[]}\n', encoding="utf-8")
            output = root / "normalized.jsonl"
            self.assertEqual(normalize_outputs.main(["--input", str(raw), "--output", str(output), "--trace", str(trace)]), 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
