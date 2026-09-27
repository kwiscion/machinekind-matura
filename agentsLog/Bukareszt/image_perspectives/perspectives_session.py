"""#178 opt-in three-perspective visual strategy vs direct control, on ONE owned llama-server with the SAME weights.

Per item (records from the prepared adapter input: {id, prompt, images[]}):
  1. DIRECT control: the unchanged original prompt plus all original images (a separate call).
  2. Three INDEPENDENT descriptions of the original images (text/inscriptions; small details/symbols/spatial;
     composition/people/events with observation vs inference). Each call sees only the images and its own
     instruction, never the other descriptions and never the question.
  3. FINAL perspective answer: the complete original prompt plus ALL original images plus the three descriptions,
     explicitly marked fallible. The images are never replaced by text.
Descriptions are never exported and never enter any essay cleanup. Optional settings key `view_attempts` gives the
three view calls their own (shorter) ladder; a truncated (`length`) view is preserved as a labelled partial and still
passed, marked fallible, to the final call. Without the key every role uses `attempts` (wave-1 behaviour). Only DIRECT and FINAL answers are exported
(answer-only, per arm). An item without images is recorded as `no_images`, with its final equal to the direct answer
and no extra calls.

The server lifecycle, owned-process identity cleanup, durable reserve-before-dispatch ledger with call/token caps,
per-call 4-attempt recovery ladder and wall-deadline gating are reused from the reviewed eval16_session.py (#117).
usage: perspectives_session.py --prepared P.jsonl --base-dir DIR --ids 6 14.1 ... --settings S.json --model M --mmproj P
       --run RUN --deadline-epoch E [--max-wave-calls 120 --max-wave-tokens N]
"""
import argparse, base64, hashlib, json, mimetypes, os, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path

R = Path('/ephemeral/mm-lora')
SERVER = R / 'src/llama.cpp/build-cuda/bin/llama-server'
PORT = 18117

VIEWS = {
    'text': ('Przepisz dokładnie wszystkie czytelne napisy, teksty, inskrypcje, podpisy, liczby i daty widoczne na załączonych '
             'obrazach, zachowując ich brzmienie i zaznaczając, gdzie się znajdują. Jeśli fragment jest nieczytelny lub niepewny, '
             'napisz [nieczytelne] zamiast zgadywać; niczego nie uzupełniaj. Nie odpowiadaj na żadne pytanie ani zadanie.'),
    'details': ('Opisz drobne szczegóły wizualne załączonych obrazów: symbole, herby, emblematy, flagi, ubiory, przedmioty, '
                'oznaczenia, strzałki, elementy legendy i skali oraz ich wzajemne położenie (co jest gdzie względem czego). '
                'Opisuj wyłącznie to, co widać. Nie odpowiadaj na żadne pytanie ani zadanie.'),
    'context': ('Opisz ogólną kompozycję załączonych obrazów: rodzaj źródła (np. mapa, plakat, fotografia, rycina, wykres), '
                'przedstawione osoby, wydarzenia i sceny oraz możliwy kontekst. Każde zdanie oznacz jako OBSERWACJA '
                '(bezpośrednio widoczne) albo WNIOSEK (twoja interpretacja). Nie odpowiadaj na żadne pytanie ani zadanie.'),
}
VIEW_TITLES = {'text': 'Opis 1: napisy i teksty', 'details': 'Opis 2: szczegóły i położenie',
               'context': 'Opis 3: kompozycja i kontekst'}
FINAL_BLOCK = ('\n\n---\nPOMOCNICZE OPISY OBRAZÓW. Poniżej są trzy niezależne, automatycznie wygenerowane opisy załączonych '
               'obrazów. Mogą zawierać błędy, pominięcia lub zmyślenia: traktuj je wyłącznie jako wskazówki, a w razie '
               'sprzeczności zawsze ufaj samym obrazom i materiałom źródłowym. Odpowiedz na zadanie powyżej w wymaganym '
               'formacie.\n\n{views}\n---')
MISSING_VIEW = '[opis niedostępny]'


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


def image_parts(paths):
    parts = []
    for p in paths:
        mime = mimetypes.guess_type(str(p))[0] or 'image/png'
        parts.append({'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,' + base64.b64encode(Path(p).read_bytes()).decode()}})
    return parts


