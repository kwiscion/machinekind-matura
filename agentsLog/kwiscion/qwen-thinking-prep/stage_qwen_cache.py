"""Stage the exact closed Qwen cache using the reviewed CPU staging implementation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROFILE_SHA='953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d'
GUARD_SHA='8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473'
STAGER_SHA='4ce10d6b5736e29acf336da78b4a1f94140f1b9d4cb0e8788acb4c32b2deca07'
EXPECTED_BYTES=6594475420
EXPECTED_FILES=5

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def stage(source,destination):
    source=Path(source);destination=Path(destination)
    if destination.resolve().is_relative_to(source.resolve()):raise ValueError('Destination must stay outside source cache')
    shared=HERE.parent/'final-package-prep'
    if sha(HERE/'closed_profile.py')!=PROFILE_SHA or sha(shared/'guard.py')!=GUARD_SHA or sha(shared/'stage_recovery_cache.py')!=STAGER_SHA:raise ValueError('Reviewed profile/guard changed')
    profile=load('qwen_stage_profile',HERE/'closed_profile.py')
    staging=load('qwen_stage_shared',shared/'stage_recovery_cache.py')
    staging.g=profile.wrap_guard(staging.g)
    # The shared implementation copies only native referenced members, then
    # hashes the exact destination set and counts every hardlink entry fully.
    result=staging.stage(source,destination)
    staging.g.require(len(result['report']['files'])==EXPECTED_FILES and result['report']['counted_bytes']==EXPECTED_BYTES,'Exact five-file Qwen cache required')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.resolve().is_relative_to(args.source.resolve()):raise ValueError('Report must stay outside source cache')
    if args.report.exists() or args.report.is_symlink() or args.report.resolve().is_relative_to(args.destination.resolve()):raise ValueError('Fresh report outside cache required')
    result=stage(args.source,args.destination)
    with args.report.open('x',encoding='utf8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':'PASS','files':EXPECTED_FILES,'counted_bytes':result['report']['counted_bytes'],'model_calls':0,'services_started':0}))

if __name__=='__main__':main()
