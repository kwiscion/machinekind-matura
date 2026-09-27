import sqlite3,tempfile,unittest
from pathlib import Path
import wiki_index as w

class Tests(unittest.TestCase):
 def test_all_characters_exact_spans(self):
  for text in ('', 'krótki tekst', ('Długi akapit źródłowy. '*170+'\n\n')*4):
   covered=set()
   for a,b,s in w.chunks(text):
    self.assertEqual(s,text[a:b]);self.assertLessEqual(len(s),1600);covered.update(range(a,b))
   self.assertEqual(covered,set(range(len(text))))
 def test_complete_articles_polish_normalization_title_and_exact_passage(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.sqlite';db=sqlite3.connect(p);w.schema(db)
   original='Konstytucja została uchwalona przez Sejm w Warszawie.'
   w.add_article(db,{'id':'1','url':'https://pl.wikipedia.org/wiki/Test','title':'Konstytucja 3 maja','text':original})
   w.add_article(db,{'id':'2','url':'https://pl.wikipedia.org/wiki/Inny','title':'Inny temat','text':'Warszawie Warszawie Warszawie'})
   w.add_article(db,{'id':'3','url':'https://pl.wikipedia.org/wiki/Pusty','title':'Pusty','text':''})
   db.commit();self.assertEqual(db.execute('select count(*) from articles').fetchone()[0],3);db.close()
   result=w.search(p,'konstytucja uchwalona');self.assertEqual(result[0]['article_id'],'1');self.assertEqual(result[0]['text'],original)
   self.assertEqual(w.norm('ŁÓDŹ łódź'),'lodz lodz');self.assertEqual(w.search(p,'i w na'),[])
 def test_exact_all_six_size(self):
  self.assertEqual(len(w.SHARDS),6);self.assertEqual(sum(x[0] for x in w.SHARDS),1765059986)

if __name__=='__main__':unittest.main()
