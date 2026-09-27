"""Champion recovery binding: actual isolated owned Ollama, dry preflight by default."""
import argparse,datetime as dt,hashlib,importlib.util,json,os,signal,stat,subprocess,sys,time,shutil
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('recovery_native',HERE/'run_native_package.py')
r=load('recovery_engine',HERE/'recovery_harness.py')
n.GlobalStop=r.Fatal
ENDPOINT='http://127.0.0.1:11435'
CLIENT='''import json,sys,urllib.request
body=json.load(sys.stdin)
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): raise RuntimeError('Redirect forbidden')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
req=urllib.request.Request("http://127.0.0.1:11435/api/chat",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
with opener.open(req,timeout=7200) as reply: print(reply.read().decode())
'''

def verify(root,m):
 for name,digest in m['files'].items():n.need(n.sha(n.safe_file(root,name))==digest,'Frozen dependency changed: '+name)
 n.need(n.sha(Path(__file__))==m['files']['run_recovery_package.py'],'Executing binding changed')
 for name,digest in n.PINS.items():n.need(m['files'].get(name)==digest,'Reviewed helper changed')

def study_module(root):
 return load('owned_study_binding',root/'study/study_binding.py')

def preflight(root,fresh=True):
 m=n.read(root/'launch.json')
 if m.get('schema')=='typed_stage_study_v1':return study_module(root).preflight(root,verify,fresh)
 n.need(m['schema']=='champion_recovery_v1','Schema')
 r.validate_config(m['recovery']);n.need(m['max_seconds']==m['recovery']['minutes']*60,'Wall budget')
 n.need(m['context']==65536 and m['model']==n.MODEL and m['temperature']=='omitted','Controls')
 verify(root,m);helper,guard,rehearsal,adapter,inf=n.modules(root)
 package=adapter.load_package(root/'exam')
 n.need(all(path.relative_to(root).as_posix() in m['files'] for path in adapter.package_inputs(package)),'Every source/image pinned')
 n.need(all(name in m['files'] for name in ('recovery_harness.py','run_native_package.py','operator_recovery.sh','input.original.jsonl','input.jsonl')),'Required dependency pins')
 original=n.rows(root/'input.original.jsonl')
 ids=[x['id'] for x in package['exam']['items']];n.need(ids==m['ids']==[x['id'] for x in original],'IDs')
 for row,item in zip(original,package['exam']['items']):
  n.need(row['prompt']==adapter.build_prompt(package['exam'],item),'Original prompt')
  n.need(row['images']==['exam/'+adapter.safe_relative(x['path'],item['id']).as_posix() for x in item.get('images',[])],'All images')
 routed,routes=n.build_routes(original,m['essay_ids'],m['no_essay']);n.need(n.rows(root/'input.jsonl')==routed,'Only declared essay suffix')
 cases=inf.load_cases(root/'input.jsonl',len(ids))
 for case in cases:case['kind']='essay' if case['id'] in m['essay_ids'] else 'ordinary'
 n.need(m['max_calls']==len(ids)*4 and m['max_requested_tokens']==len(ids)*(32768*3+49152),'Exact four-attempt envelope')
 n.need(set(m['faults'])<=set(ids) and sorted(m['faults'].values()) in ([],['length','timeout']),'Declared optional two faults')
 if m['faults']:
  eligible=sorted((x for x in original if x['id'] not in m['essay_ids']),key=lambda x:(len(x['prompt']),x['id']))
  n.need(m['faults']=={eligible[0]['id']:'timeout',eligible[1]['id']:'length'},'Mechanical fault selection')
 if fresh:n.need(not (root/'results').exists(),'Fresh results required')
 if m['status']=='DECLARED':n.declared(m)
 else:n.need(m['status']=='PREPARED' and m['authorization'] is None,'Prepared not authorized')
 return m,package,cases

