# eval16: frozen masked fast pass

Only2/16 pairs have two complete essays; Y is clearly preferred in both. The other14 preferences concern operational usability only. Across32 outputs:18 complete,2 repetitive partials and12 placeholders. No aggregate model-quality or CKE/15 result is inferred from those14 operational comparisons.

Pack SHA256: `90211d5487fbb499bd64373a8f40f919d907eba6a9fa01a50ba5661ccb7dc7ff`. All16 prompts/groups match the canonical input and checklist; canonical input SHA256 `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28`. Eight checklist pins match after CRLF-to-LF normalization only. JSON records exact32 answer hashes, prompt hashes, statuses and judgment evidence. The PR166 addendum governs over older grading instructions.

Masking limitation: no sealed key, owner result report or unblinded answer files were opened. Before this pack, root had disclosed candidate repetition/length trouble and a short recovered first answer; I had audited training code. Completion patterns and prose style further weaken blinding. This is an X/Y-masked-label assessment, not a claim of reliable model blindness. No arm mapping is assigned.

Body counts exclude the opening choice/meta paragraph, title/copied task and separators, then count whitespace-delimited tokens containing a letter/number. All18 complete bodies are below400;17 reach300. In particular eval01X has296 body words, not the supplied324, so coherence is0 under the frozen rule. Supplied400+ flags for eval12Y,13Y and16X become387,378 and368. Headings are not independently penalized. All corrected counts appear below.

| Pair | X status / body words | Y status / body words | Preference | Scope |
|---|---|---|---|---|
| bk117-eval-01 | complete / 296 | complete / 357 | Y clear | content |
| bk117-eval-02 | partial / 18019 | complete / 333 | Y clear | operational_only |
| bk117-eval-03 | complete / 336 | complete / 323 | Y clear | content |
| bk117-eval-04 | complete / 368 | partial / 14803 | X clear | operational_only |
| bk117-eval-05 | placeholder / 0 | complete / 359 | Y clear | operational_only |
| bk117-eval-06 | placeholder / 0 | complete / 337 | Y clear | operational_only |
| bk117-eval-07 | placeholder / 0 | complete / 329 | Y clear | operational_only |
| bk117-eval-08 | complete / 361 | placeholder / 0 | X clear | operational_only |
| bk117-eval-09 | complete / 337 | placeholder / 0 | X clear | operational_only |
| bk117-eval-10 | complete / 361 | placeholder / 0 | X clear | operational_only |
| bk117-eval-11 | complete / 358 | placeholder / 0 | X clear | operational_only |
| bk117-eval-12 | placeholder / 0 | complete / 387 | Y clear | operational_only |
| bk117-eval-13 | placeholder / 0 | complete / 378 | Y clear | operational_only |
| bk117-eval-14 | placeholder / 0 | complete / 339 | Y clear | operational_only |
| bk117-eval-15 | complete / 359 | placeholder / 0 | X clear | operational_only |
| bk117-eval-16 | complete / 368 | placeholder / 0 | X clear | operational_only |

## Content judgments (two complete pairs only)

**eval01, topic1, Y clear over X: argument, facts and task fulfillment.** X political/military aspects1/1, two verified factual errors, deduction1, coherence0 from296 words: component total1/11. It asserts autonomy/Athenian power and new tactics but mostly repeats conclusions without developing them. Y aspects3/3, one verified error, deduction1, coherence3:8/11. It develops expansion/autonomy, the named victories and naval/land tactics, then Athenian ascendancy and interstate rivalry, although several formulations are imprecise.

The concrete corrections are that the Ionian revolt opposed Persian rule and received Athenian/Eretrian aid (X's reversed actors and Y's Persian-supported-rebellion trigger are wrong); the burned Sardis sanctuary named by Herodotus is Cybebe/Cybele, not Artemis (X). Spelling and compressed maritime/league phrasing are not counted as extra errors. [Herodotus5.97–103](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Herodotus/5D%2A.html).

**eval03, topic1, Y clear over X: argument and task fulfillment.** X religious/political/economic3/1/1, no verified fact deduction, coherence2:7/15. Spiritual remission supplies a concise motive, but the political paragraph alternates papal strengthening/weakening and royal gains/losses without explaining phases or mechanisms. The commercial conclusions repeat generic markets/profit/urban growth. Y aspects3/3/3, no verified fact deduction, coherence3:12/15. It connects redirected noble warfare, expedition costs and consolidation, and names commercial beneficiaries and luxury trade. Neither earns rich4: religious consequences remain thin and the modernity/capitalism/European-isolation claims overgeneralize. These interpretations are not converted into invented false-fact penalties. [Urban II's letter and Fulcher account](https://sourcebooks.web.fordham.edu/source/urban2-5vers.asp); [checklist's qualified trade/political context](https://www.metmuseum.org/essays/the-crusades-1095-1291).

The religious3-versus1 boundary in eval03X is judgment-sensitive; the clear paired preference survives it. These component totals use the actually required aspect count and are not summed across topics. Zero verified errors in this bounded pass does not certify factual perfection.

For eval02X and04Y, only the first900 and last500 characters were inspected: both show extreme repeated propositions and a cut-off ending. Content evaluation is explicitly incomplete; no invented numeric grade, exhaustive factual-error count or claim that the complete counterpart is historically sound. Remaining complete counterparts received only structural/body-count inspection. A later unmasking can map these frozen labels; it must keep the2-pair content denominator separate from the14 operational preferences. No promotion follows this panel alone.
