# Full Polish Wikipedia retrieval

All six Parquet shards of the official `wikimedia/wikipedia`, configuration `20231101.pl`, revision `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`:1,765,059,986compressed bytes. This is the complete cleaned2023-11-01 Polish snapshot, not current Wikipedia or a selected history corpus. Every shard is pinned by exact size and LFS SHA256 in `wiki_index.py`.

Dataset source/card: https://huggingface.co/datasets/wikimedia/wikipedia . Declared licenses: CC-BY-SA3.0 and GFDL. Preserve article IDs, titles and original URLs with retrieved passages for attribution; derived redistributed corpus/index material must preserve the applicable license obligations. The corpus/index stays outside Git. No benchmark questions, keys, answers or rubrics are added to the index.

```bash
python wiki_index.py download /owned/fresh/corpus
python wiki_index.py build /owned/fresh/corpus
python search_query.py /owned/fresh/corpus/passages.sqlite --query "unia kalmarska 1397 Małgorzata"
```

Requires project-local PyArrow21.0.0 for Parquet streaming; search uses stdlib SQLite FTS5 only. Article coverage is checked against every Parquet row count, with duplicate IDs/malformed rows failing closed. Empty articles remain counted explicitly. Exact source spans cover all characters; paragraph-preferred1600-character windows overlap200characters. Original passage text is never normalized or rewritten; only separate search fields are case/diacritic normalized, including Polish `ł`.

The separately versioned `search_query.py` derives queries from task/source fields, excluding generic instructions and explicit bibliography lines. It ranks all query terms by corpus IDF, recalls200BM25 candidates with4x title weight and bounded inflection-prefix expansion, then reranks normalized task/source/title coverage. It permits up to3 complementary passages per article and rejects actual overlapping spans. Prefix expansion is a limited heuristic, not Polish linguistic stemming or a semantic relevance guarantee. Model-based DIRECT relevance filtering is a separate declared experiment. The older simple search in the immutable build script remains a baseline only.

`independent_queries.json` freezes eight general history checks and two inflected variants independently of held-out keys. Inspect relevant article **and specific returned passage**, record misses and latency; do not equate nonempty search results with support. No model calls are part of acquisition/index qualification. The historical107-article RAG result does not measure this full corpus.

Tests: `python test_wiki_index.py` verifies complete exact-span coverage, empty-article accounting, Polish normalization, title/body search and exact six-shard size.
