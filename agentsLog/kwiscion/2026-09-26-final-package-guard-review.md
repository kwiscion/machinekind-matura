# Independent final-package guard review

**Approve the frozen CPU guard. No blocking defect remains in the reviewed scope.** This qualifies inventory-verification code, not an actual final staged package, offline serving, model quality, or submission readiness.

Reviewer: independent Sol `/root/essay_corpus_sol`, 26 September 2026. No GPU, inference, remote-host operation, Git mutation or production-weight modification occurred. The local WSL calls ran only tiny CPU filesystem fixtures.

Publication note from lead: removed redundant trailing blank lines from the README and refreshed its hash below. Guard and test bytes remain exactly as independently reviewed; no implementation change followed approval.

| File under `agentsLog/kwiscion/final-package-prep/` | Exact SHA256 |
|---|---|
| `guard.py` | `8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473` |
| `test_guard.py` | `c3ce0882842d2243085162c891d7ed4f4c552b6b86112237feab96220e51fc70` |
| `README.md` | `569ab698c36e3341177af8ed2bc8e685836d9309c9263a2ee2f95d5478ca20c3` |

## Verified behavior

- Inventory paths must be canonical relative POSIX paths. Absolute/traversal/alternate-separator/drive/ADS paths, duplicate paths, case collisions and duplicate JSON keys are rejected. Root ancestry, nested symlinks, junction/reparse attributes and nonregular files are checked. Unreadable directory traversal fails closed.
- Every staged file must appear exactly once in the declared inventory, with a permitted purpose and matching actual byte count and streaming SHA256. Empty weight files are rejected; metadata can be empty. Missing, extra, modified and executable files fail. Runtime binaries belong outside the weight directory.
- Every file entry counts its full bytes, including hardlinked duplicates. Metadata and the native manifest also count. The production CLI cannot raise the **8,800,000,000-byte** aggregate limit. Generic inventory validates the declared file set and labels; it does not infer model suitability or architecture from arbitrary file content. Non-GGUF adapters remain supported.
- The native command derives the only allowed file set from one hash-pinned Gemma manifest and its referenced blobs, then verifies that inventory. Extra development blobs, Qwen files, alternate manifests, unknown native layer types, multiple model/projector layers or an incomplete pair fail. **No Qwen installation or weights are required.** A future trained pair requires an explicit separately reviewed pin file; fixture-only small pins do not replace production defaults.
- Current production defaults match the prior Gemma readiness evidence: model `1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606`, **7,381,382,048 bytes**; projector `675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842`, **175,115,584 bytes**; pair **7,556,497,632 bytes**. Manifest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` is unchanged. The verified cache total will exceed the pair total by its metadata bytes, conservatively.
- Optional saved-runtime checking pins the separately located runtime binary, Ollama version, one Gemma tag/digest and loaded context. Its explicit scope remains saved evidence only; it cannot prove live ownership, freshness, offline isolation or successful generation.

## Findings fixed before approval

1. **Silent unreadable-directory omission:** `os.walk` originally omitted traversal failures. Its final `onerror` raises; the dedicated regression passes.
2. **Cross-file mutation:** I independently reproduced a PASS when file A changed after its hash while file B was being hashed. The final code retains each file's identity/size/timestamps, checks root ancestry and the complete file set again, and compares all retained states. The same independent attack fixture now fails with `Staged file changed after hash`.
3. **Windows stat semantics:** the initial Windows suite had one native-fixture hash-check error. The implementation now compares lstat-before/final and fstat-opened/after separately, with cross-API identity/size/mtime equality, preserving full content hashing. This avoids confusing Windows creation/change-time semantics; the final Windows suite passes its available tests.
4. **Direct hash targets:** `fingerprint` now requires a regular file before opening, including the saved-runtime binary path. This prevents hashing a directory/device/FIFO outside inventory traversal. Empty weights also fail explicitly.

## Executed CPU checks

- **Linux/WSL: 14/14 tests PASS**, including real symlink file/directory rejection and hardlink accounting.
- **Windows: 13 tests PASS, one symlink test SKIPPED** because symlink privilege is unavailable. Linux exercised that test; the skip is not counted as a pass.
- Independent cross-file mutation fixture: **rejected after the fix**, after reproducing the original defect.
- Additional independent tiny fixtures: duplicate model layer, unknown native layer type and missing projector all rejected even with updated fixture-only manifest hashes. A mocked Windows reparse attribute is rejected. Canonical production weight arithmetic remains unchanged.

These tests allocate no real model. Final use must run the native guard on the actual isolated staged cache, preserve its report and exact inventory, and reverify after any change. Staging must remain immutable during and after verification; this guard is not an atomic filesystem snapshot against an active adversary. Historical experimental guards and runner claims were not changed.
