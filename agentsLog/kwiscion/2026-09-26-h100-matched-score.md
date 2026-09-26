# Matched H100 sampling review and decision

**Retain the preserved35/60 bare fallback. Neither new attempt is promoted.** Two independent Sol reviewers graded disjoint20-item halves against the official evaluation rubric, with A/B aliases and no configuration inspection. This is provisional first-pass agent grading, not an organizer score or independent adjudication. The reviewers knew project hypotheses and prior findings, so masking was limited.

| Configuration | Score /60 | Descriptive grading range | Completion | Nonessay /45 | Essay /15 |
| --- | ---: | --- | --- | ---: | ---: |
| A: temperature omitted |31|21–34|40 complete|27|4 [3,6]|
| B: temperature0.2 |24|19–27|38 complete,1 failed,1 unsent|24|0 unsent|

The aggregation checks40 unique IDs per arm, disjoint reviewer slices and60 total available points. Ranges sum item-level judgment uncertainty, not statistical confidence intervals. B's failed item and unsent essay stay zero; its missing essay cannot establish an essay-quality decline. The matched nonessay difference is3central points and reviewer uncertainty is material, including a two-point short-item interpretation. Do not impute an essay or call a selected composite a fresh complete candidate.

A's essay body has338 words; weak argument and factual errors are the main grading concerns, not merely length. Both arms still fail several source-grounding and historical-relation items. These findings support the already-assigned source, retrieval and essay experiments. They do not establish that H100 hardware changes quality or that temperature caused every observed difference.

All39 paired requests were identical except B's explicit temperature field. The [execution report](2026-09-26-h100-matched-result.md) records112.750seconds for complete A and97.572seconds for stopped B,79 total calls and verified local backups. B's39th response became repetitive and reached1024 output tokens; the declared stop prevented dispatch of the essay. No retry, answer editing or post hoc rescue occurred.

Next actions: [#100](https://github.com/kwiscion/machinekind-matura/issues/100) isolates strictly case-local completion failures in an opt-in launcher mode while preserving all runtime/context/transport/budget stops. [#95](https://github.com/kwiscion/machinekind-matura/issues/95), [#96](https://github.com/kwiscion/machinekind-matura/issues/96) and [#80](https://github.com/kwiscion/machinekind-matura/issues/80) remain the source-grounding, selective-retrieval and essay tracks. No further GPU calls are authorized by this report.

Evidence: detailed independent first/last20 reviews and their JSON files remain local, alongside immutable private exact-answer handoffs verified against the execution report hashes. Public totals were recomputed from40 unique IDs and60 available points. Official questions/keys, item-level rubric evidence, raw provider envelopes and infrastructure details remain private.
