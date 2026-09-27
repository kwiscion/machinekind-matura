"""Read-only IDF query selection and bounded complementary-passage retrieval."""
import argparse,json,math,re,sqlite3,time
from collections import Counter
from pathlib import Path
from wiki_index import norm,STOP

GENERIC=set('odpowiedz odpowiedzi zadanie wskaz podaj uzasadnij wyjasnij zrodla zrodlo przedstaw temat tekstu informacji podstawie rozstrzygnij ocen wybierz zapisz polecenie'.split())

def query_from_item(item):
    """Exclude organizer/global instructions and format; preserve model input elsewhere."""
    question=item['question'];source=item.get('source_text','')
    assert isinstance(question,str) and isinstance(source,str)
    source='\n'.join(line for line in source.splitlines()
        if not re.match(r'^\s*(?:na podstawie\b|źródło\s*(?:\d|:)|zrodlo\s*(?:\d|:)|https?://|www\.)',line,re.I)
        and not (re.search(r'\b(?:1[5-9]|20)\d{2}\b',line) and re.search(r'\b(?:s|ss|str)\.\s*\d',line)))
    return question,source

def tokens(text):
    return list(dict.fromkeys(t for t in re.findall(r'\w+',norm(text)) if len(t)>2 and t not in STOP|GENERIC))

def prefix(term):
    for suffix in ('owego','owej','owych','ami','ach','owie','emu','em','im','ym','om','a','u','e','y','i'):
        if term.endswith(suffix) and len(term)-len(suffix)>=5:return term[:-len(suffix)]
    return None

def select_terms(db,question,source,total):
    db.execute("CREATE VIRTUAL TABLE temp.vocab USING fts5vocab(main,'search','row')")
    primary=set(tokens(question));all_terms=list(dict.fromkeys([*tokens(question),*tokens(source)]));freq={}
    for start in range(0,len(all_terms),300):
        batch=all_terms[start:start+300]
        freq.update(db.execute('SELECT term,doc FROM temp.vocab WHERE term IN ('+','.join('?'*len(batch))+')',batch).fetchall())
    ranked=[(math.log(1+total/(freq[t]+1))*(1.4 if t in primary else 1),t) for t in all_terms if t in freq]
    ranked.sort(key=lambda x:(-x[0],x[1]));chosen=ranked[:16]
    # Bounded inflection recall, not a claim of linguistic stemming. Unknown task
    # terms receive prefix recall too, so suffix variation does not erase entities.
    pref=[]
    for t in [*(t for _,t in chosen if t in primary),*(t for t in tokens(question) if t not in freq)]:
        stem=prefix(t)
        if stem and stem not in pref:pref.append(stem)
        if len(pref)==8:break
    return chosen,pref

def overlaps(a,b):
    if a['article_id']!=b['article_id']:return False
    common=max(0,min(a['end'],b['end'])-max(a['start'],b['start']))
    return common/max(1,min(a['end']-a['start'],b['end']-b['start']))>=.5 or norm(a['text'])==norm(b['text'])

def retrieve(path,question,source='',k=5,seconds=20):
    began=time.monotonic();db=sqlite3.connect(f'file:{path.resolve()}?mode=ro',uri=True)
    db.set_progress_handler(lambda:int(time.monotonic()-began>seconds),10000)
    report=path.parent/'index-report.json'
    total=json.loads(report.read_text())['passages'] if report.exists() else db.execute('SELECT count(*) FROM passages').fetchone()[0]
    ranked,pref=select_terms(db,question,source,total)
    parts=['"'+t+'"' for _,t in ranked]+['"'+t+'"*' for t in pref]
    if not parts:db.close();return {'passages':[],'terms':[],'prefixes':pref,'seconds':time.monotonic()-began}
    db.row_factory=sqlite3.Row
    rows=db.execute('SELECT p.*,bm25(search,4.0,1.0) AS bm25 FROM search JOIN passages p ON p.id=search.rowid WHERE search MATCH ? ORDER BY bm25 LIMIT 200',(' OR '.join(parts),)).fetchall()
    candidates=[]
    primary=set(tokens(question))
    primary_weights=[(weight,term) for weight,term in ranked if term in primary]
    source_weights=[(weight,term) for weight,term in ranked if term not in primary]
    known={term for _,term in primary_weights}
    for term in sorted(primary-known):
        if prefix(term) in pref:primary_weights.append((max((w for w,_ in ranked),default=1),term))
    for row in rows:
        item=dict(row);body=set(re.findall(r'\w+',item['norm_text']));title=set(re.findall(r'\w+',item['norm_title']))
        def coverage(group):
            score=0
            for weight,term in group:
                stem=prefix(term)
                in_body=term in body or (stem in pref and any(t.startswith(stem) for t in body))
                in_title=term in title or (stem in pref and any(t.startswith(stem) for t in title))
                score+=weight*(in_body+2*in_title)
            return score
        # A generic task noun must not outweigh several informative source terms.
        # The bounded1.4 task preference is already included in IDF weights.
        item['support_score']=coverage(primary_weights)+coverage(source_weights)
        candidates.append(item)
    candidates.sort(key=lambda x:(-x['support_score'],x['bm25'],x['id']))
    result=[];counts=Counter()
    for item in candidates:
        if counts[item['article_id']]>=3 or any(overlaps(item,x) for x in result):continue
        result.append({key:value for key,value in item.items() if not key.startswith('norm_')});counts[item['article_id']]+=1
        if len(result)>=k:break
    db.close();return {'passages':result,'terms':[{'term':t,'weight':w} for w,t in ranked],'prefixes':pref,'seconds':time.monotonic()-began}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('index',type=Path);p.add_argument('--query',required=True);a=p.parse_args()
    print(json.dumps(retrieve(a.index,a.query),ensure_ascii=False,indent=2))
