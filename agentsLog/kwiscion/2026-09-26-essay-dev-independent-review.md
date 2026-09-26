# Independent review of four DEV essays — 26 September 2026

**Result: no demonstrated advantage for plan→write. Both modes contain major factual errors in both topics.** They produce complete, organized essays, but their political arguments rely on misattributed or invented events. Keep single-pass as the cheaper comparator; test a mechanism that checks historical claims before expanding them. This is an independent Sol diagnostic on two original DEV topics, four outputs, not an official essay grade or a full-exam /60 score.

## Provenance and scope

Reviewed PR109 head `f887d4d2d926140352842adec7daf08f05a258ae`, merged as `f3d548533611af970f4e0727c89a83aec61d332c`. The input and result paths are identical between head and merge. Isolated snapshot: `outputs/pr109-review-f887d4d`. Run: `pilot-h100-20260926T171456Z`; two unique IDs per arm, all four answers nonempty with null errors. Final topic is 1 in every answer. The declared single final cap is 1536 tokens; plan→write uses an additional 512-token plan and the same final cap. Six calls/7168 requested tokens are reported. No generation, remote-host operation, training write, or fixed-exam material was used for this review.

The exact LF file hashes match the published run summary:

| Artifact | SHA-256 |
|---|---|
| `answers.single.jsonl` | `eddbb522126ca4a6b74e9e32cf4764e821f2543d2537a1a9f00aceb859d6b93c` |
| `answers.write.jsonl` | `8a86b6d5e01024e7c5af7d853d63eabdb21cc7dbda036405544da1fd93b1c7e8` |
| `dev_fixtures.jsonl` | `fa546faf595b00dd13d70ea700ed8f70ade12227261313b3f24bb09866bbbf71` |

Windows archive extraction produced CRLF file endings, so raw disk hashes differ; replacing CRLF with LF restores all three declared hashes. Answer strings were not edited. Plans are not in the public handoff: final-answer grading cannot establish whether a false claim originated in planning or writing. Mirrored usage fields noted by the author also prevent a reliable actual-token efficiency comparison.

## Common diagnostic rubric

The same reviewer-defined 20-point rubric is applied to all four outputs. It is not the official matura rubric and must not be converted into exam points. Intervals are judgment ranges, not statistical confidence intervals.

- **Facts, 0–8:** relevant, accurate events, actors, institutions and consequences. 0–2: central examples are false or very thin; 3–4: some sound knowledge but a major argument rests on errors; 5–6: mostly sound and specific; 7–8: consistently precise, broad support. An unsupported plausible claim is distinguished from a confirmed error.
- **Argument, 0–6:** thesis and supported causal/evaluative reasoning across the required aspects. 1–2: formulaic assertion with little valid support; 3–4: some defensible causal chains but incomplete evaluation; 5–6: sustained, specific and balanced reasoning. Repeating that an example proves the thesis earns no additional credit. A false premise cannot support a causal inference.
- **Chronology/context, 0–4:** 0: a central argument falls outside the reign/period or confuses its sequence; 1–2: substantial chronological/contextual weakness despite some correct anchors; 3–4: mostly/consistently controlled chronology and context. Dates alone are assessed here; the facts column assesses the substantive actor/event error, rather than separately deducting twice for a mistyped year.
- **Organization/compliance, 0–2:** readable thesis, connected development and conclusion; required topic/aspects and minimum length. Headings and named entities alone carry no content credit.

| ID / mode | Body words | Facts /8 | Argument /6 | Chronology /4 | Organization /2 | Total /20 [range] |
|---|---:|---:|---:|---:|---:|---:|
| dev-essay-001 / single | 381 | 2 | 2 | 0 | 2 | **6 [5,8]** |
| dev-essay-001 / plan→write | 360 | 3 | 2 | 0 | 2 | **7 [6,9]** |
| dev-essay-002 / single | 380 | 4 | 3 | 2 | 2 | **11 [9,12]** |
| dev-essay-002 / plan→write | 336 | 4 | 3 | 1 | 2 | **10 [8,12]** |

