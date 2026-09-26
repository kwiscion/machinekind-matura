# Optional source-interpretation repair candidates

Six **draft** candidate records, separate from strict/default training. They repair existing prompts about the Union of Krewo, Bar Confederation, Warsaw Uprising, Swedish invasion, Congress Poland and liberum veto using only the original cited claims. Tasks ask students to distinguish conditions from outcomes, identify actors, separate intentions from results, preserve uncertainty, and identify evidence limits. Original records are unchanged.

`author_audit.jsonl` records both strict rubric lenses as an **author-only self-assessment**, not independent verification. Six proposed repairs pass that assessment provisionally. Two other original tasks were not emitted: the December 1970 price-impact prompt lacks the measured-quantity context in its claim, and the broad Sigismund I essay plan exceeds its cited evidence. No failed record is relabeled verified.

The quoted source passages retain their original source IDs, source groups, locators, and attribution. `manifest.json` includes six pinned Wikipedia source records and LF-normalized artifact hashes. The source passages were not fetched again; their source/verbatim verification is inherited from the original pipeline. CC BY-SA 4.0 provenance remains explicit. No exam material, new research, model API calls, or paid work was used.

Validation (lineage and quarantine only):

```bash
python agentsLog/kwiscion/data-repair-candidates-2026-09-26/validate_candidates.py
```

This checks stable unique IDs, unchanged evidence/source groups, exact derivation hashes, draft status and that strict export refuses the candidates. An independent source-grounded S/Q audit is required before any promotion. This optional set has no dependency on the lead's exam diagnostic and does not increase the accepted count of 24 strict records.
