"""Prepare the declared Gemma policy arm; never run inference."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2.jsonl'
NOTE = ROOT / 'agentsLog/kwiscion/2026-09-26-next-arm-recommendation.md'
CONFIG = ROOT / 'outputs/local-smoke/gemma4-12b-val40-1024.config.json'
V2_HASH = '6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4'
CONFIG_HASH = '3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa'
POLICY_HASH = '6a5827f450b15a0709093f3d2fd7fc2827e3cf8399befde0bfdb3b0cee768122'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(output):
    output = output.resolve()
    relative = output.relative_to(ROOT)
    if len(relative.parts) < 4 or relative.parts[:3] != ('agentsLog', 'kwiscion', 'private'):
        raise ValueError('Output must be under agentsLog/kwiscion/private/')
    manifest = output.with_name(output.name + '.manifest.json')
    if output.exists() or manifest.exists():
        raise ValueError('Both output and manifest must be fresh')
    # Keep original relative image paths byte-for-byte, not rewritten paths.
    if output.parent != SOURCE.parent:
        raise ValueError('Output must be a sibling of source v2 to preserve image paths')
    original = SOURCE.read_bytes()
    config = CONFIG.read_bytes()
    if sha(original) != V2_HASH or sha(config) != CONFIG_HASH:
        raise ValueError('Frozen v2 input or original config changed')
    policies = [line[2:] for line in NOTE.read_text(encoding='utf-8').splitlines() if line.startswith('> ')]
    if len(policies) != 1 or not policies[0].startswith('Answer in Polish.'):
        raise ValueError('Expected exactly the declared generic policy')
    policy = policies[0]
    if sha(policy.encode('utf-8')) != POLICY_HASH:
        raise ValueError('Declared policy changed; review before preparing another arm')
    rows = [json.loads(line) for line in original.splitlines()]
    if len(rows) != 40 or len({r['id'] for r in rows}) != 40:
        raise ValueError('Expected 40 unique rows')
    bootstrap_bytes = SOURCE.with_name('bootstrap_verification.json').read_bytes()
    bootstrap = json.loads(bootstrap_bytes)
    images = {}
    for row in rows:
        for image in row['images']:
            path = (SOURCE.parent / image).resolve()
            if SOURCE.parent not in path.parents:
                raise ValueError('Image resolves outside the private input folder')
            actual = sha(path.read_bytes())
            if actual != bootstrap['images'].get(image):
                raise ValueError('Image differs from bootstrap manifest')
            images[image] = actual
    prepared = [dict(row, prompt=policy + '\n\n' + row['prompt']) for row in rows]
    assert all({k: v for k, v in old.items() if k != 'prompt'} ==
               {k: v for k, v in new.items() if k != 'prompt'} for old, new in zip(rows, prepared))
    payload = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in prepared).encode('utf-8')
    report = {
        'status': 'prepared_not_authorized_to_launch', 'items': 40,
        'policy': policy, 'policy_sha256': sha(policy.encode('utf-8')),
        'policy_note_sha256': sha(NOTE.read_bytes()), 'source_v2_sha256': sha(original),
        'prepared_sha256': sha(payload), 'config_sha256': sha(config),
        'builder_sha256': sha(Path(__file__).read_bytes()),
        'bootstrap_manifest_sha256': sha(bootstrap_bytes), 'images': images,
        'ids_images_and_original_prompt_suffixes_preserved': True,
        'model_digest': '4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c',
        'context_tokens': 4096, 'max_input_tokens_including_images': 2816,
        'context_fit': 'UNPROVEN: no exact rendered multimodal token count available',
        'sampling': 'Original server defaults were not fixed; runner sends no temperature or seed',
        'max_calls': 40, 'max_output_tokens_per_call': 1024, 'max_requested_output_tokens': 40960,
        'model_calls': 0, 'paid_api_budget_usd': 0,
    }
    with output.open('xb') as stream:
        stream.write(payload)
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=SOURCE.with_name('runner_input.v2-question-policy.jsonl'))
    args = parser.parse_args()
    result = prepare(args.output)
    print(json.dumps({k: result[k] for k in ('status', 'items', 'policy_sha256', 'prepared_sha256', 'context_fit')}))
