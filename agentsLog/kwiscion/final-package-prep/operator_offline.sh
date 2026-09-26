#!/usr/bin/env bash
# Explicit launch wrapper. It never fills declaration timestamps or starts a model by default.
set -euo pipefail
if [ "$#" -ne 2 ] || [ "$2" != --execute ]; then
  echo 'Usage: bash operator_offline.sh /absolute/private/package --execute' >&2
  exit 2
fi
package=$(realpath -- "$1")
cleanup() {
  if [ -f "$package/results/network-proof.json" ]; then
    timeout --signal=KILL 5s python3 -B "$package/run_gemma_offline.py" "$package" --cleanup
  fi
}
trap cleanup EXIT
# 1190-second guardian + 5-second kill grace + 5-second cleanup <= 1200 seconds.
timeout --signal=TERM --kill-after=5s 1190s python3 -B "$package/run_gemma_offline.py" "$package" --execute
