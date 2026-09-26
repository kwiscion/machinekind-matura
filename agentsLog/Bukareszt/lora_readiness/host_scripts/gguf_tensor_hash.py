"""Read-only per-tensor data hash comparison of two GGUFs (no inference)."""
import sys, json, hashlib
sys.path.insert(0, '/ephemeral/mm-lora/src/llama.cpp/gguf-py')
from gguf import GGUFReader
def hashes(p):
    return {t.name: hashlib.sha256(t.data.tobytes()).hexdigest() for t in GGUFReader(p, 'r').tensors}
a, b = hashes(sys.argv[1]), hashes(sys.argv[2])
diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
agg = lambda h: hashlib.sha256(''.join(f'{k}:{h[k]}\n' for k in sorted(h)).encode()).hexdigest()
print(json.dumps({'label': sys.argv[3], 'tensors': [len(a), len(b)], 'identical_tensor_data': len(set(a)) - len(diff) if set(a) == set(b) else None,
                  'differing': len(diff), 'differing_first20': diff[:20], 'tensor_set_sha256': [agg(a), agg(b)]}, indent=1))