def supervisor(root,parent,fd,host_net):
 proof=n.read(root/'results/supervisor.json');identity=n.inherited_parent_identity(parent,proof['identity'])
 n.need(os.getppid()==parent and identity['namespace']==host_net and identity['executable']==str(Path(sys.executable).resolve()),'Locked parent identity')
 n.need(identity['argv'][-4:]==[str(root/'run_recovery_package.py'),str(root),'--execute','--guarded'],'Parent command')
 timer=n.inherited_parent_identity(proof['guardian']['pid'],proof['guardian'])
 n.need(Path(timer['executable']).name=='timeout' and timer['argv'][1:3]==['--signal=TERM','--kill-after=5s'],'Guardian')
 n.need(int(Path(f'/proc/{parent}/stat').read_text().split(') ',1)[1].split()[1])==timer['pid'],'Guardian ancestry')
 n.need(proof['launch_sha256']==n.sha(root/'results/launch.json') and proof['weights_sha256']==n.sha(root/'results/weights.json'),'Parent receipts')
 n.need(stat.S_ISFIFO(os.fstat(fd).st_mode),'Inherited FD');os.set_blocking(fd,False)
 try:token=os.read(fd,33);n.need(len(token)==32 and hashlib.sha256(token).hexdigest()==proof['challenge_sha256'],'Inherited challenge')
 finally:os.close(fd)

