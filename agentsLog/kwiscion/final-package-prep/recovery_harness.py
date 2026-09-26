"""Reusable single-Gemma recovery scheduler. Runtime ownership is injected, never bypassed.

The binding must verify context/model, enforce each wall timeout, and stop owned
in-flight compute before quiesce() returns True. No remote operations in this module.
"""
import copy,hashlib,json,os,re,time
from pathlib import Path
MODEL='gemma4:12b-it-q4_K_M'
PLACEHOLDER='Tadeusz Ko\u015bciuszko'
ATTEMPTS=4
class Fatal(RuntimeError):pass
class Failed(ValueError):pass

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True).encode()).hexdigest()
def append(path,value):
 with path.open('a',encoding='utf8') as f:f.write(json.dumps(value,ensure_ascii=True)+'\n');f.flush();os.fsync(f.fileno())
def atomic(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp')
 with tmp.open('w',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def config(minutes=60,context=65536):
 if minutes not in (60,120) or context!=65536:raise ValueError('60/120 minutes and reviewed target context65536 only')
 return {'minutes':minutes,'context':context,'initial_cap':32768,'escalated_cap':49152,'recovery_reserve':600,'finalize_reserve':30,'attempts':4,'max_timeout':420,'minimum_timeout':1,'notes_chars':6000}
def validate_config(c):
 expected=config(c['minutes'],c['context'])
 if c!=expected:raise ValueError('Frozen recovery settings differ; explicit reviewed config extension required')
def source(case):
 c=case['content']
 if isinstance(c,str):return c,[]
 text=c[0]['text'];images=[]
 import base64
 for part in c[1:]:
  prefix,data=part['image_url']['url'].split(',',1)
  if not prefix.startswith('data:image/') or not prefix.endswith(';base64'):raise Fatal('Nonlocal image')
  base64.b64decode(data,validate=True);images.append(data)
 return text,images

def step(case,attempt,history,c,route=None):
 cap=c['initial_cap'];think=attempt<2;suffix='';notes='';reason=None
 if attempt==1:
  observed=[x['raw'].get('prompt_eval_count') for x in history if isinstance(x.get('raw'),dict) and type(x['raw'].get('prompt_eval_count')) is int]
  if observed and max(observed)+c['escalated_cap']<=c['context']:cap=c['escalated_cap']
  else:reason='Higher cap not proven to fit; retain32768 without truncating sources'
 if attempt==3:
  usable=[x['raw'].get('message',{}).get('thinking','') for x in history if isinstance(x.get('raw'),dict) and isinstance(x['raw'].get('message'),dict)]
  notes='\n'.join(x for x in usable if isinstance(x,str) and x.strip())[:c['notes_chars']]
  suffix='\n\nPodaj wy\u0142\u0105cznie kompletn\u0105 odpowied\u017a ko\u0144cow\u0105 na oryginalne zadanie.'
  if notes:suffix+='\nPoni\u017csze przerwane notatki s\u0105 omylne; sprawd\u017a je na podstawie oryginalnych \u017ar\u00f3de\u0142:\n'+notes
 settings={'name':('initial','higher_cap','thinking_off','final_from_notes')[attempt],'suffix':suffix,'think':think,'cap':cap,'escalation_note':reason}
 if route:
  if getattr(route,'output_kind',None)!='final_answer':raise Fatal('Only final-answer suffix routes supported; planning requires a separate stage-result protocol')
  extra=route(case,attempt,history)
  if extra:
   if set(extra)-{'name','suffix','cap','think'}:raise Fatal('Unknown route field')
   settings.update(extra)
 if type(settings['cap']) is not int or not 1<=settings['cap']<=c['escalated_cap'] or type(settings['think']) is not bool or not isinstance(settings['suffix'],str):raise Fatal('Route settings')
 # Routes may customize initial behavior; the mandatory failure ladder remains enforced.
 if attempt>=2:settings['think']=False
 text,images=source(case);msg={'role':'user','content':text+settings['suffix']}
 if images:msg['images']=images
 body={'model':MODEL,'stream':False,'think':settings['think'],'truncate':False,'shift':False,'messages':[msg],'options':{'num_ctx':c['context'],'num_predict':settings['cap']}}
 return body,settings

def accepted(raw,cap,context):
 if not isinstance(raw,dict):raise Failed('malformed response')
 if raw.get('model') is None:raise Failed('Missing model identity')
 if raw['model']!=MODEL:raise Fatal('Model identity changed')
 if any(raw.get(x) is True for x in ('truncated','context_truncated')):raise Fatal('Source/context truncation')
 if raw.get('error'):raise Failed('provider error: '+str(raw['error']))
 p=raw.get('prompt_eval_count');n=raw.get('eval_count')
 if type(p) is not int or type(n) is not int or p<0 or n<0 or n>cap:raise Failed('malformed usage')
 if p+cap>context:raise Fatal('Context reserve violated')
 if raw.get('done') is not True or raw.get('done_reason')!='stop':raise Failed('length or incomplete final')
 msg=raw.get('message')
 if not isinstance(msg,dict) or not isinstance(msg.get('content'),str) or not msg['content'].strip():raise Failed('empty or malformed final')
 if len(msg['content'])>100000:raise Failed('Answer exceeds100000 Unicode codepoints')
 try:msg['content'].encode('utf8')
 except UnicodeEncodeError:raise Failed('Malformed Unicode final')
 return msg['content']

def usable_partial(raw,cap,context):
 # Only incomplete completions with independently valid identity/usage/context
 # can become a submitted partial; malformed/unsafe responses remain evidence.
 if not isinstance(raw,dict) or raw.get('done_reason')!='length':return None
 checked=copy.deepcopy(raw);checked['done']=True;checked['done_reason']='stop'
 try:return accepted(checked,cap,context)
 except (Failed,Fatal):return None
def diagnostics(text,kind):
 if kind!='essay':return []
 words=len(text.split());warnings=[]
 if words<300:warnings.append('essay_under_300_words')
 if not 400<=words<=500:warnings.append('essay_outside_requested_400_500_words')
 if re.search(r'(?im)^\s*(plan|temat\s*2|temat\s*3|liczba\s+s\u0142\u00f3w)\s*[:.)]',text):warnings.append('essay_format_or_multiple_topic_warning')
 return warnings

def load_state(out,cases,binding):
 p=out/'binding.json'
 if p.exists():
  if json.loads(p.read_text())!=binding:raise Fatal('Resume source/template/config binding changed')
 else:atomic(p,binding)
 states={x['id']:{'attempts':0,'answer':None,'history':[],'warnings':[],'partial_candidates':[]} for x in cases};pending={}
 if (out/'events.jsonl').exists():
  for line in (out/'events.jsonl').read_text().splitlines():
   e=json.loads(line);s=states[e['id']]
   if e['event']=='reserved':
    if e['attempt']!=s['attempts']:raise Fatal('Ledger attempt sequence')
    s['attempts']+=1;pending[(e['id'],e['attempt'])]=e
   elif e['event']=='completed':
    if (e['id'],e['attempt']) not in pending:raise Fatal('Unreserved completion')
    pending.pop((e['id'],e['attempt']));s['history'].append(e)
    if e.get('partial_candidate'):s['partial_candidates'].append(e['partial_candidate'])
    if e.get('answer') is not None:s['answer']=e['answer'];s['selected_answer_attempt']=e['attempt'];s['warnings']=e.get('warnings',[])
 for (id,index),e in pending.items():states[id]['history'].append({'attempt':index,'error':'interrupted_after_reservation','raw':None})
 return states

def export(out,template,states,stop=None):
 answer=copy.deepcopy(template);metadata={}
 for row in answer['answers']:
  s=states[row['id']];partial=max(s['partial_candidates'],key=len,default=None) if s['answer'] is None else None
  placeholder=s['answer'] is None and partial is None;row['answer']=s['answer'] if s['answer'] is not None else partial or PLACEHOLDER
  metadata[row['id']]={'placeholder':placeholder,'incomplete_partial':partial is not None,'selection':'complete_final' if s['answer'] is not None else 'longest_valid_partial' if partial else 'literal_placeholder','successful_recovery':s['answer'] is not None and s.get('selected_answer_attempt',0)>0,'attempts':s['attempts'],'warnings':s['warnings'],'partial_candidates_preserved':len(s['partial_candidates']),'errors':[h.get('error') for h in s['history'] if h.get('error')],'mandatory_attempts_unfulfilled':max(0,ATTEMPTS-s['attempts']) if s['answer'] is None else 0}
 # Exact organizer schema and size; preserve oversized originals in checkpoint evidence.
 if set(answer)!={'exam_id','answers'} or not isinstance(answer['exam_id'],str) or any(set(row)!={'id','answer'} or not isinstance(row['id'],str) for row in answer['answers']):raise Fatal('Organizer schema')
 def size():return len(json.dumps(answer,ensure_ascii=False,separators=(',',':')).encode('utf8'))+1
 for row in sorted(answer['answers'],key=lambda row:len(row['answer'].encode('utf8')),reverse=True):
  if size()<=1048576:break
  original=row['answer'];low=0;high=len(original)
  # Retain the longest codepoint-safe prefix that fits the exact serialized file.
  # Other complete responses remain untouched, originals stay in the ledger.
  while low<high:
   mid=(low+high+1)//2;row['answer']=original[:mid]
   if size()<=1048576:low=mid
   else:high=mid-1
  # If one row cannot resolve total overflow, retain a useful bounded prefix
  # and continue reducing other large rows instead of discarding this answer.
  row['answer']=(original[:low] if original[:low].strip() else original.lstrip()[:256]) if original.strip() else PLACEHOLDER
  metadata[row['id']].update(placeholder=row['answer']==PLACEHOLDER,successful_recovery=False,incomplete_partial=True,schema_size_replaced=True,selection='size_bounded_partial' if row['answer']!=PLACEHOLDER else 'literal_placeholder',original_codepoints=len(original),submitted_codepoints=len(row['answer']))
 if size()>1048576:raise Fatal('Template itself exceeds organizer byte cap')
 atomic(out/'answers.json',answer);atomic(out/'answer-status.json',{'stop':stop,'items':metadata,'placeholder_is_not_a_valid_answer':True})
 return answer

def run(cases,template,out,c,runtime,deadline,clock=time.time,route=None,resume=False,faults=None):
 """runtime.verify(context), send(body,timeout), quiesce(deadline)->True are required.

 quiesce must prove owned compute terminal even after timeout; a failure stops
 the whole run, never overlaps a retry. The outer reviewed OS guardian remains mandatory.
 """
 validate_config(c);out=Path(out)
 if out.exists() and not resume:raise Fatal('Fresh output or explicit resume required')
 out.mkdir(parents=True,exist_ok=True)
 ids=[x['id'] for x in cases]
 if not ids or len(ids)!=len(set(ids)) or len(template['answers'])!=len(ids) or set(x['id'] for x in template['answers'])!=set(ids):raise Fatal('Exact unique template IDs required')
 if not 0<deadline-clock()<=c['minutes']*60:raise Fatal('Absolute deadline outside declared window')
 faults=faults or {}
 if not set(faults)<=set(ids) or any(v not in ('timeout','length') for v in faults.values()):raise Fatal('Fault declaration')
 binding={'cases':digest(cases),'template':digest(template),'config':digest(c),'deadline':deadline,'model':MODEL,'route':getattr(route,'provenance_sha256',None),'faults':faults}
 if route and not binding['route']:raise Fatal('Route hook must carry frozen provenance_sha256')
 states=load_state(out,cases,binding);export(out,template,states);stop=None
 try:
  runtime.verify(c['context'])
  if runtime.quiesce(deadline) is not True:raise Fatal('Cannot prove previous owned compute stopped')
  while True:
   unresolved=[x for x in cases if (states[x['id']]['answer'] is None or states[x['id']]['warnings']) and states[x['id']]['attempts']<ATTEMPTS]
   if not unresolved:break
   # Round-robin breadth first: do not spend four attempts on the first item.
   case=min(unresolved,key=lambda x:states[x['id']]['attempts']);s=states[case['id']];attempt=s['attempts']
   left=deadline-clock();boundary=c['recovery_reserve'] if attempt==0 else c['finalize_reserve']
   # Initial passes divide only among still-unseen items. Recalculate after each
   # observed latency; do not reserve four equal shares before any throughput is known.
   obligations=sum(states[x['id']]['attempts']==0 for x in unresolved) if attempt==0 else sum(ATTEMPTS-states[x['id']]['attempts'] for x in unresolved)
   timeout=min(c['max_timeout'],max(0,left-boundary)/max(1,obligations))
   if hasattr(runtime,'timeout_for'):timeout=min(c['max_timeout'],max(0,left-boundary),runtime.timeout_for(timeout,attempt))
   if timeout<c['minimum_timeout']:raise Fatal('Hard wallclock cannot fit remaining mandatory attempts')
   runtime.verify(c['context']);body,settings=step(case,attempt,s['history'],c,route)
   fault=faults.get(case['id']) if attempt==0 else None
   if fault=='length':body['options']['num_predict']=1;settings['cap']=1
   if hasattr(runtime,'arm_fault'):runtime.arm_fault(fault)
   # Exact original text/image bytes are composed in step(), never truncated.
   reserved={'event':'reserved','id':case['id'],'attempt':attempt,'injected_fault':fault,'timeout':timeout,'allocation':'remaining_initial_items' if attempt==0 else 'remaining_recovery_attempts','allocation_denominator':obligations,'cap':settings['cap'],'settings':settings,'request_sha256':digest(body),'time':clock()}
   append(out/'requests.jsonl',{'id':case['id'],'attempt':attempt,'payload':body});append(out/'events.jsonl',reserved);s['attempts']+=1
   raw=None;text=None;error=None;fatal=None
   try:
    raw=runtime.send(body,timeout);runtime.verify(c['context']);text=accepted(raw,settings['cap'],c['context'])
    if clock()>=deadline:raise Fatal('Response arrived after hard deadline')
   except Fatal as exc:fatal=str(exc);error=type(exc).__name__+': '+str(exc);text=None
   except Exception as exc:error=type(exc).__name__+': '+str(exc)
   finally:
    try:
     if runtime.quiesce(deadline) is not True:raise Fatal('Owned compute stop not verified')
    except Exception as exc:fatal='Cannot safely retry: '+str(exc);error=fatal;text=None
   partial=usable_partial(raw,settings['cap'],c['context']) if text is None and not fatal else None
   event={'partial_candidate':partial,'event':'completed','id':case['id'],'attempt':attempt,'raw':raw,'answer':text,'error':error,'warnings':diagnostics(text,case.get('kind')) if text else [],'time':clock()}
   append(out/'events.jsonl',event);s['history'].append(event)
   if partial:s['partial_candidates'].append(partial)
   if text is not None:s['answer']=text;s['selected_answer_attempt']=attempt;s['warnings']=event['warnings']
   export(out,template,states,fatal)
   if fatal:raise Fatal(fatal)
 except Exception as exc:stop=type(exc).__name__+': '+str(exc)
 return export(out,template,states,stop)
