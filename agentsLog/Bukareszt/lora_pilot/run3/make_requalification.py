"""Derive the NEW run3 control-serving qualification record from run2's immutable evidence (no model calls).

Run2's original control report stays a terminal FAIL under its original raw-template criterion.
This writes a SEPARATE, attributable record. The one change is the template criterion: it now
compares against the lexer-normalized pinned template (llama.cpp fcb3074f /props semantics). The
record links the exact original report/ledger/log hashes and the independent verifier's evidence.
It also seeds the run3 ledger: the 2 reused run2 control calls are marked `reused_prior`, and they
count toward the 4-call cap, so at most 2 NEW candidate calls remain.

usage: make_requalification.py --run2 RUN2_DIR --verification VERIFICATION.json --out-report OUT.json --out-ledger RUN3/call-ledger.jsonl
"""
import argparse, hashlib, json, sys
from pathlib import Path

RAW_SHA = 'ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4'
NORMALIZED_SHA = '6a1015c47ccfcfa67c3b772385bccee357a4d37c3cda37bd202e9047f391ab82'
CONTROL_Q4_SHA = 'a192fac4a5989aa7db9452d91405cd401a7fb03e0af3b36343abeeb146d3282a'
CONTROL_PROJ_SHA = '9ff3ded7bf4360353a3c184aeef9fb1a15e54f08abcb1a45a46b3467333fb12e'
DRIVER_SHA = '586acd0b48f0c7aa51b5cba6da5be9ccb5913c03a9d908a8500f800b9d1e0229'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run2', type=Path, required=True)
    ap.add_argument('--verification', type=Path, required=True)
    ap.add_argument('--out-report', type=Path, required=True)
    ap.add_argument('--out-ledger', type=Path, required=True)
    a = ap.parse_args()
    for p in (a.out_report, a.out_ledger):
        if p.exists():
            sys.exit(f'refusing overwrite {p}')
    orig_p, ledger_p, log_p, probe_p = a.run2 / 'control-serving-report.json', a.run2 / 'call-ledger.jsonl', a.run2 / 'server-control.log', a.run2 / 'probe/report.json'
    orig = json.loads(orig_p.read_text())
    ver = json.loads(a.verification.read_text())
    probe = json.loads(probe_p.read_text())
    ledger = [json.loads(l) for l in ledger_p.read_text().splitlines() if l.strip()]
    # fail closed: everything except the template criterion must already hold in the original evidence
    rcv = ver.get('root_criteria_verdict')
    rcv_verdict = rcv.get('verdict') if isinstance(rcv, dict) else rcv
    assert isinstance(rcv_verdict, str) and rcv_verdict.upper().startswith('PASS'), 'independent verification not PASS against root criteria'
    assert orig['status'] == 'FAIL' and orig['artifact'] == 'control' and orig['scope'] == 'matched_unmodified_export_text_image'
    assert orig['model_sha256'] == CONTROL_Q4_SHA and orig['mmproj_sha256'] == CONTROL_PROJ_SHA
    assert orig['served_chat_template_sha256'] == NORMALIZED_SHA and orig['served_template_is_pinned_hf'] is False
    crit = dict(orig['criteria'])
    assert set(crit) == {'two_calls_http_200', 'nonempty_text', 'finish_reason_stop', 'completion_tokens_le_512',
                         'image_tokens_consumed', 'served_template_is_pinned_hf'}, crit
    others = {k: v for k, v in crit.items() if k != 'served_template_is_pinned_hf'}
    assert all(others.values()), others
    assert orig['server_exit_code'] == 0
    reserved = [r for r in ledger if r['event'] == 'reserved']
    results = [r for r in ledger if r['event'] == 'result']
    assert len(reserved) == 2 and len(results) == 2 and all(r['artifact'] == 'control' for r in reserved)
    assert probe['status'] == 'PASS' and probe['mode'] == 'synthetic_probe' and probe['synthetic_optimizer_steps'] == 1 and probe['driver_sha256'] == DRIVER_SHA
    new_crit = dict(others, served_template_is_pinned_hf_lexer_normalized=True)
    report = {
        'status': 'PASS', 'scope': 'matched_unmodified_export_text_image', 'artifact': 'control',
        'record_type': 'REQUALIFICATION_OF_RUN2_CONTROL_SERVING (separate record; run2 original remains terminal FAIL)',
        'model': orig['model'], 'model_sha256': orig['model_sha256'], 'mmproj': orig['mmproj'], 'mmproj_sha256': orig['mmproj_sha256'],
        'server_binary_sha256': orig['server_binary_sha256'], 'server_cmd': orig['server_cmd'], 'fixtures_sha256': orig['fixtures_sha256'],
        'served_chat_template_sha256': orig['served_chat_template_sha256'],
        'pinned_template_raw_sha256': RAW_SHA, 'pinned_template_lexer_normalized_sha256': NORMALIZED_SHA,
        'criteria': new_crit,
        'changed_interpretation': ('Only the template criterion changed. Original: served /props chat_template sha == raw HF chat_template.jinja sha '
                                   '(ae53464b...). Corrected: served sha == lexer-normalized pinned template sha (6a1015c4...). llama.cpp fcb3074f returns '
                                   'common_chat_template::src = jinja lexer_res.source (CRLF/CR->LF, exactly one trailing newline removed). All other criteria, '
                                   'calls, texts and settings are the original run2 values, unchanged.'),
        'calls': orig['calls'], 'load_seconds': orig.get('load_seconds'), 'server_identity': orig.get('server_identity'), 'server_exit_code': orig['server_exit_code'],
        'linked_original': {'control_serving_report_sha256': sha(orig_p), 'call_ledger_sha256': sha(ledger_p),
                            'server_log_sha256': sha(log_p), 'probe_report_sha256': sha(probe_p), 'run2_dir': str(a.run2),
                            'original_status': orig['status'], 'original_criteria': crit},
        'independent_verification': {'path': str(a.verification), 'sha256': sha(a.verification), 'overall_as_briefed': ver.get('overall'),
                                     'root_criteria_verdict': rcv,
                                     'note': 'overall_as_briefed FAILed only a worker-added sub-check (rival rewrites must differ on THIS template); root criterion judged separately'},
        'model_calls_in_requalification': 0,
    }
    a.out_report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with a.out_ledger.open('x') as f:
        for r in ledger:
            f.write(json.dumps({**r, 'reused_prior': True, 'source': 'run2 call-ledger.jsonl ' + sha(ledger_p)}) + '\n')
    print(json.dumps({'report': str(a.out_report), 'report_sha256': sha(a.out_report), 'ledger': str(a.out_ledger), 'ledger_sha256': sha(a.out_ledger)}))


if __name__ == '__main__':
    main()
