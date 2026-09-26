"""Tests for the JSONL-corpus helpers in contamination_check.py (no private data needed)."""
import json
import os
import tempfile
import unittest

import contamination_check as cc


class JsonlCorpusTest(unittest.TestCase):
    def test_record_becomes_all_and_field_chunks(self):
        rec = {"id": "r1", "prompt": "Podaj datę bitwy.", "answer": "Rok 1410.",
               "evidence": [{"claim": "stoczona 15 lipca 1410"}, {"claim": "pod Grunwaldem"}]}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "train.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n\n")
            chunks, records = cc.load_jsonl_corpus([path], d, "data/x/")
        self.assertEqual([c["section"] for c in chunks], ["all", "prompt", "answer", "claim0", "claim1"])
        self.assertEqual(chunks[0]["chunk_id"], "data/x/train.jsonl:r1#all")
        self.assertEqual({c["record_id"] for c in chunks}, {"r1"})
        self.assertIn("pod Grunwaldem", chunks[0]["text"])
        self.assertEqual(records[0]["file"], "data/x/train.jsonl")

    def test_salient_keeps_years_and_long_words_drops_boilerplate(self):
        s = cc.salient("Przykładowe: bitwa pod Grunwaldem w 1410 r., krótkie uzasadnienie.")
        self.assertIn("1410", s)
        self.assertIn("grunw", s)
        self.assertNotIn("przyk", s)
        self.assertNotIn("uzasa", s)


if __name__ == "__main__":
    unittest.main()
