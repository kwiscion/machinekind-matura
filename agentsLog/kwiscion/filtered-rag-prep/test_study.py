import copy,hashlib,importlib.util,json,sqlite3,sys,tempfile,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'full-wikipedia'))
import study_hook as h
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('test_recovery',HERE.parent/'final-package-prep/recovery_harness.py')

class Tests(unittest.TestCase):
 def test_strict_direct_verbatim_admission(self):
  p={'article_id':'a','title':'Original','url':'https://example.org','start':20,'text':'Exact useful evidence.'}
  self.assertEqual(h.admit('{"direct":true,"quote":"useful evidence"}',p)['start'],26)
  self.assertIsNotNone(h.admit('```json\n{"direct":true,"quote":"useful evidence"}\n```',p))
  for text in ['{"direct":"true","quote":"useful evidence"}','{"direct":false,"quote":"useful evidence"}','{"direct":true,"quote":"invented"}','{"direct":true,"quote":""}','{"direct":false,"direct":true,"quote":"useful evidence"}']:
   self.assertIsNone(h.admit(text,p))
 def test_query_typed_and_bounded(self):
  self.assertEqual(h.parse_query('{"query":"Aster port treaty","concepts":["port"],"hypotheses":[]}')['query'],'Aster port treaty')
  for value in [{},{'query':'x '*25,'concepts':['x'],'hypotheses':[]},{'query':'x','concepts':'x','hypotheses':[]}]:
   with self.assertRaises(ValueError):h.parse_query(json.dumps(value))
 def test_full_original_text_images_and_default_ladder_preserved(self):
  hook=object.__new__(h.Hook);hook.engine=r;hook.original=r.step
  hook.plan={'stages':{'query:x':{'kind':'query','source_id':'x'}}};hook.rows={'x':{'prompt':'COMPLETE original source\nquestion'}}
  case={'id':'query:x','content':[{'type':'text','text':'synthetic stage label'},{'type':'image_url','image_url':{'url':'data:image/png;base64,YWJj'}}]}
  before=copy.deepcopy(case);body,settings=hook.step(case,0,[],r.config())
  self.assertEqual(case,before);self.assertEqual(body['messages'][0]['images'],['YWJj'])
  self.assertTrue(body['messages'][0]['content'].startswith(hook.rows['x']['prompt']));self.assertIn(h.QUERY,body['messages'][0]['content'])
  body3,_=hook.step(case,2,[],r.config());self.assertFalse(body3['think']);self.assertEqual(body3['options']['num_predict'],32768)
 def test_admission_frozen_missing_or_late_judges_do_not_change(self):
  with tempfile.TemporaryDirectory() as tmp:
   hook=object.__new__(h.Hook);hook.out=Path(tmp);hook.retrieval=lambda source:{'passages':[{'article_id':'a','title':'t','url':'u','start':0,'text':'Evidence'}]}
   hook.answer=lambda id:None
   stage={'source_id':'x','kind':'final'};self.assertEqual(hook.suffix(stage),'')
   hook.answer=lambda id:'{"direct":true,"quote":"Evidence"}'
   self.assertEqual(hook.suffix(stage),'')
   self.assertEqual(h.read(Path(tmp)/'x.admission.json')['accepted'],[])
 def test_query_fallback_and_retrieval_frozen(self):
  with tempfile.TemporaryDirectory() as tmp:
   hook=object.__new__(h.Hook);hook.out=Path(tmp)/'out';hook.index=Path(tmp)/'index';hook.index.write_bytes(b'x');hook.index_stat=hook.index.stat();hook.engine=r
   hook.plan={'index_sha256':'pin'};hook.items={'x':{'question':'Original question','source_text':'Original source'}};hook.answer=lambda id:'malformed'
   class Search:
    calls=[]
    @staticmethod
    def query_from_item(x):return x['question'],x['source_text']
    @classmethod
    def retrieve(cls,*args):cls.calls.append(args);return {'passages':[]}
   hook.search=Search
   self.assertTrue(hook.retrieval('x')['query_fallback']);self.assertEqual(Search.calls[0][1:],('Original question','Original source'))
   hook.answer=lambda id:'{"query":"late new query","concepts":["x"],"hypotheses":[]}'
   hook.retrieval('x');self.assertEqual(len(Search.calls),1)
 def test_only_actual_answer_slots_export(self):
  export=load('test_export',HERE/'export_answers.py')
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'results').mkdir();ids=['direct:x','query:x','judge:0:x','final:x']
   h.atomic(root/'study.json',{'stages':dict.fromkeys(ids,{})});h.atomic(root/'source-exam.json',{'exam_id':'e','items':[{'id':'x'}]})
   h.atomic(root/'results/answers.json',{'exam_id':'e','answers':[{'id':id,'answer':id} for id in ids]})
   h.atomic(root/'results/engine/answer-status.json',{'items':{id:{'selection':'complete_final','placeholder':False,'incomplete_partial':False} for id in ids}})
   result=export.export(root);self.assertEqual(result['direct']['items'],1)
   self.assertEqual(h.read(root/'results/answers.filtered.json')['answers'],[{'id':'x','answer':'final:x'}])
 def test_export_preserves_complete_direct_over_partial_or_placeholder(self):
  export=load('test_export_fallback',HERE/'export_answers.py')
  for final_kind in ('literal_placeholder','longest_valid_partial'):
   for direct_complete in (False,True):
    with tempfile.TemporaryDirectory() as tmp:
     root=Path(tmp);ids=['direct:x','final:x'];h.atomic(root/'study.json',{'stages':dict.fromkeys(ids,{})})
     h.atomic(root/'source-exam.json',{'exam_id':'e','items':[{'id':'x'}]})
     h.atomic(root/'results/answers.json',{'exam_id':'e','answers':[{'id':'direct:x','answer':'Complete direct'},{'id':'final:x','answer':'Preserved incomplete'}]})
     h.atomic(root/'results/engine/answer-status.json',{'items':{'direct:x':{'selection':'complete_final' if direct_complete else 'literal_placeholder'},'final:x':{'selection':final_kind,'placeholder':final_kind=='literal_placeholder','incomplete_partial':final_kind!='literal_placeholder'}}})
     export.export(root);self.assertEqual(h.read(root/'results/answers.filtered.json')['answers'][0]['answer'],'Complete direct' if direct_complete else 'Preserved incomplete')
     self.assertEqual(len(h.read(root/'results/export-fallbacks.json')['fallbacks']),int(direct_complete))
 def test_optional_passages_bound_without_source_truncation(self):
  with tempfile.TemporaryDirectory() as tmp:
   hook=object.__new__(h.Hook);hook.out=Path(tmp);text='漢'*1600
   hook.retrieval=lambda source:{'passages':[{'article_id':str(i),'title':'title','url':'url','start':0,'text':text} for i in range(5)]}
   hook.answer=lambda id:json.dumps({'direct':True,'quote':text},ensure_ascii=False)
   suffix=hook.suffix({'source_id':'x','kind':'final'})
   self.assertLessEqual(len(suffix.encode()),14000)
   receipt=h.read(Path(tmp)/'x.admission.json');self.assertTrue(receipt['removed_for_optional_byte_budget'])
   self.assertEqual(len(receipt['accepted'])+len(receipt['removed_for_optional_byte_budget']),5)
 def test_real_scheduler_query_judge_final_durable_sequence(self):
  import wiki_index as w
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);index=root/'index.sqlite';db=sqlite3.connect(index);w.schema(db)
   w.add_article(db,{'id':'a','title':'Aster port','url':'https://example.org/a','text':'Aster port treaty evidence.'});db.commit();db.close()
   ids=['direct:x','query:x','judge:0:x','final:x'];kinds=['direct','query','judge','final']
   h.atomic(root/'study.json',{'stages':{id:{'source_id':'x','kind':kind,'rank':0} for id,kind in zip(ids,kinds)},'index_path':str(index),'index_sha256':h.sha(index),'index_bytes':index.stat().st_size})
   h.atomic(root/'source-exam.json',{'items':[{'id':'x','question':'Aster port treaty','source_text':'Original source'}]})
   (root/'source-original.jsonl').write_text(json.dumps({'id':'x','prompt':'FULL ORIGINAL Aster port treaty'})+'\n')
   hook=h.Hook(root,r);calls=[]
   class Runtime:
    def verify(self,context):assert context==65536
    def quiesce(self,deadline):return True
    def send(self,body,timeout):
     events=(root/'results/engine/events.jsonl').read_text().splitlines();assert json.loads(events[-1])['event']=='reserved'
     text=body['messages'][0]['content'];calls.append(text);assert text.startswith('FULL ORIGINAL')
     answer=json.dumps({'query':'Aster port treaty','concepts':['port'],'hypotheses':[]}) if h.QUERY in text else json.dumps({'direct':True,'quote':'Aster port treaty evidence.'}) if h.JUDGE in text else 'Final answer'
     return {'model':r.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':100,'eval_count':10,'message':{'content':answer}}
   original=r.step;r.step=hook.step
   try:r.run([{'id':id,'content':'staged label'} for id in ids],{'exam_id':'e','answers':[{'id':id,'answer':''} for id in ids]},root/'results/engine',r.config(),Runtime(),time.time()+3600)
   finally:r.step=original
   self.assertEqual(len(calls),4);self.assertIn(h.FINAL,calls[-1]);self.assertIn('Aster port treaty evidence.',calls[-1])
   self.assertEqual(len((root/'results/engine/requests.jsonl').read_text().splitlines()),4)
if __name__=='__main__':unittest.main()
