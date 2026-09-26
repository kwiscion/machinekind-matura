# Staging the pinned chrono index on another machine (issue #44)

Owner @Bukareszt. Makes the existing pinned retrieval asset from #6 portable to the RTX 5090 host (or any
fresh clone) **without changing the corpus, the retriever or the index**. This is deployment preparation only:
no new sources, embeddings, tuning or model calls, and no evidence that retrieval improves the exam score.

Pinned identity (must be reproduced exactly, never refreshed):

| item | value |
| --- | --- |
| sources | 107 licensed reference pages (100 Polish Wikipedia + 7 Polish Wikisource), pinned by revision ID + normalized-text SHA-256 in `../sources/sources.jsonl` (SHA-256 `8b77a63afd25317d783a3e511e3f1f99f09b6cec3c740bdf101a0d069aadfeed`) |
| index | `index/bm25_index.json`, 3,481 chunks, SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`, 8,514,642 bytes |
| graph | `index/graph.json`, content SHA-256 (without `built_at`) `9ed53bb99bf0599fa67535ec1a0b14d0869e6c62c210d81193fa9fd0093a004b` |
| retriever | `../scripts/retrieval.py` unchanged (SHA-256 `5ce9918fcc0151c8e15391781ace98deaf4b786977a69e6e773ccc9d7b0a51a3`), `--mode chrono --k 5 --title-weight 1.0` |
| bundle | `chrono_index_bundle_350800b1.tar.gz`, SHA-256 `da0d4ad772182d8537e81bdbfdeed267b8edf54ad2a85494fcaaed6f80dd091e`, 3,942,102 bytes, 112 members, byte-deterministic |

## One command (fresh clone, Python ≥ 3.10, stdlib only)

```bash
git clone https://github.com/kwiscion/machinekind-matura.git && cd machinekind-matura
# A) portable bundle (preferred, offline, <1 s): put the bundle at the default path or pass --bundle
python3 scripts/Bukareszt/stage_index.py stage --bundle /path/to/chrono_index_bundle_350800b1.tar.gz
# B) fallback when no bundle is present (network, ~100 s): rebuild from the pinned revisions
python3 scripts/Bukareszt/stage_index.py stage            # auto-falls back to --rebuild when the bundle is absent
```

Exit code 0 = staged and proven; 1 = any blocker (a differing hash names the source/file and both hashes;
unexpected errors are recorded the same way under `blocker` in the report). Before any path runs, the clone's
`sources.jsonl` and `scripts/retrieval.py` must hash to the manifest's pinned values. The report goes to `agentsLog/Bukareszt/private/stage_report.json`
(gitignored) unless `--report PATH` is given. Re-running on a staged clone verifies only (`path_used:
already-staged`); `--force` re-stages.

What `stage` proves, in order:

1. `sources.jsonl` hash, then every one of the 107 raw files against its pinned SHA-256; 
2. index file SHA-256 = `350800b1…0429`, embedded per-source hashes = manifest, 107 sources / 3,481 chunks;
3. graph content hash;
4. one existing TRAIN query (`ret-train-q01`, "Kiedy i przez kogo został spisany Kodeks Hammurabiego?") run
   with `--mode chrono --k 5 --title-weight 1.0` in a child process (`python -I`) with proxy variables
   stripped and a best-effort in-process socket guard (`socket.socket.__init__`, `SocketType`, `_socket.socket`,
   `create_connection`, `getaddrinfo` all raise; self-tested before the query). Hard isolation is
   `unshare -rn`, added automatically on Linux when it works; the report lists the guards actually used. The
   top-5 `chunk_id`/`source_id`/`locator` order must equal the committed proof in `manifest.json` and each score
   must be within 0.001 of it (float noise across CPU architectures is tolerated, ranking is not).

Path B fetches each Wikipedia page's **current** revision through the TextExtracts API (that API serves only
the current revision) and each Wikisource page through `parse&oldid=<pinned>`, then compares revision ID and
text hash with the manifest. Fetched text goes to a temporary directory and replaces `raw/` only when all 107
match; on any drift the run fails, lists each drifted source with both revision IDs and hashes, leaves the fetched
text under `private/rebuild-drift/` for inspection and keeps existing `raw/` untouched. The committed manifest is
never rewritten (unlike `retrieval.py fetch`, which refreshes to the latest revision and must not be used here).

## Getting the bundle to the GPU host

The bundle is kept out of Git (`agentsLog/Bukareszt/private/`, gitignored) and is not published anywhere. It
lives on Greg's laptop at `agentsLog/Bukareszt/private/chrono_index_bundle_350800b1.tar.gz`; copy it by
`scp`/shared drive on request and check `sha256sum` = `da0d4ad7…091e` before use (`stage` checks it again).
It contains only CC BY-SA 4.0 Wikipedia text, public-domain Wikisource text, the derived index/graph,
`sources.jsonl`, `MANIFEST.json` and `ATTRIBUTION.md` (same as [ATTRIBUTION.md](ATTRIBUTION.md) here). No exam
questions, answers, keys, source packs or model outputs. If the copy is not practical, path B gives the identical
result as long as no pinned Wikipedia page has been edited since 26 Sep 2026 00:10 UTC; at 15:34 and again at
15:44 CEST all 107 still matched.

## Integration with the existing runner (unchanged shared code)

`scripts/prepare_rag.py` reads the staged files at their default paths; nothing else needs configuring:

```bash
python scripts/prepare_rag.py --input <exam-input.jsonl> --output outputs/rag-input.jsonl \
  --trace outputs/rag-trace.jsonl --corpus outputs/rag-corpus.jsonl        # defaults: --mode chrono --k 5
