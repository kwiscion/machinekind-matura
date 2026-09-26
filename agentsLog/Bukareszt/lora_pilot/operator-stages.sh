#!/bin/bash
# #117 finite LoRA pilot operator (root declaration 2026-09-26 21:07Z + 21:24Z window).
# Launch exactly once, detached from the SSH session and outside the wave:
#   setsid nohup flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s 3590s bash "$RUN/operator-stages.sh"
# Everything inside is foreground, in this one process group. It fails closed: set -euo pipefail,
# every stage has its own timeout, and a common absolute deadline comes from the frozen wave.env.
# No retries, no warmups, no history eval. At most 1 synthetic step + 36 history steps + 4 synthetic calls.
set -euo pipefail
RUN=$(cd "$(dirname "$0")" && pwd)
source "$RUN/wave.env"          # WAVE_START_UTC WAVE_DEADLINE_UTC WAVE_DEADLINE_EPOCH (frozen, hash-posted)
R=/ephemeral/mm-lora
GPU_PY=$R/venv-gpu/bin/python
CONVERT_PY=$R/venv-convert-pinned/bin/python
L=$R/src/llama.cpp
QUANT=$L/build/bin/llama-quantize
PREPDIR=$R/pilot-src/agentsLog/kwiscion/essay-lora-prep
DRIVER=$PREPDIR/run_real_pilot.py
OPS=$R/pilot-ops
CONTROL_Q4=$R/control/base-q4_k_m.gguf
CONTROL_PROJ=$R/control/projector.gguf
BACKUP=/home/shadeform/mm-lora-pilot-backup/$(basename "$RUN")
STAGE=preflight

