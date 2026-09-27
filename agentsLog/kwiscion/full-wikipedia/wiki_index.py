"""Pinned full-snapshot download and disk-backed passage search; no model calls."""
import argparse, concurrent.futures, hashlib, json, re, sqlite3, time, unicodedata
import urllib.request
from pathlib import Path

REVISION = 'b04c8d1ceb2f5cd4588862100d08de323dccfbaa'
SHARDS = [
 (430727499,'e138c56e16acc8724e851c206f2b2f586e3cdf511105b1d8a81d90b6d374248c'),
 (339031459,'772b50aff9ff58ea037955325573c92c0e811e44ca38d72d3570c2f616f9b37e'),
 (273564143,'a6c4181c7446328a44aaf06d5ebaf086726a537a75cf448ad435105d0ab748c3'),
 (247648622,'6cd8e26a8502b5195dae7dd019006becccc5da17c73852f569972d2dc519fee5'),
 (243412529,'68ad1daa29e28c5f9b3cdf60d3910d63136b36a0fe45ad97ceb2d2ce348211d8'),
 (230675734,'298e4a6e137187f2024af78a6c4fa770add505e519280583f7e2d2cec8a26f62')]
STOP = set('a aby ale albo by byl byla bylo byli byc co czy dla do gdy i ich jako jak jest juz ktora ktore ktory na nad nie o od oraz po pod przez przy sie sa te ten to w we z za ze zezwzgleduna'.split())

def norm(text):
    text = text.casefold().replace('ł','l')
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))

