"""Write a DECLARED stage manifest for root's run_real_pilot.py (pins every file by absolute path + SHA256).

usage: make_manifest.py probe|history --run RUN --deadline-utc ISO [--probe-report P --control-report C]
Refuses to overwrite. The history manifest additionally pins the train/eval/clearance data and the probe and control reports.
"""
import argparse, hashlib, json, sys
from pathlib import Path

R = Path('/ephemeral/mm-lora')
PREP = R / 'pilot-src/agentsLog/kwiscion/essay-lora-prep'  # byte-identical copy of origin/main files
BASE = R / 'base/gemma-4-12B-it@707f0a3b'
DATA = R / 'real-prep-in'
EXPECT = {  # governing files: expected SHA256 (root plan fb65536b...)
    'run_real_pilot.py': '3d466395cad9a2d596a356f15904024e2102b655c79fdc6319942d17bd1443dd',
    'prepare.py': '0d3a0452ef9caf514c713766e81b3fc1f21ecfcb85db8d2b89072a9a75cf115e',
    'candidate.json': 'fc3b61de8cd061617ed5351cac441b8610cca19fff6a0b8827feb767cd617707',
    'evidence-manifest.json': '2ffac97f62bc12db94277e6cc2d3d30e876f4eb5ebb2731ada1ebee91c2db5cd',
}
DATA_EXPECT = {
    'train_sft.jsonl': '83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5',
    'eval16_input.jsonl': '5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28',
    'essay_lora_clearance_v1.json': '9a31742306e1c37aa096ff9e16e128083b8fff8e83257658e21457f2b35921fd',
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=('probe', 'history'))
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--deadline-utc', required=True)
    ap.add_argument('--probe-report', type=Path)
    ap.add_argument('--control-report', type=Path)
    a = ap.parse_args()
    files = {}
    for name, want in EXPECT.items():
        got = sha(PREP / name)
        if got != want:
            sys.exit(f'pin mismatch {name} {got}')
        files[str(PREP / name)] = got
    m = {'status': 'DECLARED', 'deadline_utc': a.deadline_utc, 'base': str(BASE),
         'base_weight_sha256': '5a84cb313260ac447237b890387116dfa8682e49a6b44bc585ae8353abbff18d', 'inference_calls': 0}
    if a.mode == 'probe':
        m.update(mode='synthetic_probe', output=str(a.run / 'probe'), lock_file=str(a.run / 'stage-probe.lock'),
                 max_optimizer_steps=1, max_seconds=600)
        out = a.run / 'probe-manifest.json'
    else:
        if not (a.probe_report and a.control_report):
            sys.exit('history needs --probe-report and --control-report')
        for name, want in DATA_EXPECT.items():
            got = sha(DATA / name)
            if got != want:
                sys.exit(f'data pin mismatch {name} {got}')
            files[str(DATA / name)] = got
        for p in (a.probe_report, a.control_report):
            files[str(p.resolve())] = sha(p)
        m.update(mode='history', output=str(a.run / 'history'), lock_file=str(a.run / 'stage-history.lock'),
                 max_optimizer_steps=36, max_seconds=1500, train_records=90,
                 train=str(DATA / 'train_sft.jsonl'), eval_inputs=str(DATA / 'eval16_input.jsonl'),
                 clearance=str(DATA / 'essay_lora_clearance_v1.json'),
                 synthetic_probe_report=str(a.probe_report.resolve()), control_serving_report=str(a.control_report.resolve()))
        out = a.run / 'history-manifest.json'
    m['files'] = files
    if out.exists():
        sys.exit(f'refusing overwrite {out}')
    out.write_text(json.dumps(m, indent=2) + '\n')
    print(out, sha(out))


if __name__ == '__main__':
    main()
