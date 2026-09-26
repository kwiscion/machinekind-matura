import copy
import json
from pathlib import Path
import unittest
import study_driver as d


class DriverTests(unittest.TestCase):
    def cases(self):
        item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        return [{'id': route, 'content': 'full source ' + route, 'kind': 'essay' if route == 'essay' else 'question',
                 'structured_route': route, **({'essay_item': item} if route == 'essay' else {})}
                for route in ('closed', 'open', 'image', 'essay')]

    def test_eight_arms_and_sixteen_slots_without_source_mutation(self):
        cases = self.cases(); before = copy.deepcopy(cases); calls = []; events = []
        def invoke(case, stage):
            self.assertEqual(case['content'], 'full source ' + case['source_case_id'])
            calls.append((case['id'], stage['name']))
            text = 'argument ' * 405
            if stage['name'] == 'selector': text = '{"choice":"c2"}'
            if stage['name'] == 'interpretation': text = '{"answer":"image answer","revisit_question":"verify symbol"}'
            if stage['name'] == 'essay_plan': text = '{}'
            return {'ok': True, 'final': text, 'error': None, 'attempt_records': []}
        results = d.run_study(cases, invoke, events.append)
        self.assertEqual(cases, before)
        self.assertEqual(len(results), 8)
        self.assertEqual(len(calls), 16)
        self.assertEqual([r['case_id'] for r in results], ['closed__strong_single', 'closed__structured_routes',
                         'open__structured_routes', 'open__strong_single', 'image__strong_single',
                         'image__structured_routes', 'essay__structured_routes', 'essay__strong_single'])
        self.assertTrue(all(r['final'] for r in results))

    def test_fatal_runtime_stops_entire_study(self):
        calls = []
        def invoke(case, stage):
            calls.append(stage)
            return {'ok': False, 'final': None, 'fatal': True, 'error': 'ownership uncertain', 'attempt_records': []}
        results = d.run_study(self.cases(), invoke, lambda e: None)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(results), 8)
        self.assertTrue(results[0]['stopped'])
        self.assertTrue(all(r['selection'] == 'unsent' for r in results[1:]))


if __name__ == '__main__': unittest.main()
