# Source-group crop prototype — 26 September 2026, 16:42

Three private, layout-only crop prototypes are ready for lead review; **no model calls or input promotion** occurred. They preserve complete source groups for numeric items **1, 6, 25**. The same rule was applied to all three, without keys, grades, historical interpretation, added OCR, or answer-derived selection of visual details.

The rule starts at the exact task heading and finds the following long bold instruction after the group's source image(s), before the answer area. It retains the union of all PDF objects in that source interval plus an 8-point margin. This includes text, raster panels, labels, arrows, callouts, citations, and surrounding boxes. It refuses boundary-crossing objects and multi-page inputs. These three cases each have one original page; cross-page handling was not exercised. **This is a review-gated prototype, not a universal automatic parser**: a bold caption can resemble an instruction, so unfamiliar layouts must retain the full-page fallback until reviewed.

Original PDF SHA-256: `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`. Crop PDFs preserve the original source objects; Poppler 26.07.0 rendered their crop boxes at **220 DPI directly from the PDF**, without enlarging the 110-DPI PNGs. All three were visually checked against the original full pages: both panels and the full source prose remain in item 1; all external callouts/arrows remain in item 6; the complete image and lettering remain in item 25. No source material was visibly clipped. The instruction text remains byte-identical in each input prompt.

| Item | Crop PNG | Expected backend image size | Expected visual tokens |
|---|---:|---:|---:|
| 1 | 1448×1373 | 816×768 | 272 |
| 6 | 1448×1250 | 864×720 | 270 |
| 25 | 1448×1146 | 864×672 | 252 |

Backend columns are CPU calculations using the [version-matched preprocessing finding](2026-09-26-vision-resolution-readiness.md), **not measured inference**. The full-page default was 672×912 / 266 tokens. Removing unrelated page area reallocates the roughly fixed pixel budget to the complete source group; the source figure's width would be about 1.5–1.6 times its full-page width in model pixels. This provides a plausible fidelity mechanism, not proof of a score gain. Original embedded raster images still limit available detail.

Private bundle: `agentsLog/kwiscion/private/source-group-crops-20260926/bundle/`.

- `manifest.json`: exact PDF-point crop coordinates, source/crop/fallback hashes, renderer, input-parent hashes. SHA-256 `0445ae26c7ca4b39669520faa3c429eed1c77d816aff968688e66477979a7d28`.
- `visual-review.json`: separate completed visual review of the frozen manifest; the manifest's initial pending status is superseded only by this review record.
- `source-v2.crops.jsonl`: three cases, SHA-256 `59f0d90e0d41255625b6b63530c5f728cdf880e361070f8f6c93cfd4685dc839`; parent `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`.
- `policy-frozen.crops.jsonl`: the same three IDs with completed-arm policy prompts unchanged, SHA-256 `a2245155c303e37e8fd4ad936e1b6f8bc4729da61dc57b2406bcdf5229818b81`; parent `3257dd89909ec1aeea1f85180244e962cc647e4f2b9d37cb24b1907cabfabb92`. This is the appropriate input if comparing against that policy arm.
- Each input has a matching `.full-pages.jsonl` comparator and original full-page PNGs under `pages/`; relative image paths resolve entirely within the private bundle. Only the `images` field differs between each crop row and its original parent. Crop PDFs/PNGs and builder remain private.

The lead may subsequently predeclare at most three diagnostic calls, unchanged model/settings and 1024 output tokens each: at most **3072 requested output tokens**, no retries or warmup, with a hard deadline that accounts for up to **21 minutes** at the existing 420-second request timeout. The proposed files themselves authorize no inference. They are pinned proposals, not replacements for the active or preserved validation inputs, and three results cannot establish a full 60-point score.
