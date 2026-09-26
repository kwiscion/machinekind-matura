"""One owned llama-server session with exactly two synthetic calls (text + image) against one GGUF pair.

Foreground only: the server is a Popen child in the operator's process group (no setsid; the operator's
inner timeouts use --foreground), so the outer `timeout` TERM/KILL reaches it too. SIGTERM to this
process raises SystemExit so the finally block still cleans up the owned server. The durable ledger allows at most 4 reservations for
the whole wave, and each call is reserved (fsync) BEFORE it is dispatched. No retries and
no warmups. Cleanup kills only the server this session started, after checking its PID,
/proc start ticks and executable. Writes a serving report and, for the control artifact,
evaluates the predeclared PASS criteria.

usage: serve_session.py --artifact control|candidate --model M.gguf --mmproj P.gguf --run RUN --report OUT.json
"""
import argparse, base64, hashlib, json, os, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path

R = Path('/ephemeral/mm-lora')
SERVER = R / 'src/llama.cpp/build-cuda/bin/llama-server'
FIX = R / 'pilot-fixtures'
PINNED_TEMPLATE_SHA = 'ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4'  # HF chat_template.jinja @707f0a3b
PORT = 18117
MAX_WAVE_CALLS = 4


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ledger_reserve(ledger, entry):
    rows = [json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    reserved = sum(1 for r in rows if r['event'] == 'reserved')
    if reserved >= MAX_WAVE_CALLS:
        raise SystemExit(f'ledger: {reserved} calls already reserved; refusing')
    rec = {'event': 'reserved', 'call_number': reserved + 1, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **entry}
    with ledger.open('a') as f:
        f.write(json.dumps(rec) + '\n'); f.flush(); os.fsync(f.fileno())
    return rec['call_number']


def ledger_result(ledger, rec):
    with ledger.open('a') as f:
        f.write(json.dumps({'event': 'result', **rec}) + '\n'); f.flush(); os.fsync(f.fileno())


def start_ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


def http(method, path, body=None, timeout=240):
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}{path}', method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact', choices=('control', 'candidate'), required=True)
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--mmproj', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    a = ap.parse_args()
    if a.report.exists():
        raise SystemExit('refusing overwrite')
    def _term(*_):
        raise SystemExit('SIGTERM')  # run finally: identity-checked server cleanup + report
    signal.signal(signal.SIGTERM, _term)
    ledger = a.run / 'call-ledger.jsonl'
    s = socket.socket()
    try:
        if s.connect_ex(('127.0.0.1', PORT)) == 0:
            raise SystemExit(f'port {PORT} already in use; not adopting a foreign server')
    finally:
        s.close()
    text_fx = json.loads((FIX / 'synthetic_text.json').read_text(encoding='utf-8'))
    img_fx = json.loads((FIX / 'synthetic_image.json').read_text(encoding='utf-8'))
    img_bytes = (FIX / img_fx['image']).read_bytes()
    report = {'artifact': a.artifact, 'status': 'FAIL', 'model': str(a.model), 'model_sha256': sha_file(a.model),
              'mmproj': str(a.mmproj), 'mmproj_sha256': sha_file(a.mmproj), 'server_binary_sha256': sha_file(SERVER),
              'fixtures_sha256': {n: sha_file(FIX / n) for n in ('synthetic_text.json', 'synthetic_image.json', img_fx['image'])},
              'calls': []}
    cmd = [str(SERVER), '-m', str(a.model), '--mmproj', str(a.mmproj), '--host', '127.0.0.1', '--port', str(PORT),
           '-ngl', '999', '-c', '8192', '-np', '1', '--jinja', '--no-webui', '--reasoning', 'off', '--no-warmup']
    report['server_cmd'] = cmd
    log = (a.run / f'server-{a.artifact}.log').open('wb')
    env = {k: v for k, v in os.environ.items() if not k.startswith('LLAMA_ARG_')}
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)  # same process group, no setsid
    ident = {'pid': proc.pid, 'start_ticks': start_ticks(proc.pid), 'exe': os.readlink(f'/proc/{proc.pid}/exe')}
    report['server_identity'] = ident
    try:
        if ident['exe'] != str(SERVER.resolve()):
            raise SystemExit('unexpected server executable')
        t0 = time.monotonic()
        while True:
            if proc.poll() is not None:
                raise SystemExit(f'server exited early rc={proc.returncode}')
            try:
                if http('GET', '/health', timeout=5)[0] == 200:
                    break
            except Exception:
                pass
            if time.monotonic() - t0 > 240:
                raise SystemExit('server not healthy within 240 s')
            time.sleep(1)
        report['load_seconds'] = round(time.monotonic() - t0, 1)
        _, props = http('GET', '/props', timeout=10)
        props = json.loads(props)
        tmpl = props.get('chat_template', '')
        report['served_chat_template_sha256'] = sha_bytes(tmpl.encode())
        report['served_template_is_pinned_hf'] = report['served_chat_template_sha256'] == PINNED_TEMPLATE_SHA
        for fx, fname in ((text_fx, 'synthetic_text.json'), (img_fx, 'synthetic_image.json')):
            content = fx['prompt'] if fx['kind'] == 'text' else [
                {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(img_bytes).decode()}},
                {'type': 'text', 'text': fx['prompt']}]
            body = {'messages': [{'role': 'user', 'content': content}], 'max_tokens': fx['max_tokens'],
                    'temperature': fx['temperature'], 'top_k': fx['top_k'], 'seed': fx['seed'],
                    'chat_template_kwargs': {'enable_thinking': fx['enable_thinking']}}
            n = ledger_reserve(ledger, {'artifact': a.artifact, 'fixture': fname, 'max_tokens': fx['max_tokens']})
            t = time.monotonic()
            rec = {'call_number': n, 'artifact': a.artifact, 'fixture': fname, 'request_sha256': sha_bytes(json.dumps(body, sort_keys=True).encode())}
            try:
                status, raw = http('POST', '/v1/chat/completions', body, timeout=300)
                rec.update(http_status=status, response_sha256=sha_bytes(raw), seconds=round(time.monotonic() - t, 2))
                resp = json.loads(raw)
                ch = resp['choices'][0]
                rec.update(finish_reason=ch.get('finish_reason'), text=ch['message'].get('content'),
                           reasoning_present=bool(ch['message'].get('reasoning_content')), usage=resp.get('usage'), model_field=resp.get('model'))
            except Exception as exc:
                rec.update(error=f'{type(exc).__name__}: {exc}'[:500])
            ledger_result(ledger, rec)
            report['calls'].append(rec)
        tc, ic = report['calls']
        crit = {
            'two_calls_http_200': all(c.get('http_status') == 200 for c in report['calls']),
            'nonempty_text': all(isinstance(c.get('text'), str) and c['text'].strip() for c in report['calls']),
            'finish_reason_stop': all(c.get('finish_reason') == 'stop' for c in report['calls']),
            'completion_tokens_le_512': all((c.get('usage') or {}).get('completion_tokens', 10**9) <= 512 for c in report['calls']),
            'image_tokens_consumed': ((ic.get('usage') or {}).get('prompt_tokens', 0) - (tc.get('usage') or {}).get('prompt_tokens', 0)) >= 64,
            'served_template_is_pinned_hf': report['served_template_is_pinned_hf'],
        }
        report['criteria'] = crit
        if all(crit.values()):
            report['status'] = 'PASS'
        if a.artifact == 'control':
            report['scope'] = 'matched_unmodified_export_text_image'
    finally:
        # Cleanup ONLY the server this session started (identity re-checked).
        try:
            if proc.poll() is None and start_ticks(proc.pid) == ident['start_ticks'] and os.readlink(f'/proc/{proc.pid}/exe') == ident['exe']:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(20)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(10)
        finally:
            report['server_exit_code'] = proc.poll()
            log.close()
            a.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': a.artifact, 'status': report['status'], 'criteria': report.get('criteria')}))
    sys.exit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
