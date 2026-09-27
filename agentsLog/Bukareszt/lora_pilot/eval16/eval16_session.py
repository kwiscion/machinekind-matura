"""One owned llama-server session answering the 16 frozen eval16 inputs for ONE arm (derived from the reviewed serve_session.py).

Same server lifecycle as the pilot: a Popen child in the operator's process group (no setsid), SIGTERM raises
SystemExit so `finally` kills only the identity-checked owned server, and cleanup waits 3 s then KILL, inside the
--kill-after grace. Every call is reserved in the durable wave ledger (fsync) BEFORE dispatch. The wave cap is
--max-wave-calls; there are no retries and no warmups (--no-warmup). Per-request timeout comes from --request-timeout.
Recovery (root declaration #117 23:22Z/23:23Z): per item up to 4 attempts = initial + 3 retries (32768 -> 49152 only if the complete input fits -> 32768 -> 32768 bounded
final-answer synthesis with the original input plus the longest preserved draft, explicitly marked fallible),
retrying only on error/timeout/empty/length; earlier usable answers are preserved; all-failed items get an explicit placeholder label.
Calls and requested tokens are capped per wave in the durable ledger; no attempt starts unless its timeout fits the arm deadline.

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
SYNTH_SUFFIX = ('\n\n---\nPoniżej znajduje się wcześniejszy, niekompletny szkic odpowiedzi. Może zawierać błędy: traktuj go ostrożnie '
                'i weryfikuj fakty.\n\n[SZKIC]\n{draft}\n[/SZKIC]\n\nNapisz teraz jedno kompletne, finalne wypracowanie (400–500 słów) '
                'na jeden wybrany temat, bez komentarzy wstępnych.')
SYNTH_DRAFT_MAX_CHARS = 12000
NORMALIZED_TEMPLATE_SHA = '6a1015c47ccfcfa67c3b772385bccee357a4d37c3cda37bd202e9047f391ab82'  # pinned HF template as served (lexer-normalized)


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ledger_reserve(ledger, cap, token_cap, entry):
    rows = [json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    reserved = [r for r in rows if r['event'] == 'reserved']
    tokens = sum(r.get('max_tokens', 0) for r in reserved)
    if len(reserved) >= cap or tokens + entry['max_tokens'] > token_cap:
        return None  # budget exhausted: caller records it, never dispatches
    rec = {'event': 'reserved', 'call_number': len(reserved) + 1, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **entry}
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
    ap.add_argument('--max-wave-tokens', type=int, required=True)
    ap.add_argument('--arm-deadline-epoch', type=int, required=True, help='no attempt starts unless its timeout fits before this')
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
            attempts, final = [], None
            for k, step in enumerate(arm_cfg['attempts'], 1):
                if time.time() + step['request_timeout_s'] > a.arm_deadline_epoch:
                    attempts.append({'attempt': k, 'skipped': 'arm wall budget'}); break
                known_prompt = max([x['usage']['prompt_tokens'] for x in attempts if (x.get('usage') or {}).get('prompt_tokens')] or [len(row['prompt']) // 2])
                if step.get('only_if_fits') and known_prompt + step['max_tokens'] > settings['ctx_size']:
                    attempts.append({'attempt': k, 'skipped': 'complete input does not fit context'}); continue
                content = row['prompt']
                if step.get('synthesis'):  # bounded final-answer synthesis: original input + longest preserved draft, marked fallible
                    drafts = sorted((x.get('text') or '' for x in attempts), key=len, reverse=True)
                    if drafts and drafts[0].strip():
                        content = row['prompt'] + SYNTH_SUFFIX.format(draft=drafts[0][:SYNTH_DRAFT_MAX_CHARS])
                body = {'messages': [{'role': 'user', 'content': content}], 'max_tokens': step['max_tokens'],
                        'temperature': settings['temperature'], 'top_k': settings['top_k'], 'seed': settings['seed'],
                        'chat_template_kwargs': {'enable_thinking': step['enable_thinking']}}
                n = ledger_reserve(ledger, a.max_wave_calls, a.max_wave_tokens, {'arm': a.arm, 'id': row['id'], 'attempt': k, 'max_tokens': step['max_tokens']})
                if n is None:
                    attempts.append({'attempt': k, 'skipped': 'wave call/token budget'}); break
                rec = {'call_number': n, 'attempt': k, 'max_tokens': step['max_tokens'], 'synthesis_with_draft': content != row['prompt'], 'request_sha256': sha_bytes(json.dumps(body, sort_keys=True).encode())}
                t = time.monotonic()
                try:
                    status, raw = http('POST', '/v1/chat/completions', body, timeout=step['request_timeout_s'])
                    resp = json.loads(raw)
                    ch = resp['choices'][0]
                    rec.update(http_status=status, response_sha256=sha_bytes(raw), seconds=round(time.monotonic() - t, 2),
                               finish_reason=ch.get('finish_reason'), text=ch['message'].get('content'),
                               reasoning_chars=len(ch['message'].get('reasoning_content') or ''), usage=resp.get('usage'))
                except Exception as exc:
                    rec.update(error=f'{type(exc).__name__}: {exc}'[:500], seconds=round(time.monotonic() - t, 2))
                append_fsync(ledger, {'event': 'result', 'arm': a.arm, 'id': row['id'], **{k2: v for k2, v in rec.items() if k2 != 'text'}})
                attempts.append(rec)
                if rec.get('http_status') == 200 and (rec.get('text') or '').strip() and rec.get('finish_reason') == 'stop':
                    final = rec; break
            usable = [x for x in attempts if (x.get('text') or '').strip()]
            if final is not None:
                fstatus, chosen = 'complete', final
            elif usable:  # preserve the earliest usable (e.g. length-truncated) answer; counted separately
                fstatus, chosen = 'partial', usable[0]
            else:
                fstatus, chosen = 'placeholder', None
            append_fsync(a.out, {'item': True, 'arm': a.arm, 'id': row['id'], 'final_status': fstatus,
                                 'text': chosen['text'] if chosen else '[PLACEHOLDER: no usable answer after recovery attempts]',
                                 'finish_reason': chosen.get('finish_reason') if chosen else None,
                                 'chosen_call_number': chosen['call_number'] if chosen else None, 'attempts': attempts})
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
    items = [r for r in done if r.get('item')]
    counts = {k: sum(1 for r in items if r['final_status'] == k) for k in ('complete', 'partial', 'placeholder')}
    status = 'PASS' if len(items) == 16 else 'FAIL'  # partial/placeholder items are recorded and counted, not hidden
    print(json.dumps({'arm': a.arm, 'status': status, 'items': len(items), **counts}))
    sys.exit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
