"""Linux counterpart of root's run_cpu_probe.py (which hardcodes a Windows venv path).

Checks the installed package identity against the pinned exact-commit archives
and root's evidence-manifest source hashes, then runs root's UNCHANGED
runtime_probe.py with CUDA hidden and HF offline under a hard timeout.
Run from a directory containing runtime_probe.py, candidate.json and
evidence-manifest.json copied byte-identically from agentsLog/kwiscion/essay-lora-prep.
"""
import argparse, datetime, hashlib, json, os, subprocess, sys
from pathlib import Path

ARCHIVE_SHA = {
    'transformers': 'c97fdf3bfb260db12b4fecf1a7647f51ca0e2b52cc75a947ca1a3d6cc4f4ed8c',
    'peft': '05a70e1ef6ac1633da4d2ca3b90db5df7cb5f24d9b9b123ce0763e9e83b42dd2',
}
SOURCES = [('transformers', 'models/gemma4_unified/modeling_gemma4_unified.py'),
           ('transformers', 'models/gemma4_unified/configuration_gemma4_unified.py'),
           ('peft', 'tuners/lora/layer.py'), ('peft', 'tuners/lora/model.py')]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--python', required=True)
    ap.add_argument('--probe-dir', type=Path, required=True)
    ap.add_argument('--src-dir', type=Path, required=True)
    ap.add_argument('--expect-torch', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--timeout', type=int, default=180)
    a = ap.parse_args()
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
    code = ("import importlib.metadata as m,json,sys,torch;print(json.dumps({'python':sys.version,'torch':torch.__version__,"
            "'torch_cuda':torch.version.cuda,'versions':{p:m.version(p) for p in ['transformers','peft']},"
            "'direct_url':{p:json.loads(m.distribution(p).read_text('direct_url.json') or 'null') for p in ['transformers','peft']},"
            "'locations':{p:str(m.distribution(p).locate_file(p)) for p in ['transformers','peft']}}))")
    ident = json.loads(subprocess.check_output([a.python, '-c', code], env=env, text=True, timeout=120))
    assert ident['torch'] == a.expect_torch, ident['torch']
    ident['archive_sha256'] = {}
    for pkg, zname in (('transformers', 'transformers-96331a9f.zip'), ('peft', 'peft-b8674c86.zip')):
        url = ident['direct_url'][pkg]['url']
        assert url.endswith('/' + zname), url
        actual = hashlib.sha256((a.src_dir / zname).read_bytes()).hexdigest()
        assert actual == ARCHIVE_SHA[pkg], (pkg, actual)
        ident['archive_sha256'][pkg] = actual
    manifest = json.loads((a.probe_dir / 'evidence-manifest.json').read_text())
    ident['installed_source_hashes'] = {}
    for pkg, rel in SOURCES:
        name = pkg + '-src_' + pkg + '_' + rel.replace('/', '_')
        expected = next(x['sha256'] for x in manifest['files'] if x['file'] == name)
        actual = hashlib.sha256((Path(ident['locations'][pkg]) / rel).read_bytes()).hexdigest()
        assert actual == expected, (rel, actual, expected)
        ident['installed_source_hashes'][pkg + '/' + rel] = actual
    report = {'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'bound_seconds': a.timeout,
              'package_identity': 'PASS', 'identity': ident,
              'probe_file_sha256': {f: hashlib.sha256((a.probe_dir / f).read_bytes()).hexdigest()
                                    for f in ('runtime_probe.py', 'candidate.json', 'evidence-manifest.json')}}
    probe_out = a.out.with_name(a.out.stem + '-runtime.json')
    try:
        done = subprocess.run([a.python, str(a.probe_dir / 'runtime_probe.py'), '--execute-synthetic', '--output', str(probe_out)],
                              env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=a.timeout)
        report['returncode'] = done.returncode
        report['status'] = 'PASS' if done.returncode == 0 else 'FAIL'
        report['output_tail'] = done.stdout[-4000:]
        if probe_out.exists():
            report['probe'] = json.loads(probe_out.read_text())
    except subprocess.TimeoutExpired:
        report['status'] = 'BLOCKED'; report['error'] = f'{a.timeout}-second hard timeout'
    report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    a.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'output_tail'}, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
