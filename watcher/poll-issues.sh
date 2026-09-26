#!/usr/bin/env bash
# Read-only GitHub issue watcher for @semberecki (Piotr) — machinekind-matura.
# Intended cadence: every quarter of an hour (cron: 7,22,37,52 * * * *).
# Read-only: no model calls, no purchases, no issue writes, no agent dispatch.
# Appends findings to watcher/2026-09-26-watcher-log.md; state snapshot lives in
# agentsLog/semberecki/private/watcher-state.json (gitignored).
# Unauthenticated GitHub REST API via stdlib python3 — works without gh/keyring.

set -u
cd "$(dirname "$0")/.."
exec python3 -B watcher/poll_issues.py "$@"
