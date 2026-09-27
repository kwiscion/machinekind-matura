# eval16 grading addendum — frozen before answer exposure

Frozen 2026-09-27 00:18:55 UTC by root instruction. Applies to the forthcoming masked paired comparison of 16 synthetic inputs / 32 essays. The evaluator has read the input topics, historical checklist and protocols, but **no current candidate answers, arm key, run outputs or candidate metrics**. Prior project experience is known; this is not a claim of never having seen the historical topics.

**Primary outcome: masked paired preference**, with basis `argument`, `facts`, `task_fulfillment`, or a stated combination, and margin `clear`, `close`, or `tie`. Report distinct verified factual errors and format compliance alongside it. Do not aggregate these heterogeneous synthetic branches into a CKE/15 score. More words alone do not establish better quality.

## Rules for this pass

1. Identify the chosen topic from the submitted body. Grade that actual task. Mixing competing topics is an explicit instruction failure: report it, analyze the content qualitatively, and set numerical total to `null`. Do not silently select a dominant essay or invent an automatic CKE-zero rule.
2. Score each **explicitly required aspect in the prompt** as absent0 / superficial1 / satisfactory3 / rich4. Cite the answer's actual evidence and causal connection. Checklist dimensions and illustrative events are evidence aids, not compulsory slots. In particular eval11 Topic1 has two required aspects, even though its checklist has three evidence dimensions.
3. Topic2 branches without a formal aspect list receive qualitative assessment of evidence, reasoning, and coverage of the chosen task; narrative total is `null`. Do not turn the checklist's varying one-to-five research dimensions into a numerical denominator. A concise supported causal argument can be satisfactory; names and dates alone are not developed argument.
4. List distinct **verified false claims** with correction and source. Repetitions count once. Apply the existing factual deduction once where a narrative subtotal is defined:1 for1–2 errors,2 for3–5,3 for more than5; floor narrative at0. Otherwise report error count and severity without manufacturing a narrative total. Omissions, vagueness, disputed interpretations and uncertain precision are not automatically factual errors.
5. Use the existing **coherence0–3** calibration:3 coherent,2 minor identified logical disturbance,1 substantial disturbance,0 disordered or under300 body words. This explicitly corrects Greg's protocol's0–2 wording; the original file remains unchanged as provenance. Factual errors or headings do not automatically reduce coherence.
6. Count actual body words, excluding topic labels/preamble; count whitespace-delimited tokens containing a letter/number, keeping abbreviations and hyphenated compounds together and excluding standalone punctuation. Report the official-calibration300 threshold separately from requested400–500 compliance. Cross-check supplied deterministic flags; do not add them as invented aspect penalties. Report truncation, metadata opening, lists and mixed-topic behavior separately.
7. Component sums are permitted only when the selected prompt defines the formal aspect denominator. Record that maximum explicitly: `4 × aspect_count + 3`, with factual deductions separate. Compare such totals only for the same chosen branch and requirements. Paired preference remains available when branches differ; assess complete chosen-task fulfillment, historically supported developed arguments and factual reliability rather than comparing incompatible totals.
8. Perform one fast masked pass. Freeze exact answer hashes and judgments before unblinding. A second pass occurs only if root determines uncertainty consequential for promotion, not automatically for every close pair. No promotion follows this essay panel alone.

## Exact input and protocol binding

- Canonical LF/Git-byte eval16 input SHA256: `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28`.
- Current Windows CRLF input raw-byte SHA256: `69b2b7caa15fa6b54d30aa71c9a3271f831caadb1e871140c0ebc9829f0ecf5f`.
- Canonical checklist SHA256: `27eb5cbe2b324039cfe61dded4563e84d0ec6f17c10325dc7d4bb015b14e8447`; Windows raw SHA256: `93c3a443dbdefcdec38045cbb0497dfdcf637b6692c688b0301310e768225a6b`.
- Original Greg protocol: `agentsLog/Bukareszt/lora_pilot/eval16/GRADING.md`; raw SHA256 `f94a902421d3929fa740e20732b0121c69958540568ebb76497819d7e38411c4`; LF-normalized SHA256 `01de73be827876ae5a6e8671cd0e35362203d33d62ba70a560f187d0463fc534`.

The unmodified checklist verifier fails its raw-byte assertion on this Windows checkout. Replacing CRLF with LF, and nothing else, reproduces the canonical input and every one of the eight manifest file hashes. All16 decoded prompt hashes and source-group bindings match; both alternatives exist for every input. This is an explicitly identified newline difference, not raw-byte equality or a semantic input change. No frozen source file was edited.

This addendum resolves scoring-contract ambiguity before exposure. It does not halt or alter the inference run, introduce training material, or authorize model calls. No grades have been assigned.
