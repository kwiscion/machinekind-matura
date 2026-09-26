"""Tests for scripts/Bukareszt/selective_rag.py (issue #96) on invented fixtures.

Run: python3 -m unittest -v scripts.Bukareszt.test_selective_rag
No network, no exam data, no model calls. CLI runs happen in child processes (process-wide socket guard).
Tests marked "pinned" need the staged pinned index (`python3 scripts/Bukareszt/stage_index.py stage`) and are
skipped when it is absent.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import prepare_bounded_rag as pbr  # noqa: E402
import selective_rag as S  # noqa: E402
from test_stage_index import SyntheticCorpus  # noqa: E402

SCRIPT = HERE / "selective_rag.py"
PINNED_ROOT = pbr.DEFAULT_ROOT
PINNED = (PINNED_ROOT / "index" / "bm25_index.json").is_file() and (PINNED_ROOT / "index" / "graph.json").is_file()
FIXTURES = PINNED_ROOT / "issue96" / "fixtures" / "synthetic_fixtures.jsonl"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


class QueryConstructionTests(unittest.TestCase):
    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("retrieval_under_test", PINNED_ROOT / "scripts" / "retrieval.py")
        self.retrieval = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.retrieval)

    def test_strip_templates_removes_only_generic_templates(self):
        q = "Zadanie 1.\nPodaj nazwę aktu z 1573 roku."
        self.assertEqual(S.strip_templates(S.BARE_HEADER + q), q)
        org = "\n\n".join([S.ORG_HEADER, "Zadanie X (maks. 1 pkt)\n" + q, "Wymagany format odpowiedzi:\nJedna nazwa.", S.ORG_FOOTER])
        stripped = S.strip_templates(org)
        self.assertIn(q, stripped)
        for gone in (S.ORG_HEADER, "Wymagany format", "Jedna nazwa", "Zwróć wyłącznie"):
            self.assertNotIn(gone, stripped)

    def test_bibliography_detection_and_number_masking_keep_words(self):
        text = ("Tekst źródłowy\nW 1569 r. zawarto unię.\nZa: J. Nowak, Unia lubelska, Warszawa 1990, s. 180.\n"
                "Na podstawie tekstu podaj rok.")
        masked, n = S.mask_bibliography_numbers(text)
        self.assertEqual(n, 2)
        self.assertIn("W 1569 r.", masked)  # event year outside bibliography untouched
        self.assertIn("Unia lubelska, Warszawa", masked)
        self.assertNotIn("1990", masked)
        self.assertNotIn("180", masked)
        self.assertFalse(S.is_bibliography("Na podstawie tekstu podaj rok."))
        self.assertTrue(S.is_bibliography("Źródło: A. B., Dzieje, Kraków 2001, t. 2, s. 5."))
        self.assertNotIn("Za: J. Nowak", S.drop_bibliography(text))

    def test_years_bce_split_without_invented_chronology(self):
        ce, bce = S.extract_years(self.retrieval, "W 490 p.n.e. i w 1410 r.; w XVII wieku; 336 przed Chr.", True)
        self.assertEqual(ce, {1410})
        self.assertEqual(bce, {490, 336})
        ce2, bce2 = S.extract_years(self.retrieval, "W 490 p.n.e. i w 1410 r.", False)
        self.assertEqual((ce2, bce2), ({490, 1410}, set()))  # production behaviour: unsigned
        self.assertTrue(S.chunk_has_year(self.retrieval, "w 509 p.n.e. wygnano", 509, True))
        self.assertFalse(S.chunk_has_year(self.retrieval, "Tarquinius (534 – 509)", 509, True))

    def test_query_never_contains_answer_side_fields_and_prompt_is_only_input(self):
        q = S.build_query(self.retrieval, S.BARE_HEADER + "Zadanie 1.\nPodaj nazwę.", S.SELECTED_VARIANT)
        self.assertNotIn("Rozstrzygnięcie", q["text"])
        self.assertEqual(q["sha256"], sha(q["text"]))


class RouterTests(unittest.TestCase):
    def test_routes(self):
        cases = {
            S.BARE_HEADER + "Zadanie 1. (0–15)\nNapisz wypracowanie na temat reform.": "essay",
            "Tekst źródłowy\nW mieście spłonęło sto domów.\nNa podstawie tekstu podaj, ile domów spłonęło.": "supplied_source",
            "Tekst 1.\nA.\nTekst 2.\nB.\nPorównaj oceny przedstawione w obu tekstach.": "supplied_source",
            "Tekst źródłowy\nKról przysiągł pokój.\nPodaj nazwę aktu, o którym mowa w tekście.": "mixed",
            S.BARE_HEADER + "Zadanie 2.\nPodaj nazwę bitwy z 1410 roku.": "external_fact",
            "Kiedy zawarto unię lubelską?": "external_fact",
            "Tekst źródłowy\nKról przysiągł pokój.": "ambiguous",
        }
        for prompt, expected in cases.items():
            with self.subTest(expected=expected, prompt=prompt[-40:]):
                r = S.route(prompt)
                self.assertEqual(r["route"], expected)
                self.assertEqual(r["retrieve"], expected in ("external_fact", "mixed"))

    def test_review_source_only_answer_verbs_and_essay_phrasing(self):
        # root's PR #104 review probes, re-expressed with independent invented text
        cases = {
            "Tekst źródłowy\nOrmel usiadł pod dębem.\nNa podstawie tekstu podaj nazwę drzewa, pod którym usiadł Ormel.":
                "supplied_source",
            "Tekst źródłowy\nOrmel usiadł pod dębem.\nNa podstawie tekstu wyjaśnij, dlaczego Ormel odpoczywał.":
                "supplied_source",
            "Tekst źródłowy\nOrmel usiadł pod dębem.\nNa podstawie tekstu i własnej wiedzy podaj nazwę krainy.": "mixed",
            "Napisz rozprawkę o Ormelu. Praca musi liczyć co najmniej 300 słów.": "essay",
            "Oceń rolę Ormela. Sformułuj tezę, podaj argumenty i zakończenie.": "essay",
            "Przedstaw w dłuższej wypowiedzi dzieje Ormela.": "essay",
        }
        for prompt, expected in cases.items():
            with self.subTest(expected=expected, prompt=prompt[-50:]):
                self.assertEqual(S.route(prompt)["route"], expected)

    def test_thesis_argument_short_task_is_not_essay(self):
        r = S.route("Tekst źródłowy\nOrmel zbudował most.\nPodaj jeden argument potwierdzający tezę autora.")
        self.assertNotEqual(r["route"], "essay")

    def test_router_ignores_answer_side_metadata(self):
        # the router takes only the prompt string; evaluator task_type / keys cannot reach it
        self.assertEqual(S.route.__code__.co_argcount, 1)


class RelationGateTests(unittest.TestCase):
    """Root's review probe 1: a same-entity passage without the requested relation must not pass."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("retrieval_gate_test", PINNED_ROOT / "scripts" / "retrieval.py")
        cls.retrieval = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.retrieval)
        chunks = [{"chunk_id": "ormel#0", "source_id": "ormel", "title": "Ormel", "locator": "Wstęp", "section": "Wstęp",
                   "text": "Ormel mieszkał nad rzeką.", "years": []},
                  {"chunk_id": "ormel#1", "source_id": "ormel", "title": "Ormel", "locator": "Młodość", "section": "Młodość",
                   "text": "Żeglarstwa uczył Ormela stary przewoźnik Tabor z wioski nad jeziorem.", "years": []}]
        chunks += [{"chunk_id": f"filler#{i}", "source_id": f"filler{i}", "title": f"Wypełniacz {i}", "locator": "x",
                    "section": "x", "text": f"Kronika numer {i} opisuje zboża, targi i pogodę w dolinie.", "years": []}
                   for i in range(40)]
        cls.idx = cls.retrieval.BM25Index(chunks)
        cls.graph = {"year_to_chunks": {}, "entity_to_chunks": {}}

    def select(self, prompt):
        return S.select_evidence(self.retrieval, self.idx, self.graph, prompt)

    def test_entity_without_relation_abstains(self):
        out = self.select("Podaj imię nauczyciela gry na harfie, który uczył Ormela.")
        self.assertTrue(out["route"]["retrieve"])
        self.assertIsNone(out["passage"], out["gate"])
        self.assertFalse(out["gate"]["pass"])

    def test_entity_with_relation_passes_in_final_window(self):
        out = self.select("Podaj imię nauczyciela żeglarstwa, który uczył Ormela.")
        self.assertIsNotNone(out["passage"], out["gate"])
        self.assertIn("Żeglarstwa", out["passage"]["text"])

    def test_source_only_probe_inserts_nothing(self):
        out = self.select("Tekst źródłowy\nOrmel usiadł pod dębem.\nNa podstawie tekstu podaj nazwę drzewa, pod którym usiadł Ormel.")
        self.assertIsNone(out["query"])
        self.assertIsNone(out["passage"])


