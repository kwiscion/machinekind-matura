"""Focused CPU test for perspectives_session.py with a fake OpenAI-compatible server (no model, no GPU; Linux /proc).

Asserts: 5 calls per image item in order direct -> 3 views -> final; each view request holds ONLY the images and its own
instruction (no question text, no other view); the direct request equals the original prompt plus images; the final
request holds the complete original prompt verbatim, ALL images and all three view texts marked fallible; an item
without images makes 1 call with the final copied from direct; a failing view becomes a labelled placeholder that the
final still survives; exports contain only direct/final answers (never view text); caps; owned-server cleanup.
usage: python3 test_perspectives.py SESSION.py WORKDIR
"""
import base64, importlib.util, json, struct, subprocess, sys, time, zlib
from pathlib import Path

FAKE = r'''
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
port = int(sys.argv[sys.argv.index('--port') + 1]); log = sys.argv[sys.argv.index('--reqlog') + 1]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        self._send(200, {'status': 'ok'} if self.path == '/health' else {'chat_template': 'TEMPLATE'})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        open(log, 'a').write(json.dumps(body) + '\n')
        parts = body['messages'][0]['content']; text = [p['text'] for p in parts if p['type'] == 'text'][0]
        if text.startswith('Opisz drobne'):  # every details view fails -> placeholder path
            return self._send(500, {'error': 'x'})
        if text.startswith('Przepisz'): out = 'VIEWTEXT-A'
        elif text.startswith('Opisz drobne'): out = 'VIEWTEXT-B'
        elif text.startswith('Opisz ogólną'): out = 'VIEWTEXT-C'
        elif 'POMOCNICZE OPISY' in text: out = 'FINAL-ANSWER'
        else: out = 'DIRECT-ANSWER'
        self._send(200, {'choices': [{'finish_reason': 'stop', 'message': {'content': out}}], 'usage': {'prompt_tokens': 50, 'completion_tokens': 3}})
HTTPServer(('127.0.0.1', port), H).serve_forever()
'''


def png():
    raw = b'\x00' + b'\xff\x00\x00' * 4
    raw = raw * 4
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', 4, 4, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b'')


