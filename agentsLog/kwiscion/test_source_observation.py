"""CPU-only synthetic stage/failure tests; no model or runtime access."""
import copy
import unittest
from unittest.mock import Mock
import run_source_observation as r

class Observation(unittest.TestCase):
    def test_triplets_preserve_inputs_and_caps(self):
        cases=[{'id':str(i),'content':[{'type':'text','text':'Original task'},{'type':'image_url','image_url':{'url':'data:image/png;base64,AA=='}}]} for i in range(6)]
        original=copy.deepcopy(cases);seen=[]
        def dispatch(case,stage,fallback):
            seen.append((copy.deepcopy(case),stage,fallback))
            return {'answer':'Observed symbol','case_error':False}
        self.assertEqual(len(r.triplets(cases,dispatch)),18)
        self.assertEqual(cases,original)
        self.assertEqual(sum(r.CAPS[x[1]] for x in seen),16896)
        for i in range(6):
            bare,obs,final=seen[i*3:i*3+3]
            self.assertEqual(bare[0],original[i])
            self.assertEqual(obs[0]['content'][:-1],original[i]['content'])
            self.assertEqual(final[0]['content'][:-1],original[i]['content'])
            self.assertIn('Observed symbol',final[0]['content'][-1]['text'])

    def test_failed_observation_uses_bare_reserved_final(self):
        case={'id':'synthetic','content':'Original input'};seen=[]
        def dispatch(c,stage,fallback):
            seen.append((copy.deepcopy(c),stage,fallback))
            return {'answer':'MUST NOT PROPAGATE','case_error':stage=='observation'}
        r.triplets([case],dispatch)
        self.assertEqual(len(seen),3)
        self.assertEqual(seen[2],(case,'final',True))

    def test_local_failure_requires_usage_context_and_runtime(self):
        for issue in (None,'truncated','context_truncated','usage','runtime'):
            with self.subTest(issue=issue):
                row={'error':{'type':'incomplete'},'raw_response':{},'usage':{'prompt_tokens':10,'completion_tokens':768,'total_tokens':778}}
                if issue in ('truncated','context_truncated'):row['raw_response'][issue]=True
                if issue=='usage':row['usage']['completion_tokens']=769
                adapter=Mock();adapter.extract_answer.return_value=(None,{'type':'incomplete'})
                verify=Mock(side_effect=RuntimeError('runtime') if issue=='runtime' else None)
                if issue:
                    with self.assertRaises(RuntimeError):r.validate(row,768,None,adapter,lambda *_:True,verify)
                else:
                    self.assertEqual(r.validate(row,768,None,adapter,lambda *_:True,verify),{'answer':'','case_error':True})
                    verify.assert_called_once()

    def test_systemic_failure_stops_without_later_stage(self):
        dispatch=Mock(side_effect=RuntimeError('transport'))
        with self.assertRaises(RuntimeError):r.triplets([{'id':'synthetic','content':'source'}],dispatch)
        self.assertEqual(dispatch.call_count,1)
        adapter=Mock();adapter.extract_answer.return_value=(None,{'type':'http'})
        with self.assertRaises(RuntimeError):r.validate({'error':{'type':'http'}},1024,None,adapter,lambda *_:False,Mock())

if __name__=='__main__':unittest.main()
