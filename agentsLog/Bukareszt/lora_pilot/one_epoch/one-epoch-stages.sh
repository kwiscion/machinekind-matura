#!/bin/bash
# #117 ONE-EPOCH pilot + eval16 operator (composed from the reviewed run2 probe, run3 history/export and eval16-run2 stages).
# Only change vs run3: epoch count 3 -> 1 (12 optimizer steps). Stages: preflight, 1 synthetic probe step (new driver provenance),
# 12 fresh-pristine-base history steps, same-pipeline export + size gate, eval16 arms A (control) and B1 (1-epoch candidate), blind pack.
# Launch exactly once, detached from the SSH session and outside the wave:
#   launch.sh: flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s "${T}s" (T = WAVE_DEADLINE_EPOCH - now, >= 3580) bash eval-stages.sh
# Everything inside is foreground in this one process group (inner timeouts use --foreground, clamped to deadline-90 s). It fails closed: set -euo pipefail,
# every stage has its own timeout, and a common absolute deadline comes from the frozen wave.env.
# No warmups. 32 primary calls, at most settings.max_wave_calls (128) incl. recovery retries; 0 training steps.
set -euo pipefail
RUN=$(cd "$(dirname "$0")" && pwd)
source "$RUN/wave.env"          # WAVE_START_UTC WAVE_START_EPOCH WAVE_DEADLINE_UTC WAVE_DEADLINE_EPOCH (frozen, hash-posted)
STAGE_DEADLINE_UTC=$(date -u -d "@$(( WAVE_DEADLINE_EPOCH - 150 ))" +%Y-%m-%dT%H:%M:%SZ)  # driver SIGALRM fires before the inner/outer kills
R=/ephemeral/mm-lora
GPU_PY=$R/venv-gpu/bin/python
CONVERT_PY=$R/venv-convert-pinned/bin/python
L=$R/src/llama.cpp
QUANT=$L/build/bin/llama-quantize
PREPDIR=$R/pilot-src2/agentsLog/kwiscion/essay-lora-prep
DRIVER=$PREPDIR/run_real_pilot.py
OPS=$R/eval16-ops2
MOPS=$R/one-epoch-ops                                        # make_manifest.py (one-epoch EXPECT)
DRIVER=$R/pilot-src-1ep/agentsLog/kwiscion/essay-lora-prep/run_real_pilot.py
PREPDIR=$R/pilot-src-1ep/agentsLog/kwiscion/essay-lora-prep
CONTROL_REPORT=$R/pilot-run3/control-requalified-report.json  # reused requalified control (pinned)
INPUTS=$R/real-prep-in/eval16_input.jsonl
SETTINGS=$OPS/settings.json
CAND_Q4=$RUN/export/candidate-q4_k_m.gguf
CAND_PROJ=$RUN/export/candidate-projector.gguf
CONTROL_Q4=$R/control/base-q4_k_m.gguf
CONTROL_PROJ=$R/control/projector.gguf
BACKUP=/home/shadeform/mm-lora-pilot-backup/$(basename "$RUN")
STAGE=preflight

