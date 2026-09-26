# PR127 exact-head review

**PASS — safe to merge at `1e1f6b0ebc8c96e2aa4eec4409462db426b9263b`.** No substantive blocker found. [PR127](https://github.com/kwiscion/machinekind-matura/pull/127) changes two owner files; the sole production change at `reasoning_lab.py:336` rejects explicit boolean `context_truncated:true` alongside `truncated:true`.

The public exact-commit archive was inspected in a scratch copy; shared branch/index and GPU were untouched. The native response is persisted and observed usage recorded before completeness validation. The new failure propagates through StopWave: the answer remains blank, the current stage fails, and remaining stages/families stay unsent. It neither retries nor changes frozen past responses.

Validation:

- `python3 -B -m unittest discover -s scripts/ljaniec -p 'test_reasoning_lab*.py' -q`: **45 tests passed** under WSL/Linux.
- Independent synthetic matrix: both flags false accepted; either or both true rejected. Removing the new condition reproduces acceptance of `truncated:false, context_truncated:true` under the old guard.
- Added wave regression verifies one generated/reserved call, original raw response and usage retained, no completed ledger event, critic follow-up and all later task families unsent.
- Initial Windows import failed because the Linux-specific suite imports `fcntl`; this is an environment limitation, not a test assertion failure. Tests were then run on the intended Linux runtime.

No inference, network generation, service changes, teammate edits or Git mutations. Runtime/data handoff claims in the PR body were not re-audited; this is the scoped code-correctness review.

Exact file SHA256:

- `scripts/ljaniec/reasoning_lab.py`: `1a77e67db4cc3fb9bca4bcfe901643afa502d80b7439f6020734ef0b3c710adf`
- `scripts/ljaniec/test_reasoning_lab.py`: `e73f10a49364cf9e7b9eeeaf398cb2d0ce604e6bb188f88feb471a8733b816bd`
