# Independent heterogeneous-source runner review — 26 September 2026

**PASS for the reviewed CPU implementation**, subject to separately declared execution and the required actual Qwen readiness. This review made no model, server or GPU calls and changed no author files.

Reviewed initial stable wrapper SHA256:`1b47c235d89e018ca5370acc839e30ae77ddb72b38772fea1604a7f657900482`; controller:`871b1147689af26172496ac2677f223ba9f5a25bc52815b03be64e82ccb3a761`.

Executed12 controller tests,3 transport tests and2 independent probes. All pass. Independent probes used the real `infer.run_case` payload with a network-free capture: unchanged source text/image parts are accepted, extra sampling/stream and cap mutations are rejected. A missing dependency pin fails before any dynamic import. No official answer keys were used.

The author repaired concrete review findings before this PASS: the original wrapper expected a `stream:false` field that the accepted runner omits; required pins were checked after imports; input image constraints were checked after loading; and the dispatch deadline needed a recheck after guards. The reviewed wrapper now checks exact actual request fields, dependency pins before imports, image paths before loading, deadline immediately before transport, and uses a Linux real-process signal timer for the hard wall limit. Systemic validation failures are blank/error rather than usable partial answers.

Code inspection confirms:

- Six original inputs are deep-copied; observation/final instructions append to the original normalized text/image content. A failed observation uses the original bare input in its reserved final slot; no partial observation is injected.
- Exactly18 reservations/18,432requested tokens for a wave,2/512 for declared readiness; no retry path. Reservations and request bytes are fsynced before HTTP, raw records afterward. Fresh output and an exclusive owned-host lock prevent accidental resume.
- Both native manifests and every declared blob are size/hash checked. Expected Gemma weights total7,556,497,632bytes and Qwen6,594,462,816bytes, each below8,000,000,000. Version, binary, process identity/start time, server settings, competing workers and per-stage loaded digest/context are guarded. Sequential model switching does not change server residency settings.
- Only known empty/length responses can continue after bounded usage and runtime/context validation. Transport/provider/tool/unknown/malformed/context/ownership/pin/budget failures stop. Errors/unsent stages remain explicit.

The runner does not by itself establish model quality, successful switching latency or real offline isolation. Snapshot/HTTP-error retention improvements were suggested as nonblocking audit improvements; any later exact file revision needs its narrow delta checked. Root owns the launch and promotion decision.
## Final frozen revision — delta checked

Final wrapper SHA256:`52be22debdd1710e488484ba94e9af07ae84d6280a52ff47f0d4964bdac27e79`.

Final controller SHA256:`b911087c9ef5167e23c65ab055f89e359ac9e73b5a06b26872f0d8944c77e266`.

**PASS retained.** The narrow final delta appends already-collected runtime snapshots with UTC/expected model using fsync and preserves existing runner errors (including HTTP status) when adding a systemic validation failure. No additional model/API calls were introduced. The independent2-probe suite passes again; author reports the15 focused tests unchanged and passing. No further polish or new prerequisite is requested by this review. Root separately authorizes execution after readiness and ownership/pin checks.
