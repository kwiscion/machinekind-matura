# Independent synthetic-smoke evidence audit — issue #27

Owner: @ljaniec. Follow-up to #5 / PR #25; reviewed infrastructure is in
merged PR #26 (`ce2a5f4cb0f30c27ef14296a2df10814bf6db65b`). This audit reads
existing private artifacts and publishes aggregates. It performs no inference,
downloads, SSH/environment repair, training, purchases or sealed-test access.
Raw bytes and the original delivery history are preserved.

## Findings

| Metric | CPU | Spark |
| --- | --- | --- |
| Records / unique IDs | 20 / 20 | 20 / 20 |
| Recorded non-null errors | 0 | 0 |
| Nonempty responses | 20 / 20 | **4 / 20** |
| Empty responses | 0 / 20 | **16 / 20** |
| Mean wall latency, all 20 records | 79.7231 s | 4.8816 s |
| Statistical median wall latency, all 20 records | 73.9035 s | 4.8825 s |
| Completion tokens | 3,972 | 4,000 |
| Records reaching the configured 200-token budget | 19 / 20 | 20 / 20 |

Both runs' IDs and prompts exactly match the committed synthetic catalog in
`agentsLog/ljaniec/baselines/dev-smoke-prompts.jsonl`. These are synthetic load
checks, not official May 2023 DEV or May 2024 VALIDATION exam results. Source
rights are clear for this self-authored catalog; no raw text is included here.

The earlier Spark "20/20, zero errors" claim describes transport records. It
does not describe 20 usable answers. Empty replies count as answer failures in
the independent audit even when the original runner wrote `error:null`. The
roughly 16.3x ratio of the two mean latencies is a timing ratio across all
records with different answer-success rates; it is not a comparable successful
answer speedup. Mean recorded Spark generation rate is 42.73 tokens/s.

The original CPU summary's median selected the upper middle record. The true
even-sample median is 73.9035 s rather than the reported 73.994 s. The original
summary is retained; the independent aggregate is authoritative for this audit.

Budget hits are a warning signal, not proof of truncation. Neither legacy raw
format retains finish reason or reasoning output. The cause of empty Spark
answers and the completeness/correctness of nonempty answers remain unknown.
No matura grade, candidate promotion or successful GPU training is established.

## Artifact identity and provenance

| Artifact | SHA-256 |
| --- | --- |
| CPU raw JSONL | `8b6d71eb4d581f4adc0b31ec25b536e546c9df8ef727bfd689f587f9abc26cac` |
| Spark raw JSONL | `10beafb69e3059b68bdc89248517559496d1e37f31b7cc7d55a06cc5d9898276` |
| Local CPU `Qwen3-8B-Q4_K_M.gguf` | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` |

The CPU weight file independently verifies at **5,027,783,488 bytes**, below
8,000,000,000 for that single text-only file. This does not verify a Spark
served-weight inventory or independently establish that no other served weights
were present. No adapter was audited. Weight bytes, artifact hashes and source
reported metadata must be distinguished from inference evidence.

Remaining provenance limits: immutable HF repository commit used for the old
download; exact runtime build/tokenizer/chat template; Spark served-file hash
and inventory; retained load/memory measurements. The GGUF SHA-256 is a file
digest, not a repository revision. Runtime/memory statements in the original
handoff are unaudited claims. No retrospective values are invented.

The pinned Gemma 4 12B and Qwen 3.5 9B public sources in
`scripts/ljaniec/model_candidates.json` correct the old "no public repos"
statement. Their file sizes/hashes are source-reported metadata; those models
were not downloaded or tested by this session. The lead owns current candidate
selection and the actual VALIDATION diagnostic under #3/#11.

## Reproduction and handoff

Existing private raw files are at:

- `/home/ljaniec/Repositories/machinekind-matura/agentsLog/ljaniec/raw/qwen3-8b-q4_k_m-smoke.jsonl`
- `/home/ljaniec/Repositories/machinekind-matura/agentsLog/ljaniec/raw/spark-smoke.jsonl`

From the repository root, audit the existing bytes into **new** aggregate
files (the command rejects output replacement):

```bash
python3 scripts/ljaniec/audit_smoke_outputs.py \
  --raw /home/ljaniec/Repositories/machinekind-matura/agentsLog/ljaniec/raw/qwen3-8b-q4_k_m-smoke.jsonl \
  --input-catalog agentsLog/ljaniec/baselines/dev-smoke-prompts.jsonl \
  --input-kind synthetic-smoke --token-budget 200 \
  --output /tmp/issue-27-cpu-audit-new.json
python3 scripts/ljaniec/audit_smoke_outputs.py \
  --raw /home/ljaniec/Repositories/machinekind-matura/agentsLog/ljaniec/raw/spark-smoke.jsonl \
  --input-catalog agentsLog/ljaniec/baselines/dev-smoke-prompts.jsonl \
  --input-kind synthetic-smoke --token-budget 200 \
  --output /tmp/issue-27-spark-audit-new.json
python3 -m unittest discover -s scripts/ljaniec -p 'test_audit_smoke_outputs.py' -v
```

Committed aggregate hashes:

- [CPU aggregate](issue-27-cpu-smoke-audit.json):
  `04d666674f6435fbc17c0d7b8af34a3e9de874eb64ac43cc29d5f22c9422111a`.
- [Spark aggregate](issue-27-spark-smoke-audit.json):
  `9757a238f8197693fb7a50247cd36ad5b7835f9270f8801d5e2f19421eef26a0`.
- Synthetic input catalog:
  `cfa1ef4a155b2652085ac0c5f4a084b3b3f168d3118ba4ddb81058b5dc610756`.

The utility fails on malformed records/numeric fields and publishes no input
or answer text. Four focused tests cover empty replies with `error:null`,
duplicate IDs, true even-sample median, reported errors with partial answers,
missing-metric denominators, catalog mismatch, malformed data, text privacy and
raw byte preservation. Sol performed the raw-file/weight audit and implemented
the utility; the coordinating session independently reviewed its code and
corrected non-null error counting. Documentation and aggregate evidence were
reviewed separately before publication.

Do not publish raw exam artifacts or evaluation keys. The legacy CPU recipe
calls `$BASE/run_smoke.py`, while the delivered file is in `$BASE/baselines/`;
its downloads are also unpinned. It is not the verified reproduction path.
Use [smoke-harness.md](smoke-harness.md) for the independently reviewed runner:
it requires explicit input/output and weight/runtime metadata, checks actual
weight bytes/hash, writes evaluator-shaped outputs and manifests, and detects
empty, malformed and explicitly truncated responses. New runs require the
issue's run authorization/cutoffs; this audit triggers none.

Issue #27 is the single bounded audit/correction task, claimed with ETA
10:20 Europe/Warsaw and handoff before 10:40. The standing 15-minute monitor
continues; do not start a duplicate worker from the same comment. Verified
results are shared through #5/#11/#27 and this owner log.
