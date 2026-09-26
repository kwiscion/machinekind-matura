import sys, json, hashlib, collections
sys.path.insert(0, '/ephemeral/mm-lora/src/llama.cpp/gguf-py')
from gguf import GGUFReader
ta = {t.name: t for t in GGUFReader(sys.argv[1], 'r').tensors}
tb = {t.name: t for t in GGUFReader(sys.argv[2], 'r').tensors}
h = lambda t: hashlib.sha256(t.data.tobytes()).digest()
c = collections.Counter()
for n in ta:
    c[f"{ta[n].tensor_type.name}:{'same' if h(ta[n]) == h(tb[n]) else 'diff'}"] += 1
out = {'by_type': dict(c)}
for n in ('token_embd.weight', 'output.weight'):
    if n in ta: out[n] = {'type': ta[n].tensor_type.name, 'same': h(ta[n]) == h(tb[n])}
print(json.dumps(out, indent=1))
