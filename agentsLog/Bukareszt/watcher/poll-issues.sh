#!/usr/bin/env bash
# Poll GitHub issues addressed to Greg (@Bukareszt) in kwiscion/machinekind-matura.
# Prints a JSON array of open issues assigned to / mentioning @Bukareszt or "Greg", with comments,
# so the watcher can diff against its private state (agentsLog/Bukareszt/private/watcher-state.json).
# Also exposes `claimed` = true when an in-progress label or a claim comment already exists, to avoid duplicate dispatch.
set -euo pipefail
REPO="${REPO:-kwiscion/machinekind-matura}"
LOGIN="${LOGIN:-Bukareszt}"
gh issue list --repo "$REPO" --state open --limit 100 \
  --json number,title,body,state,assignees,labels,author,createdAt,updatedAt,url,comments \
| jq --arg login "$LOGIN" '
  [ .[] | select(
      ([.assignees[].login] | index($login)) != null
      or ((.body // "") | test("@"+$login; "i"))
      or ((.body // "") | test("\\bgreg\\b"; "i"))
      or (.title | test("\\bgreg\\b"; "i"))
      or ([.comments[]? | .body] | join("\n") | test("@"+$login; "i"))
    )
    | {number, title, url, author: .author.login, createdAt, updatedAt,
       assignees: [.assignees[].login], labels: [.labels[].name],
       claimed: (([.labels[].name] | index("in-progress")) != null
                 or ([.comments[]? | .body] | join("\n") | test("claim"; "i"))),
       body, comments: [.comments[]? | {author: .author.login, createdAt, body}]}
  ]'
