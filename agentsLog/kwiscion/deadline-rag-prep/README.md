# Deadline-limited ordinary and essay RAG

Selected by the owner for the manual final workflow. Use [the operator runbook](../../../docs/FINAL_RUN.md) and `scripts/run-final.ps1`; the lower-level preparer is not the manual entry point.

The generic Qwen coverage package supplies all direct answers first, preserving complete text, images and received IDs. Optional stages run serially: essay RAG first, then ordinary RAG in template order. Essay processing selects one offered topic, generates six queries, retrieves up to five passages per query, checks direct relevance with literal supporting quotes, and writes a single essay. Ordinary processing uses one query, five checks and one final. Failed or unsupported stages retain the exact direct answer; auxiliary outputs never become answer-sheet entries.

The remote deadline is at most 55 minutes from local launch. Optional work ends at the earlier of 20 minutes after it starts or 10 minutes before the remote deadline. Essay work is capped at 15 minutes and reserves up to 5 minutes (25% of the available optional window) for ordinary RAG. No evidence means no optional writer. The actual deadline can limit coverage; not every item is guaranteed a RAG rewrite.

The direct/ordinary-final profile keeps its qualified requested-token ceiling of 147,456 per item including three possible retries. Ordinary queries use 512 initially and 1,024 per retry; relevance checks use 384 initially and 1,024 per retry. Essay queries use 768 initially and 1,024 per retry. Essay writers use 16,384 with thinking on, then up to three 8,192-token retries with thinking off. Full original inputs accompany answer generation.

For N received items and E essays, maximum primary slots are `N + 7*(N-E) + 32*E`, with at most four attempts each. The requested-output-token ceiling is `147456*N + 168320*(N-E) + 148480*E`. These are conservative finite ceilings; wall time governs actual work.

Preparation auto-detects explicitly typed essays and also supports explicit IDs. It preserves the original package and records derived payload hashes. Runtime uses the preverified full Wikipedia SQLite index in immutable read-only mode and one eligible Qwen cache. The manual wrapper records start/deadline, resource proofs, finite limits, status, exact outputs and cleanup. Final inference remains inside the owned offline namespace.

Run CPU tests with:

```powershell
python -B -m unittest discover -s agentsLog/kwiscion/deadline-rag-prep -p test_deadline_rag.py -v
```

Tests and a bounded real mixed DEV smoke are recorded in the manual readiness report. The prior 40/60 direct full run remains preserved. The owner selected RAG under limited quality evidence: ordinary diagnostic 4/6 versus 4/6, one completed essay diagnostic 9/15. No full-exam RAG score is claimed.