def main():
    sess, work = Path(sys.argv[1]), Path(sys.argv[2]); work.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('s', sess); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    (work / 'img').mkdir(); (work / 'img/a.png').write_bytes(png()); (work / 'img/b.png').write_bytes(png()[:-12] + png()[-12:])
    recs = [{'id': 'X1', 'prompt': 'PYTANIE-X1 BADVIEW treść zadania', 'images': ['img/a.png', 'img/b.png']},
            {'id': 'X2', 'prompt': 'PYTANIE-X2 tylko tekst', 'images': []},
            {'id': 'X3', 'prompt': 'PYTANIE-X3 z obrazem', 'images': ['img/a.png']}]
    prep = work / 'prepared.jsonl'; prep.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in recs))
    fake = work / 'fake.py'; fake.write_text(FAKE); reqlog = work / 'requests.jsonl'
    st = work / 'settings.json'
    st.write_text(json.dumps({'temperature': 0.0, 'top_k': 1, 'seed': 42, 'enable_thinking': False, 'server_reasoning': 'off', 'ctx_size': 65536,
                              'attempts': [{'max_tokens': 32768, 'request_timeout_s': 5}, {'max_tokens': 49152, 'request_timeout_s': 5, 'only_if_fits': True},
                                           {'max_tokens': 32768, 'request_timeout_s': 5}, {'max_tokens': 32768, 'request_timeout_s': 5}]}))
    m.SERVER = Path(sys.executable).resolve(); m.PORT = 18998
    real = subprocess.Popen
    m.subprocess.Popen = lambda cmd, **kw: real([sys.executable, str(fake), *cmd[1:], '--reqlog', str(reqlog)], **kw)
    run = work / 'run'; run.mkdir()
    sys.argv = ['x', '--prepared', str(prep), '--base-dir', str(work), '--ids', 'X1', 'X2', 'X3', '--settings', str(st),
                '--model', str(st), '--mmproj', str(st), '--run', str(run), '--deadline-epoch', str(int(time.time()) + 600),
                '--max-wave-calls', '120', '--max-wave-tokens', '4423680', '--expected-template-sha', m.sha_bytes(b'TEMPLATE')]
    try:
        m.main()
    except SystemExit as e:
        rc = e.code
    reqs = [json.loads(l) for l in reqlog.read_text().splitlines()]
    texts = [[p['text'] for p in r['messages'][0]['content'] if p['type'] == 'text'][0] for r in reqs]
    nimg = [sum(1 for p in r['messages'][0]['content'] if p['type'] == 'image_url') for r in reqs]
    raw = [json.loads(l) for l in (run / 'perspectives-raw.jsonl').read_text().splitlines()]
    items = {r['item']['id']: r['item'] for r in raw if 'item' in r}
    ad = [json.loads(l) for l in (run / 'answers-direct.jsonl').read_text().splitlines()]
    ap = [json.loads(l) for l in (run / 'answers-perspectives.jsonl').read_text().splitlines()]
    x1 = [t for t in texts if 'X1' in t or t.startswith(('Przepisz', 'Opisz'))][:8]
    view_texts = [t for t in texts if t.startswith(('Przepisz', 'Opisz'))]
    checks = {
        'rc0': rc == 0,
        'call_order_X1': texts[0] == recs[0]['prompt'] and texts[1].startswith('Przepisz') and all(t.startswith('Opisz drobne') for t in texts[2:6]) and texts[6].startswith('Opisz ogólną') and 'POMOCNICZE OPISY' in texts[7],
        'direct_is_original_prompt_all_images': texts[0] == recs[0]['prompt'] and nimg[0] == 2,
        'views_see_no_question_no_other_view': all('PYTANIE' not in t and 'VIEWTEXT' not in t for t in view_texts),
        'views_get_all_item_images': nimg[1:7] == [2] * 6 and nimg[-4:-1] == [1, 1, 1] and all(n > 0 for t, n in zip(texts, nimg) if t.startswith(('Przepisz', 'Opisz'))),
        'final_has_complete_prompt_images_views': any(t.startswith(recs[0]['prompt']) and 'VIEWTEXT-A' in t and 'VIEWTEXT-C' in t and 'Mogą zawierać błędy' in t and n == 2 for t, n in zip(texts, nimg)),
        'failed_view_is_placeholder_and_marked_missing': items['X1']['views']['details']['status'] == 'placeholder' and len(items['X1']['views']['details']['attempts']) == 4 and any('[opis niedostępny]' in t for t in texts),
        'final_complete_despite_failed_view': items['X1']['final']['status'] == 'complete' and items['X1']['final']['text'] == 'FINAL-ANSWER',
        'no_image_item_one_call_final_copied': items['X2']['mode'] == 'no_images' and sum(1 for t in texts if 'PYTANIE-X2' in t) == 1 and items['X2']['final']['text'] == 'DIRECT-ANSWER',
        'image_item_five_calls': sum(1 for t in texts if 'PYTANIE-X3' in t) == 2 and items['X3']['mode'] == 'perspectives',
        'exports_only_direct_final': [r['answer'] for r in ad] == ['DIRECT-ANSWER'] * 3 and [r['answer'] for r in ap] == ['FINAL-ANSWER', 'DIRECT-ANSWER', 'FINAL-ANSWER'] and not any('VIEWTEXT' in json.dumps(r) for r in ad + ap),
        'ledger_reserve_before_result': (lambda L: all(L[i]['event'] == 'reserved' and L[i + 1]['event'] == 'result' for i in range(0, len(L), 2)))([json.loads(l) for l in (run / 'ledger.jsonl').read_text().splitlines()]),
        'server_cleaned_up': raw[-1].get('end', {}).get('server_exit_code') is not None,
    }
    checks['total_requests'] = len(reqs) == 8 + 1 + 8  # X1/X3: direct + text + details(4 failing attempts) + context + final; X2: direct only
    print(json.dumps({'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks, 'requests': len(reqs), 'session_sha256': m.sha_file(sess)}, indent=1))
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
