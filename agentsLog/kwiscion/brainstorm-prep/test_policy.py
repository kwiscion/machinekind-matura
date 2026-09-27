import copy
import json
import unittest
import policy


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.exam={'exam_id':'synthetic','instructions':'KEEP','items':[dict(id='x',question='Full question',source_text='All source',answer_format='Exact original format',images=[{'path':'image.png','sha256':'abc'}],max_points=1)]}
        self.ok={'placeholder':False,'incomplete_partial':False}

    def test_complete_source_and_independent_ab(self):
        before=copy.deepcopy(self.exam);rows,mapping=policy.drafts(self.exam,['x'])
        self.assertEqual(self.exam,before);self.assertEqual(rows[0]['question'],'Full question')
        self.assertEqual(rows[1]['question'],'Full question'+policy.B_SUFFIX)
        for row in rows:
            for key in ('source_text','answer_format','images'):self.assertEqual(row[key],before['items'][0][key])
        self.assertEqual([r['arm'] for r in mapping],['A','B'])

    def test_full_candidates_opaque_order_and_exact_export(self):
        answers={'x--A':' Exact A \n','x--B':'B complete'};states={k:self.ok for k in answers}
        rows,bindings,fallbacks=policy.selection_rows(self.exam,answers,states,['x'])
        self.assertTrue(rows[0]['question'].startswith('Full question'+policy.SELECT_SUFFIX))
        self.assertEqual(rows[0]['images'],self.exam['items'][0]['images'])
        chosen=next(k for k,v in bindings['x'].items() if v['arm']=='B')
        result,receipt=policy.export({'x':'```json\n'+json.dumps({'candidate_id':chosen})+'\n```'},{'x':self.ok},bindings,fallbacks)
        self.assertEqual(result[0]['answer'],answers['x--B']);self.assertFalse(receipt[0]['rewritten'])
        self.assertEqual(policy.selection_rows(self.exam,answers,states,['x'])[1],bindings)

    def test_invalid_duplicate_unknown_or_prose_falls_back_exactly(self):
        a={'x--A':'A \n','x--B':'B'};rows,b,f=policy.selection_rows(self.exam,a,{k:self.ok for k in a},['x']);ident=next(iter(b['x']))
        for text in ['{"candidate_id":"unknown"}',f'{{"candidate_id":"{ident}","candidate_id":"{ident}"}}','prose '+json.dumps({'candidate_id':ident})]:
            out,r=policy.export({'x':text},{'x':self.ok},b,f);self.assertEqual(out[0]['answer'],'A \n');self.assertEqual(r[0]['mode'],'operational_fallback')

    def test_partial_a_uses_complete_b_without_selector(self):
        a={'x--A':'partial','x--B':'good'};rows,b,f=policy.selection_rows(self.exam,a,{'x--A':dict(placeholder=False,incomplete_partial=True),'x--B':self.ok},['x'])
        self.assertEqual(rows,[]);out,r=policy.export({}, {},b,f);self.assertEqual(out[0]['answer'],'good');self.assertEqual(r[0]['arm'],'B')

    def test_oversized_candidate_not_silently_truncated(self):
        a={'x--A':'A','x--B':'B'*6001};rows,b,f=policy.selection_rows(self.exam,a,{k:self.ok for k in a},['x'])
        self.assertEqual(rows,[]);self.assertEqual(f['x']['answer'],'A')


if __name__=='__main__':unittest.main()