def chunks(text, maximum=1600, overlap=200):
    """Exact source spans, paragraph-preferred boundaries, no dropped characters."""
    start = 0
    while start < len(text):
        end = min(len(text), start + maximum)
        if end < len(text):
            boundary = max(text.rfind('\n', start + maximum//2, end), text.rfind(' ', start + maximum//2, end))
            if boundary > start: end = boundary + 1
        yield start, end, text[start:end]
        if end == len(text): break
        start = max(start + 1, end - overlap)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def download(root):
    root.mkdir(parents=True, exist_ok=False)
    manifest={'dataset':'wikimedia/wikipedia','configuration':'20231101.pl','revision':REVISION,
              'snapshot_date':'2023-11-01','license':['CC-BY-SA-3.0','GFDL'],
              'source':'https://huggingface.co/datasets/wikimedia/wikipedia','files':[]}
    for i,(size,sha) in enumerate(SHARDS):
        name=f'train-{i:05d}-of-00006.parquet'
        manifest['files'].append({'name':name,'bytes':size,'sha256':sha,
            'url':f'https://huggingface.co/datasets/wikimedia/wikipedia/resolve/{REVISION}/20231101.pl/{name}'})
    (root/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    def one(row):
        path=root/row['name'];temporary=path.with_suffix('.partial')
        with urllib.request.urlopen(row['url'],timeout=900) as src,temporary.open('xb') as out:
            while block:=src.read(8*1024*1024):out.write(block)
        assert temporary.stat().st_size==row['bytes'] and digest(temporary)==row['sha256'],'Shard pin mismatch'
        temporary.rename(path);print(json.dumps({'downloaded':row['name'],'bytes':row['bytes']}),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,manifest['files']))
    return manifest

def schema(db):
    db.executescript("""PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-131072;
    CREATE TABLE articles(article_id TEXT PRIMARY KEY,title TEXT,url TEXT,text_sha256 TEXT,characters INTEGER,passages INTEGER);
    CREATE TABLE passages(id INTEGER PRIMARY KEY,article_id TEXT,title TEXT,url TEXT,start INTEGER,end INTEGER,text TEXT,norm_title TEXT,norm_text TEXT);
    CREATE VIRTUAL TABLE search USING fts5(norm_title,norm_text,content='passages',content_rowid='id',tokenize='unicode61 remove_diacritics 2');
    """)

def add_article(db,row):
    text=row['text'];title=row['title'];aid=str(row['id']);url=row['url']
    assert all(isinstance(x,str) for x in (text,title,url)) and aid and url,'Malformed article'
    spans=list(chunks(text))
    db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?)',(aid,title,url,hashlib.sha256(text.encode()).hexdigest(),len(text),len(spans)))
    for start,end,part in spans:
        nt,np=norm(title),norm(part)
        cursor=db.execute('INSERT INTO passages(article_id,title,url,start,end,text,norm_title,norm_text) VALUES(?,?,?,?,?,?,?,?)',
                          (aid,title,url,start,end,part,nt,np))
        db.execute('INSERT INTO search(rowid,norm_title,norm_text) VALUES(?,?,?)',(cursor.lastrowid,nt,np))
    return len(spans)

def build(root):
    import pyarrow.parquet as pq
    manifest=json.loads((root/'source-manifest.json').read_text());assert manifest['revision']==REVISION
    path=root/'passages.sqlite';assert not path.exists();db=sqlite3.connect(path);schema(db)
    total=passages=empty=0;parts=[];began=time.time()
    for i,row in enumerate(manifest['files']):
        file=root/row['name'];assert file.stat().st_size==SHARDS[i][0] and digest(file)==SHARDS[i][1]
        parquet=pq.ParquetFile(file);expected=parquet.metadata.num_rows;actual=0
        for batch in parquet.iter_batches(batch_size=256,columns=['id','url','title','text']):
            with db:
                for article in batch.to_pylist():
                    count=add_article(db,article);passages+=count;empty+=count==0;actual+=1;total+=1
            if total%25600==0:print(json.dumps({'articles':total,'passages':passages,'seconds':time.time()-began}),flush=True)
            assert path.stat().st_size < 95_000_000_000,'Disk envelope'
        assert actual==expected;parts.append({'file':row['name'],'expected_rows':expected,'indexed_rows':actual})
    db.execute("INSERT INTO search(search) VALUES('optimize')");db.commit();db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    assert db.execute('SELECT count(*) FROM articles').fetchone()[0]==total
    assert db.execute('SELECT count(*) FROM passages').fetchone()[0]==passages
    db.close()
    report={'status':'COMPLETE','revision':REVISION,'articles':total,'passages':passages,'empty_articles':empty,
            'excluded_articles':0,'shards':parts,'sqlite_bytes':path.stat().st_size,'sqlite_sha256':digest(path),'seconds':time.time()-began}
    (root/'index-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)

def search(path,query,k=5):
    terms=list(dict.fromkeys(t for t in re.findall(r'\w+',norm(query)) if t not in STOP and len(t)>2))[:32]
    if not terms:return []
    # Bounded OR recall, then exact normalized term coverage rerank; no answer/keys.
    match=' OR '.join('"'+t+'"' for t in terms)
    db=sqlite3.connect(f'file:{path.resolve()}?mode=ro',uri=True);db.row_factory=sqlite3.Row
    rows=db.execute('SELECT p.*,bm25(search,4.0,1.0) AS score FROM search JOIN passages p ON p.id=search.rowid WHERE search MATCH ? ORDER BY score LIMIT 100',(match,)).fetchall()
    candidates=[]
    for row in rows:
        item=dict(row);words=set(re.findall(r'\w+',item['norm_text']));tw=set(re.findall(r'\w+',item['norm_title']))
        item['coverage']=sum(t in words for t in terms)+2*sum(t in tw for t in terms)
        candidates.append(item)
    candidates.sort(key=lambda x:(-x['coverage'],x['score'],x['id']))
    result=[];seen=set()
    for row in candidates:
        # Avoid duplicate overlapping regions from the same article in top five.
        if row['article_id'] in seen:continue
        seen.add(row['article_id']);result.append({k:v for k,v in row.items() if not k.startswith('norm_')})
        if len(result)==k:break
    db.close();return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['download','build','search']);p.add_argument('path',type=Path);p.add_argument('--query');a=p.parse_args()
    if a.action=='download':download(a.path)
    elif a.action=='build':build(a.path)
    else:print(json.dumps(search(a.path,a.query),ensure_ascii=False,indent=2))
