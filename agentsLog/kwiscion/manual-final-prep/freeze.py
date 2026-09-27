"""Freeze source bytes before the owner acquires the final package; no model calls."""
import datetime,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];OWNER=HERE.parent
def main():
 paths=set()
 for name in ('manual-final-prep','deadline-rag-prep','coverage-prep','qwen-thinking-prep','final-package-prep','filtered-rag-prep','full-wikipedia'):
  paths.update((OWNER/name).glob('*.py'))
 paths.update(OWNER/x for x in ('essay-coverage-prep/coverage_suffix.py','essay-rag-prep/source_builder.py','essay-rag-prep/auxiliary_hook.py','offline_rehearsal.py'))
 paths.update(REPO/x for x in ('infer.py','scripts/Bukareszt/matura_package.py','scripts/run-final.ps1'))
 paths.update(HERE/x for x in ('index-proof.json','weights-proof.json'))
 excluded={'qwen-thinking-prep/prepare.py','qwen-thinking-prep/run_qwen_thinking.py','qwen-thinking-prep/runtime_guard.py'}
 paths={p for p in paths if not p.name.startswith('test_') and not (p.is_relative_to(OWNER) and p.relative_to(OWNER).as_posix() in excluded)}
 value={'schema':'manual_final_frozen_sources_v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{p.relative_to(REPO).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
 file=HERE/'frozen-sources.json';file.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({'files':len(value['files']),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
