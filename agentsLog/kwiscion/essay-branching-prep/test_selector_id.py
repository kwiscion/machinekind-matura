import json
from pathlib import Path
import tempfile
import unittest
import selector_id as s
import test_branching as fixtures


class Tests(unittest.TestCase):
    def fixture(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=Path(t.name)
        original,item=fixtures.Tests().fixture(root);first=root/'first';fixtures.b.stage1(original,item['id'],first)
        answers=root/'drafts.json';doc=fixtures.Tests().answers(first,answers,text='Exact saved candidate Ω. ')
        output=root/'selector';s.prepare(first,answers,s.sha(answers),output)
        return root,output,item,doc

    def test_complete_sources_all_candidates_and_exact_export(self):
        root,source,item,doc=self.fixture();derived=s.read(source/'exam/exam.json')['items'][0]
        self.assertTrue(derived['question'].startswith(item['question']))
        for row in doc['answers']:self.assertIn(row['answer'],derived['question'])
        self.assertEqual(derived['source_text'],item['source_text']);self.assertEqual(derived['images'],item['images'])
        self.assertEqual((source/'exam/images/x.png').read_bytes(),fixtures.PNG)
        choice=root/'choice.json';s.write(choice,{'answers':[{'id':item['id'],'answer':'{"candidate_id":"candidate-C"}'}]})
        receipt=s.export(source,choice,s.sha(choice),root/'final.json')
        self.assertEqual(s.read(root/'final.json')['answers'][0]['answer'],doc['answers'][2]['answer'])
        self.assertFalse(receipt['rewritten'])

    def test_invalid_extra_duplicate_choices_preserve_direct_control(self):
        root,source,item,doc=self.fixture()
        for i,text in enumerate(['candidate-B','{"candidate_id":"candidate-Z"}','{"candidate_id":"candidate-A","extra":1}','{"candidate_id":"candidate-B","candidate_id":"candidate-C"}']):
            choice=root/f'choice{i}.json';s.write(choice,{'answers':[{'id':item['id'],'answer':text}]})
            output=root/f'final{i}.json';receipt=s.export(source,choice,s.sha(choice),output)
            self.assertEqual(receipt['mode'],'invalid_selection_direct_fallback')
            self.assertEqual(s.read(output)['answers'][0]['answer'],doc['answers'][0]['answer'])

    def test_single_optional_json_fence_accepts_without_rewriting(self):
        root,source,item,doc=self.fixture()
        for i,text in enumerate(['```json\n{"candidate_id":"candidate-B"}\n```','```\n{"candidate_id":"candidate-B"}\n```']):
            choice=root/f'fenced{i}.json';s.write(choice,{'answers':[{'id':item['id'],'answer':text}]})
            out=root/f'fencedfinal{i}.json';receipt=s.export(source,choice,s.sha(choice),out)
            self.assertEqual(receipt['mode'],'strict_id_exact_saved_export')
            self.assertEqual(s.read(out)['answers'][0]['answer'],doc['answers'][1]['answer'])

    def test_fence_does_not_admit_prose_extra_objects_or_keys(self):
        root,source,item,doc=self.fixture()
        valid='```json\n{"candidate_id":"candidate-B"}\n```'
        bad=['Here: '+valid,valid+'\nExtra',valid+'\n'+valid,'```json\n{"candidate_id":"candidate-B"}\n{}\n```','```json\n{"candidate_id":"candidate-Z"}\n```','```json\n{"candidate_id":"candidate-B","why":"x"}\n```','```json\n{"candidate_id":"candidate-B","candidate_id":"candidate-C"}\n```']
        for i,text in enumerate(bad):
            choice=root/f'bad{i}.json';s.write(choice,{'answers':[{'id':item['id'],'answer':text}]})
            out=root/f'badfinal{i}.json';receipt=s.export(source,choice,s.sha(choice),out)
            self.assertEqual(receipt['mode'],'invalid_selection_direct_fallback')
            self.assertEqual(s.read(out)['answers'][0]['answer'],doc['answers'][0]['answer'])


if __name__=='__main__':unittest.main()
