# Retrieval (issue #6) — @Bukareszt

Licensed offline BM25 retrieval over rights-clear Polish historical reference material, with an independent evidence audit. Standalone stdlib script (only `requests` for the fetch step); no model weights, no teammate data, no paid service.

- Issue: https://github.com/kwiscion/machinekind-matura/issues/6 · Branch: `issue-6-Bukareszt-retrieval`
- Started 2026-09-26 02:10 Europe/Warsaw (00:10 UTC); first slice pushed 02:40; handoff written 04:00 Warsaw.
- Split used: **TRAIN only** (40 self-authored general-knowledge queries). No 2023/2024/2025 exam questions, keys, rubrics or source packs were read, fetched, or indexed. No claim is made that any exam is unseen by pretrained models.
- Full results, failure analysis and limitations: [`reports/REPORT.md`](reports/REPORT.md).

## Artifact inventory

| Path | What |
| --- | --- |
| `scripts/retrieval.py` | `fetch` / `index` / `graph` / `query` / `eval` / `audit-sample` / `audit-score` |
| `scripts/rights_scan.py` | manifest completeness, raw SHA-256 re-check, excerpt/attribution scan, exam-artifact guard, query hashes |
| `sources/source_list.json` | input list: 100 Polish Wikipedia titles + 7 Polish Wikisource documents, per-source rights notes |
| `sources/sources.jsonl` | CONTRACTS manifest: `source_id`, permalink `url` (with `oldid`), `title`, `publisher`, `retrieved_at`, `revision_or_sha256`, `license`, `allowed_use`, `local_path`, `source_group_id` |
| `sources/fetch_failures.json` | failures of the last fetch run (currently none) |
| `queries/train_queries.jsonl` | 40 TRAIN queries in the `examples.jsonl` shape + `expected_source_ids`, `expected_locators`, `must_contain` |
| `queries/query_hashes.json` | SHA-256 of normalized prompts (contamination cross-check hook) |
| `audit/audit_sample_bm25.jsonl`, `audit/audit_verdicts*.jsonl` | v1 audit: top-3 citations per query + independent verdicts |
| `audit/audit_sample_chrono_v2.jsonl`, `audit/audit_verdicts_chrono_v2*.jsonl` | v2 audit on the recommended configuration |
| `reports/index_meta.json` | index build metadata + deterministic index SHA-256 |
| `reports/eval_summary.json`, `reports/eval_per_query_*.jsonl`, `reports/eval_sweep_tw*.json` | top-k coverage, per mode and title-weight |
| `reports/audit_score_*.json` | citation precision from the independent audits (provisional) |
| `reports/rights_scan.json` | last rights/contamination scan |
| `examples/query_examples.{md,jsonl}` | 4 permitted example queries with 300-char excerpts |
| `ATTRIBUTION.md` | license/attribution for committed excerpts |
| `raw/`, `index/` | gitignored; rebuilt by `fetch` + `index` (+ `graph`) |

## Commands (from repo root; Python ≥ 3.10, `pip install requests` for fetch only)

```bash
python3 agentsLog/Bukareszt/scripts/retrieval.py fetch                 # ~60 s, 107 pages, 0.3 s sleep, 4.07 MB text
python3 agentsLog/Bukareszt/scripts/retrieval.py index                 # ~0.7 s, prints index SHA-256
python3 agentsLog/Bukareszt/scripts/retrieval.py graph                 # ~0.3 s, year/entity graph for --mode chrono
python3 agentsLog/Bukareszt/scripts/retrieval.py query "Kiedy zawarto unię lubelską?" --k 5 --mode chrono
python3 agentsLog/Bukareszt/scripts/retrieval.py eval --modes bm25,hybrid,chrono         # 40 queries, <2 s
python3 agentsLog/Bukareszt/scripts/retrieval.py audit-sample --k 3 --mode chrono --tag chrono_v2
python3 agentsLog/Bukareszt/scripts/retrieval.py audit-score --verdicts agentsLog/Bukareszt/audit/audit_verdicts_chrono_v2.jsonl --out audit_score_chrono_v2.json
python3 agentsLog/Bukareszt/scripts/rights_scan.py                     # exit 1 on any rights/provenance problem
```

