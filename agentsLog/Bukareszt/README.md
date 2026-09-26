# Retrieval (issue #6) — @Bukareszt

Licensed offline BM25 retrieval over rights-clear Polish historical reference material (Polish Wikipedia, CC BY-SA 4.0, revision IDs recorded; Polish Wikisource public-domain primary documents). Standalone stdlib script; no model, teammate data, or paid service used.

- Issue: https://github.com/kwiscion/machinekind-matura/issues/6 · Branch: `issue-6-Bukareszt-retrieval`
- Started 2026-09-26 02:10 Europe/Warsaw (00:10 UTC). First slice committed ~02:40 Warsaw.
- Split used: TRAIN only (self-authored general-knowledge queries). No 2023/2024/2025 exam questions, keys, rubrics or source packs were read, fetched, or indexed.

Status: **work in progress** — see timestamped notes below and `reports/`. Full handoff table is filled in at the end of the run.

## Artifacts

| Path | What |
| --- | --- |
| `scripts/retrieval.py` | fetch / index / query / eval / graph / audit-sample / audit-score (stdlib + `requests` for fetch) |
| `sources/source_list.json` | input list: 100 plwiki titles + 7 plwikisource documents, with rights notes |
| `sources/sources.jsonl` | contract manifest: source_id, url (permalink with oldid), title, publisher, retrieved_at, revision + SHA-256, license, allowed_use, local_path |
| `sources/fetch_failures.json` | fetch failures of the last run |
| `queries/train_queries.jsonl` | 40 training-only queries with expected source IDs / section locators / evidence strings |
| `reports/index_meta.json` | index build metadata and index SHA-256 |
| `reports/eval_summary.json`, `reports/eval_per_query_*.jsonl` | top-k coverage per mode |
| `audit/` | independent evidence-audit sample and verdicts (provisional) |
| `raw/`, `index/` | gitignored; rebuilt by `fetch` + `index` |

## Commands

```bash
python3 agentsLog/Bukareszt/scripts/retrieval.py fetch            # ~1 min, 107 sources, polite 0.3 s sleep
python3 agentsLog/Bukareszt/scripts/retrieval.py index            # BM25 index, prints index SHA-256
python3 agentsLog/Bukareszt/scripts/retrieval.py graph            # year/entity graph for --mode chrono
python3 agentsLog/Bukareszt/scripts/retrieval.py query "Kiedy zawarto unię lubelską?" --k 5 [--mode bm25|hybrid|chrono]
python3 agentsLog/Bukareszt/scripts/retrieval.py eval --modes bm25,hybrid,chrono
python3 agentsLog/Bukareszt/scripts/retrieval.py audit-sample --k 3
python3 agentsLog/Bukareszt/scripts/retrieval.py audit-score
```

## Notes (Europe/Warsaw)

- 02:10 claimed issue; read AGENTS/SOURCE/CONTRACTS/issue brief.
- 02:15–02:35 wrote source list + script; fetched 107 sources (4 title fixes: disambiguation pages). Wikisource `extracts` is empty for transcluded pages, so Wikisource uses `parse` HTML stripped to text.
- 02:35 first eval on 40 queries: see `reports/eval_summary.json`.
