"""CPU-only preparation of one generic Qwen coverage + optional full-Wikipedia RAG package."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deadline_runtime as policy


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coverage = load('deadline_coverage_prepare', HERE.parent / 'coverage-prep/prepare_coverage_exam.py')
INDEX_SHA = '5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36'
INDEX_BYTES = 10464555008


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Reviewed patch anchor changed: ' + old[:90])
    return text.replace(old, new)


def patch_binding(text, cleanup_sha=None):
    text = replace_once(text, "r=load('recovery_engine',HERE/'recovery_harness.py')",
        "r=load('recovery_engine',HERE/'recovery_harness.py')\n"
        "d=load('deadline_runtime',HERE/'deadline_runtime.py')")
    if cleanup_sha:
        text=replace_once(text,'n.GlobalStop=r.Fatal',"n.GlobalStop=r.Fatal\nn.PINS=dict(n.PINS);n.PINS['run_gemma_offline.py']='"+cleanup_sha+"'")
    text = replace_once(text,
        " n.need(m['max_calls']==len(ids)*4 and m['max_requested_tokens']==len(ids)*(32768*3+49152),'Exact four-attempt envelope')",
        " d.validate_envelope(root,m)")
    text = replace_once(text, ' return m,package,cases',
        ' package,cases=d.expand(root,package,cases,m)\n return m,package,cases')
    text = replace_once(text, ' runtime=OwnedRuntime(root,m,parent,proof)\n try:',
        " runtime=OwnedRuntime(root,m,parent,proof)\n try:\n"
        "  sys.path.insert(0,str(root))\n"
        "  deadline_hook=load('deadline_hook',root/'deadline_hook.py');deadline_hook.install(root,r,runtime)")
    text = replace_once(text, 'timeout=min(timeout,self.remaining()-20)',
        "timeout=min(timeout,self.remaining()-20);optional=getattr(self,'optional_deadline',None)\n"
        "  if optional is not None:timeout=min(timeout,optional-time.time()-15)")
    text = replace_once(text,
        " shutil.copyfile(out/'engine/answers.json',out/'answers.json')\n validate_final(out/'answers.json',package['template'])",
        " d.export_original(root,states,previous.get('stop') if binding else 'Stopped before dispatch')\n"
        " validate_final(out/'answers.json',n.read(root/'source-template.json'))")
    return text


def patch_harness(text):
    start=text.index('def atomic(path,value):')
    end=text.index('\ndef config(',start)
    text=text[:start]+"def atomic(path,value):\n from deadline_runtime import atomic as stable_atomic\n return stable_atomic(path,value)\n"+text[end:]
    text=replace_once(text,"   except Exception as exc:error=type(exc).__name__+': '+str(exc)",
        "   except Exception as exc:error=type(exc).__name__+': '+str(exc);text=None")
    text = replace_once(text, '   if not unresolved:break',
        '   unresolved=stage_barrier(unresolved,states,deadline,clock)\n   if not unresolved:break')
    text = replace_once(text, "   if timeout<c['minimum_timeout']:",
        "   timeout=stage_timeout(case,timeout,deadline,clock)\n"
        "   if timeout<c['minimum_timeout'] and stage_expired(case,clock):continue\n"
        "   if timeout<c['minimum_timeout']:")
    # Runtime.verify and optional retrieval can take time. Recheck the actual
    # optional time allowance immediately before the reservation / dispatch.
    text = replace_once(text, "   fault=faults.get(case['id']) if attempt==0 else None",
        "   timeout=stage_timeout(case,timeout,deadline,clock)\n"
        "   if timeout<c['minimum_timeout'] and stage_expired(case,clock):continue\n"
        "   if timeout<c['minimum_timeout']:raise Fatal('Optional budget ended before dispatch')\n"
        "   fault=faults.get(case['id']) if attempt==0 else None")
    text = replace_once(text, "    if clock()>=deadline:raise Fatal('Response arrived after hard deadline')",
        "    stage_response_deadline(case,clock)\n"
        "    if clock()>=deadline:raise Fatal('Response arrived after hard deadline')")
    return text


def prepare(args):
    if args.minutes != 60 or args.model != 'qwen':
        raise ValueError('Generic deadline RAG requires the reviewed 60-minute Qwen profile')
    root = args.output.resolve()
    if getattr(args,'auto_essay',False):
        sys.path.insert(0,str(HERE.parent/'essay-rag-prep'))
        helper=load('auto_essay_support',HERE/'essay_support.py')
        exam=policy.read(args.exam_dir/'exam.json')
        args.essay_id=[item['id'] for item in exam['items'] if helper.is_essay(item)]
        args.no_essay=not args.essay_id
    proof = policy.read(args.index_proof)
    if (proof.get('schema') != 'pre_acquisition_full_index_v1' or proof.get('index_path') != args.index
            or proof.get('sha256') != INDEX_SHA or proof.get('bytes') != INDEX_BYTES
            or set(proof.get('stat', {})) != {'st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns'}
            or not isinstance(proof.get('hostname'),str) or not proof['hostname']
            or not isinstance(proof.get('boot_id'),str) or not proof['boot_id']
            or proof['stat']['st_size'] != INDEX_BYTES
            or any(type(value) is not int for value in proof['stat'].values())):
        raise ValueError('A full-index verification receipt from the final host is required')
    manifest = coverage.prepare(copy.copy(args))
    # Exact baseline inputs and original-ID exam stay untouched in the package.
    shutil.copyfile(root / 'launch.json', root / 'coverage-prepared.json')
    shutil.copyfile(root / 'exam/answers-template.json', root / 'source-template.json')
    shutil.copyfile(args.exam_dir/'exam.json',root/'source-exam-original.json')
    shutil.copyfile(args.index_proof, root / 'index-proof.json')
    template = policy.read(root / 'source-template.json')
    plan = policy.make_plan(template, manifest['essay_ids'])
    plan.update(index_path=args.index, index_sha256=INDEX_SHA, index_bytes=INDEX_BYTES,
                articles=1587721, passages=2729746,
                fallback='Every failed, partial or unprocessed optional final preserves saved direct exactly',
                auxiliary_caps={'query_initial':512, 'essay_query_initial':768, 'judge_initial':384, 'retry':1024},
                answer_caps='Direct/ordinary unchanged32768/escalated49152; essay RAG16384thinking then8192thinking-off retries',
                dependency_policy='All direct work, essay six-query/top-five/filter/writer chains first, then ordinary query/top-five/filter/final chains')
    policy.atomic(root / 'study.json', plan)
    for name in ('deadline_runtime.py', 'deadline_hook.py', 'prepare_deadline_rag.py', 'verify_index.py','essay_support.py'):
        shutil.copyfile(HERE / name, root / name)
    for name in ('source_builder.py','auxiliary_hook.py'):
        shutil.copyfile(HERE.parent/'essay-rag-prep'/name,root/name)
    for name in ('study_hook.py', 'study_hook_v2.py'):
        shutil.copyfile(HERE.parent / 'filtered-rag-prep' / name, root / name)
    for name in ('search_query.py', 'wiki_index.py'):
        shutil.copyfile(HERE.parent / 'full-wikipedia' / name, root / name)
    search=root/'search_query.py'
    search.write_text(replace_once(search.read_text(encoding='utf8'),'?mode=ro', '?mode=ro&immutable=1'),encoding='utf8',newline='\n')
    cleanup=root/'run_gemma_offline.py';cleanup_text=cleanup.read_text(encoding='utf8')
    if cleanup_text.count('except (FileNotFoundError,ProcessLookupError):pass')!=3:raise ValueError('Reviewed cleanup scan anchors changed')
    cleanup.write_text(cleanup_text.replace('except (FileNotFoundError,ProcessLookupError):pass','except (FileNotFoundError,ProcessLookupError,PermissionError):pass'),encoding='utf8',newline='\n')
    for name, patch in [('run_recovery_package.py', patch_binding), ('recovery_harness.py', patch_harness)]:
        path = root / name
        shutil.copyfile(path, root / (name + '.baseline'))
        content=patch(path.read_text(encoding='utf8'),coverage.sha(cleanup)) if name=='run_recovery_package.py' else patch(path.read_text(encoding='utf8'))
        path.write_text(content, encoding='utf8', newline='\n')
    manifest.update(max_calls=plan['max_calls'], max_requested_tokens=plan['max_requested_tokens'])
    manifest['files'] = {path.relative_to(root).as_posix(): coverage.sha(path)
                         for path in root.rglob('*') if path.is_file() and path.name != 'launch.json'}
    policy.atomic(root / 'launch.json', manifest)
    packed = load('deadline_prepared_binding', root / 'run_recovery_package.py')
    packed.preflight(root)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exam-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--essay-id', action='append')
    group.add_argument('--no-essay', action='store_true')
    group.add_argument('--auto-essay', action='store_true')
    for name in ('cache', 'binary', 'lock', 'index'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--index-proof', type=Path, required=True)
    parser.add_argument('--minutes',type=int,choices=(60,),default=60)
    parser.set_defaults(model='qwen')
    args = parser.parse_args()
    result = prepare(args)
    print(json.dumps(dict(status='PREPARED_NOT_QUALIFIED_FOR_PROMOTION', model_calls=0,
        original_items=len(result['ids']), maximum_calls=result['max_calls'],
        maximum_requested_tokens=result['max_requested_tokens'],
        manifest_sha256=coverage.sha(args.output / 'launch.json'))))


if __name__ == '__main__':
    main()
