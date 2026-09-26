"""Acquire a fixed list of independent curriculum references; no benchmark access."""
import hashlib, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ('augustus', 'Augustus', 'history-augustan-principate'),
    ('investiture', 'Investiture_Controversy', 'history-investiture-controversy'),
    ('augsburg', 'Peace_of_Augsburg', 'history-augsburg-confessional-settlement'),
    ('vienna', 'Congress_of_Vienna', 'history-vienna-settlement'),
    ('industrial', 'Industrial_Revolution', 'history-industrial-revolution-britain'),
    ('meiji', 'Meiji_Restoration', 'history-meiji-restoration'),
    ('league', 'League_of_Nations', 'history-league-collective-security'),
    ('marshall', 'Marshall_Plan', 'history-marshall-plan'),
]

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.ignore=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.ignore += 1
        if tag in ('p','h2','h3','li'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.ignore=max(0,self.ignore-1)
        if tag in ('p','h2','h3','li'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.ignore: self.parts.append(data)

def main():
    out=ROOT/'source-private'; out.mkdir(exist_ok=True)
    rows=[]
    for key,title,group in SOURCES:
        url='https://en.wikipedia.org/wiki/'+title
        req=urllib.request.Request(url,headers={'User-Agent':'MaturaSourceBlindCorpus/1.0 attribution audit'})
        with urllib.request.urlopen(req, timeout=40) as response: raw=response.read()
        (out/(key+'.html')).write_bytes(raw)
        html=raw.decode('utf-8'); parser=Text(); parser.feed(html)
        text='\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
        (out/(key+'.txt')).write_text(text,encoding='utf-8')
        m=re.search(r'"wgRevisionId"\s*:\s*(\d+)',html) or re.search(r'oldid=(\d+)',html)
        revision=m.group(1) if m else None
        rows.append(dict(source_id='wiki-'+key,source_group_id=group,url=url,title=title.replace('_',' '),publisher='Wikipedia contributors; Wikimedia Foundation host',retrieved_at=datetime.now(timezone.utc).isoformat(),revision_id=revision,revision_or_sha256='sha256:'+hashlib.sha256(raw).hexdigest(),permalink=f'https://en.wikipedia.org/w/index.php?title={title}&oldid={revision}' if revision else None,license='CC-BY-SA-4.0 article text; separately credited material excluded',license_url='https://creativecommons.org/licenses/by-sa/4.0/',attribution='Wikipedia contributors, '+title.replace('_',' '),history_url=f'https://en.wikipedia.org/w/index.php?title={title}&action=history',allowed_use=['reference','training only after independent review and final rights/export check'],local_path='source-private/'+key+'.html',text_sha256=hashlib.sha256(text.encode()).hexdigest(),license_footer_present='creativecommons.org/licenses/by-sa/4.0' in html,notes='HTML and derived text remain ignored. No images or quoted third-party passages used. Original Polish synthesis; conservative proposed downstream attribution and share-alike treatment pending final export review.'))
        rows[-1]['text_sha256_convention']='SHA256 of UTF-8 decoded text after Python universal-newline normalization to LF; not the on-disk CRLF bytes'
        rows[-1]['text_file_sha256']=hashlib.sha256((out/(key+'.txt')).read_bytes()).hexdigest()
        print(key,revision,flush=True)
    (ROOT/'sources.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

if __name__=='__main__': main()
