"""Synthetic CPU-only preservation checks using the actual organizer adapter."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import coverage_suffix as policy

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('coverage_adapter', ROOT/'scripts/Bukareszt/matura_package.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6r1kAAAAASUVORK5CYII=')


class Tests(unittest.TestCase):
    def test_original_source_image_format_and_id_survive_real_adapter(self):
        item = dict(id='synthetic-essay', group=1, max_points=15,
                    question='Wybierz jeden temat.\n1. Syntetyczny problem A; aspekty alfa i beta.\n2. Syntetyczny problem B; aspekt gamma.',
                    source_text='Pełny syntetyczny materiał Ω.\nDrugi akapit bez skracania.',
                    answer_format='Numer tematu i jedno wypracowanie.',
                    images=[dict(path='images/fixture.png', source_page=1, sha256=hashlib.sha256(PNG).hexdigest())])
        original = copy.deepcopy(item)
        derived = policy.append_to_item(item)
        self.assertEqual(item, original)
        self.assertEqual(derived['question'], original['question']+policy.SUFFIX)
        self.assertEqual({k:v for k,v in derived.items() if k!='question'},
                         {k:v for k,v in original.items() if k!='question'})
        exam = dict(exam_id='synthetic-policy-check', language='pl', instructions='Pełna instrukcja syntetyczna.', max_points=15, items=[derived])
        with tempfile.TemporaryDirectory(prefix='essay-coverage-cpu-') as tmp:
            root=Path(tmp);(root/'images').mkdir();(root/'images/fixture.png').write_bytes(PNG)
            (root/'exam.json').write_text(json.dumps(exam,ensure_ascii=False),encoding='utf8')
            (root/'answers-template.json').write_text(json.dumps(dict(exam_id=exam['exam_id'],answers=[dict(id=item['id'],answer='')])),encoding='utf8')
            checked=adapter.load_package(root)
            prompt=adapter.build_prompt(checked['exam'],checked['exam']['items'][0])
            for untouched in (original['question'],original['source_text'],original['answer_format'],exam['instructions']):
                self.assertIn(untouched,prompt)
            self.assertIn(policy.SUFFIX,prompt)
            self.assertEqual((root/'images/fixture.png').read_bytes(),PNG)
            self.assertEqual(checked['summary']['items'],1)
        derived['images'][0]['path']='changed-copy-only'
        self.assertEqual(item,original)

    def test_duplicate_application_and_missing_task_refused(self):
        for item in ({},{'question':''},{'question':None}):
            with self.assertRaises(ValueError):policy.append_to_item(item)
        with self.assertRaises(ValueError):policy.append_to_item(policy.append_to_item({'question':'Complete synthetic task'}))


if __name__=='__main__':unittest.main()
