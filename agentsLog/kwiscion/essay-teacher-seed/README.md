# Source-grounded essay teacher seed — DRAFT

For Greg (@Bukareszt), [issue #117](https://github.com/kwiscion/machinekind-matura/issues/117). Generated 2026-09-26 in a parent-designated Astra teacher session; exact runtime model snapshot was not independently exposed or verified. No provider API, GPU, purchase, training, Git commit, or publication was performed.

**4 original Polish prompts + 4 full target essays + 4 original repair pairs; 4 unique target essays; 4 source groups; 29 evidence cards. **Independent Sol review accepts the4essay targets and4repairpairs with limitations; zero records are yet integrated/export-ready.** See independent-review.md/json. Target prose and prompts remain unchanged after that review.** Word counts: Solon 412, Casimir 409, Lublin 421, January Uprising 422. Count convention: non-whitespace tokens in the complete target body; no title/wrapper/citations in target prose.

Topics were independently chosen from general historical references: antiquity (Solon), Middle Ages (Casimir III), early modern (1569 union), nineteenth century (1863–1864 peasant policy). The generator did not open fixed exam questions, benchmark sources, keys, grading explanations, model answers or the user attachment. Reading the current project control plan is not proof of absence of all prior topic exposure in pretrained weights. No novelty-to-model claim is made.

## Files and reproduction

- `essays.jsonl`: four draft essay instruction/response records.
- `repairs.jsonl`: four draft repair records, explicit negative input and defect list. Targets intentionally duplicate paired essays.
- `essay-*.txt`: four human-readable, independently composed Polish target texts.
- `evidence-cards.jsonl`: actors/events/dates/consequences, source locators, paragraph coverage and fact/inference distinctions. Source support was inspected by the generator and then independently reviewed; the separate review records its findings and limits.
- `sources.jsonl`: four licensed Wikipedia secondary references, pinned revisions, acquisition times and actual HTML SHA-256 hashes, attribution/history/license links.
- `crosscheck-sources.jsonl`: Aristotle via MIT, Jagiellonian University archive, AGAD, Muzeum Historii Polski (explicit CC BY 4.0 text) and Muzeum Wsi Radomskiej checks. Rights to the other website presentations are not established; reference facts only, no copied prose enters examples.
- `supplementary-review-notes.md`: museum corroboration added after the target/evidence-card freeze, including differing source emphases about peasant participation. Four Wikipedia references plus the MHP article give five licensed references; there are nine acquired source pages total.
- `source-groups.jsonl`: canonical group IDs and known English/Polish aliases. Every repair and its target stay in the same group.
- `validation.json` and `SHA256SUMS.txt`: structural checks and artifact hashes.

From the repository root, offline after acquisition:

```powershell
python agentsLog/kwiscion/essay-teacher-seed/build_seed.py
python agentsLog/kwiscion/essay-teacher-seed/validate_seed.py
```

`acquire_sources.py` and `acquire_crosschecks.py` document source acquisition. They fetch current pages and overwrite acquisition manifests: **do not rerun casually on this frozen review bundle**. Existing revision permalinks and hashes identify the reviewed material; a new acquisition is a new provenance revision. Raw snapshots are retained locally under Git-ignored `sources/` and `source-private/`. No images were acquired as separate assets. The snapshot hash covers downloaded HTML, not an imagined canonical article text.

## Repair construction

1. Solon: add preamble and closing commentary; target removes both.
2. Casimir: retain only the first two paragraphs; target restores sufficient argumentation and length.
3. Lublin: append a separately headed answer to another institutional subquestion, made from the same essay's fifth paragraph; target retains only the requested essay. This is a narrow same-era multiple-answer fixture, **not** a strong cross-era topic-selection example.
4. January Uprising: truncate to two paragraphs and add wrapper/closing commentary; target expands and cleans.

All corruptions use our own target prose and synthetic wrappers; no external model answer is repurposed. The repair input explicitly names the selected topic. The fixture does not teach silently choosing among equally valid alternatives when no topic was selected.

## Independent review before integration

Greg or another reviewer must check every factual claim against the linked pinned evidence, then assess coherence, causal reasoning, prompt coverage and Polish quality. Priority details: ancient institutional attribution and limits of the Solon tradition; Casimir's statute chronology and actual early university operation; the distinction between 1 July agreement and 4 July royal ratification; peasant participation varying by region and the scope of implementation of the 1863 decrees/1864 reform. The January topic now has two museum crosschecks; their differing emphases should inform independent review rather than being flattened into a claim of passive peasantry. Generalizations and causal arguments are explicitly synthesis, not source quotations.

Merge canonical groups with Greg's existing corpus using actual source/topic overlap and multilingual aliases. These local labels are provisional global identifiers, not proof of deduplication. Hashes catch exact normalized prompt matches only; **near-duplicate and contamination review is still pending**. An isolated benchmark custodian may screen exclusion without sending benchmark content to the generator or training set. No TRAIN/DEV allocation has been invented from four topics: `split` is null throughout. Essay and repair duplicates must never cross evaluation boundaries. This bundle intentionally uses a review schema and is not yet a canonical exporter input.

For reuse of Wikipedia-derived material, retain contributor attribution, revision/history links, license notice and change indication; review whether share-alike applies to the proposed distributed derivative. Text was newly composed in Polish, without direct quotations or a sentence-by-sentence translation. Do not apply a blanket project license to third-party source material. The institutional crosscheck pages are not a licensed text corpus. Publish manifests and reviewed original artifacts, not the ignored HTML website bundles. No dataset/model license determination or public upload is implied by these drafts.

The validator checks counts, required fields, lengths, duplicate targets, group consistency, explicit corruption patterns and nine source hashes. The separate review covers content; cross-corpus grouping, exclusion review and canonical export remain pending. It cannot certify factual correctness, semantic relevance, absence of benchmark overlap, dataset rights, export feasibility, training efficacy or final offline/8 GB qualification. Those remain separate gates.