python infer.py --config <local-config.json> --input outputs/rag-input.jsonl --output outputs/rag-raw.jsonl
python scripts/normalize_outputs.py --input outputs/rag-raw.jsonl --trace outputs/rag-trace.jsonl --output outputs/rag-model.jsonl
```

The trace records `index_sha256`, which must print `350800b1…0429`. Starting an evaluation arm is a lead
decision (WINNING_PLAN.md gate 17:00); this task does not start one.

## Evidence (26 Sep 2026, Europe/Warsaw, macOS 15.6 arm64, Python 3.14.4)

| report | path used | total | phases | disk after |
| --- | --- | --- | --- | --- |
| [stage_report_local_bundle_host.json](stage_report_local_bundle_host.json) | bundle (`--force`, this worktree; `argv` is in the report) | 0.33 s | unpack 0.06 s, verify 0.09 s, offline query 0.17 s | raw 4,073,637 B, index 8,585,725 B |
| [stage_report_fresh_clone_bundle.json](stage_report_fresh_clone_bundle.json) | bundle, fresh `git clone` in a scratch dir | 0.33 s | same | same |
| [stage_report_fresh_clone_rebuild.json](stage_report_fresh_clone_rebuild.json) | rebuild from pinned revisions, fresh clone, network | 89.5 s | fetch 88.3 s (107 requests, 0.3 s sleep), index 0.9 s, verify 0.08 s, offline query 0.17 s | same |

All three: index SHA-256 `350800b1…0429`, 0/107 raw differences, graph content hash matched, offline top-5 identical
(`plwiki-kodeks-hammurabiego#0145` 52.0181, `#0147` 49.5210, `#0151` 42.4778, `#0148` 41.1652, `#0150` 41.1078);
index load 0.10 s, ranking 0.7 ms. Guards used: `socket-guard`, `proxy-env-stripped` (`unshare` is not available
on macOS; it is added automatically on Linux when `unshare -rn true` succeeds).

Tests: `python3 -m unittest -v scripts.Bukareszt.test_stage_index` (22 tests since the follow-up below, synthetic two-source corpus, no
network): bundle round trip in a fresh clone, byte-deterministic bundle, tampered member / raw file / archive hash
each fail naming the item and hashes, manifest without an archive hash refused, rebuild drift reported per source
without rewriting the manifest or `raw/`, exact rebuild reproduces the index hash without touching
`reports/index_meta.json`, modified retriever refused before unpacking, socket guard blocks `urlopen` /
`socket.socket()` / `socket.SocketType()`, query-proof score tolerance vs. order mismatch. CI does not discover `scripts/Bukareszt/` tests (workflow is shared);
run them locally.

