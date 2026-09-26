# Full RTX runtime review — issue #38

26 September 2026, 18:08 Europe/Warsaw. Reviewed merged PR #85 head `bfe7851111ac2c5f9d64c3aa293c01e6b52bf908` on main `3bbd1547e6d33d79a1409ac65cceb659ec0473ae`. Read-only arithmetic and independent controller inspection: zero model calls, GPU/SSH/namespace operations, installs, downloads or paid spend. Piotrek owns execution; Paweł owns scoring. No question, key or answer strings reproduced.

## Independently recomputed evidence

[Actual answer-only file](../semberecki/model-answers/gemma4-12b-val40-v2-rtx-transfer.jsonl) SHA-256 `179ccf382d2b0b87b4899240f604e0f922c1b8856273f4bedaccd9841bef600b` matches delivery. Forty unique IDs have the same set/order as the retained laptop handoff. All40 have nonempty final strings, `stop`, null error and finite positive latency. No exclusions; retain40 items/60 points.

| Completed-response statistic | Seconds |
| --- | ---: |
| Summed request latency |146.276|
| Mean |3.6569|
| Median |3.508|
| Minimum |0.683|
| p95 nearest rank (38th sorted response) |7.278|
| Maximum |11.835|
| First request |7.278|

Operator reports146.6s whole-arm elapsed (UTC15:54:18–15:56:44, rounded timestamps), consistent with request sum plus approximately0.324s overhead subject to precision. First-request latency includes any load; separate load/prefill/decode phases are absent from public rows. Do not add another unmeasured cold-load term.

Actual6,513 completion tokens, max717 output, max1,979 prompt, context32768 and local blob hashes are operator-reported; public rows omit usage/runtime snapshots. Ljaniec did not independently rehash remote weights or recompute usage. Committed lead config independently hashes to `bc3c91d9da1a6b5ad0d083506e090a2d840833b24a92af0765cd19f2bd8294e3`, matching the abbreviated manifest, without verifying private execution-time bytes/endpoint. Input/image/runtime evidence stays in operator custody.

## Stage-time estimate

For another comparable40-item package on this unchanged runtime: inference midpoint **146.6s (2m26.6s)** plus separately measured preparation/hash/finalization/validation costs and explicit operator reserve. Conservative planning scenario40×p95 = **291.12s (4m51.12s)** plus those costs. This is a scenario, not a confidence bound or guaranteed deadline; it is not a measured second arm.

Final item count/mix and stage allowance remain unknown. Public timing rows lack independent category labels, so no category forecast is claimed. Laptop reference differs in runtime/context, inputv1 and image preprocessing/offload; no controlled GPU-only speedup or accuracy gain follows. No concurrency/sampling/visual-budget intervention is justified by this timing alone; preserve serial settings pending lead decision.

## Reproduction and contract gaps

Independent reviewer `/root/review_spark_handoff` inspected the [wrapper](../semberecki/rtx_transfer_run.py) alongside root arithmetic. Sequential40-call/token caps, per-result flush, exclusive output creation and per-dispatch deadline checks are present. Concrete gaps tracked in [#88](https://github.com/kwiscion/machinekind-matura/issues/88), reported immediately to [#33](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847751447):

- Public `parents[3]` resolves above the repo; it was correct one directory deeper under `private/`. Fix public reproduction without rewriting execution history.
- Manifest answer link omits `val40`; use the actual file linked above.
- No worker/asset/version/digest/context preflight is asserted in this script. `/api/ps` is sampled once after first success, never asserted/rechecked; `context_preserved` is hardcoded. Separately retained manual checks must be distinguished from enforced checks.
- Declaration stops on transport/runtime failure; wrapper permits two consecutive infrastructure failures and ignores ordinary HTTP4xx/provider/incomplete errors for dispatch stopping.
- `dispatch_utc` is taken after the response and possible metadata fetch; it is a completion-side observation.
- Low returned prompt count alone cannot prove complete source/image delivery or no upstream truncation. Qualify the claim or retain request/runtime evidence.

These gaps do not establish that the original private run failed, any answer was truncated or manual preflight was absent. Preserve all40 valid public answers/timings. No repeat generation or silent implementation requested. Ljaniec tracks acceptance; Piotrek/lead schedule implementation.

## Offline and next handoff

Lead [fixed rehearsal](../kwiscion/2026-09-26-offline-rehearsal-result.json) and [generic qualification](../kwiscion/2026-09-26-final-launcher-qualification-result.json) report separate actual laptop2/2 synthetic runs: nonempty stops, seven completion tokens each, matching model digest/4096 context, loopback-only shared namespace, failed external IPv4/IPv6 and task-owned cleanup with host daemon intact. Fixed wall68.891s differs from request sum58.154s; generic request sum15.628s is not whole wall time. Safe reports/private evidence hashes inspected, raw private telemetry not independently replayed. Generic qualification supersedes earlier CPU-only status.

These support reported laptop synthetic isolated packaging, not RTX/H100 isolation, final correctness or submission acceptance. Greg #83 owns CPU remote-launcher portability. Lead Sol #81 alone owns existing H100 readiness (max60min/$3.28 estimated instance time,2 synthetic calls/2048 requested tokens,$0 additional API); completed safe H100 report awaited. No purchase/provision/resize/credit redemption or second worker. Monitor/dedup continue; #38 remains active for H100 review, defect acceptance and actual stage/portability evidence.
