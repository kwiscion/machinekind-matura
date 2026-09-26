# Evaluation-only historical checklist — #143

These original concise notes support independent grading of the 16 frozen synthetic essay inputs. Both alternative topics in each input are covered; a submitted essay must select one. This is an evidence aid, not a gold essay, mandatory thesis or exhaustive event list. Never use these notes as training data, model input or retrieval material.

## Frozen input and exposure

Input: `agentsLog/Bukareszt/essay_corpus/export_v1/eval16_input.jsonl`, canonical Git-byte SHA256 `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28`.

Checklist preparation began 26September2026 at 22:25 UTC, with 23:10 UTC hard handoff target. Three bounded researchers and the coordinating reviewer worked on disjoint four-input batches. Candidate/model answers and existing eval16 fact cards were not inspected before this checklist was frozen. General repository calibration and public aggregate results were already visible; these are not blind model grading results. No GPU/model API call, training, download of weights, purchase or fixed exam acquisition was made for this task. May2025 remained sealed.

The issued [data-only clearance](../../kwiscion/2026-09-26-pr131-data-clearance.md) permits a separate external eval16 quality test and explicitly treats existing cards as fallible. Our independent research uses original input topics and primary/authoritative historical sources. Every note records source IDs, URLs, retrieval dates and relevant locations. The research files contain original summaries rather than copied passages or source images; no source redistribution license is inferred from public access.

## Grading procedure

1. Freeze the checklist and exact submitted-answer hashes before comparing candidates. Use anonymous labels, retain initial exposure, identify the chosen topic and count body words. Evaluate only that topic; do not silently pick an answer from two competing essays.
2. For each **explicitly required** aspect, identify the actual supporting passage and its factual claims. Evaluate how the evidence supports the thesis: absent 0, superficial 1, satisfactory 3, rich 4. A date/name alone is not developed argument; a concise causal explanation may be satisfactory. Examples here are optional evidence anchors. Topic2 branches often state no formal aspect list: their organized dimensions are research aids, not invented compulsory aspects or a new official scoring denominator.
3. Record distinct **verified false factual claims** and corrections separately. Deduct 1 for 1–2 errors, 2 for 3–5, 3 for more than 5, once from the narrative subtotal. Count repeated instances of one false proposition once. Floor narrative at 0, then add coherence separately. Vague argument, omission, uncertain precision and defensible alternative interpretation are not automatically factual errors; explain their effect on argument quality independently.
4. Apply the existing coherence calibration to actual logical connections. Under 300 body words gives 0 coherence, not automatically 0 overall. The issued task requests 400–500 words; report compliance separately. Do not invent an unprovided numerical coherence maximum or normalize all synthetic two-aspect topics to15 points without a separately declared rubric. Use the established applicable scoring sheet and retain aspect/coherence components.
5. Accept alternative sound facts and theses. If a new claim falls outside these notes, verify it before penalizing it. A historical source may itself simplify chronology or statistics: unresolved disputes stay marked. Material factual disagreements require independent adjudication; preserve both first passes.

## Files

`topics-01-04.json`, `topics-05-08.json`, `topics-09-12.json` and `topics-13-16.json` contain the evaluator notes. Each record binds its input ID, source group and exact prompt hash. `manifest.json` records completeness, file hashes, freeze time and verification. `checklist.md` is the readable view of the same notes.

Claims are provisional historical research aids, not organizer grades or candidate promotion. Source access failures and outstanding precise claims are explicit limitations. Historical interpretation remains open where evidence supports more than one conclusion.

## Source manifest

`sources.jsonl` uses the source contract in `docs/overnight/CONTRACTS.md`, with globally unique input-prefixed IDs. Web references were checked as rendered page text; original response bytes/revisions were not archived, so `revision_or_sha256` is explicitly unknown. Unknown reuse rights are marked `license: unknown`; permitted use is reference only, with no source text or images redistributed. Record-local IDs in the batch JSON resolve to the same URLs. Retrieval dates use UTC.

## Reproduce structural checks

From the repository root, run `python3 agentsLog/ljaniec/eval16/verify.py`, then `git diff --check`. This checks frozen bytes, complete coverage and reference integrity; it does not replace historical source review or grade a candidate.
