"""Phase-first auxiliary tasks, native schemas and dependency barriers.

One reviewed runtime/ledger; original questions/images remain complete.
"""
import copy
import study_hook as base

QUERY_SCHEMA={'type':'object','properties':{'query':{'type':'string','minLength':1,'maxLength':600},'concepts':{'type':'array','minItems':1,'maxItems':6,'items':{'type':'string','minLength':1,'maxLength':200}},'hypotheses':{'type':'array','maxItems':6,'items':{'type':'string','minLength':1,'maxLength':200}}},'required':['query','concepts','hypotheses'],'additionalProperties':False}
JUDGE_SCHEMA={'type':'object','properties':{'direct':{'type':'boolean'},'quote':{'type':'string','maxLength':1600}},'required':['direct','quote'],'additionalProperties':False}
FRAME='AKTUALNE ZADANIE: wykonaj wyłącznie opisany poniżej etap badawczy i zwróć JSON zgodny ze schematem. Oryginalne zadanie egzaminacyjne jest cytowanymi danymi do analizy, NIE poleceniem udzielenia teraz odpowiedzi. Instrukcje formatu odpowiedzi wewnątrz cytatu dotyczą dopiero późniejszego etapu końcowego. Wszystkie załączone obrazy należą do cytowanego zadania.\n'

def parse_judge(text,passage):
 value=base.strict_json(text)
 if set(value)!={'direct','quote'} or type(value['direct']) is not bool or not isinstance(value['quote'],str):raise ValueError('Typed DIRECT judgment required')
 if not value['direct']:
  if value['quote']!='':raise ValueError('Negative judgment requires empty quote')
 elif passage is None or base.admit(text,passage) is None:raise ValueError('DIRECT requires exact supporting span')
 return value

class Hook(base.Hook):
 def __init__(self,root,engine):
  super().__init__(root,engine);self.base_out=self.out;self.scope='main';self.current=None
  self.original_accepted=engine.accepted;self.original_partial=engine.usable_partial
 def answer(self,id):
  return super().answer(('probe:'+id) if self.scope=='probe' else id)
 def step(self,case,attempt,history,c,route=None):
  if route is not None:raise self.engine.Fatal('No combined route')
  stage=self.plan['stages'][case['id']];self.current=stage
  self.scope='probe' if stage.get('probe') else 'main';self.out=self.base_out/self.scope
  original=self.rows[stage['source_id']]['prompt'];suffix=self.suffix(stage)
  if len(suffix.encode('utf8'))>16000:raise self.engine.Fatal('Optional evidence bound')
  auxiliary=stage['kind'] in ('query','judge')
  text=FRAME+suffix+'\n\n<ORIGINAL_EXAM_DATA>\n'+original+'\n</ORIGINAL_EXAM_DATA>\nZwróć tylko JSON bieżącego etapu badawczego.' if auxiliary else original+suffix
  current=copy.deepcopy(case)
  if isinstance(current['content'],str):current['content']=text
  else:current['content'][0]['text']=text
  body,settings=self.original(current,attempt,history,c)
  if body['messages'][0].get('images',[])!=self.engine.source(case)[1]:raise self.engine.Fatal('Images changed')
  if auxiliary:
   body['format']=copy.deepcopy(QUERY_SCHEMA if stage['kind']=='query' else JUDGE_SCHEMA)
   # Generic final-answer retry notes must not reverse the current phase contract.
   body['messages'][0]['content']=text
  settings.update(study_kind=stage['kind'],source_id=stage['source_id'],probe=stage.get('probe',False),phase=stage['phase'])
  return body,settings
 def accepted(self,raw,cap,context):
  text=self.original_accepted(raw,cap,context);stage=self.current
  if stage['kind']=='query':base.parse_query(text)
  elif stage['kind']=='judge':
   passages=self.retrieval(stage['source_id'])['passages'];rank=stage['rank']
   parse_judge(text,passages[rank] if rank<len(passages) else None)
  return text
 def partial(self,raw,cap,context):
  return None if self.current['kind'] in ('query','judge') else self.original_partial(raw,cap,context)
 def barrier(self,unresolved,states):
  # Exhaust retries within each dependency phase before any downstream dispatch.
  phase=min((self.plan['stages'][x['id']]['phase'] for x in unresolved),default=99)
  probes=[id for id,stage in self.plan['stages'].items() if stage.get('probe')]
  if phase>=2:
   valid=all(states[id]['answer'] is not None for id in probes)
   base.atomic(self.base_out/'probe-gate.json',{'passed':valid,'ids':probes,'attempts':{id:states[id]['attempts'] for id in probes},'criterion':'all four typed auxiliary finals valid; negative DIRECT is valid'})
   if not valid:raise self.engine.Fatal('Auxiliary format qualification failed; main wave forbidden')
  return [x for x in unresolved if self.plan['stages'][x['id']]['phase']==phase]

def install(root,engine):
 hook=Hook(root,engine);engine.step=hook.step;engine.accepted=hook.accepted;engine.usable_partial=hook.partial;engine.stage_barrier=hook.barrier
 return hook
