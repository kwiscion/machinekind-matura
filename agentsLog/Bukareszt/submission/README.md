# #37 Organizer package → offline `answers.json` — @Bukareszt

Issue: https://github.com/kwiscion/machinekind-matura/issues/37 · Branch: `issue-37-Bukareszt-submission-adapter` · Started 2026-09-26 14:40 Europe/Warsaw.

Adapter from the organizer exam package ([guide](https://matura-json-guide.ania-olchowik.chatgpt.site/)) to our `infer.py` input and back to a validated `answers.json`. Code: [`scripts/Bukareszt/matura_package.py`](../../../scripts/Bukareszt/matura_package.py) (stdlib only), tests: [`scripts/Bukareszt/test_matura_package.py`](../../../scripts/Bukareszt/test_matura_package.py). It wraps `infer.py` through its CLI; there is no second inference implementation.

## Offline command sequence

Preparation (network, once): `fetch-mock` downloads the public mock, verifies pinned SHA-256, unzips into an ignored folder and writes the aggregate manifest. For the final exam, download and unzip the organizer's package by hand into an ignored folder (e.g. `outputs/final/package/`) and start at `check`.

```bash
python3 scripts/Bukareszt/matura_package.py fetch-mock --out outputs/mock-2023 --manifest outputs/mock-2023/acquisition.json
PKG=outputs/mock-2023/package          # folder with exam.json, answers-template.json, images/
```

Offline (no internet; loopback model endpoint only):

```bash
# 1. validate the package (ids, fields, template agreement, PNG existence + sha256); optional count assertions
python3 scripts/Bukareszt/matura_package.py check --exam-dir $PKG --expect-items 37 --expect-points 60 --expect-images 19
# 2. package -> infer.py JSONL (+ input.jsonl.manifest.json)
python3 scripts/Bukareszt/matura_package.py prepare --exam-dir $PKG --output outputs/run1/input.jsonl
# 3. the existing runner, verified model config (max_output_tokens 2048-4096 recommended for the essay)
python3 infer.py --config config.qwen.local.example.json --input outputs/run1/input.jsonl --output outputs/run1/raw.jsonl --max-calls 37
# 4. raw records -> answers.json (+ answers.json.failures.json); exit 1 = valid file but some empty answers
python3 scripts/Bukareszt/matura_package.py finalize --exam-dir $PKG --raw outputs/run1/raw.jsonl --manifest outputs/run1/input.jsonl.manifest.json --output outputs/run1/answers.json
# 5. independent final check of the encoded file; exit 2 when invalid
python3 scripts/Bukareszt/matura_package.py validate outputs/run1/answers.json --exam-dir $PKG
```

Convenience wrapper (steps 2–5 in one new work folder; calls `infer.py` as a subprocess, never passes `--allow-remote`):

```bash
python3 scripts/Bukareszt/matura_package.py run --exam-dir $PKG --config <verified-config.json> --workdir outputs/run1 [--dry-run]
```

Tests: `python3 -m unittest discover -s scripts/Bukareszt -v`.

Details, evidence and limitations: [`REPORT.md`](REPORT.md) (added with the PR).
