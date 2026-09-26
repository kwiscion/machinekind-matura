# Independent review of PR137 essay edit wave

**Accept the terminal artifact and two-rater arithmetic audit; do not promote the patcher or treat the owner aggregate as independently confirmed.** Historical grading covers the deterministic first six anonymous packet codes only. These are original DEV essays, not a full exam score.

PR head `1b6f36f4cf6f29b55463d9e9ae3d10b9042a3ac7`, merged revision `9c85215c93478feb4aa1a5fd4e434a1443b438c5`, confirmed through GitHub. Artifact bytes were read from the merged revision. All nine audited working files differ from Git bytes only in line endings. Answer-string hashes in the companion JSON use exact decoded UTF-8 strings.

## Independent grading

Owner aggregates were disclosed before this task, so this is independent but not fully blind. Codes E01–E06 were selected before the key or per-item grades were opened; topics were visible. First-pass historical/aspect judgments were frozen at **21:00:45 UTC**. After unblinding, a direct rubric check caught my own arithmetic error: factual errors had been subtracted individually. The official bands deduct one point for one or two errors, two for three to five, and three for more than five, from narrative only. Correcting arithmetic changes53 to57; the original freeze remains preserved. No historical judgment was changed to match another grader.

| Code | Unblinded slot | Aspects | Errors / deduction | Independent points [range] | Owner mean |
|---|---|---|---|---|---|
| E01 | January uprising, T draft | 3/3/3 | 0/0 |12 [10,12]|12|
| E02 | Casimir III, patched |3/3/3|1/1|11 [9,12]|11|
| E03 | Underground State, T draft |3/1/3|2/1|9 [7,11]|11|
| E04 | Stanisław August, N draft |3/3/1|1/1|9 [8,11]|9|
| E05 | Underground State, N draft |3/1/3|4/2|8 [6,10]|8|
| E06 | Stanisław August, T draft |3/3/1|3/2|8 [7,10]|9.5|

All receive3 coherence points; body word counts are435,421,430,387,398,410. No mechanical heading, repetition or malformed-word penalty was imposed. **Mixed subset57/90 [47,66]**; this denominator belongs only to these six slots. The two complete N/T pairs score17/30 versus17/30, delta0 with broad judgment range[-7,+7]. This deliberately small, unbalanced subset cannot confirm or refute the full six-topic owner gain.

The main disagreements concern what the argument actually proves:

- E03 correctly develops military and social mechanisms, but its claim that the underground apparatus protected sovereignty after1945 misstates the outcome. AK dissolution in January1945 also contradicts uninterrupted readiness to the war's end. These errors weaken the political effectiveness argument itself, separately from the factual deduction. The [IPN account](https://eng.ipn.gov.pl/en/news/4673%2CThe-Polish-Underground-State-1939-1945.html) documents dissolution and the failure to restore independence. A reviewer who credits the valid wartime administration explanation more heavily can reasonably give the political aspect3; this is the principal1-versus3 adjudication item. Uncorroborated organisation names were not counted as additional certain errors merely because a search failed.
- E05 has recognisable military/social explanation but mixes anachronistic or misclassified political organisations and claims a functioning successor bureaucracy after the war. [IPN's account of underground leadership](https://ipn.gov.pl/pl/dla-mediow/komunikaty/166741%2C77-rocznica-procesu-szesnastu-przywodcow-Polskiego-Panstwa-Podziemnego-uprowadzo.html) and its [NSZ/NZW chronology](https://ipn.gov.pl/pl/dla-mediow/komunikaty/180105%2C7-marca-1944-r-podpisana-zostala-umowa-o-scaleniu-Armii-Krajowej-i-Narodowych-Si.html) support the corrections. Four distinct first-pass errors produce a two-point deduction, not four.
- E06 explicitly attributes elimination of noble privileges to the constitution, although [articleII preserves them](https://libr.sejm.gov.pl/tek01/txt/kpol/1791-r2.html). Attributing creation of a standing army to that document and suppression of Jesuit privileges to KEN also compresses different acts and causal agents into incorrect claims. [The official education account](https://zpe.gov.pl/a/komisja-edukacji-narodowej-i-jezuici/DDgr07dwi) distinguishes papal suppression from the commission's later educational role. The latter formulations admit interpretation, reflected in the range; the privileged-estate claim is a clear contradiction. Both sound constitutional and educational mechanisms still earn3; the international argument remains generic1.
- E02's changed accession formulation is still wrong:1333, not1335. The [National Museum's dated Casimir record](https://zbiory.mnk.pl/en/highlights/catalog/55719) supplies the reign dates; monetary universalisation remains overstatement rather than another certain central error. The essay otherwise supplies satisfactory mechanisms. E04's invented eighteenth-century constitutional episode is a factual mistake; its educational explanation remains functional. E01's land reform, repression and cultural responses form satisfactory causal explanations, although sweeping claims of a sudden national transformation warrant caution.

Rubric reference: [CKE2024 marking guidance](https://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2023/Arkusze_egzaminacyjne/2024/Historia/MHIP-R0-100-2405-zasady.pdf), pp24–26, used only for evaluation. Item-level rationales and exact response hashes are in the JSON.

## Terminal and export audit

-18 ledger entries, unique sequence/key coverage;17successful calls and1verifier `done_reason=length` failure. All12drafts succeeded; the failed verifier returns the original T draft exactly. Thus18nonempty essay slots do not mean18successful generation stages.
- Reserved output budget270,336 tokens; actual recorded output/evaluation tokens106,332 and prompt tokens24,054. The declared ceiling was19calls/290,816; the frozen executable envelope used18calls/270,336, zero retries/smokes.
- Declared start20:09:00UTC, worker start20:09:13, batch20:09:57.697–20:28:07.506, deadline21:09:00. All recorded calls and completion precede the deadline. These are ledger timestamps, not a new remote process inspection.
- Gemma4 12B Q4_K_M digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, Ollama0.34.4, context32768, temperature omitted. T/verify caps20480; N cap4096. This compares the declared complete settings, not isolated thinking alone.
- All18packet texts equal their mapped exported answers exactly. There are13unique texts: one actually changed final, four zero-edit final identities, one exact draft fallback. The label `patched` includes zero edits and should be reported as valid verifier completion, not five successful repairs.
- The only two accepted edits occur in the Casimir essay. The accession edit replaces one wrong relation with another; it is not a supported repair. Changing treasury income categories because a retrieved excerpt mentions some revenue sources also does not establish that the original categories were false. The editing mechanism needs claim-to-source entailment, not a relevant-looking excerpt.

Git SHA256: answers `d23f2c95ad828171a47f51706377b30d2a6b28324a233c1415b51c2c4eae66b0`; packet `5c913846ca312968ec28c6ac022d037472207a0d953dc8b021957ea70e3cdb9a`; bundle `841697abd5632f7556bffa7920ac5c9eeaa35373cb9067a6065174c0e672417b` (matches frozen ledger/manifest); ledger `071e878790cec3239f647663e6ab90cfe5c929aea6515a996ea98731ffb146c3`. Companion JSON contains all audited file hashes and18answer bindings.

## Grader provenance and code

Both files contain18complete, distinct rubric records with passages, aspect levels, factual-error classifications and coherence reasons. Thus these are substantive rubric judgments, not merely duplicated totals. The records differ, but that alone does not prove independent sessions. The README claims two isolated Anthropic Claude Opus sessions; exact checkpoint, session identifiers, instruction hashes and independent dispatch records are not exported. Independence remains owner-attested. Zero automatic disputes means only that those two files pass the configured numeric rule; E03 exposes a material shared interpretation to adjudicate.

Re-running the rater-keyed aggregator in ignored scratch reproduces the entire published aggregate exactly: N46/90, T57.5/90, patched57.5/90. These remain owner ratings. The overwrite fix correctly preserves two ratings per slot; coverage and duplicate/dispute tests pass. Command: `python -X utf8 -m unittest test_essay_edit_run test_essay_edit_export test_essay_think_export -q` from `scripts/Pewciu6`: **56 tests passed**. All five launch-pinned source files match exact merged Git bytes; the tested working files match those bytes modulo line endings.

One concrete residual bug: `score_row_v2` floors after adding coherence. Synthetic aspects0/0/0, coherence3, deduction2 return1; narrative-floor-then-coherence should return3. It affects **zero of the36actual ratings**, so it does not change this wave's aggregate. Minimal repair is `max(0, sum(levels)-deduction)+coherence`, with a regression boundary test. No owner files were edited.

The README's missing validation-essay explanation must be scoped to the owner's particular input artifact. The shared complete May2024 source-v2 contains the essay at `val2024-hist-z26`; a local short-answer-only/missing source should not be described as evidence that the project has no essay. Deferring the diagnostic avoided fabrication, but the provenance description needs correction.

## Decision

Terminal evidence is sufficient to move to a separately declared original-DEV argument-construction comparison. Current patching adds one changed text, no demonstrated score gain, and an incorrect replacement; park promotion of this patcher. Use generic event–actor–date relation checking and evidence-to-conclusion checks, preserving uncertainty and abstention. Adjudicate E03's political aspect and E06's factual-error classifications before relying on the owner's precise mean gain. No inference, training, remote changes, Git mutations, or May2025 access occurred during this review.