Mode totals: **single 17/40 [14,20]; plan→write 17/40 [14,21]**. Paired differences are +1 and −1, far below the uncertainty of this small, unreplicated comparison. All word counts were recomputed from the exact text with `essay_report.count_words`; whitespace totals including labels are 397, 381, 396 and 355 respectively in table order. All clearly exceed the original DEV prompts' 300-word requirement.

## Item findings

### dev-essay-001 / single — Kazimierz III Wielki

The cultural example of the university foundation in 1364 is correct and relevant. Connecting education of administrators to state capacity is a useful argument, although the essay overstates uninterrupted long-term institutional stability: the university's activity ceased after the king's death and it was refounded in 1400. [UJ institutional history](https://cac.historia.uj.edu.pl/uniwersytet).

The political centerpiece credits Kazimierz with the 1385 Polish-Lithuanian union. This is outside the stated 1333–1370 reign and belongs to Jagiełło/Jadwiga, invalidating the paragraph's key example. The malformed name of the union is secondary to this substantive misattribution. [Document-based ZPE account of Krewo](https://zpe.gov.pl/a/przeczytaj/DH4iIDZpt).

The cathedral's 1364 date is its consecration, not the start of construction as claimed; the castle-start date is also unsupported. Fortification activity is broadly relevant but the invented precision weakens it. [Kraków's institutional history of Wawel](https://www.krakow.pl/1460%2Cartykul%2Chistoria-zamku.html).

The 1368 statute is not wholly invented: a salt-mining ordinance really existed. The essay does not identify the salt industry and generalizes it into commercial law, so this receives only partial factual credit. [Wieliczka operator's historical account](https://www.kopalniawieliczka.eu/gornicze-dziedzictwo/). The precise 1360 coin claim is **uncertain rather than a separately confirmed error**: the MNK catalogue title dates its object approximately to 1360 while its description associates minting with 1367–1370 and limited circulation. Neither supports the essay's confident claim of a fully unified currency nationwide. [MNK coin record](https://zbiory.mnk.pl/en/highlights/catalog/55719).

Argument quality: the positive assessment is clear, but repeated modernization claims largely substitute for evaluation. The essay conflates strengthening an inherited kingdom with creating unity from a fragmented duchy. It does not weigh constraints or distinguish benefits actually established by its examples.

### dev-essay-001 / plan→write

The university foundation remains correct, and the culture paragraph is cleaner than single-pass. The economic paragraph has a plausible trade/security mechanism, but a nationwide road-building program and complete monetary uniformity are asserted without concrete support.

The political paragraph replaces one major hallucination with another: Płowce occurred in **1331 under Władysław Łokietek**, before Kazimierz's reign, not as the king's victory in 1332. The result also cannot simply be treated as stable eastern borders. [Battle-site institutional account](https://szlakpiastowski.pl/obiekty/plowce/plowce-pole-bitwy-pod-plowcami). Recovery of Warmia in the 1330s is wrong. If the malformed second territory means Dobrzyń, its recovery with Kujawy belongs to the **1343 Kalisz settlement**, not the asserted decade. [ZPE account of Dobrzyń](https://zpe.gov.pl/a/z-dziejow-ziemi-dobrzynskiej-w-sredniowieczu/DBG3CzrKa).

Calling the reign a foundation of later modern history can be defensible as retrospective framing; I do not count that wording alone as an error. The damaging failures are the specific military/territorial evidence and the unsupported causal conclusion built on it. The extra planning call has not secured the political facts.

### dev-essay-002 / single — Swedish Deluge

The overall negative assessment, plunder → weakened production/trade, and population loss → reduced labor/tax capacity are defensible. The essay correctly places the war's opening in 1655 and Oliwa in 1660. These provide real, though general, support for the economic and social arguments. [ZPE account of the Deluge and its consequences](https://zpe.gov.pl/a/potop-szwedzki/D195SQOlB).

The Ujście capitulation was not signed by Jan Kazimierz. The museum's published historical account and capitulation text identify the Wielkopolska representatives, including Krzysztof Opaliński. This changes the actor and political meaning of the event. [Wilanów, Gordon's account and capitulation](https://wilanow-palac.pl/pasaz-wiedzy/pierwsze-starcie-patrick-gordon-i-bitwa-pod-ujsciem).

The alleged coastal confederation is unsupported. If the intended reference is Tyszowce, that confederation formed on **29 December 1655**, not in consequence of a 1657 capture of Warsaw. [Wilanów biography of Grzymułtowski](https://wilanow-palac.pl/pasaz-wiedzy/grzymultowski-krzysztof-1620-1687). I do **not** mark the mere mention of Warsaw being occupied in 1657 false: a further Swedish/Transylvanian capture did occur; the false causal link is the issue. [Public institutional campaign chronology](https://www.leczycki.pl/asp/historia-samorzadu%2C296).

Near-total destruction and a specifically dated 1658 annihilation of the craft-production system are overstatements without a locality or evidence. The essay identifies consequences but overattributes the wider mid-century crisis to one invasion and offers no concrete territorial settlement. Nonetheless, the economic/social causal chains are more defensible than its political paragraph.

### dev-essay-002 / plan→write

The political centerpiece is decisively false: the Grzymułtowski peace was made with Russia in **1686**, not 1658, and the asserted Royal-Prussian terms are not its settlement. The museum history discusses the eastern territorial settlement and Sobieski's diplomacy. [Wilanów analysis of the 1686 agreement](https://wilanow-palac.pl/pasaz-wiedzy/rzeczpospolita-i-rosja-1685-1686).

An alleged grant of greater privileges to magnates is unspecified and cannot establish the claimed institutional mechanism. The economic account is broadly sound and less cluttered by spurious exact dates than single-pass; the labor-loss/production link earns argument credit. The social account adds a plausible intolerance theme, but identifies neither a group nor a concrete decision, and the broad isolation/modernization conclusion remains insufficiently demonstrated. No deduction is made merely because a correct illustrative event was omitted; the limitation is thin support for the claims actually made.

This output exchanges single-pass's Ujście/confederation errors for an even clearer treaty/period conflation. It does not establish a beneficial planning effect.

## Source dependence, uncertainty and next experiment

These prompts request historical knowledge and contain no source passages. Their `source_ids` are premise-check metadata, not evidence that a reference text was supplied to the solver. I do not penalize missing citations that the task did not request, claim source-grounding ability from these essays, or infer corpus copying/pretraining provenance. The source links above are the reviewer's evaluation evidence only; they must not turn these fixed DEV outputs into training examples. No official exam rubric or source pack was consulted.

Confidence is high in the core union, battle, capitulation and treaty corrections; lower in broad social/economic generalizations and the exact coin chronology. An expert could reasonably move the numerical scores within the stated ranges, but none of these uncertainties rescues the incorrect political centerpiece in any essay.

The useful next mechanism is an **actor–event–date–consequence check before prose expansion**, optionally grounded in independently licensed general references or followed by a focused critic. Keep the topics and final budget fixed for its first comparison, add the required third independent era/topic, and measure whether false central claims actually disappear. Do not reward a higher date/name count, more labels, or longer text. A plan made by the same ungrounded model is not a fact check. Any supplied evidence experiment is a separate mechanism from the current closed-book comparison.

Correct the PR109 README's broad baseline-underlength claim: root's latest issue80 clarification says the newly reviewed H100 bare essay had 338 body words and still scored poorly. The four DEV essays establish adequate length and organization, not recovery of that content failure. At the final issue80 check (latest comment 17:25:54 UTC), no public completed known-validation essay handoff was present. Review it separately when delivered; do not combine its score with these /20 DEV diagnostics.
