#!/usr/bin/env bash
# Rebuild all #117 derived artifacts from committed drafts + independent reviews (deterministic).
# Usage: bash scripts/Bukareszt/essay_corpus_build.sh   (from repo root; raw sources must be staged locally)
set -euo pipefail
PY="python3 scripts/Bukareszt/essay_corpus.py"
E=agentsLog/Bukareszt/essay_corpus; D=$E/drafts; R=$E/reviews
ESS=(); REV=(); CHK=()
for b in b1 b1r b2 b2r b3 b3r; do
  [ -f "$D/${b}_essays.jsonl" ] || continue
  ESS+=("$D/${b}_essays.jsonl")
  cards=("$D/${b%r}_factcards.jsonl"); [ -f "$D/${b}_factcards.jsonl" ] && [ "$b" != "${b%r}" ] && cards+=("$D/${b}_factcards.jsonl")
  [ "$b" = b3 ] && cards+=("$D/b1_factcards.jsonl" "$D/b2_factcards.jsonl")
  [ "$b" = b3r ] && cards+=("$D/b1_factcards.jsonl" "$D/b2_factcards.jsonl")
  $PY check --essays "$D/${b}_essays.jsonl" --factcards "${cards[@]}" --out "$E/checks_${b}.json" >/dev/null
  CHK+=("$E/checks_${b}.json")
done
for f in b1_review1 b1r_review b2_review1 b2r_review b3_review1 b3r_review; do
  [ -f "$R/$f.jsonl" ] && REV+=("$R/$f.jsonl")
done
$PY groups >/dev/null
$PY evalcards >/dev/null
$PY ledger --essays "${ESS[@]}" --reviews "${REV[@]}" --checks "${CHK[@]}" --out "$E/ledger.jsonl"
$PY repairs --essays "${ESS[@]}" --reviews "${REV[@]}" --out "$E/repairs_v1.jsonl"
rm -rf "$E/export_v1"
$PY export --essays "${ESS[@]}" --reviews "${REV[@]}" --repairs "$E/repairs_v1.jsonl" --out-dir "$E/export_v1"
