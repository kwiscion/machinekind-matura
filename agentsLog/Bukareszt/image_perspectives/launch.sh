#!/bin/bash
# Outside-the-wave launcher: waits for the frozen, hash-posted start, then execs the wave detached from SSH.
set -euo pipefail
RUN=/ephemeral/mm-lora/image-perspectives-run1
source "$RUN/wave.env"
while [ "$(date +%s)" -lt "$WAVE_START_EPOCH" ]; do sleep 1; done
T=$(( WAVE_DEADLINE_EPOCH - $(date +%s) ))
[ "$T" -ge 3580 ] || { echo "$(date -u +%FT%TZ) late start (T=$T); not launching" >&2; exit 9; }
exec flock -n "$RUN.parent-lock" timeout --signal=TERM --kill-after=10s "${T}s" bash "$RUN/operator-stages.sh" > "$RUN/operator.out" 2>&1 < /dev/null
