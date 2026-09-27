#!/bin/bash
# #178 three-perspective visual strategy vs direct control (derived from the reviewed #117 eval16 operator).
# One owned llama-server with the eligible registry Gemma weights; 6 items x (direct + 3 independent views + final) = 30 primary calls.
# Answer-only exports per arm; descriptions are never exported.
# Launch exactly once, detached from the SSH session and outside the wave:
#   launch.sh: flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s "${T}s" (T = WAVE_DEADLINE_EPOCH - now, >= 3580) bash operator-stages.sh
# Everything inside is foreground in this one process group (inner timeouts use --foreground, clamped to deadline-90 s). It fails closed: set -euo pipefail,
# every stage has its own timeout, and a common absolute deadline comes from the frozen wave.env.
# No warmups. 30 primary calls, at most 120 attempts, at most 4,423,680 requested tokens; 0 training steps.
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
OPS=$R/image-perspectives-ops
PIN=$R/private-inputs/may2024-source-crops-v1
PREPARED=$PIN/prepared-six.jsonl
REG_Q4=/home/shadeform/mm/models/blobs/sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606
REG_PROJ=/home/shadeform/mm/models/blobs/sha256-675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842
REG_TEMPLATE_SHA=36e3a42e5cf14cd0020e72d92e1fdd9970f59b82170e421f0cbe1bb42bead3f0
INPUTS=$R/real-prep-in/eval16_input.jsonl
SETTINGS=$OPS/settings.json
CAND_Q4=$R/pilot-run3/export/candidate-q4_k_m.gguf
CAND_PROJ=$R/pilot-run3/export/candidate-projector.gguf
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
need 3300 "whole wave"
[ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ] || { log "competing GPU process; not adopting"; exit 4; }
( cd / && sha256sum -c --quiet "$RUN/pins.sha256" )
for f in "$RUN/ledger.jsonl" "$RUN/perspectives-raw.jsonl" "$RUN"/answers-*.jsonl; do [ ! -e "$f" ] || { log "stale $f"; exit 4; }; done

# ---- one owned session: per item direct, 3 independent views, final; 10-min reserve before the deadline ----
STAGE=perspectives
ATTEMPT_END=$(( WAVE_DEADLINE_EPOCH - 600 ))
log "attempts must start and finish before $(date -u -d @$ATTEMPT_END +%FT%TZ)"
TO $(( ATTEMPT_END - $(date +%s) + 300 )) "$GPU_PY" "$OPS/perspectives_session.py" --prepared "$PREPARED" --base-dir "$PIN" \
  --ids 6 14.1 18 25 1 23.2 --settings "$OPS/settings.json" --model "$REG_Q4" --mmproj "$REG_PROJ" --run "$RUN" \
  --deadline-epoch "$ATTEMPT_END" --max-wave-calls 120 --max-wave-tokens 4423680 --expected-template-sha "$REG_TEMPLATE_SHA"
log "ALL STAGES PASS"
