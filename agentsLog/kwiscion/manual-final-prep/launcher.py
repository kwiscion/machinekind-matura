"""Manual Windows preparation, single detached dispatch and resumable exact fetch."""
import argparse,datetime,hashlib,json,os,re,shutil,stat,subprocess,sys,tarfile,time,uuid,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
ROOT=REPO/'agentsLog/kwiscion/private/final-runs'
REMOTE='/home/shadeform/machinekind-matura-pawel-20260927/manual-final-stage'
OPS=REMOTE+'/remote_ops.py'
HOST='matura-pawel'
WSL=['wsl','-d','Ubuntu','-u','kuba','--']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');os.replace(tmp,path)
def command(args,timeout=90):
 result=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
 if result.returncode:raise RuntimeError((result.stderr or result.stdout)[-3000:])
 return result.stdout
def ssh(*args):
 result=command(WSL+['ssh','-T','-o','ConnectTimeout=15',HOST,'python3','-B',OPS,*args])
 lines=[x for x in result.splitlines() if x.startswith('{')]
 if not lines:raise RuntimeError('Remote response missing JSON: '+result[-1000:])
 value=json.loads(lines[-1])
 if value.get('ops_sha256')!=sha(HERE/'remote_ops.py'):raise ValueError('Remote operations code does not match frozen local code')
 return value
def wslpath(path):
 value=Path(path).resolve().as_posix()
 if not re.match(r'^[A-Za-z]:/',value):raise ValueError('Use a local Windows drive path')
 return '/mnt/'+value[0].lower()+value[2:]
def transfer(src,dest):command(WSL+['scp','-q','-o','ConnectTimeout=15',src,dest],timeout=120)
def verify_sources():
 freeze=HERE/'frozen-sources.json'
 if not freeze.exists():raise ValueError('Frozen source inventory missing; preparation must be qualified before final access')
 pins=json.loads(freeze.read_text(encoding='utf8'))
 for rel,digest in pins['files'].items():
  p=REPO/rel
  if not p.is_file() or sha(p)!=digest:raise ValueError('Frozen source changed: '+rel)
 return sha(freeze)
def source_directory(path,out):
 path=Path(path).expanduser().resolve()
 if path.is_dir():source=path
 elif path.is_file() and zipfile.is_zipfile(path):
  source=out/'extracted-input';source.mkdir()
  with zipfile.ZipFile(path) as z:
   for entry in z.infolist():
    relative=Path(entry.filename.replace('\\','/'))
    mode=entry.external_attr>>16
    if relative.is_absolute() or '..' in relative.parts or ':' in entry.filename or stat.S_ISLNK(mode):raise ValueError('Unsafe ZIP member')
    target=(source/relative).resolve()
    if not target.is_relative_to(source.resolve()):raise ValueError('ZIP escapes extraction directory')
   z.extractall(source)
 else:raise ValueError('ExamPath must be an organizer directory or ZIP')
 candidates=[p.parent for p in source.rglob('exam.json') if (p.parent/'answers-template.json').is_file()]
 if len(candidates)!=1:raise ValueError('Expected exactly one exam.json with answers-template.json')
 return candidates[0]
def validate_answers(path,template):
 blob=path.read_bytes();doc=json.loads(blob);original=json.loads(template.read_text(encoding='utf-8-sig'))
 if len(blob)>1048576 or set(doc)!={'exam_id','answers'} or doc['exam_id']!=original['exam_id']:raise ValueError('Invalid answer schema/exam/size')
 ids=[x['id'] for x in original['answers']]
 if [x.get('id') for x in doc['answers']]!=ids or len(ids)!=len(set(ids)):raise ValueError('Answer IDs differ from template')
 if any(set(x)!={'id','answer'} or not isinstance(x['answer'],str) or not x['answer'].strip() or len(x['answer'])>100000 for x in doc['answers']):raise ValueError('Blank/malformed/oversized answer')
 return {'items':len(ids),'sha256':sha(path),'bytes':len(blob)}
