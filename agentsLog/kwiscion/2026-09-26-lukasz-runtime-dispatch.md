# Final runtime and throughput handoff — Lukasz

Owner: @ljaniec. Parent #3; GPU execution stays with @semberecki on #33. Target: support 48/60 reviewed validation points by18:00, then a reliable Sunday exam run. Consult WINNING_PLAN.md.

Your Gemma download/failed-Spark-load evidence is accepted. The owner now confirms Piotrek has an RTX5090 and an active watcher; Blackwells are unavailable. Do not continue Spark/CPU Gemma preparation or launch another model worker. Preserve existing files and other workloads.

Claim this task with ETA. Deliver a concrete deployment/throughput handoff within60minutes, using existing scripts/configs rather than another runner. Owned paths: agentsLog/ljaniec/ and scripts/ljaniec/; do not edit Greg's adapter or shared infer.py.

1. Read the organizer guide and Greg's #37 adapter contract. Produce the minimal pinned-runtime setup/start/check commands for Piotrek's selected Gemma route on RTX5090 (confirm his chosen route in#33). Verify documented runtime/GPU support from primary docs and separate metadata from actual success. Provide offline start instructions after weights/dependencies are present. No unattended global installs, purchases or unrelated credentials.
2. Audit final-runtime pitfalls from existing evidence: all saved model/projector bytes, actual serving binding, required local assets, network-free inference path, model output versus thinking, timeout/finish reasons, and shutdown/cleanup limited to task-owned processes. Existing VLLM or unrelated services must remain untouched.
3. Give a stage-time budget based on completed-response latency/usage only. The laptop's slow partial run and Spark's failed-request timings are not GPU throughput. Once Piotrek posts actual RTX5090 baseline timings, estimate full exam runtime, identify the bottleneck, and propose one concrete improvement through supported server batching/concurrency only if needed. Do not implement concurrency or run probes before the current single baseline is complete; preserve result IDs/order and fixed settings.
4. Independently review Piotrek's model/runtime manifest and Greg's offline command when their PRs arrive. Report reproducible defects immediately to their issues; do not start duplicate implementations.

Initial work is read-only documentation/config validation with **zero model calls and zero paid API spend**. Optional live rehearsal needs a separate bounded lead assignment after the baseline; do not infer permission to disrupt a shared GPU. First deliverable may use the known route with clearly listed pending measured fields, then update it with Piotrek's evidence.

Success is a short usable command/runbook and an honest latency budget, not another smoke-audit loop or a claim that a download is inference. All public artifacts exclude exam text, raw answers, keys and team code. Post a scoped PR plus clear handoff; keep #5 closed.
