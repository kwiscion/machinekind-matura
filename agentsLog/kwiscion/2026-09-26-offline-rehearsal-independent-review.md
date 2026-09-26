# Offline rehearsal: independent CPU review

**PASS after the narrow worker-guard repair. No remaining code blocker identified in the reviewed scope. Actual server/CUDA/model rehearsal remains unexecuted and requires separate lead authorization.**

Reviewer: GPT-6 Sol. Time: 2026-09-26T17:01:16.300056+02:00.

## Finding and repair

The original host worker scan omitted run_bounded_gemma.py. A synthetic cold/waiting generic dispatcher passed the guard when the GPU PID list was empty. This was a launch blocker because the rehearsal could overlap a separately scheduled model worker.

The source author added the missing name and a regression before handing edit ownership to this reviewer. At the lead's request, this reviewer preserved that patch and extended the exact-name set to the verified inference helpers run_source_correction.py, run_local_smoke.py and run_smoke.py. Existing run_gemma/run_qwen/run_rag prefixes cover crop and RAG launchers. CPU-only prepare_rag.py and prepare_bounded_rag.py remain allowed.

Self-fix limitation: this reviewer changed the helper-name list and regression coverage after finding the issue. A separate harness_sol reviewer subsequently inspected the narrow patch and independently reran all six tests successfully; no model calls occurred.

## Evidence

- Six supplied/revised CPU tests passed: synthetic package preparation, two mocked requests totaling 2048 requested output tokens, valid adapter output, output boundaries/freshness, host-namespace rejection, no-argument launch refusal, and worker-helper regressions.
- Additional mocked network checks rejected a non-loopback interface and external main-table route before opening sockets, and verified the IPv4/IPv6 unreachable-error proof path.
- Additional mocked inside() success made exactly two calls. First-call timeout preserved one reservation and one raw failure, made no retry/second call, and emitted no success record. Both paths signaled only the newly created server process group and wrote cleanup evidence.
- Real, separately authorized CPU capability probe: `wsl --exec unshare -rn -- ip -brief link` exited **0**, displaying only `lo DOWN 00:00:00:00:00:00 <LOOPBACK>`. The first sandbox attempt failed with Wsl/Service/CreateInstance/E_ACCESSDENIED; the normal escalated retry succeeded. No server/model or host-network change was made.

## Code assessment

- Isolation: outer launch creates a user and network namespace; inside brings up only its own loopback, requires namespace identity different from the parent, rejects non-loopback interfaces/routes, and requires both external probes to fail. New server and runner namespace identities must match. This is network isolation, not a filesystem sandbox.
- Assets: the existing model manifest, model blob and projector sizes/full hashes are checked before launch; combined weight bytes are 7556497632. Code neither downloads nor rewrites those assets. The server receives the existing cache path and a fresh private HOME; the cache is not remounted read-only.
- Budget: exactly two fixture IDs are prepared; each is reserved/flushed before a single infer.run_case call with max1024 output and timeout420. Any error stops without retry. Actual prompt/completion usage is checked and recorded. The transport has no retry loop.
- Runtime: host resident-model and known-worker/GPU-process guards run before launch; the inner scan repeats before server start and each call, excluding only its own server group. Version, model digest and context4096 are checked; the first real call performs the cold load.
- Cleanup: the new server uses a fresh session/process group. Inner cleanup signals that group only; outer fallback additionally requires matching group and recorded network namespace. There is no global process-name kill, host daemon stop, host firewall edit or download.
- Freshness: private output must not exist; package/config/results are written under that new owner-private directory. Parent lock prevents concurrent copies of this rehearsal.

## Remaining launch prerequisites and limits

The namespace creation capability is now verified, superseding only that part of the fallback report's earlier unverified note. Full isolation proof, Ollama readiness, CUDA loading inside the user namespace, actual responses and real answers.json remain unverified. Host queue ownership and explicit unload of the lead's resident model remain prerequisites. No permission is implied to stop another worker or modify the host environment.

Known limits: process snapshots are not an atomic queue lock shared by all workers; forced parent termination can defeat cleanup; model/cache verification precedes the 980-second outer execution bound. Reserve time for both asset hashing and the bounded runtime. A namespace-only probe does not prove GPU compatibility or complete offline inference.

No actual server/model requests, shared inference-input edits, Git writes, installs or credential searches occurred in this review.

## Reviewed file hashes

| File | SHA-256 |
| --- | --- |
| agentsLog/kwiscion/offline_rehearsal.py | `58792cd6365befcca74112d09a8ccab490bc9749e9f6f205c100179aa1f69f8c` |
| agentsLog/kwiscion/test_offline_rehearsal.py | `ee39310bcb4e257abaa03187fe371108bfcd217c010ff30a5be6923f62e323aa` |
| agentsLog/kwiscion/2026-09-26-offline-rehearsal-fallback.md | `7c87e27f99505a24680f4967d05a83763a25af7e379a1fdba894e25e5b02d2a0` |
