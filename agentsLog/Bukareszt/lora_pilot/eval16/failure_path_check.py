"""Focused CPU failure-path check for eval16_session.py's recovery adapter (no model, no GPU).

Swaps llama-server for a tiny fake OpenAI-compatible HTTP server (same process group, same identity-checked
cleanup path) with scripted per-item behaviours, then runs the REAL session main() with short timeouts and asserts:
retry ladder, preserved earlier usable answers, partial/placeholder labels, ledger reserve-before-dispatch,
call and token caps, the arm wall-budget skip, and owned-server cleanup.
usage (Linux, needs /proc): python3 failure_path_check.py EVAL16_SESSION.py EVAL16_INPUT.jsonl WORKDIR
"""
import importlib.util, json, os, sys, time, subprocess
from pathlib import Path

FAKE = r'''
import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
port = int(sys.argv[sys.argv.index('--port') + 1]); seen = {}
TEMPLATE = open(sys.argv[sys.argv.index('--tmpl') + 1]).read()
PLAN = {  # per item id suffix -> outcomes per attempt
  '01': ['ok'], '02': ['length', 'ok'], '03': ['err', 'err', 'err', 'err'], '04': ['empty', 'length', 'empty', 'ok'],
  '05': ['sleep', 'ok'], '06': ['length', 'length', 'length', 'length']}
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        self._send(200, {'status': 'ok'} if self.path == '/health' else {'chat_template': TEMPLATE})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt = body['messages'][0]['content']; key = prompt.split('synthetic prompt ')[1][:2] if 'synthetic prompt ' in prompt else prompt[-2:]
        n = seen.get(key, 0); seen[key] = n + 1
        plan = PLAN.get(key, ['ok']); o = plan[min(n, len(plan) - 1)]
        if o == 'err': return self._send(500, {'error': 'x'})
        if o == 'sleep': time.sleep(3)
        text = {'ok': 'essay ' * 420, 'length': 'partial ' * 50, 'empty': '', 'sleep': 'late'}[o]
        fr = 'length' if o == 'length' else 'stop'
        self._send(200, {'choices': [{'finish_reason': fr, 'message': {'content': text}}], 'usage': {'completion_tokens': 10, 'prompt_tokens': 5}})
HTTPServer(('127.0.0.1', port), H).serve_forever()
'''


