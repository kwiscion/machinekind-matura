# Final Qwen stage receipt

Verified 27 September 2026 after 08:08 Europe/Warsaw. This is a receipt retrieval and idle-state check, not a model run or final inference qualification.

- Existing stage completed PASS at 2026-09-27T05:23:54.892333+00:00 (07:23 Warsaw).
- Dedicated Qwen cache: 5 files, 6,594,475,420 bytes; cap 8,800,000,000 bytes; headroom 2,205,524,580 bytes.
- Existing stage reports zero model calls, zero services started, and identical before/after service and GPU snapshots.
- Current read-only host check: GPU utilization 0%, memory 0 MiB; original port 11436 `/api/ps` returned `{"models":[]}`. Existing service was preserved.
- Downloaded only three JSON metadata receipts to `agentsLog/kwiscion/private/final-qwen-stage-20260927/`; all local SHA-256 values match remote receipts. No weights or credentials downloaded.

| Receipt | SHA-256 |
|---|---|
| inventory.json | 27f999955eb135ba1d66697ccfaac2721f42c3aef791889fa03c465d09b00d93 |
| runtime-inventory.json | fdb2797f135806032281fd84bb49d8df2bd4f46135c521faf581d42d5a04c7f5 |
| terminal.json | 8a60fc23ab88b3148518e53b2bf2e28380f28fcb802b5910733f33f759241ea7 |

Runtime inventory contains 62 entries. Recorded Ollama binary SHA-256: `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`; version 0.34.4. Hash verification on retrieval covers receipt bytes; the original stage receipt records runtime and model-file hashing. No repeated multi-GB weight scan was performed.

Private remote cache location: `/home/shadeform/machinekind-matura-h100-readiness-20260926/root-final-qwen-stage-20260927/models`. Runtime location: `/home/shadeform/machinekind-matura-h100-readiness-20260926/runtime`.

The existing Brev copy commands completed successfully after readiness/SSH waits; no duplicate copy or worker was started. No code, prompts, settings, services, or model performance were changed. Root owns the documentation commit and final freeze.
