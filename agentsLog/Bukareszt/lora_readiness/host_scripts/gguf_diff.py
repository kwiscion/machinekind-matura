"""Read-only GGUF header/tensor-table diff (no inference). usage: gguf_diff.py A B label"""
import sys, json
sys.path.insert(0, '/ephemeral/mm-lora/src/llama.cpp/gguf-py')
from gguf import GGUFReader
def load(p):
    r = GGUFReader(p, 'r')
    kv = {}
    for f in r.fields.values():
        if f.name.startswith('GGUF.'): continue
        try: v = f.contents()
        except Exception: v = '?'
        if isinstance(v, list) and len(v) > 8: v = f'list[{len(v)}] hash={hash(json.dumps(v, default=str))}'
        kv[f.name] = v
    t = {x.name: (x.tensor_type.name, [int(s) for s in x.shape], int(x.n_bytes)) for x in r.tensors}
    return kv, t
a, b = load(sys.argv[1]), load(sys.argv[2])
kd = {k: [a[0].get(k, '<absent>'), b[0].get(k, '<absent>')] for k in sorted(set(a[0]) | set(b[0])) if a[0].get(k) != b[0].get(k)}
td = {k: [a[1].get(k), b[1].get(k)] for k in sorted(set(a[1]) | set(b[1])) if a[1].get(k) != b[1].get(k)}
print(json.dumps({'label': sys.argv[3], 'kv_counts': [len(a[0]), len(b[0])], 'tensor_counts': [len(a[1]), len(b[1])],
  'kv_diffs': kd, 'tensor_meta_diff_count': len(td), 'tensor_meta_diff_first10': dict(list(td.items())[:10]),
  'tensor_types': [sorted({v[0] for v in a[1].values()}), sorted({v[0] for v in b[1].values()})]}, indent=1, default=str))
