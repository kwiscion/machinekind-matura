# Independent content audit of PR 23 draft candidates

Reviewed exact head `31b8537bdf743ebaa60606f0e17a5f65faf789b8` of [PR #23](https://github.com/kwiscion/machinekind-matura/pull/23). This audit reads the candidate questions, answers, inherited evidence and original source manifests independently of the author's lens verdicts. No external source fetch, exam material, inference or training. Source authenticity against the original article is inherited evidence, not freshly reverified.

Q = self-contained, determinate question with supported premises. S = every substantive answer conclusion follows from the supplied passages. Verdicts are provisional independent judgments by this Codex reviewer, not human certification.

| Candidate suffix | Q | S | Evidence and reasoning |
| --- | --- | --- | --- |
| 001 | pass | pass | `src-plwiki-unia-w-krewie`, lead / Tło historyczne, oldid 80354694: the passage explicitly makes baptism necessary for marriage and refers to the beginning of Christianization. The answer correctly rejects an inference of completion without adding an outcome or claiming marriage and union are identical. |
| 002 | repair | repair | `src-plwiki-konfederacja-barska`, Tło, oldid 80595425: the first passage attributes constitutional changes to Poniatowski; the second attributes demands to Prussia and Russia. Neither says the king did not also make such a demand. The prompt's claim of erroneous attribution and the answer's categorical rejection turn absent evidence into an exclusive historical conclusion. Limit the task to what these excerpts actually attribute. |
| 003 | pass | pass | `src-plwiki-powstanie-warszawskie`, lead, oldid 80788930: the quoted verbs describe a military plan and hoped-for political benefit. The answer separates intention from achieved result and does not assert the hoped-for result occurred. |
| 004 | pass | pass | `src-plwiki-potop-szwedzki`, lead, oldid 79761633: the explicit estimate marker warrants preserving uncertainty around the stated 90% figure. The answer does so and neither invents an interval nor adds a cause beyond the excerpt's wartime wording. |
| 005 | pass | pass | `src-plwiki-krolestwo-polskie-kongresowe`, lead, oldid 80728653: the excerpt lists institutions and symbols, without describing Russia or a shared monarch. The answer correctly limits what this passage establishes; it does not deny that a personal union existed historically. The task assumes the ordinary definition of personal union but requires no unstated historical event. |
| 006 | repair | repair | `src-plwiki-liberum-veto`, Geneza, oldid 79646244: the phrase 'choć niesłusznie' rejects the whole conventional account (actor/event/instrument/first occurrence/date). It does not identify which component is wrong. Asking whether the author rejects the date specifically is narrower than the evidence warrants. The answer's refusal to invent an alternative date is sound; change the first question and initial answer to address the whole account. |

## Minimal repairs

- **002 prompt:** replace the premise of false attribution with: `Wskaż, której części zdania ucznia nie potwierdzają przytoczone fragmenty. Jakim podmiotom fragmenty przypisują wymienione działania?` Answer: the fragments attribute constitutional changes to Poniatowski and the religious-rights demands to Prussia and Russia; they do not establish whether Poniatowski also made those demands. This is a source-support judgment, not proof of the historical negation.
- **006 prompt:** ask whether the author endorses the entire quoted account of Siciński's alleged first disruption using liberum veto, then ask whether the excerpt supplies an alternative correct account/date. Answer: the author rejects that account, but the excerpt alone does not identify the mistaken component or give an alternative date. Do not infer that the date itself is necessarily false.

## Provenance and eligibility checks

The candidate validator passed all six lineage records and confirmed draft status and rejection by the strict exporter. A separate comparison found all six embedded source manifest objects identical to the original `data/przemeknowak781/sources.jsonl` objects, including revision URLs, attribution and licensing. Existing evidence/source groups were unchanged. No default strict artifact or exporter was edited.

```text
python agentsLog/kwiscion/data-repair-candidates-2026-09-26/validate_candidates.py
candidates=6; lineage_valid=true; drafts_rejected_by_strict_export=true
```

Recommendation: retain the six as auditable draft artifacts with this independent audit; four currently pass, two need the wording repairs above before a positive independent verdict. Do not promote any record through this PR or change the 24-record strict policy. The original author's self-assessments are not substituted for this review.
