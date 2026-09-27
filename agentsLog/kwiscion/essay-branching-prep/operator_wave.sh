#!/usr/bin/env bash
set -euo pipefail
[ "$#" -eq 1 ] || exit 2
root=$(realpath -- "$1")
python3 -B "$root/staged_wave.py" check "$root"
lock=$(python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["host_lock"])' "$root/wave.json")
exec 9>>"$lock"
flock -n 9
cleanup() {
  timeout --signal=KILL 10s python3 -B "$root/staged_wave.py" cleanup "$root"
}
trap cleanup EXIT
budget=$(python3 -B -c 'import datetime,json,math,sys,time; m=json.load(open(sys.argv[1])); assert m["status"]=="DECLARED"; n=math.floor(datetime.datetime.fromisoformat(m["deadline_utc"]).timestamp()-time.time())-15; assert 0<n<=3585; print(n)' "$root/wave.json")
timeout --signal=TERM --kill-after=5s "${budget}s" python3 -B "$root/staged_wave.py" execute "$root" --guarded
