# Narrow cleanup follow-up — independently CPU reviewed

See the [frozen independent review](../2026-09-27-offline-cleanup-independent-review.md) for exact accepted code hashes and limits.

The shared parent/CLI `cleanup_from_receipts` now implements the proposal below. Strict `lstat` absence checks propagate permission errors, and only recognized terminal return codes (0, SIGKILL, SIGTERM) permit the receipt path. Invalid or tampered receipts use the independent-proof strict fallback, never a successful skip. Seventeen CPU regressions pass; runtime requalification has not occurred. Immutable package-v4 and its original failed operator result remain unchanged.

Observed stage: inner `inside()` completed both semantic checks, killed its identity-checked owned server process group and wrote `cleanup.json`. Parent `execute()` then called `namespace_cleanup()` unconditionally. An unrelated same-UID process denied namespace inspection, causing operator failure; the shell EXIT cleanup repeated the same unnecessary fallback. Later read-only checks proved both recorded server/backend PIDs absent and the original service untouched.

Proposed bounded change to a new version only:

1. Centralize parent/shell cleanup dispatch in one receipt validator. Bind `cleanup.json` to `server-identity.json` and `network-proof.json`: same PID, start ticks and isolated namespace; expected successful owned-group cleanup fields and terminal return code.
2. On a complete matching receipt, inspect only its recorded server/group members. Require recorded server and killed member PIDs absent, or reject live/reused identities without signaling unrelated processes. A valid completed receipt plus absent recorded processes skips broad namespace discovery.
3. Use the existing strict namespace fallback when the receipt is absent, incomplete, malformed or mismatched. Do not blanket-ignore PermissionError: uncertain ownership in this recovery path stays a reported failure. A valid receipt naming a still-live or reused PID fails closed without signaling it automatically.
4. Keep immutable package-v4 and its failed run. No payload, model, budget, namespace setup or inference behavior changes. CPU tests first; independent review before any separately declared requalification.

Regression cases: complete bound receipt + absent recorded processes + unrelated unreadable process (no broad scan); missing/partial receipt (fallback required); mismatched namespace/PID/start ticks (reject); a recorded process still live (do not falsely succeed); foreign PID reuse (never signal); fallback inability to inspect potentially owned process (fail closed). Preserve the existing pre-receipt crash test.

This addresses a cleanup reporting/control defect. It does not authorize rerunning the successful two model calls or extending the generic Sunday runner.
