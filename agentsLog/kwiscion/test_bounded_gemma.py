import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bounded', Path(__file__).with_name('run_bounded_gemma.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=b.ROOT / 'agentsLog/kwiscion/private', prefix='dispatcher-synthetic-')
        self.addCleanup(self.temp.cleanup)
        p = Path(self.temp.name)
        image = p / 'invented.png'
        image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        inp = p / 'input.jsonl'
        ids = [f'invented-{i}' for i in range(40)]
        inp.write_text(''.join(json.dumps({'id': i, 'prompt': 'Invented neutral fixture', 'images': ['invented.png']})+'\n' for i in ids), encoding='utf-8')
        self.m = {'input': str(inp), 'input_sha256': b.limits.sha(inp), 'config': 'outputs/local-smoke/gemma4-12b-val40-1024.config.json',
            'config_sha256': b.limits.CONFIG_HASH, 'output': str(p/'raw.jsonl'), 'expected_ids': ids,
            'images': {'invented.png': b.limits.sha(image)}, 'model_digest': b.limits.DIGEST,
            'deadline': '2026-09-26T17:20:00+02:00', 'max_elapsed_seconds': 3600,
            'max_calls': 40, 'max_requested_output_tokens': 40960, 'max_output_tokens': 1024,
            'timeout_seconds': 420, 'context_tokens': 4096, 'paid_api_budget_usd': 0}

    def test_preflight_no_status_or_model_calls(self):
        with patch.object(b.limits, 'local_status', side_effect=AssertionError('status forbidden')):
            result = b.preflight(self.m)
        self.assertEqual(len(result[4]), 40)
        self.assertFalse(Path(self.m['output']).exists())

    def test_pins_ids_images_and_freshness(self):
        for key in ('input_sha256', 'config_sha256', 'model_digest'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.preflight(dict(self.m, **{key: 'wrong'}))
        m = copy.deepcopy(self.m); m['expected_ids'].reverse()
        with self.assertRaisesRegex(ValueError, 'order/IDs'): b.preflight(m)
        with self.assertRaisesRegex(ValueError, 'exactly all'): b.preflight(dict(self.m, images={}))
        with self.assertRaisesRegex(ValueError, 'Image pin'): b.preflight(dict(self.m, images={'invented.png': 'wrong'}))
        out = Path(self.m['output']); out.write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'Fresh'): b.preflight(self.m)
        self.assertEqual(out.read_text(), 'preserve')

    def test_budget_expansion_and_public_paths_refused(self):
        for key, value in [('max_calls',41),('max_requested_output_tokens',40961),('max_output_tokens',2048),
                           ('timeout_seconds',421),('context_tokens',8192),('paid_api_budget_usd',1),('max_elapsed_seconds',3601)]:
            with self.subTest(key=key), self.assertRaises(ValueError): b.preflight(dict(self.m, **{key:value}))
        with self.assertRaises(ValueError): b.preflight(dict(self.m, output='outputs/not-private.jsonl'))
        with self.assertRaises(ValueError): b.preflight(dict(self.m, deadline='2026-09-26T17:20:00'))

    def test_declared_stops_reuse_reviewed_logic(self):
        deadline=b.dt.datetime.fromisoformat(self.m['deadline']).timestamp()
        good={'error':None,'usage':{'prompt_tokens':100}}
        self.assertIsNone(b.stop([good]*4, 500, deadline-1000, self.m))
        self.assertIn('projected',b.stop([good]*5,500,deadline-1000,self.m))
        self.assertIn('declared deadline',b.stop([],0,deadline,self.m))
        self.assertIn('elapsed',b.stop([],3600,deadline-1000,self.m))
        self.assertIn('competing',b.stop([],0,deadline-1000,self.m,[2]))
        self.assertIn('token count',b.stop([{'error':None,'usage':{'prompt_tokens':2817}}],1,deadline-1000,self.m))


if __name__ == '__main__': unittest.main()
