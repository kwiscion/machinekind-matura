#!/usr/bin/env python3
"""Read-only GitHub issue watcher for @semberecki (Piotr) — machinekind-matura.

Polls the public GitHub REST API (unauthenticated; conditional GETs via ETag
save rate limit), filters issues assigned to or mentioning Piotr
(semberecki / Piotr / Piotrek), and appends new findings to the watcher log.

Rules (standing, from the owner — pass verbatim to any session):
- Poll every quarter of an hour; on new items dispatch a subagent task.
- Post results into the triggering issue; open new issues marking Piotr for
  discovered follow-ups; inform other agents.
- Results go to agentsLog/ (agentsLog/semberecki/) as the shared knowledge center.
- Keep polling while subagents run. Do not wait for owner approval to merge
  scoped additive PRs.
- NEVER buy anything.

This script is read-only: no model calls, no purchases, no issue writes,
no agent dispatch. It only records findings.

Stdlib only. Machine-local state lives under agentsLog/semberecki/private/
(gitignored by the shared .gitignore).
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO = "kwiscion/machinekind-matura"
API = f"https://api.github.com/repos/{REPO}"
WATCHER_DIR = Path(__file__).resolve().parent.parent / "watcher"
LOG = WATCHER_DIR / "2026-09-26-watcher-log.md"
STATE_DIR = Path(__file__).resolve().parent.parent / "agentsLog/semberecki/private"
STATE = STATE_DIR / "watcher-state.json"
CACHE_DIR = WATCHER_DIR / ".cache"
MENTION_TOKENS = ("semberecki", "piotr", "piotrek")
PER_PAGE = 100


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url: str, etag: str | None = None):
    """Conditional GET. Returns (status, data_json_or_None, etag)."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "semberecki-watcher (read-only issue monitor)",
    })
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), resp.headers.get("ETag")
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return 304, None, etag
        return e.code, None, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"[watcher] fetch error for {url}: {e}", file=sys.stderr)
        return 0, None, None


def load_state() -> dict:
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
            # JSON round-trips int keys to strings; normalize defensively so
            # in-memory int keys never duplicate string keys.
            issues = state.get("issues")
            if isinstance(issues, dict):
                state["issues"] = {str(k): v for k, v in issues.items()}
            return state
        except json.JSONDecodeError:
            pass
    return {"issues": {}, "last_poll": None, "last_change": None}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def is_relevant(issue: dict) -> bool:
    assignees = {a.get("login", "").lower() for a in issue.get("assignees", [])}
    if "semberecki" in assignees:
        return True
    haystack = f"{issue.get('title', '')}\n{issue.get('body', '')}".lower()
    return any(tok in haystack for tok in MENTION_TOKENS)


def log_section(header: str, lines: list[str]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = LOG.read_text(encoding="utf-8").count("\n") if LOG.exists() else 0  # noqa: F841
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n## {header}\n\n")
        for line in lines:
            f.write(f"{line}\n")


def main() -> int:
    state = load_state()
    first_run = state.get("last_poll") is None
    state["last_poll"] = now_utc()

    list_etag = state.get("list_etag")
    status, issues, etag = get(f"{API}/issues?state=all&per_page={PER_PAGE}&sort=updated", list_etag)
    if status == 304:
        # Quiet poll: nothing changed on the board.
        save_state(state)
        return 0
    if status != 200 or issues is None:
        state.setdefault("errors", []).append({"at": now_utc(), "what": f"issue list status={status}"})
        save_state(state)
        return 1
    if etag:
        state["list_etag"] = etag

    relevant = [i for i in issues if is_relevant(i)]
    findings: list[str] = []
    changed_issues: list[str] = []

    for issue in relevant:
        num = str(issue["number"])
        rec = state["issues"].setdefault(num, {"comments": [], "last_seen": None})
        prev_updated = rec.get("updated_at")
        rec["last_seen"] = now_utc()
        rec["updated_at"] = issue.get("updated_at")
        rec["state"] = issue.get("state")
        rec["title"] = issue.get("title")

        if prev_updated is None and not first_run:
            # New issue appeared (list was updated but we had not seen it).
            findings.append(f"- NEW issue #{num} [{issue.get('state')}] {issue.get('title')} — {issue.get('html_url')}")
            changed_issues.append(str(num))

        if issue.get("updated_at") != prev_updated or prev_updated is None:
            changed_issues.append(str(num))
            c_etag = rec.get("comments_etag")
            cs, comments, cetag = get(f"{API}/issues/{num}/comments?per_page=100", c_etag)
            if cs == 200 and comments is not None:
                if cetag:
                    rec["comments_etag"] = cetag
                known = {c.get("id") for c in rec.get("comments", [])}
                for c in comments:
                    if c.get("id") in known:
                        continue
                    body = c.get("body", "")
                    author = c.get("user", {}).get("login") or "unknown"
                    rec["comments"].append({
                        "id": c.get("id"),
                        "author": author,
                        "created_at": c.get("created_at"),
                        "body_hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
                    })
                    findings.append(
                        f"- #{num} comment @ {c.get('created_at')} by {author}:\n"
                        f"  ```\n{body}\n  ```"
                    )
            elif cs != 200:
                state.setdefault("errors", []).append(
                    {"at": now_utc(), "what": f"comments #{num} status={cs}"})

    if findings:
        header = f"Tick @ {now_utc()} — {len(findings)} new finding(s)"
        log_section(header, findings)
        state["last_change"] = now_utc()
    else:
        log_section(f"Tick @ {now_utc()} — quiet (board unchanged; relevant issues: "
                    f"{', '.join('#' + num for num in sorted(state['issues'])) or 'none'})", [])
        # Keep the log light: a quiet tick is recorded as one line for provenance.

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
