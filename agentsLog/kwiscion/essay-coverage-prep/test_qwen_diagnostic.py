import copy
import unittest
from prepare_qwen_diagnostic import derive_exam
from coverage_suffix import SUFFIX


class FourCases(unittest.TestCase):
    def test_original_sources_and_three_topics_remain_complete(self):
        item={'id':'26','max_points':15,'question':'Choose one:1.A;2.B;3.C. Address each aspect.',
              'source_text':'Untouched evidence, including ambiguous content.',
              'images':[{'path':'images/example.png','sha256':'abc'}],
              'answer_format':'Topic number plus essay','group':'essay'}
        original={'exam_id':'synthetic','instructions':'All original instructions.',
                  'max_points':15,'items':[item]}
        before=copy.deepcopy(original)
        exam,template,mappings=derive_exam(original,'26',SUFFIX)
        self.assertEqual(original,before)
        self.assertEqual(exam['instructions'],original['instructions'])
        self.assertEqual(len(exam['items']),4)
        self.assertEqual(len({x['id'] for x in exam['items']}),4)
        self.assertEqual([x['forced_topic'] for x in mappings],[None,1,2,3])
        self.assertEqual([x['id'] for x in template['answers']],[x['id'] for x in exam['items']])
        for derived in exam['items']:
            self.assertTrue(derived['question'].startswith(item['question']+SUFFIX))
            for field in ('source_text','images','answer_format','max_points','group'):
                self.assertEqual(derived[field],item[field])

    def test_only_forced_choice_differs_between_forced_arms(self):
        source={'exam_id':'synthetic','items':[{'id':'26','max_points':15,'question':'ALL TOPICS'}]}
        exam,_,_=derive_exam(source,'26',SUFFIX)
        free=exam['items'][0]['question']
        suffixes=[]
        for topic,item in enumerate(exam['items'][1:],1):
            self.assertTrue(item['question'].startswith(free))
            suffixes.append(item['question'][len(free):].replace(f'numer {topic}','numer N'))
        self.assertEqual(len(set(suffixes)),1)


if __name__=='__main__':
    unittest.main()
