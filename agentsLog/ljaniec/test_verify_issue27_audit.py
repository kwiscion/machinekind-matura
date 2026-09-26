import json
from pathlib import Path
import tempfile
import unittest
from verify_issue27_audit import audit, values_match


class VerifierTests(unittest.TestCase):
    def test_union_whitespace_and_non_null_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            raw, inputs = Path(directory)/'raw', Path(directory)/'inputs'
            raw.write_text(json.dumps({'id':'a','prompt':'secret','raw_response':'  ','error':'timeout','wall_s':1})+'\n')
            inputs.write_text(json.dumps({'id':'a','prompt':'secret'})+'\n')
            result = audit(raw, inputs)
            self.assertEqual(result['reported_error_or_empty_response_count'], 1)
            self.assertEqual(result['response_empty_count'], 1)
            self.assertTrue(result['input_comparison']['all_record_prompts_match_by_id'])
            self.assertTrue(result['input_comparison']['exact_id_sequence_match'])
            self.assertNotIn('secret', json.dumps(result))
            self.assertIsNone(result['completion_tokens']['sum'])

    def test_strict_structure_types_and_finite_numbers(self):
        for left, right in [(1.0,float('nan')), (float('inf'),float('inf')),
                            (1,True), (1,1.0), ({'a':1},{'a':1,'extra':2}),
                            ({'a':1},{})]:
            with self.subTest(left=left,right=right):
                self.assertFalse(values_match(left,right))
        self.assertTrue(values_match({'a':1.0},{'a':1.0000001}))
        self.assertFalse(values_match({'a':1.0},{'a':1.00001}))

    def test_null_error_semantics_and_prompt_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            raw, inputs = Path(directory)/'raw', Path(directory)/'inputs'
            raw.write_text(json.dumps({'id':'a','prompt':'wrong','raw_response':'partial','error':''})+'\n')
            inputs.write_text(json.dumps({'id':'a','prompt':'expected'})+'\n')
            result=audit(raw,inputs)
            self.assertEqual(result['reported_error_count'],1)
            self.assertEqual(result['reported_error_or_empty_response_count'],1)
            self.assertFalse(result['input_comparison']['all_record_prompts_match_by_id'])
            self.assertEqual(result['latency']['denominator_records_with_latency'],0)

    def test_invalid_numeric_values_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            raw, inputs = Path(directory)/'raw', Path(directory)/'inputs'
            inputs.write_text(json.dumps({'id':'a','prompt':'expected'})+'\n')
            for value in [float('nan'),float('inf'),True,'1',-1]:
                raw.write_text(json.dumps({'id':'a','raw_response':'answer','wall_s':value})+'\n')
                with self.subTest(value=value),self.assertRaises(ValueError):
                    audit(raw,inputs)


if __name__ == '__main__':
    unittest.main()
