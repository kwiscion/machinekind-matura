"""One owned llama-server session answering the 16 frozen eval16 inputs for ONE arm (derived from the reviewed serve_session.py).

Same server lifecycle as the pilot: a Popen child in the operator's process group (no setsid), SIGTERM raises
SystemExit so `finally` kills only the identity-checked owned server, and cleanup waits 3 s then KILL, inside the
--kill-after grace. Every call is reserved in the durable wave ledger (fsync) BEFORE dispatch. The wave cap is
--max-wave-calls; there are no retries and no warmups (--no-warmup). Per-request timeout comes from --request-timeout.
A truncated or failed call is recorded as-is and never repeated.

Arms: A = unchanged export control, B = run3 merged candidate. Both use the identical nonthinking request/settings.
Optional arm C = unchanged export with native thinking (--reasoning on, enable_thinking=true, larger cap).
usage: eval16_session.py --arm A|B|C --model M.gguf --mmproj P.gguf --inputs eval16_input.jsonl --settings SETTINGS.json --run RUN --out ANSWERS.jsonl
"""
import argparse, hashlib, json, os, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path

R = Path('/ephemeral/mm-lora')
SERVER = R / 'src/llama.cpp/build-cuda/bin/llama-server'
PORT = 18117
INPUT_SHA = '5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28'
NORMALIZED_TEMPLATE_SHA = '6a1015c47ccfcfa67c3b772385bccee357a4d37c3cda37bd202e9047f391ab82'  # pinned HF template as served (lexer-normalized)


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ledger_reserve(ledger, cap, entry):
    rows = [json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    reserved = sum(1 for r in rows if r['event'] == 'reserved')
    if reserved >= cap:
        raise SystemExit(f'ledger: {reserved} calls already reserved (cap {cap}); refusing')
    rec = {'event': 'reserved', 'call_number': reserved + 1, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **entry}
    with ledger.open('a') as f:
        f.write(json.dumps(rec) + '\n'); f.flush(); os.fsync(f.fileno())
    return rec['call_number']


def append_fsync(path, rec):
    with path.open('a') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())


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
    ap.add_argument('--arm', choices=('A', 'B', 'C'), required=True)
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--mmproj', type=Path, required=True)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--settings', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--max-wave-calls', type=int, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit('refusing overwrite')

    def _term(*_):
        raise SystemExit('SIGTERM')  # run finally: identity-checked server cleanup
    signal.signal(signal.SIGTERM, _term)
    if sha_file(a.inputs) != INPUT_SHA:
        raise SystemExit('eval16 input hash mismatch')
    settings = json.loads(a.settings.read_text())
    arm_cfg = settings['arms'][a.arm]
    rows = [json.loads(l) for l in a.inputs.read_text(encoding='utf-8').splitlines() if l.strip()]
    if len(rows) != 16:
        raise SystemExit('expected 16 inputs')
    ledger = a.run / 'call-ledger.jsonl'
    s = socket.socket()
    try:
        if s.connect_ex(('127.0.0.1', PORT)) == 0:
            raise SystemExit(f'port {PORT} already in use; not adopting a foreign server')
    finally:
        s.close()
    cmd = [str(SERVER), '-m', str(a.model), '--mmproj', str(a.mmproj), '--host', '127.0.0.1', '--port', str(PORT),
           '-ngl', '999', '-c', str(settings['ctx_size']), '-np', '1', '--jinja', '--no-webui',
           '--reasoning', arm_cfg['server_reasoning'], '--no-warmup']
    meta = {'arm': a.arm, 'model': str(a.model), 'model_sha256': sha_file(a.model), 'mmproj_sha256': sha_file(a.mmproj),
            'server_binary_sha256': sha_file(SERVER), 'settings_sha256': sha_file(a.settings), 'inputs_sha256': INPUT_SHA, 'server_cmd': cmd}
    log = (a.run / f'server-arm{a.arm}.log').open('wb')
    env = {k: v for k, v in os.environ.items() if not k.startswith('LLAMA_ARG_')}
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)  # same process group, no setsid
    ident = None
    try:
        ident = {'pid': proc.pid, 'start_ticks': start_ticks(proc.pid), 'exe': os.readlink(f'/proc/{proc.pid}/exe')}
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
        props = json.loads(http('GET', '/props', timeout=10)[1])
        meta.update(load_seconds=round(time.monotonic() - t0, 1), server_identity=ident,
                    served_chat_template_sha256=sha_bytes(props.get('chat_template', '').encode()))
        if meta['served_chat_template_sha256'] != NORMALIZED_TEMPLATE_SHA:
            raise SystemExit('served template is not the pinned template')
        append_fsync(a.out, {'meta': meta})
        for row in rows:
            body = {'messages': [{'role': 'user', 'content': row['prompt']}], 'max_tokens': arm_cfg['max_tokens'],
                    'temperature': settings['temperature'], 'top_k': settings['top_k'], 'seed': settings['seed'],
                    'chat_template_kwargs': {'enable_thinking': arm_cfg['enable_thinking']}}
            n = ledger_reserve(ledger, a.max_wave_calls, {'arm': a.arm, 'id': row['id'], 'max_tokens': arm_cfg['max_tokens']})
            rec = {'call_number': n, 'arm': a.arm, 'id': row['id'], 'request_sha256': sha_bytes(json.dumps(body, sort_keys=True).encode())}
            t = time.monotonic()
            try:
                status, raw = http('POST', '/v1/chat/completions', body, timeout=arm_cfg['request_timeout_s'])
                resp = json.loads(raw)
                ch = resp['choices'][0]
                rec.update(http_status=status, response_sha256=sha_bytes(raw), seconds=round(time.monotonic() - t, 2),
                           finish_reason=ch.get('finish_reason'), text=ch['message'].get('content'),
                           reasoning_chars=len(ch['message'].get('reasoning_content') or ''), usage=resp.get('usage'))
            except Exception as exc:
                rec.update(error=f'{type(exc).__name__}: {exc}'[:500], seconds=round(time.monotonic() - t, 2))
            append_fsync(ledger, {'event': 'result', **{k: v for k, v in rec.items() if k != 'text'}})
            append_fsync(a.out, rec)
    finally:
        try:
            if proc.poll() is None and (ident is None or (start_ticks(proc.pid) == ident['start_ticks'] and os.readlink(f'/proc/{proc.pid}/exe') == ident['exe'])):
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(3)  # KILL escalation stays inside the 10 s --kill-after grace
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(10)
        finally:
            log.close()
            append_fsync(a.out, {'end': {'server_exit_code': proc.poll()}})
    done = [json.loads(l) for l in a.out.read_text().splitlines()]
    calls = [r for r in done if 'call_number' in r]
    ok = sum(1 for r in calls if r.get('http_status') == 200 and r.get('text'))
    print(json.dumps({'arm': a.arm, 'calls': len(calls), 'ok': ok, 'length_truncated': sum(1 for r in calls if r.get('finish_reason') == 'length')}))
    sys.exit(0 if len(calls) == 16 else 1)


if __name__ == '__main__':
    main()
