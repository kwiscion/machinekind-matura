"""CPU-only integration tests; synthetic source data, mocked transport, no server."""
import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('native_test_runner', HERE / 'run_native_package.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
prep = r.load('native_test_prepare', HERE / 'prepare_native_package.py')


class Tests(unittest.TestCase):
    def setUp(self):
        private = REPO / 'agentsLog/kwiscion/private'
        private.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='native-cpu-test-', dir=private)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def package(self, count=3, essays=('essay-custom',)):
        source = self.base / ('source-' + str(len(list(self.base.iterdir())))); source.mkdir()
        image = REPO / 'agentsLog/Bukareszt/submission/fixtures/tiny-package/images/fixture-red.png'
        (source / 'images').mkdir(); (source / 'images/red.png').write_bytes(image.read_bytes())
        items = []
        for i in range(count):
            id = 'essay-custom' if i == 1 else 'id/' + str(i)
            items.append({'id': id, 'max_points': 1, 'question': 'Invented task ' + str(i),
                          'source_text': 'Original source\nzażółć\u2028kept', 'answer_format': 'Original format',
                          'unknown_source': {'note': 'Preserve extra fields'},
                          'images': [{'path': 'images/red.png', 'sha256': r.sha(image)}] if i == 0 else []})
        exam = {'exam_id': 'synthetic-only', 'instructions': 'Original instructions', 'items': items}
        template = {'exam_id': exam['exam_id'], 'answers': [{'id': x['id'], 'answer': ''} for x in reversed(items)]}
        r.write(source / 'exam.json', exam); r.write(source / 'answers-template.json', template)
        (source / 'unrelated-private-key.txt').write_text('must not copy')
        dest = source.with_name(source.name + '-package')
        m = prep.prepare(source, dest, essay_ids=list(essays), no_essay=not essays,
                         cache='/owned/stage/models', binary='/owned/runtime/bin/ollama', lock='/owned/offline.lock',
                         max_seconds=5400, request_timeout=600)
        packed = r.load('packed_test_runner', dest / 'run_native_package.py')
        m, package, cases, routes = packed.preflight(dest)
        return dest, packed, m, package, cases, routes

    def response(self, content=' Native final. \n', **updates):
        value = {'model': r.MODEL, 'done': True, 'done_reason': 'stop', 'prompt_eval_count': 100,
                 'eval_count': 50, 'message': {'content': content, 'thinking': 'Synthetic private thinking.'}}
        value.update(updates)
        return value

    def test_adapter_routes_images_template_and_unchanged_strings(self):
        dest, packed, m, package, cases, routes = self.package()
        self.assertEqual(m['max_calls'], 3); self.assertEqual(m['max_requested_tokens'], 40960)
        self.assertEqual([x['cap'] for x in routes], [10240, 20480, 10240])
        self.assertFalse((dest / 'exam/unrelated-private-key.txt').exists())
        original = r.rows(dest / 'input.original.jsonl'); routed = r.rows(dest / 'input.jsonl')
        self.assertEqual(original[0], routed[0]); self.assertEqual(original[2], routed[2])
        self.assertEqual(routed[1]['prompt'], original[1]['prompt'] + '\n\n' + r.ESSAY_POLICY)
        self.assertIn('Original source\nzażółć\u2028kept', routed[0]['prompt'])
        helper, _, _, adapter, _ = packed.modules(dest)
        body = packed.payload(cases[0], 10240, helper)
        self.assertEqual(r.base64.b64decode(body['messages'][0]['images'][0]), (dest / 'exam/images/red.png').read_bytes())
        self.assertEqual(body['options'], {'num_ctx': 32768, 'num_predict': 10240})
        self.assertTrue(body['think']); self.assertFalse(body['truncate']); self.assertFalse(body['shift'])
        out = dest / 'results'; out.mkdir(); sent = []
        def send(body):
            ledger = r.rows(out / 'reservations.jsonl')
            self.assertEqual(len(ledger), len(sent) + 1)
            self.assertEqual(ledger[-1]['cap'], body['options']['num_predict'])
            self.assertLessEqual(sum(x['cap'] for x in ledger), m['max_requested_tokens'])
            sent.append(body)
            return self.response(content=' Native final ' + str(len(sent)) + '. \n')
        with patch.object(packed, 'remaining', return_value=5000):
            result = packed.dispatch(cases, routes, m, out, helper, adapter, send, lambda loaded: None, lambda: None)
        report = packed.finalize(dest, adapter, package)
        answers = r.read(out / 'answers.json')
        self.assertEqual([x['id'] for x in answers['answers']], [x['id'] for x in package['template']['answers']])
        self.assertEqual(answers['answers'][0]['answer'], ' Native final 3. \n')
        self.assertEqual(result['requested_tokens'], 40960); self.assertFalse(report['failures'])
        self.assertFalse(adapter.validate_submission_bytes((out / 'answers.json').read_bytes(), package['template']))

    def test_any_count_and_explicit_no_essay(self):
        _, _, m, _, cases, routes = self.package(count=101, essays=())
        self.assertEqual(len(cases), 101); self.assertEqual(m['max_calls'], 101)
        self.assertEqual(m['max_requested_tokens'], 101 * 10240)
        self.assertTrue(all(x['route'] == 'ordinary' for x in routes))

    def test_route_mapping_required_unique_and_received(self):
        original = [{'id': 'any', 'prompt': 'original', 'images': []}]
        for ids, none in (([], False), (['any'], True), (['wrong'], False), (['any', 'any'], False)):
            with self.subTest(ids=ids, none=none), self.assertRaises(r.GlobalStop):
                r.build_routes(original, ids, none)

    def test_route_tamper_cannot_hide_behind_rehashed_file(self):
        dest, packed, m, *_ = self.package()
        route = r.read(dest / 'routes.json'); route[0]['cap'] = 20480
        (dest / 'routes.json').write_text(r.line(route))
        m['files']['routes.json'] = r.sha(dest / 'routes.json'); m['routes_sha256'] = m['files']['routes.json']
        (dest / 'launch.json').write_text(r.line(m))
        with self.assertRaises(packed.GlobalStop):
            packed.preflight(dest)

    def test_source_or_helper_mutation_stops_preflight(self):
        dest, packed, m, *_ = self.package()
        (dest / 'exam/images/red.png').write_bytes(b'changed')
        with self.assertRaises(packed.GlobalStop):
            packed.preflight(dest)

    def dispatch_case(self, responses, check=lambda loaded: None, left=5000):
        dest, packed, m, package, cases, routes = self.package()
        helper, _, _, adapter, _ = packed.modules(dest)
        out = dest / 'results'; out.mkdir(); sent = []
        def send(body):
            sent.append(body)
            answer = responses[len(sent) - 1]
            if isinstance(answer, Exception):
                raise answer
            return answer
        with patch.object(packed, 'remaining', return_value=left):
            result = packed.dispatch(cases, routes, m, out, helper, adapter, send, check, lambda: None)
        packed.finalize(dest, adapter, package)
        return result, sent, {x['id']: x['answer'] for x in r.read(out / 'answers.json')['answers']}

    def test_local_length_empty_and_embedded_reasoning_continue_without_retry(self):
        result, sent, answers = self.dispatch_case([self.response(done_reason='length'), self.response(content=''), self.response()])
        self.assertEqual(len(sent), 3); self.assertIsNone(result['stop'])
        self.assertEqual(answers['id/0'], ''); self.assertEqual(answers['essay-custom'], '')
        self.assertEqual(answers['id/2'], ' Native final. \n')
        self.assertEqual(result['item_error_ids'], ['id/0', 'essay-custom'])
        result, sent, answers = self.dispatch_case([self.response(content='<think>hidden</think>answer'), self.response(), self.response()])
        self.assertEqual(answers['id/0'], ''); self.assertEqual(len(sent), 3)

    def test_global_truncation_usage_identity_and_uncertain_transport_stop(self):
        failures = [self.response(**{flag: True}) for flag in ('truncated', 'context_truncated')]
        failures += [self.response(eval_count=10241), self.response(prompt_eval_count=30000),
                     self.response(model='wrong'), TimeoutError('uncertain server state')]
        for failure in failures:
            with self.subTest(failure=str(failure)[:40]):
                result, sent, answers = self.dispatch_case([failure])
                self.assertEqual(len(sent), 1); self.assertIsNotNone(result['stop'])
                self.assertEqual(result['unsent_ids'], ['essay-custom', 'id/2'])
                self.assertTrue(all(value == '' for value in answers.values()))

    def test_budget_and_ownership_before_send(self):
        result, sent, answers = self.dispatch_case([], left=610)
        self.assertEqual(sent, []); self.assertEqual(result['requested_tokens'], 0)
        def bad(_):
            raise r.GlobalStop('Foreign worker')
        result, sent, answers = self.dispatch_case([], check=bad)
        self.assertEqual(sent, []); self.assertTrue(all(x == '' for x in answers.values()))

    def test_absolute_declaration_and_above_240k_authority(self):
        _, _, m, *_ = self.package(count=24, essays=())
        m.update(status='DECLARED', declared_utc='2026-09-26T18:00:00+00:00', deadline_utc='2026-09-26T19:00:00+00:00')
        now = dt.datetime.fromisoformat('2026-09-26T18:01:00+00:00').timestamp()
        m['authorization'] = {'owner': 'root', 'reference': 'synthetic-test-only', 'max_calls': m['max_calls'],
                              'max_requested_tokens': m['max_requested_tokens'], 'max_seconds': m['max_seconds']}
        with self.assertRaises(r.GlobalStop): r.declared(m, now)
        m['authorization']['above_240k_explicit'] = True
        self.assertEqual(r.declared(m, now), 3540)
        for change in ({'deadline_utc': '2026-09-26T19:00:00'}, {'deadline_utc': '2026-09-26T18:00:01+00:00'},
                       {'deadline_utc': '2026-09-26T21:00:00+00:00'}):
            bad = dict(m, **change)
            with self.subTest(change=change), self.assertRaises(r.GlobalStop): r.declared(bad, now)

    def test_policy_preserves_prior_contract_and_required_topic_number(self):
        old = r.load('policy_only_no_execution', REPO / 'agentsLog/kwiscion/full-thinking-prep/prepare.py')
        self.assertTrue(r.ESSAY_POLICY.startswith(old.ESSAY_POLICY));self.assertIn('numeru wybranego tematu',r.ESSAY_POLICY)

    def test_cleanup_receipt_integration_and_fallback_error_visibility(self):
        helper = r.load('cleanup_integration_helper', HERE / 'run_gemma_offline.py')
        out = self.base / 'results'; out.mkdir()
        identity = {'pid': 123, 'ticks': '456', 'namespace': 'net:isolated-test'}
        r.write(out / 'network-proof.json', {'isolated_namespace': identity['namespace']})
        r.write(out / 'server-identity.json', identity)
        r.write(out / 'cleanup.json', {'owned': identity, 'returncode': -9, 'matched_pids': [123, 124]})
        with patch.object(helper, 'process_absent', return_value=True), patch.object(helper, 'namespace_cleanup', side_effect=PermissionError('unrelated process')) as fallback:
            result = r.cleanup_root(self.base, {'binary': '/owned/runtime/bin/ollama'}, helper)
            self.assertEqual(result['mode'], 'verified_completed_receipt'); fallback.assert_not_called()
            (out / 'cleanup.json').unlink()
            with self.assertRaises(PermissionError):
                r.cleanup_root(self.base, {'binary': '/owned/runtime/bin/ollama'}, helper)

    def test_guardian_absolute_budget_and_no_redirect(self):
        shell = prep.guardian(5400)
        self.assertIn('end.timestamp()-time.time()', shell)
        self.assertIn('--kill-after=5s "${budget}s"', shell)
        if sys.platform == 'linux':
            subprocess.run(['bash', '-n'], input=shell, text=True, check=True)
        with self.assertRaises(r.GlobalStop):
            r.NoRedirect().redirect_request(None, None, 302, None, None, 'http://localhost/other')

    def test_direct_inside_refused_before_server_or_transport(self):
        with patch.object(r, 'modules', return_value=(SimpleNamespace(), None, None, None, None)), \
             patch.object(r.subprocess, 'Popen') as process, self.assertRaises(r.GlobalStop):
            r.inside(self.base, {}, {}, [], [], 'net:host', os.getppid(), None)
        process.assert_not_called()

    def test_genuine_supervisor_binding_and_inherited_challenge(self):
        out = self.base / 'results'; out.mkdir()
        r.write(out / 'launch.json', {'synthetic': True}); r.write(out / 'weights.json', {'synthetic': True})
        identity = {'pid': 123, 'ticks': '111', 'executable': str(Path(sys.executable).resolve()),
                    'argv': ['python3', '-B', str(self.base / 'run_native_package.py'), str(self.base), '--execute', '--guarded'],
                    'namespace': 'net:host'}
        guardian = {'pid': 55, 'ticks': '100', 'executable': '/usr/bin/timeout',
                    'argv': ['timeout', '--signal=TERM', '--kill-after=5s', '5390s'], 'namespace': 'net:host'}
        token = b'1' * 32
        r.write(out / 'supervisor.json', {'identity': identity, 'guardian': guardian,
                'launch_sha256': r.sha(out / 'launch.json'), 'weights_sha256': r.sha(out / 'weights.json'),
                'challenge_sha256': r.hashlib.sha256(token).hexdigest()})
        actual_read = Path.read_text
        def proc_read(path, *args, **kwargs):
            return '123 (python3) S 55 0' if str(path).replace('\\', '/') == '/proc/123/stat' else actual_read(path, *args, **kwargs)
        for bad in (False, True):
            receiver, sender = os.pipe(); os.write(sender, b'2' * 32 if bad else token); os.close(sender)
            with patch.object(r.os, 'getppid', return_value=123), \
                 patch.object(r, 'inherited_parent_identity', side_effect=lambda pid, _: identity if pid == 123 else guardian), \
                 patch.object(r.Path, 'read_text', proc_read), patch.object(r.os, 'set_blocking'):
                if bad:
                    with self.assertRaises(r.GlobalStop): r.check_supervisor(self.base, {}, 123, receiver, 'net:host', None)
                else:
                    r.check_supervisor(self.base, {}, 123, receiver, 'net:host', None)


if __name__ == '__main__':
    unittest.main()
