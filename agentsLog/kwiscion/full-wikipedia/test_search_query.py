import sqlite3,tempfile,unittest
from pathlib import Path
import wiki_index as w
import search_query as q

class Tests(unittest.TestCase):
 def test_late_entity_and_inflected_query(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.sqlite';db=sqlite3.connect(p);w.schema(db)
   w.add_article(db,{'id':'1','url':'https://example.org/1','title':'Konstytucja','text':'Konstytucja oraz sejm. '+('Rzadkie szczegóły. '*100)})
   w.add_article(db,{'id':'2','url':'https://example.org/2','title':'Zwykłe informacje','text':' '.join('naglowek'+str(i) for i in range(50))})
   db.commit();db.close()
   query=('podaj odpowiedzi na podstawie zrodla '*50)+' konstytucji'
   r=q.retrieve(p,query);self.assertEqual(r['passages'][0]['article_id'],'1');self.assertIn('konstytucj',r['prefixes'])
 def test_complementary_sections_not_whole_article_dedup(self):
  a={'article_id':'1','start':0,'end':100,'text':'pierwsza'}
  self.assertFalse(q.overlaps(a,dict(a,start=200,end=300,text='druga')))
  self.assertTrue(q.overlaps(a,dict(a,start=20,end=110)))
 def test_generic_task_noun_cannot_erase_informative_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.sqlite';db=sqlite3.connect(p);w.schema(db)
   w.add_article(db,{'id':'1','url':'https://example.org/1','title':'Berenika','text':'Aster Berenika traktat portowy.'})
   w.add_article(db,{'id':'2','url':'https://example.org/2','title':'Imiona','text':'Imiona i ich znaczenie.'})
   db.commit();db.close()
   self.assertEqual(q.retrieve(p,'Podaj imiona','Aster Berenika traktat portowy')['passages'][0]['article_id'],'1')
 def test_only_task_and_source_no_instructions(self):
  question,source=q.query_from_item({'question':'History task','source_text':'Źródło 1. Fragment\nOriginal fact\nŹródło: bibliography\nA. Autor, Book, Warszawa 2005, s. 12.','instructions':'never retrieved','answer_format':'format'})
  self.assertEqual(question,'History task');self.assertEqual(source,'Original fact')

if __name__=='__main__':unittest.main()
