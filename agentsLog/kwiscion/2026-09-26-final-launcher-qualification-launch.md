# Generic launcher qualification — 26 September 2026, 17:47 Europe/Warsaw

Root owns one distinct local qualification run for issue #66. The fixed rehearsal is terminal; its calls are not being retried. Test the independently reviewed generic arbitrary-package launcher against the same two invented package items. No exam or held-out material is involved.

Limits: **2 sequential generation calls, 2,048 requested output tokens, 900 seconds total supervisor wall bound, $0, no retries or warmup**. Original bare Gemma configuration (thinking off, 1024 output, 420 request timeout), model digest and 4096 context are unchanged. One task-owned isolated server and runner; external networking unavailable inside their shared namespace, no host service/firewall changes. Root is the only laptop worker. Existing guards must pass before dispatch; retain failed/unsent IDs and raw evidence.

- Launcher SHA-256: `64ebf4a89c3538ead8a8a84cdea471655eb2c321974530ac6032c4a9fbea0611`.
- Config SHA-256: `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`.
- Package: ignored `agentsLog/kwiscion/private/offline-rehearsal-run-01/package`, exactly `offline-text` and `offline-image`.
- Exam JSON SHA-256: `432e2476b07972f6c97ab94c49a6dbd2bbdb9d9801107d40cb21d5bf8618f350`.
- Template SHA-256: `07dece40c46a3cae9f344f7b4d4ec34bb72fbcd47b9a3b5fbd785d4e66eca6ff`.
- Synthetic image SHA-256: `b4467f0dd939cb7b8af870bf39e79c2433610e765485791c8524ca7a245577b8`.
- Fresh output: ignored `agentsLog/kwiscion/private/final-launcher-qualification-01`.

Independent Sol dry preflight passed under actual WSL with zero calls, matching all hashes. Nine CPU tests and seven additional edge checks already passed. This launch aims to verify actual isolated CUDA execution, valid final answers and scoped cleanup for the generic command. It cannot establish exam accuracy, a final candidate, stage timing or organizer acceptance. May 2025 remains sealed.
