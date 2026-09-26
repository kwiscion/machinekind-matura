#!/usr/bin/env python3
"""Smoke-test the contract JSONL path with a free local OpenAI-compatible server (LM Studio).

NON-CANDIDATE SMOKE MODEL. Use ONLY on synthetic prompts (never exam, VALIDATION, or
SEALED_TEST prompts) and never send answer keys. Outputs carry provenance: synthetic.

  python3 agentsLog/Pewciu6/harness/smoke_lmstudio.py --inputs agentsLog/Pewciu6/smoke/smoke_runner_input.jsonl \
      --out agentsLog/Pewciu6/smoke/smoke_outputs_qwen.jsonl
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matura_harness as mh  # noqa: E402

BLOCKED = ("VALIDATION", "SEALED", "validation_2024", "private/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://localhost:1234/v1/chat/completions")
    ap.add_argument("--model", default="qwen3.6-35b-a3b-abliterated-heretic-mlx")
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--timeout", type=float, default=300)
    a = ap.parse_args()
    if any(b in os.path.abspath(a.inputs) for b in BLOCKED):
        raise SystemExit("smoke runner refuses non-synthetic inputs")
    rows = mh.read_jsonl(a.inputs)
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in rows:
            body = {"model": a.model, "temperature": 0, "max_tokens": a.max_tokens,
                    "messages": [{"role": "user", "content": r["prompt"]}]}
            rec = {"id": r["id"], "backend": "lmstudio-openai-compat", "model": a.model,
                   "model_revision": "local-lmstudio (weights hash not recorded; non-candidate)",
                   "provenance": "synthetic", "provider": "local-lmstudio", "candidate": False,
                   "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
            t0 = time.time()
            try:
                req = urllib.request.Request(a.url, data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=a.timeout) as resp:
                    js = json.loads(resp.read().decode())
                msg = js["choices"][0]["message"]
                rec["raw_response"] = msg.get("content") or ""
                if msg.get("reasoning_content"):
                    rec["reasoning_chars"] = len(msg["reasoning_content"])
                rec["finish_reason"] = js["choices"][0].get("finish_reason")
                rec["usage"] = {k: v for k, v in (js.get("usage") or {}).items() if isinstance(v, (int, float))}
                rec["error"] = None
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                rec["raw_response"] = None
                rec["error"] = "%s: %s" % (type(exc).__name__, exc)
            rec["latency_s"] = round(time.time() - t0, 3)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(r["id"], rec.get("finish_reason"), rec["latency_s"], "error" if rec["error"] else "ok",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
