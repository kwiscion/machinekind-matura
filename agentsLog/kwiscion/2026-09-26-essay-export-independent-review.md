# Independent essay export integration audit

**The root-only 24-row subset is ready for a bounded data pilot.** It contains 12 independently reviewed original essays and 12 repair pairs, with 12 unique targets. The full 90-row export passes structural and review-binding checks; its four historical source corrections still await the separately assigned authoritative check. This is data integration acceptance, not a training/runtime result.

## Executed checks

All 15 audit assertions and 6 focused existing unit tests pass. The initial test invocation used the wrong import directory; rerunning from `scripts/Bukareszt` passed. Tests that rewrite another owner's group reports were excluded; equivalent graph checks ran independently without those writes.

- 90 unique rows:34 essays and56 repairs;16 unique evaluation inputs.
- Root24: every original prompt and response matches its accepted independent-review hash and the exact exported chat content. No blanket or newly manufactured accept verdicts.
- Greg66:22 target essays match an independent accept verdict, exact essay SHA and original constructed prompt. All44 repairs reproduce the declared deterministic defect, fail the clean-output contract, and target the unchanged accepted essay. Flagged off-topic paragraphs are not exported as negative defects.
- Both withdrawn duplicate-topic essays are absent. Every training target passes the existing structural contract; all IDs have attribution.
- Independent union-find:30 source groups form28 training components;16 evaluation components share none. Augsburg–Vienna and League–Marshall dependencies are preserved, including content present only in malformed input.
- LF-normalized train SHA matches `83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5`. Windows disk-byte SHA is `c5bd1b58678eeec3745437d9ea866130e9276471af34aff8ff3e559fee20fb57`; the difference is line endings, not JSON content.

## Exact root-only handoff

Ignored folder: `agentsLog/kwiscion/private/essay-export-audit/`.

| File | SHA256 |
|---|---|
| root24-train.jsonl | `768f419504c26028482951d80abddeb889b46e8066276fdd4c8a497fdd2ed5b3` |
| root24-attribution.jsonl | `48229c5691976df821c593754c176bf57ba188f963371c3427391281f4caf735` |
| eval16-input.jsonl | `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28` |

`root24-manifest.json` lists all24 record IDs, accepted prompt/response SHA bindings and evaluation exclusions. Training rows are selected unchanged from export_v1, preserving original line order and LF bytes. `checks.json` retains all90 bindings and the executable audit results. Audit commands are reproducible with `outputs/audit-essay-export.py` and `outputs/scan-root24-reference-text.py` using the bundled Python runtime.

## Rights and reference-only material

Three nonredistributable crosscheck references appear in attribution: [MIT Aristotle](https://classics.mit.edu/Aristotle/athenian_const.1.1.html), [UJ archive](https://archiwum.uj.edu.pl/historia-auj), and [AGAD Lublin](https://agad.gov.pl/Unia%20Lubelska/uni_lub.html). They are references, not copied source payloads. Exported root prompts/responses are unchanged from the independently reviewed original compositions, and no quote/factcard/source-text fields were inserted. An additional normalized20-word scan found zero shared passages against all three snapshots, including alternative Polish HTML encodings. This check does not certify absence of every shorter phrase.

A concrete metadata omission exists: canonical attribution keeps the restrictive license description but omits `allowed_use`. The derived root-only attribution restores `reference_fact_check_only` and records `source_text_exported: false`. Source and teacher files were not modified. This metadata repair does not grant a new license or authorize source redistribution.

## Evaluation and remaining work

Root groups CasimirIII, LublinUnion and JanuaryUprising overlap #80DEV. Do not present those existing topics as a clean posttraining test. The16 separate inputs are suitable for external historical-quality evaluation; missing gold essay targets is expected, so no `eval_loss` is required. Existing factcard caveats remain relevant for graders.

The title-key comparison is a narrow check, not exhaustive exclusion of benchmark question paraphrases or source-derived examples. Root24 provenance records original independently selected topics and prior independent content review; this audit supports that bounded subset without claiming benchmark novelty or sealed-test clearance. May2025 remained sealed.

For the full 90, finish the assigned authoritative checks of the four corrected historical claims; no additional structural defect was reproduced here. Do not count56 repair rows as56 new unique essay targets. No inference, training, GPU, Git mutation, source redistribution or other-owner file edits occurred.