## #44 follow-up: Windows CRLF checkouts and fail-closed pinned inputs

The lead's portability review of #50 found that a Windows checkout (`core.autocrlf=true`, no `.gitattributes`)
hashes `sources.jsonl` as `701ad15…` instead of the pinned LF `8b77a63a…`, and that a retriever hash mismatch was
only recorded. Fix (branch `issue-44-Bukareszt-identity-fix`, `scripts/Bukareszt/` only):

- **Text identity.** The two Git-tracked pinned inputs, `sources/sources.jsonl` and `scripts/retrieval.py`, are
  hashed as SHA-256 of their bytes with every CR LF replaced by LF. Nothing else is normalized: a trailing newline
  is kept or left absent exactly as committed, and a lone CR or a UTF-8 BOM still changes the hash. For LF files
  this is the identity, so every pinned value (`8b77a63a…`, `5ce9918f…`, `350800b1…`, bundle `da0d4ad7…`) is
  unchanged. `sources.jsonl` is written into the bundle as LF bytes, so `bundle` on a CRLF checkout rebuilds the
  byte-identical archive. Untracked assets (`raw/`, `index/`, the bundle) keep exact byte hashes. Parsed-only
  text (`manifest.json`, `queries/*.jsonl`) is read in text mode and is newline-agnostic.
- **Fail closed.** `stage` checks both inputs before importing the retriever, before unpacking a bundle and before
  any rebuild request. `verify` checks them too. A mismatch or missing file exits 1, and the message names each file
  path with the expected hash, the actual normalized hash and the raw byte hash.
- **Paths.** `DEFAULT_ROOT` derives from the script location, not from the current working directory. Relative
  `--root`/`--bundle`/`--report` resolve against the caller's working directory. A test stages a fresh clone from
  another working directory using only relative paths.

Evidence (real `git -c core.autocrlf=true clone`, macOS, bundle `da0d4ad7…`):

| report | code | result |
| --- | --- | --- |
| [before](stage_report_crlf_clone_before_fix.json) | main `a8f4c79` | FAIL: `retrieval.py` `7c30237b…` ≠ `5ce9918f…` (`sources.jsonl` `701ad15…` would fail next) |
| [after](stage_report_crlf_clone_after_fix.json) | fix | PASS via bundle, index `350800b1…`, identical top-5, 0.33 s |
| [tampered](stage_report_crlf_clone_tampered_retriever.json) | fix, `--rebuild`, no bundle, edited `retrieval.py` | exit 1 after the `pinned_inputs` phase; no import, fetch or rebuild |

`bundle` run on the CRLF clone reproduced `da0d4ad7…` (3,942,102 B) and the same manifest `files`, hashes and query
proof. Recommended for the lead (the shared root file was not edited here): add `agentsLog/Bukareszt/** text eol=lf`
to the root `.gitattributes` so that checkouts also stay LF on disk.

## Limits

- No RTX 5090 run yet: staging was proven on Greg's laptop and in fresh local clones. The GPU host needs only
  Python ≥ 3.10 and either the bundle file or network access to `pl.wikipedia.org`/`pl.wikisource.org`.
- Path B depends on Wikipedia revisions staying current; the first edit to any of the 100 pages makes path B fail
  for that page (by design), and the bundle becomes the only exact route.
- `unshare -rn` requires unprivileged user namespaces; otherwise only the in-process socket guard is used and
  recorded. That guard is a monkeypatch: code holding a pre-existing reference to the C socket class could still
  open a socket; the pinned retriever imports no such code (the child prints the guards it used).
- Independent review (fresh-context subagent, 15:50 CEST) found no false-PASS path and five should-fix items
  (temp-dir rebuild, up-front pin check, retriever hash enforcement, guard coverage, tar member types), all
  applied before merge; its remaining nits (members count, argv, score tolerance) are applied too.
- The bundle is not published (rights review for redistribution is limited to the attribution file); `stage`
  refuses any bundle whose SHA-256 is not the one in `manifest.json`.
