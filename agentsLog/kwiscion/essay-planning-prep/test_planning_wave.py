"""Original synthetic CPU mocks only; never opens HTTP or launches a service."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

import planning_wave as w


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.package = self.root / 'package'
        w.prepare(self.package)
        self.items = json.loads((self.package / 'inputs.json').read_text(encoding='utf8'))
        self.now = 1800000000
        m = json.loads((self.package / 'manifest.json').read_text(encoding='utf8'))
        self.prepared = copy.deepcopy(m)
        m.update(status='DECLARED', declared_utc=dt.datetime.fromtimestamp(self.now - 1, dt.timezone.utc).isoformat(),
                 deadline_utc=dt.datetime.fromtimestamp(self.now + 2699, dt.timezone.utc).isoformat(),
                 authorization={'owner': 'root', 'reference': 'synthetic CPU test only'})
        w.wr.write_json_atomic(self.package / 'manifest.json', m)
        self.out = self.root / 'results'
        self.calls = []

    def plan(self, item):
        return json.dumps({'thesis': 'Teza', 'aspects': [dict(aspect=a, fact='Fakt', cause_effect='Przyczyna',
                         thesis_link='Związek', uncertainty='Brak pewności szczegółu') for a in item['aspects']]}, ensure_ascii=False)

    def native(self, text, think=True, reason='stop', count=500):
        return {'model': w.tr.MODEL, 'done': True, 'done_reason': reason, 'eval_count': count,
                'prompt_eval_count': 900, 'message': {'content': text, 'thinking': 'reasoning' if think else ''}}

    def transport(self, payload, timeout):
        self.calls.append(payload)
        ledger = json.loads((self.out / 'ledger.json').read_text(encoding='utf8'))
        self.assertEqual(len(ledger['entries']), len(self.calls))  # persisted before transport
        self.assertEqual(ledger['entries'][-1]['status'], 'reserved')
        self.assertEqual(timeout, 420)
        p = payload['messages'][0]['content']
        item = next(i for i in self.items if p.endswith(i['full_task']))
        text = self.plan(item) if payload['options']['num_predict'] == 8192 else '  ' + 'argument ' * 405 + '\n'
        return self.native(text, payload['think'])

    def run_wave(self, transport=None, guard=lambda: None, clock=None):
        return w.run_declared(self.package, self.out, transport or self.transport, guard, clock or (lambda: self.now))

    def test_complete_exact_caps_alternation_and_strings(self):
        r = self.run_wave()
        self.assertEqual((r['calls'], r['requested_tokens'], r['answer_slots']), (18, 196608, 12))
        self.assertEqual(r['status'], 'complete')
        self.assertEqual([x['options']['num_predict'] for x in self.calls[:6]], [20480, 8192, 4096, 8192, 4096, 20480])
        self.assertTrue(all('temperature' not in x['options'] and x['truncate'] is False and x['options']['shift'] is False for x in self.calls))
        a = json.loads((self.out / 'answers.json').read_text(encoding='utf8'))
        self.assertTrue(all(x['answer'].startswith('  ') and x['answer'].endswith('\n') for x in a))
        self.assertTrue(all(x['error'] is None for x in a))

    def test_failed_plan_skips_writer_no_control_fallback(self):
        def send(p, timeout):
            data = self.transport(p, timeout)
            if p['options']['num_predict'] == 8192:
                data['message']['content'] = '{}'
            return data
        r = self.run_wave(send)
        self.assertEqual((r['calls'], r['requested_tokens']), (12, 172032))
        a = json.loads((self.out / 'answers.json').read_text(encoding='utf8'))
        self.assertEqual(sum(bool(x['answer']) for x in a), 6)
        self.assertTrue(all(not x['answer'] and x['error'] == 'failed_plan' for x in a if x['arm'] == 'candidate'))

    def test_length_plan_and_empty_control_are_local_failures(self):
        def send(p, timeout):
            data = self.transport(p, timeout)
            if p['options']['num_predict'] == 8192:
                data['done_reason'] = 'length'
            elif p['options']['num_predict'] == 20480:
                data['message']['content'] = ''
            return data
        r = self.run_wave(send)
        self.assertEqual(r['calls'], 12)
        self.assertEqual(r['status'], 'complete')
        self.assertTrue(all(not x['answer'] for x in json.loads((self.out / 'answers.json').read_text(encoding='utf8'))))

    def test_transport_failure_keeps_reservation_and_all_denominator_slots(self):
        def fail(p, timeout):
            raise TimeoutError('mock lost connection')
        r = self.run_wave(fail)
        self.assertEqual((r['calls'], r['requested_tokens'], r['unsettled_reservations']), (1, 20480, 1))
        self.assertEqual(r['answer_slots'], 12)
        self.assertEqual(r['status'], 'stopped')

    def test_global_invalid_usage_raw_saved_and_no_next_call(self):
        def send(p, timeout):
            d = self.transport(p, timeout)
            d['eval_count'] = 99999
            return d
        r = self.run_wave(send)
        self.assertEqual(r['calls'], 1)
        self.assertEqual(r['status'], 'stopped')
        self.assertTrue((self.out / 'native-raw.jsonl').exists())

    def test_failed_writer_does_not_replace_with_control_and_continues(self):
        def send(p, timeout):
            d = self.transport(p, timeout)
            if p['options']['num_predict'] == 4096:
                d['message']['content'] = ''
            return d
        r = self.run_wave(send)
        self.assertEqual(r['calls'], 18)
        a = json.loads((self.out / 'answers.json').read_text(encoding='utf8'))
        self.assertTrue(all(x['answer'] == '' for x in a if x['arm'] == 'candidate'))
        self.assertTrue(all(x['answer'] for x in a if x['arm'] == 'control'))

    def test_deadline_after_response_preserves_raw_and_stops(self):
        now = [self.now]
        def send(p, timeout):
            d = self.transport(p, timeout)
            now[0] += 2695
            return d
        r = self.run_wave(send, clock=lambda: now[0])
        self.assertEqual(r['calls'], 1)
        self.assertIn('deadline_after_response', r['stop_reason'])
        self.assertTrue((self.out / 'native-raw.jsonl').exists())

    def test_guard_failure_zero_calls(self):
        def guard():
            raise w.StopWave('owned host unavailable')
        r = self.run_wave(guard=guard)
        self.assertEqual(r['calls'], 0)

    def test_deadline_refuses_incomplete_request_window(self):
        r = self.run_wave(clock=lambda: self.now + 2300)
        self.assertEqual(r['calls'], 0)
        self.assertIn('insufficient_full', r['stop_reason'])

    def test_prepared_expired_and_replay_refused(self):
        w.wr.write_json_atomic(self.package / 'manifest.json', self.prepared)
        with self.assertRaises(w.StopWave): self.run_wave()
        self.assertFalse(self.out.exists())
        with self.assertRaises(w.StopWave): w.validate_declaration(self.prepared, self.now)

    def test_replay_and_pin_tamper_refused(self):
        self.run_wave()
        with self.assertRaises(FileExistsError): self.run_wave()
        (self.package / 'inputs.json').write_text('[]', encoding='utf8')
        with self.assertRaises(w.StopWave): w.preflight(self.package)

    def test_plan_shape_duplicate_aspects_and_uncertainty(self):
        item = self.items[0]
        self.assertTrue(w.parse_plan(self.plan(item), item))
        d = json.loads(self.plan(item)); d['aspects'][0]['uncertainty'] = ''
        self.assertFalse(w.parse_plan(json.dumps(d), item))
        d = json.loads(self.plan(item)); d['aspects'][1] = d['aspects'][0]
        self.assertFalse(w.parse_plan(json.dumps(d), item))
        self.assertFalse(w.parse_plan('{"thesis":"a","thesis":"b","aspects":[]}', item))

    def test_full_original_task_in_every_prompt_no_retrieval(self):
        for item in self.items:
            for stage in w.STAGES:
                p = w.prompt(item, stage, self.plan(item))
                self.assertTrue(p.endswith(item['full_task']))
                self.assertNotIn('evidence', item)
        self.assertEqual([x['item'] for x in self.items], list(w.IDS))

    def test_exact_prose_contract_rejects_wrappers_underlength(self):
        item = self.items[0]
        self.assertFalse(w.essay_check('Krótki tekst.', item)['ok'])
        self.assertFalse(w.essay_check('```\n' + 'argument ' * 405 + '\n```', item)['ok'])


if __name__ == '__main__':
    unittest.main()
