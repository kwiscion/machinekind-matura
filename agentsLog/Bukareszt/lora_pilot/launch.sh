#!/bin/bash
# Outside-the-wave launcher: waits for the frozen, hash-posted start, then execs the wave detached from SSH.
set -euo pipefail
RUN=/ephemeral/mm-lora/pilot-run1
source "$RUN/wave.env"
[ "$(date +%s)" -le $((WAVE_START_EPOCH + 120)) ] || { echo "start window passed; not launching" >&2; exit 9; }
while [ "$(date +%s)" -lt "$WAVE_START_EPOCH" ]; do sleep 1; done
exec flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s 3590s bash "$RUN/operator-stages.sh" > "$RUN/operator.out" 2>&1 < /dev/null