class Caller:
    """One logical call = up to len(ladder) ledgered attempts; success = HTTP 200, non-empty text, finish 'stop'."""

    def __init__(self, a, settings, ledger):
        self.a, self.s, self.ledger = a, settings, ledger

    def __call__(self, item_id, role, parts):
        attempts, final = [], None
        known_prompt = None
        ladder = self.s['view_attempts'] if role.startswith('view_') and 'view_attempts' in self.s else self.s['attempts']
        for k, step in enumerate(ladder, 1):
            if time.time() + step['request_timeout_s'] > self.a.deadline_epoch:
                attempts.append({'attempt': k, 'skipped': 'wall deadline'}); break
            if step.get('only_if_fits') and known_prompt is not None and known_prompt + step['max_tokens'] > self.s['ctx_size']:
                attempts.append({'attempt': k, 'skipped': 'complete input does not fit context'}); continue
            body = {'messages': [{'role': 'user', 'content': parts}], 'max_tokens': step['max_tokens'],
                    'temperature': self.s['temperature'], 'top_k': self.s['top_k'], 'seed': self.s['seed'],
                    'chat_template_kwargs': {'enable_thinking': self.s['enable_thinking']}}
            n = ledger_reserve(self.ledger, self.a.max_wave_calls, self.a.max_wave_tokens,
                               {'id': item_id, 'role': role, 'attempt': k, 'max_tokens': step['max_tokens']})
            if n is None:
                attempts.append({'attempt': k, 'skipped': 'wave call/token budget'}); break
            rec = {'call_number': n, 'attempt': k, 'max_tokens': step['max_tokens'],
                   'request_sha256': sha_bytes(json.dumps(body, sort_keys=True, ensure_ascii=False).encode())}
            t = time.monotonic()
            try:
                status, raw = http('POST', '/v1/chat/completions', body, timeout=step['request_timeout_s'])
                resp = json.loads(raw)
                ch = resp['choices'][0]
                rec.update(http_status=status, response_sha256=sha_bytes(raw), seconds=round(time.monotonic() - t, 2),
                           finish_reason=ch.get('finish_reason'), text=ch['message'].get('content'),
                           reasoning_chars=len(ch['message'].get('reasoning_content') or ''), usage=resp.get('usage'))
                known_prompt = (resp.get('usage') or {}).get('prompt_tokens', known_prompt)
            except Exception as exc:
                rec.update(error=f'{type(exc).__name__}: {exc}'[:500], seconds=round(time.monotonic() - t, 2))
            append_fsync(self.ledger, {'event': 'result', 'id': item_id, 'role': role, **{x: v for x, v in rec.items() if x != 'text'}})
            attempts.append(rec)
            if rec.get('http_status') == 200 and (rec.get('text') or '').strip() and rec.get('finish_reason') == 'stop':
                final = rec; break
        usable = [x for x in attempts if (x.get('text') or '').strip()]
        if final is not None:
            status, chosen = 'complete', final
        elif usable:
            status, chosen = 'partial', usable[0]  # preserve the earliest usable answer, labelled
        else:
            status, chosen = 'placeholder', None
        return {'role': role, 'status': status, 'text': chosen['text'] if chosen else None,
                'chosen_call_number': chosen['call_number'] if chosen else None, 'attempts': attempts}


