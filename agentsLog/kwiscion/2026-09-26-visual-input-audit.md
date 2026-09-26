# Source-v2 visual input audit

26 September 2026. **No additional missing required image, panel, legend or cross-page source was found across all30 image-labelled v2 cases.** The previously demonstrated z13 omission is repaired. This is a source-presence audit, not proof of model perception, fine-detail readability or answer correctness. No keys, marking guides or May2025 material were opened; no inference occurred and no frozen inputs changed.

## Scope and method

Reviewed every one of the21 distinct model-facing PNGs visually at its native910×1287 resolution, then checked each of the30 image-case lists against the source pack and task boundaries visible on those pages. There are43 image references;13 cases receive two pages. Page numbers below are one-based PDF/printed page numbers, not zero-based indices.

Pinned question PDF: `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`. Source-v2 input: `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`. Existing bootstrap renders full pages at110 DPI. Independent CPU-only rerender verification is recorded privately in `agentsLog/kwiscion/private/visual-input-audit-20260926/render-verification.json`; reproduction script is `agentsLog/kwiscion/private/verify_visual_pages.py`. No official page images are included in this public report.

Independent rerender result: **all21 pages are byte-identical to the frozen model-facing PNGs**. No clipping or substituted-page discrepancy was detected.

The parser unions each subtask's pages with its shared preamble pages. This correctly retains cross-page sources here, but also includes neighboring tasks whenever they share a full page. Source-v2 has one explicit image-list repair; the underlying lexical modality heuristic remains unable to guarantee completeness on a different paper.

## All image cases

| Item suffix(es) | Attached pages | Visual/source-presence finding |
| --- | --- | --- |
|1|4|Both labelled relief panels and accompanying prose present.|
|2|5|Full map, complete external colour legend, prose and question present.|
|4|7|Full architecture photograph, caption and task present.|
|5.1|8|Shared prose and full routes map, including projecting legend, present.|
|5.2|8,9|Same map retained from preceding page; own task on9 present.|
|6|9|Whole woodcut and all three external translated callouts present.|
|8.1,8.2|10,11|Prose begins at bottom10; illustration, all letter labels and legend plus tasks on11 retained.|
|9|12|Whole woodcut, translated inscription and task present.|
|10|13|Chart, fractions, brackets and explanation retained.|
|11.1,11.2|13,14|Both prose fragments on13; entire genealogy, symbol legend and tasks on14 retained.|
|12.1,12.2,12.3|14,15|Shared prose on14; full monument photo and three subtasks on15 present.|
|13|16|Engraving and external date callout now attached by v2.|
|14.1,14.2|16,17|Prose at bottom16; complete map, projecting arrow legend and both tasks on17.|
|16.1,16.2|19,20|Cartoon with all external translated labels and prose on19; second question/options on20.|
|17.1|20|Both prose and complete drawing with translated callout present.|
|17.2|20,21|Shared sources on20; own short task on21 present.|
|18|21|Whole poster, including lower foreground figures, and task present.|
|19.1,19.2|22|All four A–D stamp panels, translation notes, numbered statement table and second task present.|
|21|24|Complete film still and task present.|
|23.1,23.2|26|Poster, full numerical table with row/column headings, and both subtasks present.|
|24|27|Map with all colour categories, prose and task present.|
|25|28|Full cartoon, including left lettering, window and foreground elements, present.|

## Concrete remaining risks

**Neighboring assignments are genuinely visible.** Examples: z5.2 also sees z6 on page9; z8 sees z7 on page10; z11 sees z10/page13 and the start of z12/page14; z12 sees z11/page14; z13 sees the start of z14/page16; z16 sees z17/page20; z17.2 sees z18/page21; z21 sees z22/page24. Multiple subtasks also share one page. This is additional material, not an omitted source. It provides a plausible mechanism for answering neighboring questions, but this audit did not read/model-score outputs and establishes no causal score effect.

**Full-page resolution dilutes small details.** Dense labels on pages5/8/17, small letter markers on11, stamp inscriptions on22 and the genealogy on14 remain present, but their pixel area is limited at110 DPI. Inscriptions near native raster quality cannot be repaired merely by enlarging the existing PNG. Model-specific resize/tiling behavior was not inspected here. Do not claim a resolution intervention improves recognition without a separate test.

**Image-object-only extraction or a tight photograph crop is unsafe.** It would exclude external legends/callouts on pages5,8,9,11,14,16,17,19,20 or22. The translated date on16, political-cartoon labels on19 and symbol legend on14 are particularly clear examples. Cross-page prose must also remain available for items8,11,12 and14. The source itself may intentionally be an excerpt; that is not an input omission introduced by this pipeline.

## Reproducible improvement proposal — not applied

No universal automatic crop was demonstrated safe enough to replace this complete full-page fallback, so no crop prototype was promoted or attached to an active input. A future declared preprocessing experiment should use a general layout rule: identify each complete task-group source region from the question PDF, include all labelled source panels plus legends, translation callouts and attribution, and retain every cross-page region associated with that group. Suppress only independently verified neighboring task regions and response whitespace. Keep unchanged original question text and full-page assets as audit evidence.

Implement a private manifest of PDF hash, page, point-coordinate bounding boxes, rendering DPI, output hashes and per-case ordered region IDs. Derive regions from question layout alone; never from answers, grading or historical interpretation. Render from the original PDF at a declared resolution rather than upscaling low-resolution PNGs. Review at least a multi-panel source, an external-callout source and a cross-page source before applying one frozen rule to all cases. Check preservation of every label/panel/legend and actual multimodal context cost. Retaining full-page images alongside crops may double context, so that choice requires an explicit budget rather than automatic addition.

For now, prioritize the active question-compliant policy's measured outcome. This audit finds no new source-completeness repair to justify interrupting it or replacing v2. No score gain, new candidate or model call is authorized by this report.
