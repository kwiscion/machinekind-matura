import json
import unittest
from pathlib import Path
import shared_routes as r


class SharedRoutesTests(unittest.TestCase):
    def setUp(self):
        self.item = json.loads((Path(__file__).parent / 'prepared-v1/inputs.json').read_text(encoding='utf8'))[0]
        self.plan = json.dumps({'thesis': 'Teza', 'aspects': [dict(aspect=a, fact='Fakt', cause_effect='Przyczyna',
                               thesis_link='Związek', uncertainty='Niepewna data') for a in self.item['aspects']]})

    def test_suffix_only_and_caps(self):
        for stage, (think, cap) in r.w.STAGES.items():
            hook = r.route_stage(self.item, stage, self.plan)
            self.assertEqual(set(hook), {'name', 'suffix', 'think', 'cap'})
            self.assertEqual((hook['think'], hook['cap']), (think, cap))
            self.assertNotIn(self.item['full_task'], hook['suffix'])

    def test_invalid_plan_blocks_writer(self):
        with self.assertRaises(r.w.StopWave): r.route_stage(self.item, 'write', '{}')
        self.assertIsNone(r.stage_result(self.item, 'plan', '{}')['next_stage'])

    def test_success_plan_passes_exact_notes(self):
        result = r.stage_result(self.item, 'plan', self.plan)
        self.assertEqual(result['plan'], self.plan)
        self.assertEqual(result['next_stage'], 'write')
        self.assertIn(self.plan, r.route_stage(self.item, 'write', result['plan'])['suffix'])

    def test_failed_native_final_not_salvaged(self):
        result = r.stage_result(self.item, 'control', 'argument ' * 405, 'length')
        self.assertFalse(result['ok'])
        self.assertEqual(result['final'], '')


if __name__ == '__main__': unittest.main()