def run_item(call, rec, base_dir):
    imgs = [(base_dir / p) for p in rec['images']]
    for p in imgs:
        if not p.is_file():
            raise SystemExit(f'missing image {p}')
    orig = image_parts(imgs) + [{'type': 'text', 'text': rec['prompt']}]
    out = {'id': rec['id'], 'images': [str(p) for p in rec['images']], 'image_sha256': [sha_file(p) for p in imgs]}
    out['direct'] = call(rec['id'], 'direct', orig)
    if not imgs:
        out['mode'] = 'no_images'
        out['views'] = {}
        out['final'] = dict(out['direct'], role='final', copied_from='direct')
        return out
    out['mode'] = 'perspectives'
    out['views'] = {v: call(rec['id'], f'view_{v}', image_parts(imgs) + [{'type': 'text', 'text': VIEWS[v]}]) for v in VIEWS}
    block = '\n\n'.join(f'[{VIEW_TITLES[v]}]\n' + ((out['views'][v]['text'] or '').strip() or MISSING_VIEW) for v in VIEWS)
    final_prompt = rec['prompt'] + FINAL_BLOCK.format(views=block)
    assert rec['prompt'] in final_prompt  # the complete original input is preserved verbatim
    out['final'] = call(rec['id'], 'final', image_parts(imgs) + [{'type': 'text', 'text': final_prompt}])
    out['final_prompt_sha256'] = sha_bytes(final_prompt.encode())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--base-dir', type=Path, required=True, help='directory image paths in the prepared records are relative to')
    ap.add_argument('--ids', nargs='+', required=True)
    ap.add_argument('--settings', type=Path, required=True)
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--mmproj', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--deadline-epoch', type=int, required=True, help='no attempt starts unless its timeout fits before this')
    ap.add_argument('--max-wave-calls', type=int, default=120)
    ap.add_argument('--max-wave-tokens', type=int, required=True)
    ap.add_argument('--expected-template-sha', required=True, help='lexer-normalized served chat template sha256')
    a = ap.parse_args()
    out_path = a.run / 'perspectives-raw.jsonl'
    if out_path.exists() or (a.run / 'ledger.jsonl').exists():
        raise SystemExit('refusing overwrite / stale ledger')

    def _term(*_):
        raise SystemExit('SIGTERM')  # run finally: identity-checked server cleanup
    signal.signal(signal.SIGTERM, _term)
    settings = json.loads(a.settings.read_text())
    recs = {r['id']: r for r in (json.loads(l) for l in a.prepared.read_text(encoding='utf-8').splitlines() if l.strip())}
    missing = [i for i in a.ids if i not in recs]
    if missing:
        raise SystemExit(f'ids not in prepared input: {missing}')
    s = socket.socket()
    try:
        if s.connect_ex(('127.0.0.1', PORT)) == 0:
            raise SystemExit(f'port {PORT} already in use; not adopting a foreign server')
    finally:
        s.close()
    cmd = [str(SERVER), '-m', str(a.model), '--mmproj', str(a.mmproj), '--host', '127.0.0.1', '--port', str(PORT),
           '-ngl', '999', '-c', str(settings['ctx_size']), '-np', '1', '--jinja', '--no-webui',
           '--reasoning', settings['server_reasoning'], '--no-warmup']
    meta = {'prepared_sha256': sha_file(a.prepared), 'ids': a.ids, 'model': str(a.model), 'model_sha256': sha_file(a.model),
            'mmproj_sha256': sha_file(a.mmproj), 'server_binary_sha256': sha_file(SERVER), 'settings_sha256': sha_file(a.settings),
            'session_sha256': sha_file(Path(__file__)), 'server_cmd': cmd}
    log = (a.run / 'server.log').open('wb')
    env = {k: v for k, v in os.environ.items() if not k.startswith('LLAMA_ARG_')}
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)  # same process group, no setsid
    ident = None
    ledger = a.run / 'ledger.jsonl'
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
        if meta['served_chat_template_sha256'] != a.expected_template_sha:
            raise SystemExit('served template differs from the expected pinned template')
        append_fsync(out_path, {'meta': meta})
        call = Caller(a, settings, ledger)
        for iid in a.ids:
            append_fsync(out_path, {'item': run_item(call, recs[iid], a.base_dir)})
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
            append_fsync(out_path, {'end': {'server_exit_code': proc.poll()}})
    items = [json.loads(l)['item'] for l in out_path.read_text(encoding='utf-8').splitlines() if '"item"' in l[:10]]
    for arm in ('direct', 'final'):  # answer-only exports; descriptions are never exported
        with (a.run / f'answers-{"direct" if arm == "direct" else "perspectives"}.jsonl').open('x', encoding='utf-8') as f:
            for it in items:
                r = it[arm]
                f.write(json.dumps({'id': it['id'], 'answer': r['text'] if r['status'] != 'placeholder' else '',
                                    'status': r['status']}, ensure_ascii=False) + '\n')
    counts = {arm: {st: sum(1 for it in items if it[arm]['status'] == st) for st in ('complete', 'partial', 'placeholder')} for arm in ('direct', 'final')}
    status = 'PASS' if len(items) == len(a.ids) else 'FAIL'
    print(json.dumps({'status': status, 'items': len(items), 'counts': counts}))
    sys.exit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
