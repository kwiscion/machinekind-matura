# Bounded manifest dispatcher — preparation only

`run_bounded_gemma.py` reuses the reviewed policy dispatcher's runtime verification, local status transport and stopping functions. It does not edit the policy runner or current inputs. No RAG experiment manifest has been finalized and no inference was launched.

Required JSON manifest fields:

| Field | Contract |
| --- | --- |
| `input`, `input_sha256` | Frozen40-row private JSONL and exact SHA-256 |
| `config`, `config_sha256` | Original Gemma config, exact pinned `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa` |
| `output` | Fresh path within this repository's `agentsLog/kwiscion/private/`; metadata sibling must also be fresh |
| `expected_ids` | Exactly40 unique nonempty strings, matching input order |
| `images` | Map of every input image-path string to its SHA-256; no missing/extra entries; resolved paths restricted to private owner directory |
| `model_digest` | Full fixed Gemma digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| `deadline` | Explicit ISO8601 datetime with timezone; lead declares before launch |
| `max_elapsed_seconds` | Positive integer, at most3600 |
| `max_calls`, `max_requested_output_tokens` | Exactly40 and40960; neither expandable |
| `max_output_tokens`, `timeout_seconds`, `context_tokens` | Exactly1024,420,4096 |
| `paid_api_budget_usd` | Integer0 |

Keep the manifest itself private. CLI default is a network-free dry preflight:

```sh
python3 -B agentsLog/kwiscion/run_bounded_gemma.py --manifest agentsLog/kwiscion/private/<declared-arm>/experiment.json
```

Only the lead's separate launch signal authorizes adding `--execute`. Execute in WSL/Linux for `/proc` concurrency checks. No resume, warmup or retry. Installed model may be unloaded initially; the first real request must establish the exact resident digest and4096 context before continuing. Read-only show/version metadata records original sampling defaults; temperature and seed remain unset. Manifest, input/config, dispatcher, shared stop logic, runner, output hashes and Git revision are recorded.

The loop stops new requests for a competing inference worker, elapsed/deadline limit, after-five-response projection past the deadline, prompt usage above2816 or missing success usage, context/OOM indicators or two consecutive infrastructure failures. Current request retains420-second timeout. One private raw file is flushed per attempt; completion metadata contains all unsent IDs. Context fit is estimated, not exact multimodal tokenizer proof. Ownership coordination is still needed for races between process checks; silent server truncation is not conclusively detectable from returned usage.

Validation: four synthetic-input manifest/preflight tests passed; four reused policy-stop/runtime tests passed. Covered hash/ID/image drift, freshness/preservation, public paths, expanded budgets, timezone requirement, deadline/projection/concurrency/usage stops. Tests made no status/model calls. Root owns review, manifest freeze and Git publication.