Recommended configuration for integration: `--mode chrono --title-weight 1.0 --k 5` (fast, best evidence@1); `--mode bm25` is the plain baseline; `--mode hybrid` costs ~45 ms/query in pure Python.

## Revisions and hashes

- Sources: 107 rows, every row has `revision_id` and `sha256` of the fetched UTF-8 text; `sources.jsonl` SHA-256 `8b77a63afd25317d783a3e511e3f1f99f09b6cec3c740bdf101a0d069aadfeed`.
- Index (v2, split title/content fields): 3481 chunks, SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429` (deterministic: identical raw text ⇒ identical hash, verified from a fresh clone at 03:55 with zero revision drift; per-source content hashes are embedded in the index, timestamps are not).
- Audited v1 index (title concatenated into chunk text): SHA-256 `f18b12fa19081b4f0439e7bb1e8dd62e538a01bb01cd81a35328f421d59a084c` (first commit `6197fbc`).
- Queries: `train_queries.jsonl` SHA-256 in `reports/eval_summary.json` (`queries_sha256`).
- Wikipedia revisions are the ones current on 2026-09-26 00:10–00:13 UTC; re-running `fetch --refresh` later will fetch newer revisions and change hashes, which is why the manifest and index hash are committed.

## Measurements (40 TRAIN queries; provisional)

See `reports/REPORT.md` for the full tables. Headline, v2 index, `--title-weight 1.0`:

| mode | source@1 | source@5 | evidence@1 | evidence@5 | MRR(evidence) |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.925 | 0.975 | 0.70 | 0.95 | 0.821 |
| hybrid | 0.95 | 1.0 | 0.725 | 0.975 | 0.830 |
| chrono | 0.95 | 1.0 | 0.75 | 0.95 | 0.843 |

Independent citation audit (fresh-context subagent, judged from chunk text only, labeled provisional), top-3 citations × 40 queries:

| config | strict precision | lenient | top-1 strict | top-1 lenient | queries with ≥1 supported chunk in top-3 |
| --- | --- | --- | --- | --- | --- |
| v1 bm25 | 0.167 | 0.567 | 0.25 | 0.625 | 18/40 |
| v2 chrono | 0.217 | 0.558 | 0.40 | 0.725 | 22/40 |

Strict chunk-level support is much lower than source-level coverage: the retriever finds the right article far more often than the exact passage that answers. Three claim errors in my own query set were caught by the auditors and corrected (q09, q20, q26).

## Failures and limits (short; details in REPORT.md)

- Section-level misses: long articles with many subsections (Mur Berliński, Powstanie styczniowe, Kulturkampf) rank memorial/background sections above the one with the asked fact.
- Auditor is a Claude subagent, not the Sol model named in the issue (no Sol access here); label stays provisional.
- Corpus is 107 pages, Polish only; no images/OCR, no English cross-lingual retrieval.
- Wikipedia text quality and revision drift are not audited; only the revision is pinned.

## Next action

Lead decides whether to wire `retrieval.py` (mode `chrono`, k=5) into the answerer as a context provider; the retrieval contract (chunk schema `chunk_id`, `source_id`, `locator`, `text`) is additive and can be adapted. Cheap next steps are listed at the end of REPORT.md.

## #15 context selection (complete answer support)

Optional follow-up to #6 (issue https://github.com/kwiscion/machinekind-matura/issues/15, branch `issue-15-Bukareszt-context`, started 2026-09-26 03:10 Europe/Warsaw). Baseline frozen: same corpus, index (SHA-256 `350800b1…0429`, 0 revision drift on rebuild), graph and 40 TRAIN queries (`b2e359bf…024d`). Full results: [`reports/REPORT_15.md`](reports/REPORT_15.md).

- `scripts/context_select.py` (new, additive; imports `retrieval.py` unchanged): `select` / `eval` / `audit-sample` / `audit-score`. Candidate = chrono top-1 anchor + article prior across articles + residual/coverage section re-rank within an article + greedy 3000-char multi-chunk assembly; `candidate_c` adds evidence-retaining sentence compression; `candidate_t` (unaudited) drops filler chunks from distant articles.
- `reports/ctx_eval_ctx15.json`, `reports/ctx_eval_per_query_ctx15.jsonl`: automatic proxies for `baseline3`, `baseline5`, `candidate`, `candidate_c`, `candidate_t`.
- `audit/ctx_audit_sample_ctx15.jsonl` (blind A/B pairs, side randomised with seed 15), `audit/ctx_audit_key_ctx15.json` (hidden key), `audit/ctx_audit_verdicts_ctx15*.jsonl` (two fresh-context auditors), `reports/ctx_audit_score_ctx15.json`.

```bash
python3 agentsLog/Bukareszt/scripts/context_select.py select "Kiedy zawarto unię lubelską?" --variant candidate   # or baseline3 / candidate_c
python3 agentsLog/Bukareszt/scripts/context_select.py eval --tag ctx15
python3 agentsLog/Bukareszt/scripts/context_select.py audit-sample --tag ctx15 --baseline baseline3 --candidate candidate
python3 agentsLog/Bukareszt/scripts/context_select.py audit-score --tag ctx15 --verdicts agentsLog/Bukareszt/audit/ctx_audit_verdicts_ctx15.jsonl
```

Headline (40 TRAIN queries, provisional): automatic evidence-in-context 0.975 (candidate) vs 0.925 (chrono top-3) at ~2.9 kB either way; blind audit of complete answer support: **no measurable gain** — complete support 13/40 (candidate) vs 14/40 (chrono top-3), partial 26 vs 24, none 1 vs 2, auditor preference 8 / 6 / 26 ties, 1 win (q02), 1 regression (q39, 1948-vs-1947 contradiction). Recommendation: keep `--mode chrono --k 5`; reuse the blind A/B audit protocol.

## Watcher (separate PR #9, merged to main)

Owner log entry for the issue watcher that dispatches Greg's issues to Orca worktrees; unrelated to the retrieval code above.

- Path: `agentsLog/Bukareszt/watcher/` — `AGENT_BRIEF.md` (brief passed to every worker), `poll-issues.sh` (poll script), `2026-09-26-watcher-log.md` (timestamped log incl. dry-run evidence).
- Time: started 2026-09-26 01:30 Europe/Warsaw (23:30 UTC 25 Sep); polling stops 08:30 Warsaw.
- Mutable state lives in `agentsLog/Bukareszt/private/watcher-state.json` (gitignored, never committed).
- Command: `agentsLog/Bukareszt/watcher/poll-issues.sh` (prints candidate issues as JSON).
- Split/model/sources: none touched by the watcher. Failures/limits: see the watcher log.

## Notes (Europe/Warsaw, 2026-09-26)

- 02:10 claimed issue; read AGENTS/SOURCE/CONTRACTS/issue brief/agentsLog.
- 02:15–02:35 source list + script; fetched 107 sources (4 title fixes for disambiguation pages). Wikisource `extracts` returns empty text for transcluded pages, so Wikisource uses `parse` HTML stripped to text.
- 02:40 first commit `6197fbc` pushed; progress comment on #6.
- 02:45–02:55 audit sample (top-3, bm25 v1); two independent auditor subagents (q01–q20, q21–q40).
- 02:55 rights scan script, query hashes, attribution note, examples. Auditor flagged q20 claim imprecision (Belweder attacked by civilian conspirators, not cadets) → answer corrected in the query file; audit sample keeps original wording.
- 03:00–03:15 split title/content BM25 fields + `twostage` mode; title-weight sweep (0/0.25/0.5/1.0). Split field alone lifts evidence@1 0.60→0.70; `twostage` does not help; `chrono` best.
- 03:15 v2 audit sample (chrono, tw=1.0) sent to two fresh auditors. Index hash made deterministic (timestamp moved out of the index file).
- 03:25 residual-query `twostage` re-rank: negative result (ev@1 0.725 vs chrono 0.75, caps at 3 articles). Stopped iterating.
- 03:30 v2 audit scored: top-1 strict 0.25→0.40, lenient 0.625→0.725. Auditors caught claim errors in q26 (Wileńszczyzna) and q09 (Warmia); corrected.
- 03:45 REPORT.md, README, rights scan re-run (exit 0); commit + PR.
- 03:55 fresh-clone reproduction in a scratch directory: fetch → 0 revision drift, identical metrics, identical index SHA-256 after removing the manifest-file hash (timestamps) from the index payload. `fetch` now reports revision drift vs the committed manifest in `sources/fetch_failures.json`.

## #37 submission adapter (organizer package → offline `answers.json`)

Issue https://github.com/kwiscion/machinekind-matura/issues/37, branch `issue-37-Bukareszt-submission-adapter`, started 2026-09-26 14:40 Europe/Warsaw. Code in `scripts/Bukareszt/matura_package.py` (stdlib; `fetch-mock` / `check` / `prepare` / `finalize` / `validate` / `run` / `synthetic-outputs`) with 43 tests in `scripts/Bukareszt/test_matura_package.py`. Docs, command sequence, hashes and limits are in [`submission/README.md`](submission/README.md) and [`submission/REPORT.md`](submission/REPORT.md). The public mock was verified at 37 items / 60 points / 19 unique PNGs; its contents stay only in the ignored `private/`. No model was run and no score is claimed.

## #45 adapter acceptance fix (explicit completion, non-null errors, mandatory source fields)

Issue https://github.com/kwiscion/machinekind-matura/issues/45 (filed by @ljaniec from an independent review of the merged #37 adapter), branch `issue-45-Bukareszt-adapter-fix`, started 2026-09-26 15:25 Europe/Warsaw. Narrow change to `scripts/Bukareszt/matura_package.py` only: (1) a choice is complete only with an explicit supported `finish_reason` (`stop`/`eos`/`end_turn`/`stop_sequence`); a missing or `null` value now keeps the ID as `""` with an `incomplete` failure record; (2) every non-null `error` (including `""`, `{}`, `false`) is an `infer_*` failure; (3) `check`/`prepare`/`finalize` reject an absent `exam.instructions` or item `source_text`, while an explicitly supplied empty string stays allowed (the fixture item `2.1` has one). IDs, template order, blank failures and the failure report are unchanged. Eight regression tests were added in `scripts/Bukareszt/test_matura_package.py` (51 total, invented data only). No runner, retrieval, model or network change; the proxy finding from #38 is lead-owned.

## #44 staged pinned chrono index (portable bundle + pinned rebuild)

Issue https://github.com/kwiscion/machinekind-matura/issues/44, branch `issue-44-Bukareszt-stage-index`, started 2026-09-26 15:25 Europe/Warsaw. Deployment preparation only: corpus, retriever and index unchanged. `scripts/Bukareszt/stage_index.py stage [--bundle PATH]` stages `raw/` + `index/` from a fresh clone (bundle in <1 s, or rebuild from the pinned revisions in ~100 s), verifies 107 raw hashes, index SHA-256 `350800b1…0429`, graph content hash, and runs one TRAIN query with `--mode chrono --k 5` under a socket guard; any difference exits nonzero naming the source/hash. Bundle `chrono_index_bundle_350800b1.tar.gz` (3,942,102 B, SHA-256 `da0d4ad7…091e`) stays in gitignored `private/`; its manifest, attribution and three PASS reports are in [`staging/`](staging/README.md). 11 tests in `scripts/Bukareszt/test_stage_index.py`. No RTX 5090 run yet; no evaluation arm started.

## #44 follow-up (CRLF-safe identity, fail-closed pinned inputs)

Requested by the lead's portability review of PR #50 on issue https://github.com/kwiscion/machinekind-matura/issues/44, branch `issue-44-Bukareszt-identity-fix`, started 2026-09-26 15:55 Europe/Warsaw. `stage_index.py` now hashes the Git-tracked `sources.jsonl` and `retrieval.py` after CRLF→LF normalization, so Windows `autocrlf` and Linux checkouts both match `8b77a63a…`/`5ce9918f…`. It checks them before importing the retriever or starting any bundle/rebuild step, and `verify` also exits 1 on a mismatch. All pinned hashes and the bundle `da0d4ad7…` are unchanged. The change adds 8 regression tests (22 total). Details, evidence and the `.gitattributes` recommendation are in [`staging/README.md`](staging/README.md#44-follow-up-windows-crlf-checkouts-and-fail-closed-pinned-inputs). The PR is held for the lead's review and was not self-merged. The same PR also covers the three #54 blockers (https://github.com/kwiscion/machinekind-matura/issues/54): a nested `.gitattributes` setting `eol=lf` for the two hashed files, `--root` and destination guards before any delete/move, and verification of the retriever bytes before import (29 tests).