log()  { echo "$(date -u +%FT%TZ) [$STAGE] $*" | tee -a "$RUN/stages.log"; }
left() { echo $(( WAVE_DEADLINE_EPOCH - $(date +%s) )); }
need() { local l; l=$(left); if [ "$l" -lt "$1" ]; then log "STOP: $l s left < $1 s needed for $2"; exit 3; fi; }
cap()  { local l=$(( $(left) - 90 )); if [ "$l" -le 0 ]; then log "STOP: no time left for next command"; exit 3; fi; echo $(( $1 < l ? $1 : l )); }
TO()   { local n=$1; shift; local c; c=$(cap "$n"); timeout --foreground --signal=TERM --kill-after=10s "${c}s" "$@"; }
report_pass() { "$GPU_PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("status")=="PASS" else 1)' "$1"; }
backup() {
  mkdir -p "$BACKUP"
  ( cd "$RUN" && find . -maxdepth 3 -type f \( -name '*.json' -o -name '*.jsonl' -o -name '*.log' -o -name '*.sh' -o -name '*.env' -o -name '*.txt' -o -name '*.out' -o -name '*.sha256' \) -size -50M -print0 \
      | xargs -0 -r cp --parents -t "$BACKUP" ) || return 1
  if [ -d "$RUN/history/adapter" ]; then mkdir -p "$BACKUP/history" && cp -r "$RUN/history/adapter" "$BACKUP/history/" || return 1; fi
  ( cd "$BACKUP" && find . -type f ! -name BACKUP_SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > BACKUP_SHA256SUMS && sha256sum -c --quiet BACKUP_SHA256SUMS ) || return 1
  echo "$(date -u +%FT%TZ) backup verified: $BACKUP ($(wc -l < "$BACKUP/BACKUP_SHA256SUMS") files)" >> "$RUN/stages.log"
}
finish() { local rc=$?; trap - EXIT; log "TERMINAL rc=$rc left=$(left)s"; backup || log "BACKUP FAILED"; exit $rc; }
trap finish EXIT
trap 'log "TERM received"; exit 143' TERM

# ---- preflight (no model use) ----
log "wave start=$WAVE_START_UTC deadline=$WAVE_DEADLINE_UTC left=$(left)s"
need 3300 "whole one-epoch wave"
[ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ] || { log "competing GPU process; not adopting"; exit 4; }
[ "$(df --output=avail -B1 /ephemeral | tail -1)" -gt 150000000000 ] || { log "insufficient disk"; exit 4; }
( cd / && sha256sum -c --quiet "$RUN/pins.sha256" )
for d in probe history export blind; do [ ! -e "$RUN/$d" ] || { log "stale $RUN/$d"; exit 4; }; done
for f in "$RUN/call-ledger.jsonl" "$RUN"/answers-*.jsonl; do [ ! -e "$f" ] || { log "stale $f"; exit 4; }; done
report_pass "$CONTROL_REPORT"

# ---- stage 1: synthetic real-base probe with the one-epoch driver (1 optimizer step) ----
STAGE=probe; need 3000 "probe+rest"
"$GPU_PY" "$MOPS/make_manifest.py" probe --run "$RUN" --deadline-utc "$STAGE_DEADLINE_UTC" | tee -a "$RUN/stages.log"
"$GPU_PY" "$DRIVER" "$RUN/probe-manifest.json"
TO 610 "$GPU_PY" "$DRIVER" "$RUN/probe-manifest.json" --execute > "$RUN/probe-driver.log" 2>&1
report_pass "$RUN/probe/report.json"
log "probe PASS"

# ---- stage 2: fresh pristine-base ONE-EPOCH history (12 steps, <=1500 s) ----
STAGE=history; need 2700 "history + export + eval reserve"
"$GPU_PY" "$MOPS/make_manifest.py" history --run "$RUN" --deadline-utc "$STAGE_DEADLINE_UTC" \
  --probe-report "$RUN/probe/report.json" --control-report "$CONTROL_REPORT" | tee -a "$RUN/stages.log"
"$GPU_PY" "$DRIVER" "$RUN/history-manifest.json"
TO 1510 "$GPU_PY" "$DRIVER" "$RUN/history-manifest.json" --execute > "$RUN/history-driver.log" 2>&1
report_pass "$RUN/history/report.json"
log "history PASS"

# ---- stage 3: same-pipeline export + aggregate size gate ----
STAGE=export; need 1800 "export + eval"
mkdir "$RUN/export"
TO 600 "$CONVERT_PY" "$L/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" --outtype bf16 --outfile "$RUN/export/candidate-bf16.gguf" > "$RUN/export/convert_text.log" 2>&1
TO 300 "$CONVERT_PY" "$L/convert_hf_to_gguf.py" "$RUN/history/merged-bf16" --mmproj --outtype bf16 --outfile "$RUN/export/candidate-projector.gguf" > "$RUN/export/convert_mmproj.log" 2>&1
test -s "$RUN/export/candidate-bf16.gguf"; test -s "$RUN/export/candidate-projector.gguf"
TO 600 "$QUANT" "$RUN/export/candidate-bf16.gguf" "$RUN/export/candidate-q4_k_m.gguf" Q4_K_M > "$RUN/export/quantize.log" 2>&1
test -s "$RUN/export/candidate-q4_k_m.gguf"
"$GPU_PY" "$PREPDIR/prepare.py" size "$RUN/export/candidate-q4_k_m.gguf" "$RUN/export/candidate-projector.gguf" > "$RUN/export/size-candidate.json"
sha256sum "$RUN"/export/*.gguf > "$RUN/export/sha256.txt"
log "export PASS $(grep -o '"total_bytes": [0-9]*' "$RUN/export/size-candidate.json")"

# ---- stage 4: eval16 paired arms (reviewed eval16-run2 session/ladder, unchanged settings) ----
ARMS=$("$GPU_PY" -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["run_arms"]))' "$SETTINGS")
CAP=$("$GPU_PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["max_wave_calls"])' "$SETTINGS")
TOKCAP=$("$GPU_PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["max_wave_requested_tokens"])' "$SETTINGS")
RESERVE=600   # 10 min recovery/finalization kept before the wave deadline (root declaration)
log "arms=$ARMS call_cap=$CAP token_cap=$TOKCAP"

# ---- one owned server session per arm; per-item recovery ladder inside the session ----
NARMS=$(echo $ARMS | wc -w); I=0
for ARM in $ARMS; do
  STAGE=arm_$ARM; I=$((I+1))
  case $ARM in
    A|C) M=$CONTROL_Q4; P=$CONTROL_PROJ ;;
    B)   M=$CAND_Q4;    P=$CAND_PROJ ;;
  esac
  need $((RESERVE + 600)) "arm $ARM"
  NOW=$(date +%s); AVAIL=$(( WAVE_DEADLINE_EPOCH - RESERVE - NOW ))
  ARM_END=$(( NOW + AVAIL / (NARMS - I + 1) ))   # equal split of the remaining budget across remaining arms
  log "arm $ARM attempts must start and finish before $(date -u -d @$ARM_END +%FT%TZ)"
  TO $(( ARM_END - NOW + 300 )) "$GPU_PY" "$OPS/eval16_session.py" --arm "$ARM" --model "$M" --mmproj "$P" --inputs "$INPUTS" \
    --settings "$SETTINGS" --run "$RUN" --out "$RUN/answers-$ARM.jsonl" --max-wave-calls "$CAP" --max-wave-tokens "$TOKCAP" --arm-deadline-epoch "$ARM_END"
  log "arm $ARM done"
done

# ---- CPU-only: deterministic checks + blinded grading pack (sealed key) ----
STAGE=blind_pack
TO 120 "$GPU_PY" "$OPS/make_blind_pack.py" --run "$RUN" --inputs "$INPUTS" --arms $ARMS
log "ALL STAGES PASS"
