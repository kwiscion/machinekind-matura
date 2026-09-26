#!/usr/bin/env python3
"""Smoke runner for issue #5 baseline: 10-20 fixed DEV prompts through llama.cpp.

Writes raw outputs to agentsLog/ljaniec/raw/<model>-smoke.jsonl and prints
a metrics summary (peak memory, latency, per-item latency). DEV prompts are
synthetic, rights-clear, inspired by public DEV structure (no real exam content).
"""
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # agentsLog/ljaniec
RAW = BASE / "raw"
MODELS = BASE / "models"

# 20 fixed DEV smoke prompts (synthetic, rights-clear; Polish-history flavored,
# NOT from any real exam — structure only). Deterministic across runs.
DEV_PROMPTS = [
    ("dev-smoke-001", "Wymień trzy przyczyny wojny północnej 1700-1721 w skrócie."),
    ("dev-smoke-002", "Podaj rok chrztu Polski i jeden źródłowy problem z tą datą."),
    ("dev-smoke-003", "Uporządkuj chronologicznie: konstytucja 3 maja, unia lubelska, pokój westfalski."),
    ("dev-smoke-004", "Kto był królem Polski w chwili bitwy pod Grunwaldem? Odpowiedz jednym zdaniem."),
    ("dev-smoke-005", "Krótko: co było treścią przywileju koszyckiego?"),
    ("dev-smoke-006", "Wymień dwa skutki rozbiorów Polski dla społeczeństwa."),
    ("dev-smoke-007", "Podaj rok pierwszego rozbioru Polski i mocarstwa rozbiorowe."),
    ("dev-smoke-008", "Krótko opisz rolę Sejmu Czteroletnego."),
    ("dev-smoke-009", "Uporządkuj: hołd pruski, potop szwedzki, elekcja Henryka Walezego."),
    ("dev-smoke-010", "Kto spisał pierwszą kronikę polską? Odpowiedz krótko."),
    ("dev-smoke-011", "Co to była demokracja szlachecka? Dwa zdania maksymalnie."),
    ("dev-smoke-012", "Podaj rok unii horodelskiej i jej główny skutek."),
    ("dev-smoke-013", "Wymień trzy nazwiska związane z oświeceniem stanisławowskim w Polsce."),
    ("dev-smoke-014", "Krótko: czym był rejestr pospolitego ruszenia? Jeśli nie wiesz, napisz 'nie wiem'."),
    ("dev-smoke-015", "Uporządkuj chronologicznie: sejm niemy, konfederacja barska, wojna o sukcesję polską."),
    ("dev-smoke-016", "Które miasto było stolicą Polski przed 1596? Krótko uzasadnij."),
    ("dev-smoke-017", "Podaj rok powstania listopadowego i jedną przyczynę."),
    ("dev-smoke-018", "Krótko: co regulował traktat ryski 1921?"),
    ("dev-smoke-019", "Wymień dwie formy oporu społecznego w Królestwie Polskim po 1864."),
    ("dev-smoke-020", "Podaj rok powstania warszawskiego 1944 i jedną kontrowersję historyczną z nim związaną."),
]

SYSTEM = "Jesteś asystentem historii. Odpowiadaj zwięźle po polsku. Jeśli nie masz pewności, napisz 'nie wiem'."


def peak_mem_mib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def run_model(llm, model_name):
    out_path = RAW / f"{model_name}-smoke.jsonl"
    latencies = []
    errors = 0
    t0 = time.time()
    with open(out_path, "w", encoding="utf-8") as f:
        for pid, prompt in DEV_PROMPTS:
            try:
                ts = time.time()
                resp = llm.create_chat_completion(
                    messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.0,
                )
                dt = time.time() - ts
                latencies.append(dt)
                text = resp["choices"][0]["message"]["content"]
                usage = resp.get("usage", {})
                rec = {
                    "id": pid, "model": model_name, "prompt": prompt,
                    "raw_response": text, "usage": usage, "latency_s": round(dt, 3),
                    "error": None, "timestamp": time.strftime("%FT%TZ", time.gmtime()),
                }
            except Exception as e:  # noqa: BLE001 — record, keep going
                errors += 1
                rec = {"id": pid, "model": model_name, "prompt": prompt, "raw_response": None,
                       "usage": None, "latency_s": None, "error": str(e), "timestamp": time.strftime("%FT%TZ", time.gmtime())}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
    total_s = time.time() - t0
    return {
        "model": model_name, "items": len(DEV_PROMPTS), "errors": errors,
        "total_s": round(total_s, 1),
        "latency_mean_s": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "latency_median_s": round(sorted(latencies)[len(latencies)//2], 3) if latencies else None,
        "peak_mem_mib": round(peak_mem_mib(), 1),
        "raw_output": str(out_path),
        "output_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }


def main():
    from llama_cpp import Llama
    results = []
    for gguf in sorted(MODELS.glob("*/*.gguf")):
        name = gguf.parent.name
        print(f"== loading {gguf} (n_threads={os.cpu_count()})")
        t0 = time.time()
        llm = Llama(model_path=str(gguf), n_ctx=4096, n_threads=os.cpu_count(), verbose=False)
        load_s = round(time.time() - t0, 1)
        print(f"   loaded in {load_s}s")
        m = run_model(llm, name)
        m["load_s"] = load_s
        results.append(m)
        print(f"   {name}: items={m['items']} errors={m['errors']} mean={m['latency_mean_s']}s peak={m['peak_mem_mib']}MiB")
        del llm
    summary_path = BASE / "baselines" / "smoke-summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("summary ->", summary_path)
    if not results:
        print("NO MODELS RAN — environment blocked; record blockers and fall back")


if __name__ == "__main__":
    main()