log()  { echo "$(date -u +%FT%TZ) [$STAGE] $*" | tee -a "$RUN/stages.log"; }
left() { echo $(( WAVE_DEADLINE_EPOCH - $(date +%s) )); }
need() { local l; l=$(left); if [ "$l" -lt "$1" ]; then log "STOP: $l s left < $1 s needed for $2"; exit 3; fi; }
report_pass() { "$GPU_PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("status")=="PASS" else 1)' "$1"; }
backup() {
  mkdir -p "$BACKUP"
  ( cd "$RUN" && find . -maxdepth 3 -type f \( -name '*.json' -o -name '*.jsonl' -o -name '*.log' -o -name '*.sh' -o -name '*.env' -o -name '*.txt' -o -name '*.out' \) -size -50M -print0 \
      | xargs -0 -r cp --parents -t "$BACKUP" )
  if [ -d "$RUN/history/adapter" ]; then mkdir -p "$BACKUP/history" && cp -r "$RUN/history/adapter" "$BACKUP/history/"; fi
  ( cd "$BACKUP" && find . -type f ! -name BACKUP_SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > BACKUP_SHA256SUMS && sha256sum -c --quiet BACKUP_SHA256SUMS )
  echo "$(date -u +%FT%TZ) backup verified: $BACKUP ($(wc -l < "$BACKUP/BACKUP_SHA256SUMS") files)" >> "$RUN/stages.log"
}
finish() { local rc=$?; trap - EXIT; log "TERMINAL rc=$rc left=$(left)s"; backup || log "BACKUP FAILED"; exit $rc; }
trap finish EXIT
trap 'log "TERM received"; exit 143' TERM

# ---- preflight (no model use) ----
log "wave start=$WAVE_START_UTC deadline=$WAVE_DEADLINE_UTC left=$(left)s"
need 3000 "whole pilot"
[ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ] || { log "competing GPU process; not adopting"; exit 4; }
[ "$(df --output=avail -B1 /ephemeral | tail -1)" -gt 150000000000 ] || { log "insufficient disk"; exit 4; }
( cd / && sha256sum -c --quiet "$RUN/pins.sha256" )
for d in probe history export; do [ ! -e "$RUN/$d" ] || { log "stale $RUN/$d"; exit 4; }; done
[ ! -e "$RUN/call-ledger.jsonl" ] || { log "stale ledger"; exit 4; }

# ---- stage 1: real-base synthetic probe (1 optimizer step, <=600 s) ----
STAGE=probe; need 2900 "probe+rest"
"$GPU_PY" "$OPS/make_manifest.py" probe --run "$RUN" --deadline-utc "$WAVE_DEADLINE_UTC" | tee -a "$RUN/stages.log"
"$GPU_PY" "$DRIVER" "$RUN/probe-manifest.json"
timeout --signal=TERM --kill-after=10s 610s "$GPU_PY" "$DRIVER" "$RUN/probe-manifest.json" --execute > "$RUN/probe-driver.log" 2>&1
report_pass "$RUN/probe/report.json"
log "probe PASS"

# ---- stage 2: unmodified export control serving (2 synthetic calls) ----
STAGE=control_serving; need 2600 "control serving+history+export"
timeout --signal=TERM --kill-after=10s 480s "$GPU_PY" "$OPS/serve_session.py" --artifact control \
  --model "$CONTROL_Q4" --mmproj "$CONTROL_PROJ" --run "$RUN" --report "$RUN/control-serving-report.json"
report_pass "$RUN/control-serving-report.json"
log "control serving PASS (predeclared criteria)"

# ---- stage 3: fresh pristine-base history pilot (36 steps, <=1500 s) ----
STAGE=history; need 2400 "history 1500 s + export/candidate/backup reserve 900 s"
"$GPU_PY" "$OPS/make_manifest.py" history --run "$RUN" --deadline-utc "$WAVE_DEADLINE_UTC" \
  --probe-report "$RUN/probe/report.json" --control-report "$RUN/control-serving-report.json" | tee -a "$RUN/stages.log"
"$GPU_PY" "$DRIVER" "$RUN/history-manifest.json"
timeout --signal=TERM --kill-after=10s 1510s "$GPU_PY" "$DRIVER" "$RUN/history-manifest.json" --execute > "$RUN/history-driver.log" 2>&1
report_pass "$RUN/history/report.json"
log "history PASS"

# ---- stage 4: fresh candidate export with the same pinned pipeline as the control ----
STAGE=export; need 600 "export"
mkdir "$RUN/export"
timeout 600s "$CONVERT_PY" "$L/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" --outtype bf16 --outfile "$RUN/export/candidate-bf16.gguf" > "$RUN/export/convert_text.log" 2>&1
timeout 300s "$CONVERT_PY" "$L/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" --mmproj --outtype bf16 --outfile "$RUN/export/candidate-projector.gguf" > "$RUN/export/convert_mmproj.log" 2>&1
test -s "$RUN/export/candidate-bf16.gguf"; test -s "$RUN/export/candidate-projector.gguf"
timeout 600s "$QUANT" "$RUN/export/candidate-bf16.gguf" "$RUN/export/candidate-q4_k_m.gguf" Q4_K_M > "$RUN/export/quantize.log" 2>&1
test -s "$RUN/export/candidate-q4_k_m.gguf"
"$GPU_PY" "$PREPDIR/prepare.py" size "$RUN/export/candidate-q4_k_m.gguf" "$RUN/export/candidate-projector.gguf" > "$RUN/export/size-candidate.json"
log "export PASS $(grep -o '"total_bytes": [0-9]*' "$RUN/export/size-candidate.json")"

# ---- stage 5: candidate serving (2 synthetic calls, identical fixtures/settings) ----
STAGE=candidate_serving; need 360 "candidate serving"
CAND_RC=0
timeout --signal=TERM --kill-after=10s 480s "$GPU_PY" "$OPS/serve_session.py" --artifact candidate \
  --model "$RUN/export/candidate-q4_k_m.gguf" --mmproj "$RUN/export/candidate-projector.gguf" --run "$RUN" --report "$RUN/candidate-serving-report.json" || CAND_RC=$?
log "candidate serving rc=$CAND_RC"

# ---- stage 6: inventory (read-only) ----
STAGE=inventory
( sha256sum "$RUN"/export/*.gguf "$CONTROL_Q4" "$CONTROL_PROJ"; find "$RUN/history/adapter" "$RUN/history/merged-bf16" -type f -print0 | xargs -0 sha256sum ) > "$RUN/inventory-sha256.txt"
ls -l "$RUN"/export/*.gguf "$CONTROL_Q4" "$CONTROL_PROJ" >> "$RUN/inventory-sha256.txt"
timeout 300s "$CONVERT_PY" "$OPS/gguf_diff.py" "$CONTROL_Q4" "$RUN/export/candidate-q4_k_m.gguf" "control vs candidate text" > "$RUN/gguf-diff-control-candidate.json" 2>&1 || log "gguf diff failed (non-fatal, read-only)"
[ "$CAND_RC" -eq 0 ] || { log "candidate serving did not meet criteria"; exit 5; }
log "ALL STAGES PASS"
