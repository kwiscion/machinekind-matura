#!/usr/bin/env python3
"""Spark GPU smoke: same 20 fixed DEV prompts through ollama REST (localhost:11434).

Run on dell-gb10: python3 spark-smoke.py
Writes: ~/models/spark-smoke.jsonl + prints summary. Stdlib only.
"""
import json
import sys
import time
import urllib.request

PROMPTS_PATH = "/home/ljaniec/models/prompts.jsonl"
OUT_PATH = "/home/ljaniec/models/spark-smoke.jsonl"
SYSTEM = "Jesteś asystentem historii. Odpowiadaj zwięźle po polsku. Jeśli nie masz pewności, napisz 'nie wiem'."


def chat(prompt):
    body = json.dumps({
        "model": "qwen3-8b-q4km",
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 200},
    }).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    return d, time.time() - t0


def main():
    # ensure model is warm
    chat("Cześć.")
    items = []
    with open(PROMPTS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    lat = []
    errors = 0
    t_start = time.time()
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for it in items:
            try:
                d, dt = chat(it["prompt"])
                lat.append(dt)
                rec = {
                    "id": it["id"], "model": "qwen3-8b-q4km@ollama-gpu-dell-gb10",
                    "prompt": it["prompt"],
                    "raw_response": d.get("message", {}).get("content"),
                    "prompt_tokens": d.get("prompt_eval_count"),
                    "completion_tokens": d.get("eval_count"),
                    "prompt_eval_s": round(d.get("prompt_eval_duration", 0) / 1e9, 3),
                    "eval_s": round(d.get("eval_duration", 0) / 1e9, 3),
                    "eval_rate_tok_s": round(d.get("eval_count", 0) / (d.get("eval_duration", 1) / 1e9), 2),
                    "wall_s": round(dt, 3), "error": None,
                    "timestamp": time.strftime("%FT%TZ", time.gmtime()),
                }
            except Exception as e:  # noqa: BLE001
                errors += 1
                rec = {"id": it["id"], "model": "qwen3-8b-q4km@ollama-gpu-dell-gb10",
                       "prompt": it["prompt"], "raw_response": None, "error": str(e),
                       "timestamp": time.strftime("%FT%TZ", time.gmtime())}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print(it["id"], rec.get("wall_s"), rec.get("eval_rate_tok_s"), flush=True)
    total = time.time() - t_start
    summary = {
        "model": "qwen3-8b-q4km@ollama-gpu-dell-gb10", "items": len(items), "errors": errors,
        "total_s": round(total, 1),
        "latency_mean_s": round(sum(lat) / len(lat), 3) if lat else None,
        "latency_median_s": round(sorted(lat)[len(lat) // 2], 3) if lat else None,
        "raw_output": OUT_PATH,
        "machine": "dell-gb10 (NVIDIA GB10, ollama 0.32.14, 100% GPU)",
    }
    with open("/home/ljaniec/models/spark-smoke-summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("SUMMARY", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