def extract_backup(archive,dest):
 if dest.exists():return
 dest.mkdir()
 with tarfile.open(archive) as t:
  for entry in t.getmembers():
   p=Path(entry.name)
   if p.is_absolute() or '..' in p.parts or entry.issym() or entry.islnk() or not (entry.isfile() or entry.isdir()):raise ValueError('Unsafe backup member')
  t.extractall(dest)
def prepare(args):
 if not args.smoke and args.remote_minutes!=55:raise ValueError('Final deadline must be55minutes')
 started=datetime.datetime.fromisoformat(args.started_utc);now=datetime.datetime.now(datetime.timezone.utc)
 if started.tzinfo is None or not 0<=(now-started).total_seconds()<120:raise ValueError('Invalid local start clock')
 freeze=verify_sources();run=started.strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8];out=ROOT/run;out.mkdir(parents=True)
 deadline=started+datetime.timedelta(minutes=args.remote_minutes)
 state={'run_id':run,'started_utc':started.isoformat(timespec='microseconds'),'deadline_utc':deadline.isoformat(timespec='microseconds'),'local_target_utc':(started+datetime.timedelta(minutes=60)).isoformat(timespec='microseconds'),'phase':'PREPARING','smoke':args.smoke,'frozen_sources_sha256':freeze}
 atomic(out/'run-state.json',state);print('Run ID: '+run,flush=True)
 source=source_directory(args.exam,out)
 builder=REPO/'agentsLog/kwiscion/deadline-rag-prep/prepare_deadline_rag.py'
 command([sys.executable,'-B','-X','utf8',str(builder),'--exam-dir',str(source),'--output',str(out/'package'),'--auto-essay','--cache',REMOTE+'/runs/'+run+'/models','--binary','/home/shadeform/machinekind-matura-pawel-20260927/runtime/bin/ollama','--lock','/home/shadeform/machinekind-matura-pawel-20260927/final-offline.lock','--index',REMOTE+'/wiki/passages.sqlite','--index-proof',str(HERE/'index-proof.json'),'--minutes','60'],timeout=180)
 launch=out/'package/launch.json';m=json.loads(launch.read_text(encoding='utf8'));shutil.copyfile(launch,out/'prepared-launch.json')
 m.update(status='DECLARED',declared_utc=now.isoformat(timespec='microseconds'),deadline_utc=state['deadline_utc'],authorization={'owner':'root','reference':'Root-authorized manual-user command; owner-selected ordinary+essay RAG; manual65-minute workflow; issue3','max_calls':m['max_calls'],'max_requested_tokens':m['max_requested_tokens'],'max_seconds':m['max_seconds'],'above_240k_explicit':True})
 atomic(launch,m)
 command([sys.executable,'-B',str(out/'package/run_recovery_package.py'),str(out/'package')],timeout=60)
 with tarfile.open(out/'package.tar.gz','x:gz') as t:t.add(out/'package',arcname='package')
 state.update(phase='PREPARED',archive_sha256=sha(out/'package.tar.gz'),manifest_sha256=sha(launch),max_calls=m['max_calls'],max_requested_tokens=m['max_requested_tokens'])
 atomic(out/'run-state.json',state);return out,state
def resume(run):
 verify_sources()
 if not re.fullmatch(r'[0-9]{8}T[0-9]{6}-[a-f0-9]{8}',run):raise ValueError('Invalid Resume run ID')
 out=ROOT/run;state=json.loads((out/'run-state.json').read_text(encoding='utf8'))
 if state['phase']=='PREPARING':raise ValueError('Preparation was interrupted before a frozen package existed; no remote inference started. Inspect local run evidence.')
 return out,state