class OwnedRuntime:
 def __init__(self,root,m,parent,proof):
  self.root=root;self.m=m;self.parent=parent;self.proof=proof;self.out=root/'results';self.helper,self.guard,self.rehearsal,self.adapter,_=n.modules(root)
  self.server=None;self.record=None;self.loaded=False;self.fault=None;self.index=0;self.response_terminal=False
  self.pins=dict(self.guard.CANONICAL,context_length=65536)
  self.weights=n.read(self.out/'weights.json')['files']
  self.weight_stats={x['path']:(Path(m['cache'])/x['path']).stat() for x in self.weights}
 def arm_fault(self,fault):self.fault=fault
 def timeout_for(self,proposed,attempt):return max(proposed,240) if not self.loaded else proposed
 def remaining(self):return n.remaining(self.m)
 def verify(self,context):
  try:return self._verify(context)
  except Exception as exc:raise r.Fatal('Runtime integrity: '+str(exc)) from exc
 def _verify(self,context):
  n.need(context==65536,'Runtime target context');verify(self.root,self.m)
  for row in self.weights:
   path=Path(self.m['cache'])/row['path'];before=self.weight_stats[row['path']];after=path.stat()
   n.need(not path.is_symlink() and (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Pinned weight changed after initial full hash')
  self.remaining()
  if self.server:
   n.need(self.server.poll() is None and self.helper.ticks(self.server.pid)==self.record['ticks'],'Owned service identity')
   n.need(Path(f'/proc/{self.server.pid}/exe').resolve()==Path(self.m['binary']),'Owned executable')
   actual=dict(x.split('=',1) for x in Path(f'/proc/{self.server.pid}/environ').read_bytes().decode().split('\0') if '=' in x)
   n.need(all(actual.get(k)==v for k,v in self.env.items()),'Owned environment')
   snap={k:self.rehearsal.api(k) for k in ('version','tags','ps')};
   try:self.guard.verify_snapshot(snap,self.pins,self.loaded)
   except Exception as exc:raise r.Fatal('Runtime identity/context: '+str(exc))
   self.helper.workers({os.getpid(),self.parent},self.server.pid);n.append(self.out/'runtime.jsonl',snap)
 def start(self):
  self.verify(65536);self.helper.workers({os.getpid(),self.parent});self.index+=1
  home=self.out/f'server-home-{self.index}';home.mkdir()
  self.env={'PATH':os.environ['PATH'],'HOME':str(home),'OLLAMA_MODELS':self.m['cache'],'OLLAMA_HOST':'127.0.0.1:11435','OLLAMA_CONTEXT_LENGTH':'65536','OLLAMA_NUM_PARALLEL':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_NO_CLOUD':'1','OLLAMA_KEEP_ALIVE':'5m'}
  # Remove stale completed receipt before spawning; crash fallback remains strict.
  (self.out/'cleanup.json').unlink(missing_ok=True)
  with (self.out/f'server-{self.index}.log').open('xb') as log:self.server=subprocess.Popen([self.m['binary'],'serve'],env=self.env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  self.record={'pid':self.server.pid,'ticks':self.helper.ticks(self.server.pid),'namespace':os.readlink(f'/proc/{self.server.pid}/ns/net')}
  r.atomic(self.out/'server-identity.json',self.record);n.append(self.out/'server-history.jsonl',self.record)
  until=time.monotonic()+min(45,self.remaining()-15)
  while True:
   try:self.rehearsal.api('version')
   except OSError:
    n.need(time.monotonic()<until and self.server.poll() is None,'Owned server readiness');time.sleep(.2);continue
   self.verify(65536);break
 def send(self,body,timeout):
  reserved=[x for x in n.rows(self.out/'engine/events.jsonl') if x['event']=='reserved']
  n.need(len(reserved)<=self.m['max_calls'] and sum(x['cap'] for x in reserved)<=self.m['max_requested_tokens'],'Frozen call/token envelope')
  if self.server is None:self.start()
  self.verify(65536);self.response_terminal=False;timeout=min(timeout,self.remaining()-20)
  n.need(timeout>0,'No request window');actual=min(3,timeout) if self.fault=='timeout' else timeout
  child=subprocess.Popen([sys.executable,'-B','-c',CLIENT],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  started=time.monotonic();raw=None
  try:
   stdout,stderr=child.communicate(json.dumps(body).encode(),timeout=actual)
   if child.returncode!=0:raise RuntimeError('HTTP client failure: '+stderr.decode(errors='replace')[-200:])
   raw=json.loads(stdout);self.loaded=True;self.verify(65536);self.response_terminal=isinstance(raw,dict) and raw.get('done') is True
   if self.fault=='timeout':self.response_terminal=False;raise TimeoutError('Declared first-attempt timeout injection after client completion')
   return raw
  except subprocess.TimeoutExpired:
   child.kill();child.communicate();raise TimeoutError('Declared injected timeout' if self.fault=='timeout' else 'Request wall timeout')
  finally:n.append(self.out/'transport.jsonl',{'latency_s':time.monotonic()-started,'timeout':actual,'fault':self.fault,'usage_known':isinstance(raw,dict),'prompt_eval_count':raw.get('prompt_eval_count') if isinstance(raw,dict) else None,'eval_count':raw.get('eval_count') if isinstance(raw,dict) else None,'load_duration_ns':raw.get('load_duration') if isinstance(raw,dict) else None,'eval_duration_ns':raw.get('eval_duration') if isinstance(raw,dict) else None,'active_backend_cancellation_proven':False})
 def quiesce(self,deadline):
  if self.server is None:return True
  if self.response_terminal:
   self.verify(65536);return True
  # Stop/reap the exact owned server AND runner group after every attempt. This
  # deliberately favors simple proven isolation over warm-cache throughput.
  killed=self.helper.cleanup(self.record);self.server.wait(timeout=5)
  until=time.monotonic()+5
  while not all(self.helper.process_absent(pid) for pid in set(killed)|{self.server.pid}):
   n.need(time.monotonic()<until,'Owned backend still live');time.sleep(.05)
  receipt={'owned':self.record,'matched_pids':killed,'returncode':self.server.returncode}
  r.atomic(self.out/'cleanup.json',receipt);n.append(self.out/'cleanup-history.jsonl',receipt)
  self.server=None;self.loaded=False;self.helper.workers({os.getpid(),self.parent});return True

def recover_owned(root,m,helper):
 out=root/'results'
 try:
  record=n.read(out/'server-identity.json');proof=n.read(out/'network-proof.json')
 except (FileNotFoundError,ValueError):return helper.cleanup_from_receipts(out,m['binary'])
 valid=(isinstance(record,dict) and isinstance(proof,dict) and type(record.get('pid')) is int and record['pid']>0 and str(record.get('ticks','')).isdigit() and record.get('namespace')==proof.get('isolated_namespace') and record.get('namespace')!=os.readlink('/proc/self/ns/net'))
 if not valid:return helper.cleanup_from_receipts(out,m['binary'])
 try:receipt=n.read(out/'cleanup.json')
 except (FileNotFoundError,ValueError):receipt=None
 if isinstance(receipt,dict) and receipt.get('owned')==record and receipt.get('returncode') in (0,-9,-15) and isinstance(receipt.get('matched_pids'),list) and all(type(pid) is int and pid>0 for pid in receipt['matched_pids']):
  return helper.cleanup_from_receipts(out,m['binary'])
 # A valid durable group identity is narrower than a broad namespace scan.
 # cleanup() verifies group/namespace/start ticks and never signals reused PID.
 killed=helper.cleanup(record);until=time.monotonic()+5
 while not all(helper.process_absent(pid) for pid in set(killed)|{record['pid']}):
  n.need(time.monotonic()<until,'Recorded owned process still present after cleanup');time.sleep(.05)
 receipt={'owned':record,'matched_pids':killed,'returncode':-9,'returncode_basis':'inferred SIGKILL and verified absence; not waitpid observation'}
 r.atomic(out/'cleanup.json',receipt)
 return {'mode':'recorded_identity_group','matched_pids':killed}

def final_export(root,m,cases,package):
 if m.get('schema')=='typed_stage_study_v1':return study_module(root).final_export(root,m,cases,validate_final)
 out=root/'results';binding=n.read(out/'engine/binding.json') if (out/'engine/binding.json').exists() else None
 if binding:
  states=r.load_state(out/'engine',cases,binding)
  previous=n.read(out/'engine/answer-status.json') if (out/'engine/answer-status.json').exists() else {}
  r.export(out/'engine',package['template'],states,previous.get('stop') or ('Interrupted supervisor' if any(s['attempts'] and not s['history'] for s in states.values()) else None))
 else:
  (out/'engine').mkdir(exist_ok=True);states={x['id']:{'answer':None,'attempts':0,'history':[],'warnings':[],'partial_candidates':[]} for x in cases};r.export(out/'engine',package['template'],states,'Stopped before dispatch')
 shutil.copyfile(out/'engine/answers.json',out/'answers.json')
 validate_final(out/'answers.json',package['template'])
 events=n.rows(out/'engine/events.jsonl') if (out/'engine/events.jsonl').exists() else []
 reserved=[e for e in events if e['event']=='reserved'];completed=[e for e in events if e['event']=='completed']
 r.atomic(out/'terminal.json',{'calls':len(reserved),'requested_tokens':sum(e['cap'] for e in reserved),'ids':m['ids'],'stop':n.read(out/'engine/answer-status.json')['stop'],'answers_sha256':n.sha(out/'answers.json'),'unknown_usage_calls':len(reserved)-len(completed)+sum(not isinstance(e.get('raw'),dict) or type(e['raw'].get('eval_count')) is not int or type(e['raw'].get('prompt_eval_count')) is not int for e in completed),'injected_calls':sum(bool(e.get('injected_fault')) for e in reserved),'no_namespace_claim_without_proof':not (out/'network-proof.json').exists()})


def validate_final(path,template):
 data=path.read_bytes();n.need(len(data)<=1048576,'Final UTF8 bytes');doc=json.loads(data)
 n.need(set(doc)=={'exam_id','answers'} and doc['exam_id']==template['exam_id'],'Final exam/schema')
 ids=[x['id'] for x in template['answers']]
 n.need([x.get('id') for x in doc['answers']]==ids and len(ids)==len(set(ids)),'Exact final template IDs/order')
 n.need(all(set(x)=={'id','answer'} and isinstance(x['id'],str) and isinstance(x['answer'],str) and x['answer'].strip() and len(x['answer'])<=100000 for x in doc['answers']),'Final answer schema/nonblank/codepoints')
 for x in doc['answers']:x['answer'].encode('utf8')
 return doc

def inside(root,m,package,cases,parent,fd,host_net):
 supervisor(root,parent,fd,host_net);helper,guard,rehearsal,adapter,_=n.modules(root);out=root/'results'
 proof=rehearsal.network_proof(host_net);n.write(out/'network-proof.json',proof)
 runtime=OwnedRuntime(root,m,parent,proof)
 try:
  if m.get('schema')=='typed_stage_study_v1':study_module(root).run(root,m,cases,runtime)
  else:r.run(cases,package['template'],out/'engine',m['recovery'],runtime,dt.datetime.fromisoformat(m['deadline_utc']).timestamp(),faults=m['faults'])
 finally:
  runtime.response_terminal=False;runtime.quiesce(dt.datetime.fromisoformat(m['deadline_utc']).timestamp());final_export(root,m,cases,package)
 if m.get('schema')=='typed_stage_study_v1':return 2 if n.read(out/'terminal.json').get('stop') else 0
 return 2 if n.read(out/'engine/answer-status.json').get('stop') else 0

def execute(root,m,package,cases):
 import fcntl
 helper,guard,rehearsal,adapter,_=n.modules(root);out=root/'results';out.mkdir()
 lock=Path(m['lock']).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  n.need(guard.fingerprint(Path(m['binary']))['sha256']==guard.CANONICAL['runtime_binary_sha256'],'Runtime pin')
  weights=guard.verify_inventory(m['cache'],guard.native_inventory(m['cache'],guard.CANONICAL))
  helper.workers({os.getpid()});rehearsal.isolation_probe()
  if m.get('schema')=='typed_stage_study_v1':study_module(root).verify_original_idle(out,rehearsal,n)
  else:n.need(not rehearsal.api('ps',11436)['models'],'Original service must remain idle')
  n.write(out/'launch.json',m);n.write(out/'weights.json',weights);verify(root,m);n.remaining(m)
  receiver,sender=os.pipe();token=os.urandom(32);os.write(sender,token);os.close(sender)
  n.write(out/'supervisor.json',{'identity':n.process_identity(os.getpid(),helper),'guardian':n.process_identity(os.getppid(),helper),'launch_sha256':n.sha(out/'launch.json'),'weights_sha256':n.sha(out/'weights.json'),'challenge_sha256':hashlib.sha256(token).hexdigest()})
  command=['unshare','-rn','--',sys.executable,'-B',str(root/'run_recovery_package.py'),str(root),'--execute','--inside','--parent',str(os.getpid()),'--fd',str(receiver),'--host-net',os.readlink('/proc/self/ns/net')]
  child=None;status=2
  try:
   child=subprocess.Popen(command,start_new_session=True,pass_fds=(receiver,));os.close(receiver);receiver=None;status=child.wait(timeout=max(1,n.remaining(m)-15))
  finally:
   if receiver is not None:os.close(receiver)
   if child and child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
   r.atomic(out/'parent-cleanup.json',recover_owned(root,m,helper))
  return status
 finally:
  final_export(root,m,cases,package);lock.close()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('package',type=Path)
 for k in ('execute','guarded','inside','cleanup'):ap.add_argument('--'+k,action='store_true')
 ap.add_argument('--parent',type=int);ap.add_argument('--fd',type=int);ap.add_argument('--host-net');a=ap.parse_args();root=a.package.resolve()
 if a.cleanup:
  m=n.read(root/'results/launch.json')
  n.need(n.sha(root/'run_gemma_offline.py')==n.PINS['run_gemma_offline.py'],'Cleanup helper pin')
  helper=n.load('recovery_cleanup_only',root/'run_gemma_offline.py');print(json.dumps(recover_owned(root,m,helper)));return 0
 if a.execute:
  m=n.read(root/'launch.json');n.declared(m)
  def stop(*_):raise r.Fatal('Absolute operation deadline')
  signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.1,n.remaining(m)-15))
 m,package,cases=preflight(root,fresh=not a.inside)
 if not a.execute:print(json.dumps({'preflight':'PASS','calls':m['max_calls'],'tokens':m['max_requested_tokens'],'model_calls':0}));return 0
 if a.inside:return inside(root,m,package,cases,a.parent,a.fd,a.host_net)
 if not a.guarded:
  signal.setitimer(signal.ITIMER_REAL,0);os.execvp('bash',['bash',str(root/'operator_recovery.sh'),str(root),'--execute'])
 guardian=n.process_identity(os.getppid(),n.modules(root)[0]);n.need(Path(guardian['executable']).name=='timeout' and guardian['argv'][1:3]==['--signal=TERM','--kill-after=5s'],'External guardian')
 return execute(root,m,package,cases)
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:print('STOP: '+str(exc),file=sys.stderr);raise SystemExit(2)
