"""CPU-only preservation checks for the full confirmation builder."""
import copy
import unittest
from prepare_qwen_full40 import derive_exam

class Tests(unittest.TestCase):
    def test_only_essay_question_changes(self):
        items=[{'id':str(i),'max_points':15 if i==26 else 1,'question':'Original '+str(i),'source_text':'Complete source','answer_format':'Exact format','images':[{'path':'images/complete.png','sha256':'f'*64}]} for i in range(1,41)]
        source={'exam_id':'synthetic','instructions':'Complete instructions','items':items,'max_points':60}
        frozen=copy.deepcopy(source)
        result,template,mapping=derive_exam(source,'26','\nGeneric coverage policy')
        self.assertEqual(source,frozen)
        self.assertEqual(len(template['answers']),40)
        self.assertEqual([x['id'] for x in result['items']],[x['id'] for x in items])
        for old,new in zip(items,result['items']):
            expected=copy.deepcopy(old)
            if old['id']=='26':expected['question']+='\nGeneric coverage policy'
            self.assertEqual(new,expected)
        self.assertEqual(sum(x['coverage'] for x in mapping),1)
    def test_missing_essay_rejected(self):
        source={'exam_id':'synthetic','items':[{'id':'x'+str(i),'question':'q'} for i in range(40)],'max_points':60}
        with self.assertRaises(AssertionError):derive_exam(source,'26','suffix')

if __name__=='__main__':unittest.main()