@unittest.skipUnless(PINNED, "pinned index not staged")
class PinnedIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retrieval, cls.idx, cls.graph, cls.identity = pbr.load_pinned_assets(
            PINNED_ROOT, PINNED_ROOT / "staging" / "manifest.json", False)

    def test_base_variant_reproduces_production_chrono_ranking(self):
        prompts = [json.loads(l)["prompt"] for l in FIXTURES.read_text(encoding="utf-8").splitlines()]
        prompts += ["Kiedy zawarto unię lubelską?", "W 490 p.n.e. Ateńczycy pokonali Persów."]
        for p in prompts:
            ours = S.rank(self.retrieval, self.idx, self.graph, S.build_query(self.retrieval, p, "base"))
            prod = self.retrieval.rank(self.idx, p, S.RANK_K, mode="chrono", graph=self.graph, title_weight=1.0)
            self.assertEqual([h["chunk_id"] for h in ours], [h["chunk_id"] for h in prod])
            self.assertEqual([h["score"] for h in ours], [h["score"] for h in prod])

    def test_gate_returns_zero_hits_out_of_corpus_and_one_compact_passage_in_corpus(self):
        out = S.select_evidence(self.retrieval, self.idx, self.graph,
                                "Podaj imię faraona, dla którego wzniesiono największą piramidę w Gizie.")
        self.assertTrue(out["route"]["retrieve"])
        self.assertIsNone(out["passage"])
        hit = S.select_evidence(self.retrieval, self.idx, self.graph,
                                "Podaj nazwę planu pomocy gospodarczej USA dla Europy ogłoszonego po II wojnie światowej.")
        self.assertEqual(hit["passage"]["source_id"], "plwiki-plan-marshalla")
        self.assertLessEqual(len(hit["passage"]["text"]), S.WINDOW_CHARS)
        chunk = next(c for c in self.idx.chunks if c["chunk_id"] == hit["passage"]["chunk_id"])
        self.assertIn(hit["passage"]["text"], " ".join(chunk["text"].split()))  # verbatim, no new text

    def test_essay_and_supplied_source_never_retrieve(self):
        for p in (S.BARE_HEADER + "Zadanie 9. (0–15)\nNapisz wypracowanie: Unia lubelska i jej skutki.",
                  "Tekst źródłowy\nUnia lubelska 1569.\nNa podstawie tekstu podaj, ile państw zawarło unię."):
            out = S.select_evidence(self.retrieval, self.idx, self.graph, p)
            self.assertIsNone(out["query"])
            self.assertIsNone(out["passage"])

    def test_prepare_cli_preserves_unrouted_cases_and_writes_pairs(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="sel-rag-"))
        cases = [
            {"id": "a", "prompt": "Podaj nazwę planu pomocy gospodarczej USA dla Europy ogłoszonego po II wojnie światowej.",
             "images": ["img/a.png"]},
            {"id": "b", "prompt": "Tekst źródłowy\nSpłonęło sto domów.\nNa podstawie tekstu podaj, ile domów spłonęło.", "extra": 1},
            {"id": "c", "prompt": "Podaj imię faraona, dla którego wzniesiono największą piramidę w Gizie."},
            {"id": "d", "prompt": S.BARE_HEADER + "Zadanie 9. (0–15)\nNapisz wypracowanie o reformacji."},
        ]
        (tmp / "img").mkdir()
        (tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)  # invented bytes, only hashed
        inp = tmp / "in.jsonl"
        inp.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
        out = tmp / "out" / "sel.jsonl"
        proc = run_cli("prepare", "--input", inp, "--output", out, "--pairs", 12)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        trace = json.loads(Path(str(out) + ".trace.json").read_text(encoding="utf-8"))
        self.assertEqual([r["id"] for r in rows], ["a", "b", "c", "d"])
        self.assertEqual(rows[1:], cases[1:])  # gated-out / unrouted rows byte-identical
        self.assertTrue(rows[0]["prompt"].endswith(cases[0]["prompt"]))
        self.assertTrue(rows[0]["prompt"].startswith(pbr.HEADER))
        self.assertLessEqual(len(rows[0]["prompt"]) - len(cases[0]["prompt"]), S.BUDGET_CHARS)
        self.assertEqual(trace["model_calls"], 0)
        self.assertEqual(trace["summary"]["changed"], 1)
        self.assertEqual(trace["pairs"]["ids"], ["a"])
        self.assertEqual(trace["index"]["index_sha256"], "350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429")
        for c, row in zip(trace["cases"], rows):
            self.assertEqual(c["output_prompt_sha256"], sha(row["prompt"]))
        bare = [json.loads(l) for l in out.with_name("sel.pairs-bare.jsonl").read_text(encoding="utf-8").splitlines()]
        sel = [json.loads(l) for l in out.with_name("sel.pairs-selective.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows[0]["images"], ["../img/a.png"])  # re-expressed relative to the output dir
        self.assertEqual(bare, [dict(cases[0], images=rows[0]["images"])])
        self.assertEqual(sel, rows[:1])
        self.assertTrue((out.parent / bare[0]["images"][0]).is_file())
        again = run_cli("prepare", "--input", inp, "--output", out)
        self.assertNotEqual(again.returncode, 0)  # never overwrites
        self.assertIn("refusing to overwrite", again.stderr)


class SyntheticRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = SyntheticCorpus()

    @classmethod
    def tearDownClass(cls):
        cls.c.cleanup()

    def test_identity_mismatch_fails_closed(self):
        work = self.c.tmp / "work"
        work.mkdir(exist_ok=True)
        inp = work / "in.jsonl"
        inp.write_text(json.dumps({"id": "x", "prompt": "Kiedy zawarto unię lubelską?"}) + "\n", encoding="utf-8")
        bad = work / "manifest.json"
        m = json.loads((self.c.root / "staging" / "manifest.json").read_text(encoding="utf-8"))
        m["index_sha256"] = "0" * 64
        bad.write_text(json.dumps(m), encoding="utf-8")
        proc = run_cli("prepare", "--input", inp, "--output", work / "o.jsonl", "--root", self.c.root,
                       "--manifest", bad, "--allow-unpinned")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((work / "o.jsonl").exists())

    def test_pairs_bound(self):
        proc = run_cli("prepare", "--input", "x", "--output", "y", "--pairs", 13)
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
