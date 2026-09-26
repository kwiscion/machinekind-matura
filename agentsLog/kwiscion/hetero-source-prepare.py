"""Prepare metadata-only public manifest; does not generate or contact a model."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('hetero', HERE / 'hetero-source-controller.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
input_path = HERE / 'private/validation_2024_keyfree/runner_input.v2.jsonl'
ids = ['val2024-hist-z1', 'val2024-hist-z2', 'val2024-hist-z4',
       'val2024-hist-z5.1', 'val2024-hist-z14.1', 'val2024-hist-z15.2']
rows = [json.loads(line) for line in input_path.read_text(encoding='utf8').splitlines()]
if len({row['id'] for row in rows}) != len(rows):
    raise ValueError('Duplicate source input IDs')
panel = [row for row in rows if row['id'] in ids]
if [row['id'] for row in panel] != ids:
    raise ValueError('Panel membership/order')
manifest = {
    'status': 'CPU_PREPARATION_NOT_AUTHORIZATION_TO_RUN',
    'family': 'qwen_observer_gemma_solver_full_sources',
    'scope': 'six-case known-validation development; no full-exam score claim',
    'ids': ids, 'parent_input_sha256': sha(input_path),
    'original_prompt_sha256': {x['id']: hashlib.sha256(x['prompt'].encode()).hexdigest() for x in panel},
    'images': {p: sha(input_path.parent / p) for x in panel for p in x.get('images', [])},
    'models_by_stage': r.MODELS, 'model_digests': r.PINS,
    'qwen_native_weights': {'bytes': 6594462816,
        'sha256': 'dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c',
        'separate_projector': False, 'local_disk_verified': False},
    'gemma_native_weights': {'bytes': 7556497632,
        'model_sha256': '1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606',
        'projector_sha256': '675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842'},
    'runtime_version': '0.34.4', 'context_length': 32768,
    'runtime_executable_sha256': None, 'deadline_utc': None,
    'caps': {s: 1024 for s in r.STAGES}, 'max_calls': 18,
    'max_requested_output_tokens': 18432, 'max_elapsed_seconds': 2700,
    'request_timeout_seconds': 420, 'retries': 0,
    'sampling': 'reasoning_effort none; temperature and other sampling overrides omitted',
    'fallback': 'Only validated local empty/length observation uses unchanged original final in its reserved slot; systemic/uncertain errors stop all stages',
    'observation_prompt': r.OBSERVATION, 'final_prompt': r.FINAL,
    'files': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in [
        HERE / 'hetero-source-controller.py', HERE / 'hetero-source-test.py',
        HERE / 'hetero-source-prepare.py', HERE / 'run_source_observation.py',
        HERE / 'run_gemma_package.py', ROOT / 'infer.py',
        ROOT / 'scripts/Bukareszt/matura_package.py']},
    'launch_requirements': [
        'Independent CPU review; actual immutable host/weights/runtime/file pins',
        'Owned worker lock, GPU process ownership, enforced deadline and durable reservations',
        'Reviewed transport capture and guard wiring; controller alone is not an inference CLI',
        'Any readiness calls separately declared within parent envelope, never hidden in18',
        'Root launch declaration and no conflicting worker'],
}
destination = HERE / 'hetero-source-manifest-template.json'
destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(destination)
