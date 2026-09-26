"""Bare organizer-package launcher. Default is CPU preflight; --execute needs exclusive GPU ownership.

Runtime paths/version/context come from a frozen runtime profile (#83); omitted means the qualified laptop default.

No downloads, retries, warmup, policy or RAG. Server and requests share an isolated network namespace.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

import offline_rehearsal as r

SELF = Path(__file__).resolve()
CONFIG_SHA = '3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa'


def worker_guard(server_group=None, parent_pid=None, profile=r.LAPTOP_PROFILE):
    """Exclude only this process, its exact supervisor and its owned server group."""
    names = {'infer.py','run_question_policy.py','run_bounded_gemma.py','run_visual_crops.py',
             'run_crop_diagnostic.py','run_source_correction.py','run_local_smoke.py','run_smoke.py'}
    def allowed(pid):
        return pid in (os.getpid(),parent_pid) or (server_group is not None and os.getpgid(pid) == server_group)
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            pid = int(proc.name)
            args = (proc/'cmdline').read_bytes().decode(errors='replace').split('\0')
            exe = Path(args[0]).name
            runner = exe.startswith('python') and any(Path(x).name in names or
                Path(x).name.startswith(('run_gemma','run_qwen','run_rag')) for x in args[1:])
            backend = exe in ('llama-server','ollama_llama_server') or 'vllm' in exe or \
                (profile['block_foreign_ollama'] and r.foreign_ollama(args))
            r.require(not (runner or backend) or allowed(pid), 'Competing inference worker')
        except (FileNotFoundError,ProcessLookupError): pass
    gpu = subprocess.run([profile['nvidia_smi'],'--query-compute-apps=pid','--format=csv,noheader,nounits'],
                         capture_output=True,text=True,check=True)
    for line in gpu.stdout.splitlines():
        r.require(line.strip().isdigit(), 'Unrecognized GPU process listing')
        try: r.require(allowed(int(line)), 'Competing GPU process')
        except ProcessLookupError: pass


def preflight(a):
    out = r.output_path(a.output)
    profile, profile_digest, profile_file_digest = r.load_profile(getattr(a, 'runtime_profile', None))
    inf, adapter = r.modules()
    r.require(1 <= a.max_calls <= inf.MAX_CALLS, 'Declare 1..100 maximum calls')
    r.require(a.max_output_tokens_total == a.max_calls * 1024, 'Total requested token budget must equal max-calls * 1024')
    r.require(480 <= a.wall_seconds <= 86400, 'Declare wall bound in 480..86400 seconds')
    cfg = Path(a.config).resolve()
    r.require(r.sha(cfg) == CONFIG_SHA, 'Original bare Gemma config hash mismatch')
    config = inf.load_config(cfg, False)
    r.require(config['model'] == r.MODEL and config['max_output_tokens'] == 1024 and
              config['timeout_seconds'] == 420 and config['reasoning_effort'] == 'none', 'Config settings changed')
    package = adapter.load_package(Path(a.exam_dir).resolve())
    r.require(len(package['exam']['items']) <= a.max_calls, 'Package exceeds declared call budget')
    # Validate every encoded image before execution without touching the future run directory.
    with tempfile.TemporaryDirectory(prefix='final-preflight-') as tmp:
        prepared = Path(tmp) / 'input.jsonl'
        adapter.prepare(package, prepared)
        cases = inf.load_cases(prepared, a.max_calls)
    pins = {str(p.resolve()): r.sha(p) for p in adapter.package_inputs(package)}
    return out, package, config, {'package_files': pins, 'ids': [c['id'] for c in cases],
        'config_sha256': CONFIG_SHA, 'model_digest': r.DIGEST, 'weight_bytes': sum(r.ASSETS.values()),
        'max_calls': a.max_calls, 'max_output_tokens_total': a.max_output_tokens_total,
        'wall_seconds': a.wall_seconds, 'runtime_profile': profile, 'runtime_profile_sha256': profile_digest,
        'runtime_profile_file': None if getattr(a, 'runtime_profile', None) is None else str(Path(a.runtime_profile).resolve()),
        'runtime_profile_file_sha256': profile_file_digest, 'cost_usd': 0, 'retries': 0, 'context_fit': 'UNPROVEN',
        'script_sha256': r.sha(SELF), 'helper_sha256': r.sha(Path(r.__file__)),
        'infer_sha256': r.sha(r.ROOT/'infer.py'), 'adapter_sha256': r.sha(r.ROOT/'scripts/Bukareszt/matura_package.py')}


def verify_pins(pins):
    for name, digest in pins.items():
        r.require(r.sha(Path(name)) == digest, 'Frozen file changed: ' + name)


def request_loop(cases, config, out, max_calls, deadline, guard, verify, inf):
    """One reservation per attempted request; any failure stops and leaves remaining IDs unsent."""
    rows, stop = [], 'complete'
    _, adapter = r.modules()
    with (out/'raw.jsonl').open('x', encoding='utf-8') as raw, (out/'calls.jsonl').open('x', encoding='utf-8') as calls:
        for case in cases:
            try:
                r.require(len(rows) < max_calls, 'Call budget exhausted')
                r.require(time.monotonic() + 420 + 20 < deadline, 'Insufficient wall budget for full timeout and cleanup')
                guard()
                calls.write(json.dumps({'call': len(rows)+1, 'id': case['id'], 'max_output_tokens': 1024,
                                        'reserved_at_utc':r.dt.datetime.now(r.dt.timezone.utc).isoformat()})+'\n')
                calls.flush(); os.fsync(calls.fileno())
                result = inf.run_case(case, config)
                try:
                    _, failure = adapter.extract_answer(result)
                    r.require(failure is None, 'Incomplete/failed response: '+str(failure))
                    usage = result.get('usage') or {}
                    r.require(type(usage.get('prompt_tokens')) is int and 0 <= usage['prompt_tokens'] <= 2816, 'Missing/excess prompt usage')
                    r.require(type(usage.get('completion_tokens')) is int and 0 <= usage['completion_tokens'] <= 1024, 'Missing/excess completion usage')
                    r.require(not (result.get('raw_response') or {}).get('truncated', False), 'Context truncation reported')
                    verify()
                except (RuntimeError, OSError, ValueError) as exc:
                    stop = str(exc)
                    if result.get('error') is None:
                        result['error'] = {'type':'launcher_validation','message':stop}
                raw.write(json.dumps(result, ensure_ascii=False)+'\n'); raw.flush(); os.fsync(raw.fileno())
                rows.append(result)
                if stop != 'complete': break
            except (RuntimeError, OSError, ValueError) as exc:
                stop = str(exc)
                break
    return {'completed_records': len(rows), 'unsent_ids': [c['id'] for c in cases[len(rows):]], 'stop_reason': stop,
            'actual_cost_usd': 0, 'usage': [x.get('usage') for x in rows]}


def cleanup_owned(out):
    """Parent safety net: signal only a recorded process group still in the recorded namespace."""
    record = out/'server-pid.json'
    if not record.exists():
        return
    owned = json.loads(record.read_text())
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if os.getpgid(int(proc.name)) == owned['process_group'] and os.readlink(proc/'ns/net') == owned['namespace']:
                os.killpg(owned['process_group'], signal.SIGKILL)
                return
        except (OSError, ProcessLookupError):
            continue


def inside(a):
    out = Path(a.output).resolve()
    record = json.loads((out/'launch.json').read_text())
    r.require(os.getppid() == record['parent_pid'], 'Inside mode requires the recorded live supervisor')
    verify_pins(record['frozen_files'])
    profile = r.validate_profile(record['runtime_profile'])
    r.require(r.profile_sha(profile) == record['runtime_profile_sha256'], 'Runtime profile changed after launch record')
    context = profile['context_length']
    proof = r.network_proof(a.host_net)
    r.write(out/'network-proof.json', proof)
    inf, _ = r.modules()
    cases = inf.load_cases(out/'input.jsonl', record['max_calls'])
    r.require([c['id'] for c in cases] == record['ids'], 'Prepared IDs changed')
    config = inf.load_config(out/'config.json', False)
    inf.OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), inf.NoRedirect)
    worker_guard(parent_pid=record['parent_pid'], profile=profile)
    home = out/'server-home'; home.mkdir()
    env = r.server_env(profile, home)
    server = None
    deadline = time.monotonic() + record['wall_seconds'] - 20
    try:
        with (out/'server.log').open('xb') as log:
            server = subprocess.Popen([profile['ollama_binary'],'serve'], env=env, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
        ns = os.readlink(f'/proc/{server.pid}/ns/net')
        r.write(out/'server-pid.json', {'process_group':server.pid, 'namespace':ns})
        r.require(ns == proof['isolated_namespace'], 'Server namespace mismatch')
        ready = time.monotonic() + 45
        while True:
            r.require(server.poll() is None, 'Server exited')
            try:
                version = r.api('version')
                r.require(version.get('version') == profile['ollama_version'], 'Runtime version changed')
                r.verify_model()
                break
            except (OSError, ValueError):
                r.require(time.monotonic() < ready, 'Readiness timeout')
                time.sleep(.5)
        r.write(out/'readiness.json', {'version':version, 'digest':r.DIGEST, 'context_expected':context,
                                        'runtime_profile_sha256':record['runtime_profile_sha256']})
        def loaded_runtime():
            models = r.api('ps')['models']
            with (out/'runtime.jsonl').open('a',encoding='utf-8') as runtime:
                runtime.write(json.dumps({'checked_at_utc':r.dt.datetime.now(r.dt.timezone.utc).isoformat(),
                                          'models':models})+'\n')
            r.require(len(models) == 1 and models[0].get('digest') == r.DIGEST and
                      models[0].get('context_length') == context, 'Loaded model digest/context mismatch')
        result = request_loop(cases, config, out, record['max_calls'], deadline,
                              lambda: worker_guard(server.pid,record['parent_pid'],profile), loaded_runtime, inf)
        r.write(out/'execution.json', result)
        return 0 if result['stop_reason'] == 'complete' else 1
    finally:
        if server is not None:
            try:
                os.killpg(server.pid, signal.SIGTERM)
                server.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            cleanup_owned(out)
            r.write(out/'cleanup.json', {'owned_process_group':server.pid, 'host_daemon_stopped':False,
                                        'host_firewall_changed':False})


def finalize(out, package):
    _, adapter = r.modules()
    raw = out/'raw.jsonl'
    if not raw.exists():
        raw.touch(exist_ok=False)
    report = adapter.finalize(package, [raw], out/'answers.json', out/'failures.json', out/'input.jsonl.manifest.json')
    r.require(adapter.main(['validate',str(out/'answers.json'),'--exam-dir',str(package['exam_dir'])]) == 0,
              'Final JSON invalid')
    return report


def execute(a):
    r.require(sys.platform == 'linux', 'Execute only under WSL/Linux')
    import fcntl
    out, package, config, record = preflight(a)
    profile = record['runtime_profile']
    r.check_platform(profile)
    (r.OWN/'private').mkdir(exist_ok=True)
    with (r.OWN/'private/offline-rehearsal.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        r.host_idle(profile)
        worker_guard(profile=profile)
        r.verify_binary(profile)
        r.verify_assets(profile)
        record['isolation_probe'] = r.isolation_probe()
        out.mkdir(parents=True)
        _, adapter = r.modules()
        adapter.prepare(package, out/'input.jsonl')
        config_bytes = Path(a.config).read_bytes()
        r.require(r.hashlib.sha256(config_bytes).hexdigest() == CONFIG_SHA, 'Original config changed during preflight')
        config = json.loads(config_bytes)
        config['base_url'] = r.ENDPOINT+'/v1'  # isolated endpoint only; generation settings unchanged
        r.write(out/'config.json', config)
        record['frozen_files'] = dict(record['package_files'])
        for p in [out/'input.jsonl',out/'input.jsonl.manifest.json',out/'config.json', SELF, Path(r.__file__),
                  r.ROOT/'infer.py',r.ROOT/'scripts/Bukareszt/matura_package.py']:
            record['frozen_files'][str(p)] = r.sha(p)
        if record['runtime_profile_file'] is not None:
            r.require(r.sha(Path(record['runtime_profile_file'])) == record['runtime_profile_file_sha256'], 'Runtime profile file changed')
            record['frozen_files'][record['runtime_profile_file']] = record['runtime_profile_file_sha256']
        if profile['ollama_binary_sha256'] is not None:
            record['frozen_files'][profile['ollama_binary']] = profile['ollama_binary_sha256']
        record['git_revision'] = subprocess.check_output(['git','rev-parse','HEAD'], cwd=r.ROOT, text=True).strip()
        record['parent_pid'] = os.getpid()
        record['endpoint_change'] = '127.0.0.1:11434 -> isolated 127.0.0.1:11435; no sampling changes'
        r.write(out/'launch.json', record)
        command = ['unshare','-rn','--',sys.executable,'-B',str(SELF),'--inside',
                   '--host-net',os.readlink('/proc/self/ns/net'),'--output',str(out)]
        child = None
        status = 2
        try:
            child = subprocess.Popen(command, start_new_session=True)
            status = child.wait(timeout=a.wall_seconds)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if child is not None:
                try: os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError: pass
                try: child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL); child.wait()
        finally:
            cleanup_owned(out)
            # This CPU-only step also preserves unsent template IDs after infrastructure failure.
            verify_pins(record['package_files'])
            report = finalize(out, package)
            r.write(out/'outcome.json', {'child_status':status,'answered':report['answered'],'empty':report['empty'],
                'answers_sha256':report['answers_sha256'],'actual_cost_usd':0,'submission_performed':False})
        return 0 if status == 0 and not report['failures'] else 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--inside',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--host-net',default='',help=argparse.SUPPRESS)
    p.add_argument('--exam-dir',type=Path)
    p.add_argument('--config',type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--max-calls',type=int)
    p.add_argument('--max-output-tokens-total',type=int)
    p.add_argument('--wall-seconds',type=int)
    p.add_argument('--runtime-profile',type=Path,default=None,
                   help='Frozen runtime profile JSON; omitted = qualified laptop WSL 0.30.7/context 4096 default')
    a = p.parse_args(argv)
    if a.inside:
        r.require(not a.execute, 'Conflicting execution modes')
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
        return inside(a)
    for key in ('exam_dir','config','max_calls','max_output_tokens_total','wall_seconds'):
        if getattr(a,key) is None: p.error('--'+key.replace('_','-')+' is required')
    if a.execute:
        return execute(a)
    _, _, _, report = preflight(a)
    print(json.dumps({'dry_preflight':True,'model_calls':0,**report},ensure_ascii=False,indent=2))
    return 0


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (RuntimeError,OSError,ValueError) as exc:
        print('STOP: '+str(exc),file=sys.stderr)
        raise SystemExit(2)
