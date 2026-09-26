"""Explicitly authorized bounded isolated dependency install; no model weights."""
import argparse,datetime,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-install',action='store_true');ap.add_argument('--archive-fallback',action='store_true');a=ap.parse_args()
    if not a.execute_install:raise SystemExit('Explicit install flag required')
    directory=ROOT/'evidence-private';python=directory/'cpu-venv/Scripts/python.exe'
    if not python.exists():raise SystemExit('Create the dedicated cpu-venv first')
    # Root bounded authorization: setup start19:36:30UTC +15minutes.
    deadline=datetime.datetime.fromisoformat('2026-09-26T19:51:30+00:00').timestamp()
    cfg=json.loads((ROOT/'candidate.json').read_text());report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-09-26T19:51:30Z','steps':[]}
    constraints=directory/'constraints.txt';constraints.write_text('torch==2.8.0+cpu\n',encoding='utf-8')
    commands=[
        [str(python),'-m','pip','install','torch==2.8.0','--index-url','https://download.pytorch.org/whl/cpu'],
        [str(python),'-m','pip','install','--constraint',str(constraints),'git+https://github.com/huggingface/transformers.git@'+cfg['transformers_git_revision'],'git+https://github.com/huggingface/peft.git@'+cfg['peft_git_revision']],
    ]
    if a.archive_fallback:
        commands=[[str(python),'-m','pip','install','--constraint',str(constraints),'https://codeload.github.com/huggingface/transformers/zip/'+cfg['transformers_git_revision'],'https://codeload.github.com/huggingface/peft/zip/'+cfg['peft_git_revision']]]
    try:
        for index,command in enumerate(commands):
            remaining=int(deadline-time.time())
            if remaining<=0:raise TimeoutError('Setup deadline reached')
            log=directory/(f'install-archive-{index+1}.log' if a.archive_fallback else f'install-{index+1}.log')
            print('Starting bounded install step',index+1,'remaining_seconds',remaining,flush=True)
            with log.open('w',encoding='utf-8') as stream:
                completed=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining,check=False)
            report['steps'].append({'step':index+1,'returncode':completed.returncode,'log':str(log.relative_to(ROOT))})
            if completed.returncode:raise RuntimeError('Install failed; see owned log')
        freeze=subprocess.check_output([str(python),'-m','pip','freeze'],text=True,timeout=30)
        (ROOT/'cpu-dependencies.txt').write_text(freeze,encoding='utf-8')
        report['status']='INSTALL_COMPLETED_IDENTITY_CHECK_PENDING'
    except Exception as exc:report['status']='BLOCKED';report['error']=str(exc)
    report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/('cpu-install-archive-report.json' if a.archive_fallback else 'cpu-install-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
    raise SystemExit(report['status']=='BLOCKED')
if __name__=='__main__':main()