def workflow(out,state,explicit_resume=False):
 run=state['run_id'];statefile=out/'run-state.json'
 if state['phase'] in ('PREPARED','STAGING'):
  state['phase']='STAGING';atomic(statefile,state)
  transfer(wslpath(out/'package.tar.gz'),HOST+':'+REMOTE+'/incoming/'+run+'.tar.gz')
  staged=ssh('stage',run,state['archive_sha256'],state['manifest_sha256']);atomic(out/'remote-stage.json',staged)
  state['phase']='STAGED';atomic(statefile,state)
 if state['phase']=='STAGED':
  before=time.time();clock=ssh('status',run);after=time.time();remote=datetime.datetime.fromisoformat(clock['utc']).timestamp()
  if remote<before-5 or remote>after+5:raise RuntimeError('Remote UTC clock differs by more than5seconds; no inference dispatched')
  atomic(out/'clock-proof.json',{'local_before':before,'remote_utc':clock['utc'],'local_after':after,'accepted_skew_seconds':5})
  receipt=ssh('start',run);atomic(out/'remote-dispatch.json',receipt);state['phase']='RUNNING';atomic(statefile,state)
 last=None
 while True:
  try:status=ssh('status',run)
  except (RuntimeError,subprocess.TimeoutExpired) as exc:
   print('Connection interrupted; remote run remains independent. Resume with scripts/run-final.ps1 -Resume '+run,flush=True)
   atomic(out/'connection-error.json',{'error':str(exc),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});return 3
  atomic(out/'status.json',status)
  compact=(status['status'],status.get('answer_summary'),status.get('reserved'),status.get('completed'))
  if compact!=last:print('Status: '+str(compact),flush=True);last=compact
  if status['status'] in ('FAILED_START','ORPHANED'):raise RuntimeError(str(status.get('error'))+'; inference will not restart automatically')
  if status.get('terminal'):break
  if time.time()>datetime.datetime.fromisoformat(state['local_target_utc']).timestamp():
   print('Local60-minute target exceeded; remote deadline remains enforced. Resume to fetch.');return 4
  time.sleep(10)
 if not status['terminal']['answers_present']:raise ValueError('Remote worker produced no answer export; inspect terminal status. Inference will not restart.')
 # Fetch the small final artifact first. A large trace backup must never withhold it.
 transfer(HOST+':'+REMOTE+'/runs/'+run+'/package/results/answers.json',wslpath(out/'answers.download.json'))
 answer=out/'answers.download.json'
 if sha(answer)!=status['terminal']['answers_sha256']:raise ValueError('Answer hash differs from remote terminal receipt')
 proof=validate_answers(answer,out/'package/exam/answers-template.json');shutil.copyfile(answer,out/'answers.json')
 proof.update(local_ready_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-datetime.datetime.fromisoformat(state['started_utc']).timestamp(),remote_terminal=status['terminal'])
 atomic(out/'validation.json',proof);state.update(phase='FETCHED',answers_sha256=proof['sha256']);atomic(statefile,state)
 print('Original-answer status: '+json.dumps(status.get('answer_summary',{})),flush=True)
 print('Validated answers: '+str(out/'answers.json'),flush=True);print('Review status and submit this exact file manually; no submission was made.',flush=True)
 try:
  status=ssh('status',run);atomic(out/'status.json',status)
  if status.get('backup') and (explicit_resume or time.time()<datetime.datetime.fromisoformat(state['local_target_utc']).timestamp()-120):
   transfer(HOST+':'+REMOTE+'/runs/'+run+'/terminal.tar.gz',wslpath(out/'terminal.tar.gz'))
   if sha(out/'terminal.tar.gz')!=status['backup']['sha256']:raise ValueError('Downloaded backup hash differs')
   extract_backup(out/'terminal.tar.gz',out/'backup')
  else:print('Full trace backup remains remote; Resume can fetch it later.',flush=True)
 except Exception as exc:print('Answers are ready; optional backup fetch failed: '+str(exc),flush=True)
 return 0
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--exam');g.add_argument('--resume');p.add_argument('--started-utc');p.add_argument('--smoke',action='store_true');p.add_argument('--remote-minutes',type=int,default=55);a=p.parse_args()
 try:return workflow(*(resume(a.resume) if a.resume else prepare(a)),explicit_resume=bool(a.resume))
 except Exception as exc:print('STOP: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
