# #117 one-epoch (12-step) checkpoint: exact rerun, export and eval16 plan (CPU-prepared, NOT run)

## 1. Does a 1-epoch or 12-step checkpoint already exist? **No.**

I searched `/ephemeral/mm-lora` and `/home/shadeform/mm-lora-pilot-backup` for `*checkpoint*`, `adapter_model.safetensors`, `adapter_config.json`, `*.pt` and `optimizer*`. The only adapters are:
- run3's final 36-step adapter, `pilot-run3/history/adapter/adapter_model.safetensors` (`6f6a5c3a…`, F32, 20,800,952 B), plus its backup copy;
- the synthetic converter-probe adapter, `control/adapter-probe/`.

Root's driver saves only the final adapter, never intermediate steps, so a 12-step state cannot be recovered and needs a rerun.

## 2. Change vs audited run3: epoch count only

The driver delta (`driver-one-epoch.diff`, 2 lines, applied to root's `run_real_pilot.py` `586acd0b…`, giving `run_real_pilot.py` `a64f5d70…`):
- line 27: the history step bound goes from 36 to **12**;
- line 108: `groups(len(rows))` becomes `groups(len(rows), epochs=1)`.

**Unchanged:**
- data: cleared train `83153814…` and clearance `9a317423…`, with the data gate still checking prepare.py's cleared 36-step envelope;
- row order: fixed, no shuffle; batch 1 × accumulation 8; the final 2-row group is kept, exactly as run3's epoch boundary;
- LR 1e-4, AdamW, seed 42, LoRA r8/α16/dropout 0.05 on q/v, BF16 pristine base `5a84cb31…`;
- tokenizer and template;
- torch 2.8.0+cu128 / transformers `96331a9f` / peft `b8674c86`;
- merge (`safe_merge`) with the multimodal-hash check;
- converter (`venv-convert-pinned`, llama.cpp `fcb3074f`), quantizer (`build/bin/llama-quantize`, Q4_K_M), serving binary and eval16 settings/ladder.

Because order and seed are fixed, epoch 1 is exactly run3's first 12 groups (`groups(90,1) == groups(90,3)[:12]`, checked). So the rerun reproduces run3's optimizer steps 1–12, subject to GPU-kernel nondeterminism. Run3's logged mean loss over steps 1–12 was 2.449, 2.356, 1.971, 0.770, 0.620, 0.427, 0.632, 0.544, 1.320, 1.778, 0.951, 0.530.

**New driver hash → new probe:** the history stage requires the probe report to come from the *same* driver hash, so the plan includes 1 synthetic real-base step with the one-epoch driver. The requalified control report (`pilot-run3/control-requalified-report.json`, `7e268798…`) is reused and pinned. There are no new control-serving calls.

## 3. One wave (≤ 60 min, one absolute deadline, the reviewed guards)

`one-epoch-stages.sh` is composed from the reviewed stages: the run2 probe, the run3 history/export and the eval16-run2 arms/ladder/blind pack. It keeps the same `TO`/`cap`, traps, verified backup, pins preflight and launcher.

| Stage | Bound | Expected, from measured run2/run3/eval16-run2 |
|---|---|---|
| preflight (pins, GPU idle, disk, stale checks) | none | < 1 min |
| probe: 1 synthetic step, new driver | ≤ 600 s | ~1 min (run2: 44 s) |
| history: **12 steps**, fresh pristine base, adapter + BF16 merge | ≤ 1500 s | ~3 min (run3's 36 steps took 346 s, about 6.7 s per step, plus load and merge) |
| export: text BF16 → Q4_K_M, projector, aggregate size gate | 600 + 300 + 600 s | ~3–4 min (run3: 2.2 min + size) |
| eval16 A (control) + B1 (one-epoch candidate): identical greedy nonthinking prompts, 4-attempt ladder 32768 → 49152 → 32768 → 32768 synthesis, per-arm wall budgets | ≤ 128 calls, ≤ 4,718,592 requested tokens, 600 s reserve | A ~2.3 min (eval16-run2: 16/16 first attempt). B1 ~2.3 min if it stops like the control; the worst case is bounded by the wall budget, with placeholders |
| blind pack (masked, sealed key) + verified backup | ≤ 120 s | < 1 min |

**Expected about 12–15 min, ≈ $0.7–0.8 at the unverified $3.28/h proxy. Hard cap 60 min, ≤ $3.28.**
- Disk: +23 GB merged BF16 and +30 GB export; 587 GB is free.
- Training: 1 synthetic step and 12 history steps. Calls: 32 primary, at most 128. No new downloads or builds.

Optional saving, root's choice: reuse eval16-run2's arm A answers (identical request bytes and greedy settings) and run only B1, which saves about 2.5 min. The default reruns A in the same wave for a clean within-wave pairing.

## 4. Files (host) and exact commands

```bash
R=/ephemeral/mm-lora
# CPU staging only (already done, frozen, hashes in pins.sha256):
#   $R/pilot-src-1ep/...  = copy of pilot-src2 with run_real_pilot.py replaced by the one-epoch driver (a64f5d70…)
#   $R/one-epoch-ops/make_manifest.py   (EXPECT driver a64f5d70…, history max_optimizer_steps 12)
#   $R/one-epoch-run1/{one-epoch-stages.sh, launch.sh, pins.sha256}
# Launch after a root declaration: write wave.env (start ≈ now + 2 min, deadline start + 3590 s), post the hashes, then
setsid nohup bash $R/one-epoch-run1/launch.sh > $R/one-epoch-run1/launch.err 2>&1 < /dev/null &
```

**Grading:** the same PR166 single pass by root/Sol on the masked pack; the sealed key is handed over after the grade is frozen. **No promotion** without full40/nonessay/image regression.
