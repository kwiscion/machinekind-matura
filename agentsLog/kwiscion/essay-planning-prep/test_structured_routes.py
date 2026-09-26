"""Synthetic stage callbacks only. No networking, service or GPU operations."""
import copy
import json
from pathlib import Path
import unittest

import structured_routes as r


def okay(text):
    return {'ok': True, 'final': text, 'error': None, 'attempt_records': []}


def failed(partial=None, fatal=False):
    return {'ok': False, 'final': None, 'partial_final': partial, 'error': 'synthetic failure',
            'fatal': fatal, 'attempt_records': []}


class RoutesTests(unittest.TestCase):
    def setUp(self):
        self.case = {'id': 'original-001', 'content': [{'type': 'text', 'text': 'Complete original source and question'},
                     {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,YWJj'}}]}
        self.calls, self.events = [], []

    def callback(self, results):
        def invoke(case, stage):
            self.assertEqual(case, self.case)
            self.assertEqual(set(stage) - {'validation_context'}, {'name', 'output_kind', 'suffix', 'profile', 'validation'})
            self.assertNotIn('timeout', stage)
            self.assertNotIn('cap', stage)
            self.calls.append(copy.deepcopy(stage))
            case['content'][0]['text'] = 'callback mutation must not escape'
            result = results[stage['name']]
            if isinstance(result, Exception): raise result
            return result
        return invoke

    def run_route(self, route, results):
        original = copy.deepcopy(self.case)
        out = r.orchestrate(self.case, route, self.callback(results), self.events.append)
        self.assertEqual(self.case, original)
        self.assertEqual(self.events[-1]['event'], 'route_complete')
        return out

    def test_closed_independent_candidates_and_exact_selection(self):
        finals = [' A \n', 'B', 'C']
        out = self.run_route('closed', {**{'candidate_' + str(i): okay(x) for i, x in enumerate(finals, 1)},
                             'selector': okay('{"choice":"c1","answer":" A \\n"}')})
        self.assertEqual(out['final'], finals[0])
        self.assertEqual([x['answer'] for x in out['candidates']], finals)
        self.assertEqual(out['selection'], 'selected_candidate')
        self.assertEqual(len(self.calls), 4)
        for c in self.calls[:3]:
            self.assertNotIn('"answer":', c['suffix'])
        self.assertTrue(any(e['event'] == 'candidate_retained' for e in self.events[:4]))

    def test_invalid_selector_falls_back_without_extra_call(self):
        out = self.run_route('closed', {'candidate_1': okay('A'), 'candidate_2': okay('B'), 'candidate_3': okay('C'),
                             'selector': okay('{"choice":"c2","answer":"changed B"}')})
        self.assertEqual(out['final'], 'A')
        self.assertEqual(out['selection'], 'retained_complete')
        self.assertEqual(len(self.calls), 4)

    def test_selector_new_answer_is_labelled_and_originals_retained(self):
        out = self.run_route('closed', {'candidate_1': okay('A'), 'candidate_2': okay('B'), 'candidate_3': failed(),
                             'selector': okay('{"choice":"NEW","answer":" new final "}')})
        self.assertEqual(out['selection'], 'new_answer')
        self.assertEqual(out['final'], ' new final ')
        self.assertEqual([x['answer'] for x in out['candidates']], ['A', 'B', ' new final '])

    def test_all_closed_failed_use_only_remaining_fourth_stage(self):
        out = self.run_route('closed', {'candidate_1': failed(), 'candidate_2': failed(), 'candidate_3': failed(),
                             'selector_direct_fallback': okay('source-only answer')})
        self.assertEqual(out['final'], 'source-only answer')
        self.assertEqual(len(self.calls), 4)

    def test_known_complete_preferred_to_partial_on_selection_failure(self):
        out = self.run_route('closed', {'candidate_1': failed('partial A'), 'candidate_2': okay('B'),
                             'candidate_3': failed(), 'selector': failed()})
        self.assertEqual(out['final'], 'B')
        self.assertEqual(out['candidates'][0]['answer'], 'partial A')

    def test_open_failed_matrix_still_drafts_and_checks_coverage(self):
        out = self.run_route('open', {'claims_evidence': failed('unverified partial map'),
                             'draft': okay('draft'), 'coverage': okay('covered final')})
        self.assertEqual(out['final'], 'covered final')
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.calls[0]['output_kind'], 'intermediate')
        self.assertIn('niepełny etap', self.calls[1]['suffix'])
        self.assertEqual([c['answer'] for c in out['candidates']], ['draft', 'covered final'])

    def test_open_failed_review_retains_exact_draft(self):
        out = self.run_route('open', {'claims_evidence': okay('map'), 'draft': okay(' draft \n'), 'coverage': failed('partial review')})
        self.assertEqual(out['final'], ' draft \n')
        self.assertEqual(len(out['candidates']), 2)

    def test_image_no_ambiguity_skips_revisit(self):
        out = self.run_route('image', {'observations': okay('observations, not answer'),
                             'interpretation': okay('{"answer":"answer","revisit_question":""}')})
        self.assertEqual(out['final'], 'answer')
        self.assertEqual(len(self.calls), 2)
        self.assertNotIn('observations, not answer', [c['answer'] for c in out['candidates']])

    def test_image_targeted_revisit_and_failed_revisit_retains_interpretation(self):
        out = self.run_route('image', {'observations': okay('visible marks'),
                             'interpretation': okay('{"answer":"A","revisit_question":"Which mark?"}'),
                             'targeted_revisit': failed()})
        self.assertEqual(out['final'], 'A')
        self.assertIn('Which mark?', self.calls[-1]['suffix'])
        self.assertEqual(len(self.calls), 3)

    def test_invalid_image_envelope_is_never_exported(self):
        out = self.run_route('image', {'observations': okay('PLAN'),
                             'interpretation': okay('{"plan":"NOT AN ANSWER"}'),
                             'targeted_revisit': failed()})
        self.assertIsNone(out['final'])
        self.assertEqual(out['candidates'], [])

    def test_failed_essay_plan_uses_defined_writer_new_policy(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.case['essay_item'] = item
        out = self.run_route('essay', {'essay_plan': okay('{"bad_plan":"do not export"}'),
                             'essay_write': okay('argument ' * 405)})
        self.assertEqual(out['final'], 'argument ' * 405)
        self.assertEqual(len(self.calls), 2)
        self.assertIn('Plan nie przeszedł', self.calls[-1]['suffix'])
        self.assertEqual(self.calls[-1]['profile'], 'direct')

    def test_no_essay_plan_can_be_exported_when_writer_fails(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.case['essay_item'] = item
        out = self.run_route('essay', {'essay_plan': okay('INTERMEDIATE PLAN'), 'essay_write': failed()})
        self.assertIsNone(out['final'])
        self.assertEqual(out['candidates'], [])

    def test_fatal_stops_dispatch_and_retains_prior_final(self):
        out = self.run_route('closed', {'candidate_1': okay('A'), 'candidate_2': failed(fatal=True)})
        self.assertEqual(out['final'], 'A')
        self.assertTrue(out['stopped'])
        self.assertEqual(len(self.calls), 2)

    def test_exception_stops_without_exporting_intermediate(self):
        out = self.run_route('open', {'claims_evidence': okay('map'), 'draft': TimeoutError('owned runtime failed')})
        self.assertIsNone(out['final'])
        self.assertTrue(out['stopped'])
        self.assertEqual(len(self.calls), 2)

    def test_control_has_entire_single_logical_slot(self):
        out = self.run_route('control', {'control': okay('strong control')})
        self.assertEqual(out['final'], 'strong control')
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn('timeout', self.calls[0])

    def test_duplicate_selector_keys_rejected(self):
        candidates = [{'candidate_id': 'c1', 'answer': 'A', 'complete': True}]
        self.assertIsNone(r.parse_selection('{"choice":"c1","choice":"NEW","answer":"x"}', candidates))

    def test_writer_returning_plan_json_is_not_a_final(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.case['essay_item'] = item
        out = self.run_route('essay', {'essay_plan': failed(), 'essay_write': okay('{"thesis":"plan","aspects":[]}')})
        self.assertIsNone(out['final'])
        self.assertEqual(out['candidates'], [])

    def test_short_clean_essay_retained_as_incomplete(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.case['essay_item'] = item
        out = self.run_route('essay', {'essay_plan': failed(), 'essay_write': okay('argument ' * 120)})
        self.assertEqual(out['final'], 'argument ' * 120)
        self.assertFalse(out['complete'])
        self.assertEqual(out['selection'], 'retained_partial')

    def test_partial_writer_plan_envelope_is_not_exported(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.case['essay_item'] = item
        out = self.run_route('essay', {'essay_plan': failed(), 'essay_write': failed('{"thesis":"partial plan"}')})
        self.assertIsNone(out['final'])

    def test_intermediate_partial_is_not_fallback_final(self):
        out = self.run_route('open', {'claims_evidence': failed('claims and evidence'),
                             'draft': failed(), 'coverage': failed()})
        self.assertIsNone(out['final'])
        self.assertEqual(out['candidates'], [])

    def test_every_event_has_arm_and_route_identity(self):
        self.case.update(study_arm='strong_single', source_case_id='source-001')
        self.run_route('control', {'control': okay('A')})
        for event in self.events:
            self.assertEqual(event['case_id'], self.case['id'])
            self.assertEqual(event['source_case_id'], 'source-001')
            self.assertEqual(event['study_arm'], 'strong_single')
            self.assertEqual(event['route'], 'control')

    def test_selector_validation_has_exact_candidates_inside_shared_hook(self):
        self.run_route('closed', {'candidate_1': okay(' A '), 'candidate_2': failed(),
                                 'candidate_3': okay('C'), 'selector': okay('{"choice":"c1"}')})
        stage = self.calls[-1]
        self.assertTrue(r.validate_stage_text(self.case, stage, '{"choice":"c1"}')['ok'])
        for text in ('{"choice":"c2"}', '{"choice":"c1","answer":"A"}'):
            self.assertFalse(r.validate_stage_text(self.case, stage, text)['ok'])
        del stage['validation_context']
        self.assertFalse(r.validate_stage_text(self.case, stage, '{"choice":"c1"}')['ok'])


if __name__ == '__main__': unittest.main()