def main():
    sess_path, inputs, work = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('sess', sess_path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    # 6 synthetic items whose prompts end in the plan key; hash check bypassed only by pointing INPUT_SHA at the synthetic file
    rows = [{'id': f't-{i:02d}', 'prompt': f'synthetic prompt {i:02d}', 'source_group_id': 'SYN'} for i in range(1, 7)]
    rows += [{'id': f't-{i:02d}', 'prompt': f'synthetic prompt x{i:02d}'[-20:] + 'zz', 'source_group_id': 'SYN'} for i in range(7, 17)]
    inp = work / 'inputs.jsonl'; inp.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    tmpl = work / 'tmpl.txt'; tmpl.write_text('TEMPLATE')
    fake = work / 'fake_server.py'; fake.write_text(FAKE)
    m.INPUT_SHA = m.sha_file(inp); m.NORMALIZED_TEMPLATE_SHA = m.sha_bytes(b'TEMPLATE')
    m.SERVER = Path(sys.executable).resolve(); m.PORT = 18999
    real_popen = subprocess.Popen
    def fake_popen(cmd, **kw):  # same process group; argv keeps the real flags for inspection
        return real_popen([sys.executable, str(fake), *cmd[1:], '--tmpl', str(tmpl)], **kw)
    m.subprocess.Popen = fake_popen
    settings = {'temperature': 0.0, 'top_k': 1, 'seed': 42, 'ctx_size': 65536,
                'arms': {'A': {'server_reasoning': 'off', 'attempts': [
                    {'max_tokens': 32768, 'enable_thinking': False, 'request_timeout_s': 2},
                    {'max_tokens': 49152, 'enable_thinking': False, 'request_timeout_s': 2, 'only_if_fits': True},
                    {'max_tokens': 32768, 'enable_thinking': False, 'request_timeout_s': 2},
                    {'max_tokens': 32768, 'enable_thinking': False, 'request_timeout_s': 2, 'synthesis': True}]}}}
    st = work / 'settings.json'; st.write_text(json.dumps(settings))
    results = {}
    def run(tag, calls, tokens, deadline_offset):
        d = work / tag; d.mkdir()
        sys.argv = ['x', '--arm', 'A', '--model', str(st), '--mmproj', str(st), '--inputs', str(inp), '--settings', str(st),
                    '--run', str(d), '--out', str(d / 'answers-A.jsonl'), '--max-wave-calls', str(calls),
                    '--max-wave-tokens', str(tokens), '--arm-deadline-epoch', str(int(time.time()) + deadline_offset)]
        try:
            m.main()
        except SystemExit as e:
            rc = e.code
        items = {r['id']: r for r in (json.loads(l) for l in (d / 'answers-A.jsonl').read_text().splitlines()) if r.get('item')}
        lp = d / 'call-ledger.jsonl'
        ledger = [json.loads(l) for l in lp.read_text().splitlines()] if lp.exists() else []
        end = [json.loads(l) for l in (d / 'answers-A.jsonl').read_text().splitlines()][-1]
        return rc, items, ledger, end
    # T1: normal budgets
    rc, it, led, end = run('t1', 128, 4718592, 600)
    st_ = {k: (v['final_status'], len(v['attempts'])) for k, v in it.items()}
    checks = {
        'all_16_items': len(it) == 16 and rc == 0,
        'ok_first_attempt': st_['t-01'] == ('complete', 1),
        'length_then_ok_retries_once': st_['t-02'] == ('complete', 2) and it['t-02']['attempts'][1]['max_tokens'] == 49152,
        'four_errors_placeholder': st_['t-03'] == ('placeholder', 4) and it['t-03']['text'].startswith('[PLACEHOLDER'),
        'synthesis_4th_uses_preserved_draft': st_['t-04'] == ('complete', 4) and it['t-04']['attempts'][3]['synthesis_with_draft'] and not it['t-03']['attempts'][3]['synthesis_with_draft'],
        'timeout_then_ok': st_['t-05'] == ('complete', 2) and 'error' in it['t-05']['attempts'][0],
        'all_length_keeps_first_partial': st_['t-06'] == ('partial', 4) and it['t-06']['chosen_call_number'] == it['t-06']['attempts'][0]['call_number'],
        'ladder_32768_49152_32768_32768': [x['max_tokens'] for x in it['t-03']['attempts']] == [32768, 49152, 32768, 32768],
        'reserve_before_result': all(led[i]['event'] == 'reserved' and led[i + 1]['event'] == 'result' and led[i]['call_number'] == led[i + 1]['call_number'] for i in range(0, len(led), 2)),
        'server_cleaned_up_exit_recorded': end.get('end', {}).get('server_exit_code') is not None,
    }
    # T2: call cap 5 -> later items skipped with explicit budget label, no 6th reservation
    rc2, it2, led2, _ = run('t2', 5, 4718592, 600)
    checks['call_cap_enforced'] = sum(1 for r in led2 if r['event'] == 'reserved') == 5 and any(a.get('skipped') == 'wave call/token budget' for v in it2.values() for a in v['attempts'])
    # T3: token cap 100000 -> at most 3 reservations of 32768 (98304), then skip
    rc3, it3, led3, _ = run('t3', 128, 100000, 600)
    checks['token_cap_enforced'] = sum(r['max_tokens'] for r in led3 if r['event'] == 'reserved') <= 100000 and sum(1 for r in led3 if r['event'] == 'reserved') == 3
    # T4: arm deadline already too close -> no dispatch at all, every item placeholder with wall-budget skip
    rc4, it4, led4, _ = run('t4', 128, 4718592, 1)
    checks['wall_budget_skip'] = len(led4) == 0 and all(v['final_status'] == 'placeholder' and v['attempts'][0].get('skipped') == 'arm wall budget' for v in it4.values())
    out = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
           'session_sha256': m.sha_file(sess_path), 'item_status_t1': st_}
    print(json.dumps(out, indent=1))
    sys.exit(0 if out['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
