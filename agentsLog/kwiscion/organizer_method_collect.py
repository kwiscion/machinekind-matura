"""Evaluation-only HTML parser for the public organizer method site. No external dependencies."""
from pathlib import Path
from html.parser import HTMLParser
class Node:
 def __init__(self,tag='',attrs=(),parent=None): self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def text(self): return ' '.join(' '.join(c.text() if isinstance(c,Node) else c for c in self.children).split())
 def find(self,tag=None,cls=None):
  out=[]
  for c in self.children:
   if isinstance(c,Node):
    if (tag is None or c.tag==tag) and (cls is None or cls in c.attrs.get('class','').split()):out.append(c)
    out.extend(c.find(tag,cls))
  return out
class DOM(HTMLParser):
 def __init__(self,text): super().__init__();self.root=Node();self.cur=self.root;self.feed(text)
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs,self.cur);self.cur.children.append(n)
  if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.cur=n
 def handle_endtag(self,tag):
  c=self.cur
  while c.parent and c.tag!=tag:c=c.parent
  if c.parent:self.cur=c.parent
 def handle_data(self,data):self.cur.children.append(data)
def extract_page(path):
 """Extract actual scores/reasons from cached public HTML; no generation or grading."""
 import re, hashlib
 s=DOM(path.read_text(encoding='utf-8-sig')).root
 items=[]
 for a in s.find('article','review-task'):
  scores=a.find(cls='task-score'); why=a.find(cls='grade-explanation')
  match=re.search(r'(\d+)\s*/\s*(\d+)',scores[0].text()) if scores else None
  if match:
   items.append({'id':a.attrs['id'],'points':int(match[1]),'max_points':int(match[2]),'why':why[0].text() if why else ''})
 if items:
  assert len({i['id'] for i in items})==len(items)
  assert all(i['why'] and 0<=i['points']<=i['max_points'] for i in items)
 return {'page':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'items':items}

if __name__=='__main__':
 import argparse,json
 parser=argparse.ArgumentParser(description='Extract cached organizer HTML into ignored evaluation-only outputs; never training/retrieval.')
 parser.add_argument('--cache',type=Path,default=Path('outputs/organizers-model-method'))
 args=parser.parse_args(); cache=args.cache.resolve()
 assert cache.is_relative_to((Path.cwd()/'outputs').resolve()), 'Raw material must stay under ignored outputs'
 root=DOM((cache/'index.html').read_text(encoding='utf-8-sig')).root
 names=list(dict.fromkeys(a.attrs['href'] for a in root.find('a') if a.attrs.get('href','').endswith('.html') and '/' not in a.attrs['href']))
 records=[extract_page(cache/name) for name in names if (cache/name).exists()]
 (cache/'collected-reasons.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'pages_with_items':sum(bool(r['items']) for r in records),'items':sum(len(r['items']) for r in records)}))
