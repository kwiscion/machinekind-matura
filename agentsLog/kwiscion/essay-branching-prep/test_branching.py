import base64
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('branching', Path(__file__).with_name('branching.py'))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6r1kAAAAASUVORK5CYII=')


class Tests(unittest.TestCase):
    def fixture(self, root, count=3):
        p = root/'source'; p.mkdir(); (p/'images').mkdir(); (p/'images/x.png').write_bytes(PNG)
        item = {'id': 'actual-essay', 'group': 1, 'max_points': 15, 'question': 'Wybierz jeden temat.\n'+'\n'.join(f'Temat {i}. Omów syntetyczny problem {i}.' for i in range(1,count+1)),
                'source_text': 'Pełne źródło synthetic Ω bez usuwania.', 'images': [{'path': 'images/x.png', 'source_page': 1, 'sha256': b.sha(p/'images/x.png')}], 'answer_format': 'Jedno wypracowanie.'}
        b.write(p/'exam.json', {'exam_id': 'synthetic', 'language':'pl', 'instructions':'Oryginalna instrukcja.', 'max_points':15, 'items':[item]})
        b.write(p/'answers-template.json', {'exam_id':'synthetic','answers':[{'id':'actual-essay','answer':''}]})
        return p,item

    def answers(self, stage, path, text='Synthetic final essay. ' * 20):
        template = b.adapter.load_package(stage/'exam')['template']
        for row in template['answers']:row['answer'] = text+row['id']
        b.write(path,template);return template

    def test_two_and_three_topic_forms(self):
        self.assertEqual(len(b.topics('Choose one\n1. First\ncontinued\n2. Second')),2)
        self.assertEqual(len(b.topics('Temat 1. A\nTemat 2. B\nTemat 3. C')),3)

    def test_ambiguous_duplicate_extra_topic_refusal(self):
        for s in ['1. A\n1. B','1. A\n3. C','1. A\n2. B\n3. C\n4. D','Temat 1. A\n2. B','Topic A: first; Topic B: second','1. Same\n2. Same']:
            with self.subTest(s=s),self.assertRaises(ValueError):b.topics(s)

    def test_actual_adapter_source_and_image_preservation_and_budget(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src,item=self.fixture(root);stage=root/'drafts';m=b.stage1(src,item['id'],stage)
            doc=b.adapter.load_package(stage/'exam')
            self.assertEqual(doc['exam']['items'][0]['question'],item['question'])
            for x in doc['exam']['items']:
                self.assertTrue(x['question'].startswith(item['question']));self.assertEqual(x['source_text'],item['source_text']);self.assertEqual(x['images'],item['images'])
            self.assertEqual((stage/'exam/images/x.png').read_bytes(),PNG)
            self.assertEqual((m['primary_calls_entire_wave'],m['max_attempts_entire_wave'],m['max_requested_tokens_entire_wave']),(5,20,737280))
            self.assertEqual((stage/'original/exam.json').read_bytes(),(src/'exam.json').read_bytes())

    def test_duplicate_original_ids_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src,item=self.fixture(root);p=src/'exam.json';doc=json.loads(p.read_text(encoding='utf8'));doc['items'].append(item);p.write_text(json.dumps(doc),encoding='utf8')
            with self.assertRaises(Exception):b.stage1(src,item['id'],root/'out')
            self.assertFalse((root/'out').exists())

    def test_candidates_exact_preserved_bounded_view_single_final(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src,item=self.fixture(root);one=root/'one';b.stage1(src,item['id'],one)
            answers=root/'draft.answers.json';doc=self.answers(one,answers,text='word '*1500);two=root/'two';m=b.selector(one,answers,b.sha(answers),two)
            self.assertEqual((two/'raw-candidates.answers.json').read_bytes(),answers.read_bytes())
            selected=b.adapter.load_package(two/'exam');q=selected['exam']['items'][0]['question'];self.assertTrue(q.startswith(item['question']))
            views=json.loads(q.split('OMYLNE PROPOZYCJE (JSON):\n',1)[1]);self.assertEqual(len(views),4)
            for v in views:self.assertEqual(len(v['answer']),6000);self.assertTrue(v['view_is_excerpt']);self.assertGreater(v['original_characters'],6000)
            for row in doc['answers']:self.assertEqual(m['candidate_answer_sha256'][row['id']],b.textsha(row['answer']))
            final=root/'selected.json';self.answers(two,final,text='Selected one final.');out=root/'submission.json';result=b.export_final(one,two,final,b.sha(final),out)
            self.assertEqual(set(result),{'exam_id','answers'});self.assertEqual(len(result['answers']),1);self.assertEqual(result['answers'][0]['id'],item['id'])

    def test_extra_missing_blank_and_changed_candidate_refusal(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src,item=self.fixture(root,2);one=root/'one';b.stage1(src,item['id'],one);p=root/'answers.json';doc=self.answers(one,p)
            for kind in ['extra','missing','blank','duplicate']:
                bad=copy.deepcopy(doc)
                if kind=='extra':bad['answers'].append({'id':'topic-99','answer':'extra'})
                if kind=='missing':bad['answers'].pop()
                if kind=='blank':bad['answers'][0]['answer']=' '
                if kind=='duplicate':bad['answers'].append(bad['answers'][0])
                f=root/(kind+'.json');b.write(f,bad)
                with self.assertRaises(ValueError):b.selector(one,f,b.sha(f),root/('out-'+kind))
            with self.assertRaises(ValueError):b.selector(one,p,'0'*64,root/'wronghash')
            (one/'original/exam.json').write_text('{}',encoding='utf8')
            with self.assertRaises(ValueError):b.selector(one,p,b.sha(p),root/'drift')

    def test_shared_deadline_not_reset_between_stages(self):
        a={'declared_utc':'2026-09-27T00:00:00+00:00','deadline_utc':'2026-09-27T01:00:00+00:00'};b.common_deadline(a,dict(a))
        with self.assertRaises(ValueError):b.common_deadline(a,dict(a,deadline_utc='2026-09-27T02:00:00+00:00'))
        over=dict(a,deadline_utc='2026-09-27T02:00:00+00:00')
        with self.assertRaises(ValueError):b.common_deadline(over,over)

    def test_fallback_is_exact_control_not_best_by_grade(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src,item=self.fixture(root);one=root/'one';b.stage1(src,item['id'],one);p=root/'answers.json';doc=self.answers(one,p)
            result=b.baseline_fallback(one,p,b.sha(p),root/'fallback.json','budget_exhausted')
            self.assertEqual(result['answers'][0]['answer'],doc['answers'][0]['answer'])
            doc['answers'][1]['answer']='';blank=root/'blank-draft.json';b.write(blank,doc)
            kept=b.baseline_fallback(one,blank,b.sha(blank),root/'fallback-blank.json','selector_runtime_failed')
            self.assertEqual(kept['answers'][0]['answer'],doc['answers'][0]['answer'])
            with self.assertRaises(ValueError):b.baseline_fallback(one,p,b.sha(p),root/'bad.json','grade_prefers_another')


if __name__=='__main__':unittest.main()
