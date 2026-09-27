# Source-complete filtered retrieval study

Preparation only until a separately declared launch. One Gemma weight set, native thinking,65,536context, normal reviewed four-attempt recovery.48primary slots:6matched direct controls,6typed query-generation stages,30independent passage judgments,6filtered answers. Ceiling192attempts/7,077,888requested output tokens/60minutes/$3.28planning estimate; actual billing unverified.

Every stage receives the complete original question, source text and original image bytes. The hook restores the original printed ID/prompt before native payload construction. Query generation produces a compact query and labels possible identifications as hypotheses. Invalid query JSON falls back to generic task/source lexical retrieval. The complete pinned Polish Wikipedia index supplies top5passages; no107article fallback or live internet access.

Each judgment sees only one passage plus original inputs. Only strict `direct:true` with an exact nonempty substring is admitted. One optional JSON fence is accepted; duplicate keys and invented quotations are rejected. Optional admitted evidence is bounded to14,000UTF8bytes by dropping lowest-ranked entries, recording removals; originals and full passage artifacts remain intact. No accepted evidence means the original bare answer prompt.

Retrieval is frozen at first judgment use; admission is frozen at first final use. Late recovery of an intermediate does not retroactively modify those inputs. This makes incomplete intermediates a conservative fallback, not a silently changing experiment. Intermediate slots remain private study outputs; `export_answers.py` emits only six direct and six final answers with original IDs.

`prepare.py` creates a fresh private package using the existing organizer adapter/recovery preparer. Its copied binding differs from reviewed54983970 only by installing the pinned hook immediately before the scheduler. Runtime identity, source pins, durable reservations, absolute guardian, network namespace, usage/context checks and owned timeout cleanup remain unchanged. The hook verifies the full index SHA before any model request and detects subsequent file changes. Model-generated query hypotheses are not factual evidence.

CPU checks:
```
python -X utf8 agentsLog/kwiscion/filtered-rag-prep/test_study.py
python -X utf8 agentsLog/kwiscion/full-wikipedia/test_search_query.py
python /private/package/run_recovery_package.py /private/package
```
After root declaration and fresh sole-worker/cache checks, use the package's existing `operator_recovery.sh PACKAGE --execute` once. Export terminal slots with `python PACKAGE/export_answers.py PACKAGE`; retain all12answers/errors/placeholders and all48stage records. No calls are authorized by preparation or this README.

Retrieval qualification is limited: ten short independent queries were easy health checks, not measured real-question recall. Full original task lexical queries exposed weaknesses; generated queries and independent DIRECT filtering are the proposed mechanism under test. No score or promotion claim.
