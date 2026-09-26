"""#83 runtime-profile checks. Mocked only: no server, namespace, GPU, network or model call."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import run_gemma_package as f

REAL_LOOP = f.request_loop

r = f.r
PROFILES = r.ROOT/'scripts/Bukareszt/runtime_profiles'
TEMPLATE = PROFILES/'h100-native-linux-ollama-0.34.4.template.json'
# Literal values from the qualified pre-#83 launcher (commit 2bec025), not derived from the profile code.
LEGACY_PATH = '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/usr/lib/wsl/lib'
LEGACY_SMI = ['/usr/lib/wsl/lib/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']


def filled_h100(root, **changes):
    profile = json.loads(TEMPLATE.read_text())
    binary = root/'opt/ollama/bin/ollama'
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b'invented binary bytes')
    profile.update({'ollama_binary':str(binary), 'ollama_binary_sha256':r.sha(binary),
                    'server_path_env':'/remote/ollama/bin:/usr/bin:/bin', 'nvidia_smi':'/remote/bin/nvidia-smi',
                    'model_cache':'/remote/models'}, **changes)
    path = root/('h100-%d.json' % len(list(root.glob('h100-*.json'))))
    path.write_text(json.dumps(profile, indent=2))
    return path, profile


class Server:
    pid = 424242
    returncode = 0
    def poll(self): return None
    def wait(self, timeout=None): return 0


class RuntimeProfile(unittest.TestCase):
    def setUp(self):
        (r.OWN/'private').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=r.OWN/'private', prefix='profile-test-')
        self.root = Path(self.tmp.name)
        self.pkg = self.root/'package'
        shutil.copytree(r.ROOT/'agentsLog/Bukareszt/submission/fixtures/tiny-package', self.pkg)
        self.config = self.root/'config.json'
        tracked = (r.OWN/'gemma4-12b-val40-1024.config.json').read_bytes().replace(b'\r\n', b'\n')
        self.config.write_bytes(tracked.replace(b'\n', b'\r\n'))

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, name, profile=None):
        return argparse.Namespace(output=self.root/name, exam_dir=self.pkg, config=self.config, max_calls=4,
                                  max_output_tokens_total=4096, wall_seconds=1800, runtime_profile=profile)

    # --- laptop default is unchanged -------------------------------------------------------------
    def test_laptop_default_matches_legacy_constants_and_committed_json(self):
        p, digest, file_digest = r.load_profile(None)
        self.assertEqual((p['ollama_binary'], p['ollama_version'], p['context_length']), ('/usr/local/bin/ollama','0.30.7',4096))
        self.assertEqual((p['nvidia_smi'], p['server_path_env'], p['model_cache']),
                         (LEGACY_SMI[0], LEGACY_PATH, '/usr/share/ollama/.ollama/models'))
        self.assertEqual(p['host_endpoint_check'], {'port':11434,'require_reachable':True})
        self.assertFalse(p['block_foreign_ollama'] or p['verify_all_manifest_blobs'])
        self.assertIsNone(file_digest)
        committed, committed_digest, _ = r.load_profile(PROFILES/'laptop-wsl2-ollama-0.30.7.json')
        self.assertEqual((committed, committed_digest), (p, digest))

    def launch(self, name, profile_path=None, version='0.30.7', context=4096, loop=None):
        """Run inside() with every OS/server/model touchpoint mocked; returns captured commands."""
        out, package, _, record = f.preflight(self.args(name, profile_path))
        out.mkdir()
        _, adapter = r.modules()
        adapter.prepare(package, out/'input.jsonl')
        cfg = json.loads(self.config.read_bytes()); cfg['base_url'] = r.ENDPOINT+'/v1'
        r.write(out/'config.json', cfg)
        record.update(frozen_files={}, parent_pid=777, git_revision='test')
        r.write(out/'launch.json', record)
        seen = {'popen':[], 'run':[], 'killpg':[]}
        def popen(cmd, env=None, **kw):
            seen['popen'].append((cmd, env)); return Server()
        def run(cmd, **kw):
            seen['run'].append(cmd); return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')
        def api(path, port=r.PORT):
            if path == 'version': return {'version':version}
            return {'models':[{'digest':r.DIGEST,'context_length':context}]}
        proc = self.root/('proc-'+name); proc.mkdir()
        def checked_loop(cases, config, out, n, deadline, guard, verify, inf, *, context_length):
            self.assertEqual(context_length, record['runtime_profile']['context_length'])
            return (guard(), verify(), {'stop_reason':'complete','completed_records':0})[2]
        loop = loop or checked_loop
        with patch.object(f.os,'getppid',return_value=777), \
             patch.object(r,'network_proof',return_value={'isolated_namespace':'net:[iso]'}), \
             patch.object(f.os,'readlink',return_value='net:[iso]'), \
             patch.object(f.subprocess,'Popen',side_effect=popen), patch.object(f.subprocess,'run',side_effect=run), \
             patch.object(f,'Path',side_effect=lambda x: proc if x=='/proc' else Path(x)), \
             patch.object(r,'api',side_effect=api), patch.object(r,'verify_model'), \
             patch.object(f.os,'getpgid',return_value=1,create=True), \
             patch.object(f.os,'killpg',side_effect=lambda g,s: seen['killpg'].append(g),create=True), \
             patch.object(f.signal,'SIGTERM',15,create=True), patch.object(f.signal,'SIGKILL',9,create=True), \
             patch.object(f,'request_loop',side_effect=loop):
            status = f.inside(argparse.Namespace(output=out, host_net='net:[host]'))
        return status, out, seen

    def test_laptop_inside_issues_exact_legacy_commands(self):
        status, out, seen = self.launch('laptop')
        self.assertEqual(status, 0)
        [(cmd, env)] = seen['popen']
        self.assertEqual(cmd, ['/usr/local/bin/ollama','serve'])
        self.assertEqual(env, {'PATH':LEGACY_PATH,'HOME':str(out/'server-home'),'OLLAMA_HOST':'127.0.0.1:11435',
            'OLLAMA_MODELS':'/usr/share/ollama/.ollama/models','OLLAMA_CONTEXT_LENGTH':'4096','OLLAMA_NUM_PARALLEL':'1',
            'OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_NO_CLOUD':'1','OLLAMA_KEEP_ALIVE':'5m'})
        self.assertTrue(seen['run'] and all(c == LEGACY_SMI for c in seen['run']))
        readiness = json.loads((out/'readiness.json').read_text())
        self.assertEqual((readiness['context_expected'], readiness['version']['version']), (4096, '0.30.7'))
        self.assertEqual(seen['killpg'][0], Server.pid)  # owned group only
        self.assertEqual(json.loads((out/'cleanup.json').read_text())['owned_process_group'], Server.pid)

    # --- native profile ----------------------------------------------------------------------------
    def test_native_profile_selects_profile_paths_context_and_records_hash(self):
        path, profile = filled_h100(self.root)
        status, out, seen = self.launch('native', path, version='0.34.4', context=32768)
        self.assertEqual(status, 0)
        [(cmd, env)] = seen['popen']
        self.assertEqual(cmd, [profile['ollama_binary'],'serve'])
        self.assertEqual((env['PATH'], env['OLLAMA_MODELS'], env['OLLAMA_CONTEXT_LENGTH']),
                         ('/remote/ollama/bin:/usr/bin:/bin','/remote/models','32768'))
        self.assertTrue(all(c[0] == '/remote/bin/nvidia-smi' for c in seen['run']))
        launch = json.loads((out/'launch.json').read_text())
        self.assertEqual(launch['runtime_profile'], profile)
        self.assertEqual(launch['runtime_profile_sha256'], r.profile_sha(profile))
        self.assertEqual(launch['runtime_profile_file_sha256'], r.sha(path))
        self.assertEqual(json.loads((out/'readiness.json').read_text())['runtime_profile_sha256'], r.profile_sha(profile))

    def test_version_and_context_mismatch_stop_without_relaxing(self):
        path, _ = filled_h100(self.root)
        with self.assertRaisesRegex(RuntimeError, 'Runtime version changed'):
            self.launch('old-version', path, version='0.30.7', context=32768)
        with self.assertRaisesRegex(RuntimeError, 'context mismatch'):
            self.launch('laptop-ctx', None, version='0.30.7', context=32768)
        with self.assertRaisesRegex(RuntimeError, 'context mismatch'):
            self.launch('h100-ctx', path, version='0.34.4', context=4096)
        with self.assertRaisesRegex(RuntimeError, 'Runtime version changed'):
            self.launch('laptop-on-h100-runtime', None, version='0.34.4', context=4096)

    def test_real_request_loop_stops_on_context_mismatch_and_sends_nothing_else(self):
        path, _ = filled_h100(self.root)
        inf, _ = r.modules()
        row = {'id':'x','error':None,'usage':{'prompt_tokens':10,'completion_tokens':2},
               'raw_response':{'choices':[{'finish_reason':'stop','message':{'content':'ok'}}]}}
        calls = []
        def loop(cases, config, out, n, deadline, guard, verify, _inf, *, context_length):
            with patch.object(_inf,'run_case',side_effect=lambda *a: (calls.append(1), dict(row, id=a[0]['id']))[1]):
                return REAL_LOOP(cases, config, out, n, deadline, guard, verify, _inf, context_length=context_length)
        status, out, _ = self.launch('ctx', path, version='0.34.4', context=4096, loop=loop)
        self.assertEqual((status, len(calls)), (1, 1))
        result = json.loads((out/'execution.json').read_text())
        self.assertEqual(len(result['unsent_ids']), 3)

    def test_profile_pin_and_binary_hash_mismatch_rejected(self):
        for change, message in [({'manifest_digest':'0'*64}, 'pins differ'),
                                ({'assets':{'0'*64:1}}, 'pins differ'),
                                ({'context_length':'32768'}, 'context_length'),
                                ({'ollama_version':'0.34'}, 'exact x.y.z'),
                                ({'ollama_binary_sha256':None}, 'must pin ollama_binary_sha256'),
                                ({'model_cache':'relative/models'}, 'absolute path'),
                                ({'namespace_method':'none'}, 'unshare-rn'),
                                ({'block_foreign_ollama':False}, 'every manifest blob'),
                                ({'verify_all_manifest_blobs':False}, 'every manifest blob'),
                                ({'platform':'darwin'}, 'wsl2 or native-linux'),
                                ({'host_endpoint_check':{'port':11435,'require_reachable':False}}, 'isolated port')]:
            with self.subTest(change=change):
                path, _ = filled_h100(self.root, **change)
                with self.assertRaisesRegex(RuntimeError, message):
                    f.preflight(self.args('bad', path))
        path, profile = filled_h100(self.root, extra=1)
        with self.assertRaisesRegex(RuntimeError, 'unknown'):
            r.load_profile(path)
        path, profile = filled_h100(self.root, ollama_binary_sha256='f'*64)
        with self.assertRaisesRegex(RuntimeError, 'binary hash mismatch'):
            r.verify_binary(profile)

    def test_launch_record_profile_tamper_rejected(self):
        path, _ = filled_h100(self.root)
        out, package, _, record = f.preflight(self.args('tamper', path))
        out.mkdir()
        record.update(frozen_files={}, parent_pid=777)
        record['runtime_profile']['context_length'] = 4096
        r.write(out/'launch.json', record)
        with patch.object(f.os,'getppid',return_value=777):
            with self.assertRaisesRegex(RuntimeError, 'profile changed'):
                f.inside(argparse.Namespace(output=out, host_net='net:[host]'))

    def test_template_placeholders_refused_even_for_dry_preflight(self):
        with self.assertRaisesRegex(RuntimeError, 'PLACEHOLDER.*ollama_binary'):
            r.load_profile(TEMPLATE)
        a = self.args('dry', TEMPLATE)
        with self.assertRaisesRegex(RuntimeError, 'PLACEHOLDER'):
            f.preflight(a)
        self.assertFalse(a.output.exists())
        with patch.object(f.subprocess,'Popen',side_effect=AssertionError('no process')):
            with self.assertRaisesRegex(RuntimeError, 'PLACEHOLDER'):
                f.main(['--output',str(a.output),'--exam-dir',str(self.pkg),'--config',str(self.config),'--max-calls','4',
                        '--max-output-tokens-total','4096','--wall-seconds','1800','--runtime-profile',str(TEMPLATE)])
        self.assertFalse(a.output.exists())

    def test_dry_preflight_records_default_profile(self):
        _, _, _, record = f.preflight(self.args('dry-default'))
        self.assertEqual(record['runtime_profile'], r.LAPTOP_PROFILE)
        self.assertEqual(record['runtime_profile_sha256'], r.profile_sha(r.LAPTOP_PROFILE))
        self.assertIsNone(record['runtime_profile_file'])

    def test_native_profile_verifies_every_manifest_blob(self):
        cache = self.root/'store'; (cache/'blobs').mkdir(parents=True)
        def blob(data):
            p = cache/'blobs'/'tmp'; p.write_bytes(data); d = r.sha(p)
            p.rename(cache/'blobs'/('sha256-'+d)); return {'digest':'sha256:'+d,'size':len(data)}
        model, proj, cfg, lic = blob(b'model'), blob(b'projector'), blob(b'{}'), blob(b'license')
        manifest = cache/'manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'config':cfg,'layers':[model,proj,lic]}))
        assets = {x['digest'][7:]:x['size'] for x in (model, proj)}
        _, native = filled_h100(self.root, model_cache=str(cache))
        laptop = dict(r.LAPTOP_PROFILE, model_cache=str(cache))
        with patch.object(r,'DIGEST',r.sha(manifest)), patch.object(r,'ASSETS',assets):
            r.verify_assets(native); r.verify_assets(laptop)
            (cache/'blobs'/('sha256-'+lic['digest'][7:])).write_bytes(b'LICENSE')
            with self.assertRaisesRegex(RuntimeError, 'blob missing or mismatched'):
                r.verify_assets(native)
            r.verify_assets(laptop)  # legacy laptop scope unchanged: manifest + model/projector only
            (cache/'blobs'/('sha256-'+model['digest'][7:])).write_bytes(b'MODEL')
            with self.assertRaisesRegex(RuntimeError, 'mismatch'):
                r.verify_assets(laptop)

    # --- isolation / platform / host / guard ------------------------------------------------------
    def test_isolation_denied_is_concrete(self):
        with patch.object(r.shutil,'which',side_effect=lambda t: None if t=='unshare' else '/usr/bin/'+t):
            with self.assertRaisesRegex(RuntimeError, '`unshare` not found'):
                r.isolation_probe()
        with patch.object(r.shutil,'which',return_value='/usr/bin/x'), patch.object(r.os,'readlink',return_value='net:[host]'):
            denied = subprocess.CompletedProcess([], 1, stdout='', stderr='unshare: write failed /proc/self/uid_map: Operation not permitted')
            with patch.object(r.subprocess,'run',return_value=denied):
                with self.assertRaisesRegex(RuntimeError, 'isolation denied.*uid_map'):
                    r.isolation_probe()
            same = subprocess.CompletedProcess([], 0, stdout='net:[host]\n', stderr='')
            with patch.object(r.subprocess,'run',return_value=same):
                with self.assertRaisesRegex(RuntimeError, 'stayed in host namespace'):
                    r.isolation_probe()
            ok = subprocess.CompletedProcess([], 0, stdout='net:[iso]\n', stderr='')
            with patch.object(r.subprocess,'run',return_value=ok):
                self.assertEqual(r.isolation_probe()['probe_namespace'], 'net:[iso]')

    def test_execute_stops_before_output_or_child_when_isolation_denied(self):
        path, _ = filled_h100(self.root)
        a = self.args('exec-denied', path)
        with patch.object(f.sys,'platform','linux'), patch.object(r,'check_platform'), patch.object(r,'host_idle'), \
             patch.object(f,'worker_guard'), patch.object(r,'verify_binary'), patch.object(r,'verify_assets'), \
             patch.object(r,'isolation_probe',side_effect=RuntimeError('Network isolation denied: test')), \
             patch.object(f.subprocess,'Popen',side_effect=AssertionError('no child')):
            with self.assertRaisesRegex(RuntimeError, 'isolation denied'):
                f.execute(a)
        self.assertFalse(a.output.exists())

    def test_native_profile_refuses_wsl_kernel(self):
        _, profile = filled_h100(self.root)
        version = self.root/'version'; version.write_text('Linux version 6.6.87.2-microsoft-standard-WSL2')
        with patch.object(r.sys,'platform','linux'), \
             patch.object(r,'Path',side_effect=lambda x: version if x=='/proc/version' else Path(self.root/'absent')):
            with self.assertRaisesRegex(RuntimeError, 'kernel is WSL'):
                r.check_platform(profile)
            r.check_platform(r.LAPTOP_PROFILE)  # laptop keeps its historical linux-only check
            version.write_text('Linux version 6.8.0-generic')
            r.check_platform(profile)

    def test_host_endpoint_check(self):
        _, profile = filled_h100(self.root)
        with patch.object(r,'api',side_effect=ConnectionRefusedError()):
            r.host_idle(profile)  # declared optional host endpoint may be absent
            with self.assertRaises(ConnectionRefusedError):
                r.host_idle(r.LAPTOP_PROFILE)  # laptop still requires reachable 11434
        with patch.object(r,'api',return_value={'models':[{'name':'resident'}]}) as api:
            with self.assertRaisesRegex(RuntimeError, 'unload'):
                r.host_idle(profile)
            api.assert_called_with('ps', 11436)

    def test_foreign_ollama_blocked_only_by_native_profile(self):
        _, profile = filled_h100(self.root)
        proc = self.root/'proc'; (proc/'999993').mkdir(parents=True)
        (proc/'999993/cmdline').write_bytes(b'/home/x/ollama\0serve\0')
        run = subprocess.CompletedProcess([], 0, stdout='', stderr='')
        with patch.object(f,'Path',side_effect=lambda x: proc if x=='/proc' else Path(x)), \
             patch.object(f.subprocess,'run',return_value=run), patch.object(f.os,'getpgid',return_value=5,create=True):
            f.worker_guard(parent_pid=1)
            with self.assertRaisesRegex(RuntimeError, 'Competing inference'):
                f.worker_guard(parent_pid=1, profile=profile)
            f.worker_guard(server_group=5, parent_pid=1, profile=profile)  # own server group allowed


if __name__ == '__main__':
    unittest.main()
