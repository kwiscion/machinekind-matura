# Independent staged-package evidence review

**PASS for the reported staged-cache contents and size.** This is a local audit of preserved execution evidence, not a new remote rehash, offline-serving result or final-submission qualification.

The public stage report matches the private extracted inventory/report exactly: **six file entries, 7,556,509,301 bytes**, comprising the pinned **7,556,497,632-byte** Gemma model/projector pair and **11,669 bytes** of manifest/metadata. Remaining capacity under the conservative 8,800,000,000-byte limit is **1,243,490,699 bytes**. No Qwen file appears in the staged inventory. All six entries were hardlinked and counted at full size; the report correctly warns that this is not an immutable independent copy.

The local 5,217-byte evidence archive hashes to `90e45ebcecb80cf5516393768200594b20dd47dc51a359e841426e6389e05a57`, matching the recorded remote result. Its members are exactly `guard.py`, `declaration.json`, `weight-inventory.json` and `report.json`; every member equals the extracted private copy. **No model weights are in the local evidence archive.** Public wording claims an evidence backup, not a local backup of the weight files, and is accurate.

The inventory SHA256 is `cd00de981f52adeef9f2b09265fcfa382edc5e81352e652ebcb4432e37c8ec2c`. Archived guard SHA256 `8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473` equals the independently reviewed guard. Both native discovery and frozen inventory verification are present in the staging script and recorded as equal.

Pre/post evidence retains the same server PID/start ticks, environment and read-only API snapshots, with no experiment workers or GPU compute processes at either inspection. The staging script contains only file staging/hashing and read-only runtime inspection, supporting **zero inference calls and zero training steps**; it neither starts nor stops a server. This is bounded inspection evidence, not continuous process monitoring.

The separately saved namespace probe shows a network namespace distinct from the host, only a down loopback interface and empty IPv4/IPv6 routes. That establishes namespace capability, not serving inside it. Offline inference still requires its own finite qualification.

Reviewed public file hashes:

- `2026-09-26-final-package-stage.md`: `d975442c24dd086707014f43498c26895c5f695643708a8c11bebc6c60d213b8`
- `2026-09-26-final-package-stage.json`: `f3cfa6b7ddc73fd117c374c9c055d94df9b8138dd5306952a64c8dc6aa2a8ed9`

Reviewer: independent Sol `/root/essay_corpus_sol`. CPU/read-only evidence inspection only; no GPU, remote operations, inference or Git mutation. Private host/process evidence remains private.
