"""Synthetic adapter -> GGUF conversion probe (converter support + real byte size only).

Builds a SYNTHETIC, UNTRAINED PEFT-format adapter (random small tensors, correct
shapes from the pinned base config and candidate.json regex) WITHOUT loading base
weights, then runs pinned llama.cpp convert_lora_to_gguf.py. This measures the
converter's support for Gemma4 Unified adapters and the emitted file size. It does
NOT prove adapter loading, serving, switching or any quality effect; no inference.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--llama', type=Path, required=True)
    ap.add_argument('--convert-python', required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    import torch
    from safetensors.torch import save_file
    cand = json.loads(a.candidate.read_text())
    lcfg = cand['lora']; r = lcfg['r']
    t = json.loads((a.base / 'config.json').read_text())['text_config']
    hid = t['hidden_size']; tensors = {}; modules = []
    for i, kind in enumerate(t['layer_types']):
        full = kind == 'full_attention'
        hd = t['global_head_dim'] if full else t['head_dim']
        outs = {'q_proj': t['num_attention_heads'] * hd}
        if not (full and t.get('attention_k_eq_v')):
            outs['v_proj'] = t['num_key_value_heads'] * hd
        for proj, out in outs.items():
            name = f'model.language_model.layers.{i}.self_attn.{proj}'
            assert re.fullmatch(lcfg['target_modules'], name), name
            modules.append(name)
            g = torch.Generator().manual_seed(len(modules))
            tensors[f'base_model.model.{name}.lora_A.weight'] = (torch.randn(r, hid, generator=g) * 0.01).to(torch.bfloat16)
            tensors[f'base_model.model.{name}.lora_B.weight'] = (torch.randn(out, r, generator=g) * 0.01).to(torch.bfloat16)
    params = sum(x.numel() for x in tensors.values())
    ad = a.work / 'synthetic-adapter'; ad.mkdir(parents=True, exist_ok=False)
    save_file(tensors, str(ad / 'adapter_model.safetensors'), metadata={'format': 'pt'})
    (ad / 'adapter_config.json').write_text(json.dumps({
        'peft_type': 'LORA', 'r': r, 'lora_alpha': lcfg['lora_alpha'], 'lora_dropout': lcfg['lora_dropout'], 'bias': 'none',
        'task_type': lcfg['task_type'], 'target_modules': lcfg['target_modules'], 'base_model_name_or_path': str(a.base),
        'SYNTHETIC_UNTRAINED_CONVERTER_PROBE': True}, indent=2))
    report = {'scope': 'SYNTHETIC untrained adapter; converter support and bytes only; no load/inference',
              'modules': len(modules), 'lora_parameters': params, 'bf16_tensor_bytes': params * 2,
              'peft_safetensors_bytes': (ad / 'adapter_model.safetensors').stat().st_size, 'gguf': {}}
    for outtype in ('bf16', 'f16', 'q8_0'):
        out = a.work / f'synthetic-adapter-{outtype}.gguf'
        done = subprocess.run([a.convert_python, str(a.llama / 'convert_lora_to_gguf.py'), str(ad), '--base', str(a.base),
                               '--outtype', outtype, '--outfile', str(out)], capture_output=True, text=True, timeout=600)
        entry = {'returncode': done.returncode, 'log_tail': (done.stdout + done.stderr)[-1500:]}
        if done.returncode == 0 and out.exists():
            entry['bytes'] = out.stat().st_size
            entry['sha256'] = hashlib.sha256(out.read_bytes()).hexdigest()
        report['gguf'][outtype] = entry
    report['status'] = 'PASS' if any(v['returncode'] == 0 for v in report['gguf'].values()) else 'FAIL'
    a.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: (v if k != 'gguf' else {o: {kk: vv for kk, vv in e.items() if kk != 'log_tail'} for o, e in v.items()}) for k, v in report.items()}, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
