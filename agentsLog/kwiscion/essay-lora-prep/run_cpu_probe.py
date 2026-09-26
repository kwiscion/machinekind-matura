"""Verify exact installed VCS identities, then enforce120s synthetic CPU probe."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-synthetic',action='store_true');a=ap.parse_args()
    if not a.execute_synthetic:raise SystemExit('Explicit opt-in required')
    python=ROOT/'evidence-private/cpu-venv/Scripts/python.exe';cfg=json.loads((ROOT/'candidate.json').read_text())
    code="import importlib.metadata as m,json,torch; print(json.dumps({'torch':torch.__version__,'torch_cuda':torch.version.cuda,'vcs':{p:json.loads(m.distribution(p).read_text('direct_url.json')) for p in ['transformers','peft']},'locations':{p:str(m.distribution(p).locate_file(p)) for p in ['transformers','peft']}}))"
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    identity=json.loads(subprocess.check_output([str(python),'-c',code],env=env,text=True,timeout=60))
    assert identity['torch']=='2.8.0+cpu' and identity['torch_cuda'] is None,identity
    for package in ('transformers','peft'):
        info=identity['vcs'][package];revision=cfg[package+'_git_revision']
        if 'vcs_info' in info:assert info['vcs_info']['commit_id']==revision,identity
        else:
            assert info['url']=='https://codeload.github.com/huggingface/'+package+'/zip/'+revision,identity
            assert info['archive_info']['hashes']['sha256'],identity
    manifest=json.loads((ROOT/'evidence-manifest.json').read_text());identity['installed_source_hashes']={}
    for package,relative in [('transformers','models/gemma4_unified/modeling_gemma4_unified.py'),('transformers','models/gemma4_unified/configuration_gemma4_unified.py'),('peft','tuners/lora/layer.py'),('peft','tuners/lora/model.py')]:
        file=Path(identity['locations'][package])/relative
        name=package+'-src_'+package+'_'+relative.replace('/','_')
        expected=next(x['sha256'] for x in manifest['files'] if x['file']==name)
        actual=hashlib.sha256(file.read_bytes()).hexdigest();assert actual==expected,(file,actual,expected)
        identity['installed_source_hashes'][package+'/'+relative]=actual
    (ROOT/'cpu-package-identity.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bound_seconds':120,'package_identity':'PASS','scope':'random tiny model CPU synthetic attach/backward/merge; no pretrained weights or generation'}
    output=ROOT/'cpu-runtime-probe.json'
    try:
        completed=subprocess.run([str(python),str(ROOT/'runtime_probe.py'),'--execute-synthetic','--output',str(output)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
        (ROOT/'evidence-private/cpu-probe.log').write_text(completed.stdout,encoding='utf-8')
        report['returncode']=completed.returncode;report['status']='PASS' if completed.returncode==0 else 'BLOCKED'
        if completed.returncode:report['failure_tail']=completed.stdout[-3000:]
    except subprocess.TimeoutExpired:report['status']='BLOCKED';report['error']='120-second hard timeout'
    report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/'cpu-probe-dispatch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
    raise SystemExit(report['status']!='PASS')
if __name__=='__main__':main()
