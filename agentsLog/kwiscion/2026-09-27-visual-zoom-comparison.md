# Visual zoom: exact frozen-grade comparison

**Control1/6 [1,2]; zoom1/6 [1,2]. Central difference0.** The bracketed values are scoring interpretation ranges, not confidence intervals.

| Item | Full-page control | Full page + generic tiles |
|---|---:|---:|
| 5.1 | 0/1 | 0/1 |
| 18 | 0/1 | 0/1 |
| 23.2 | 1/1 | 1/1 |
| 25 | 0/3 | 0/3 |

- Added generic tiles show no score benefit on this four-item panel. No candidate promotion follows; this is not evidence that all crop strategies fail.
- Item23.2 is correct in both arms. Its improvement over an earlier answer cannot be attributed to added tiles.
- Zoom consumed more prompt and generated tokens without a central score gain. Cold loading was unbalanced, so these data do not establish a fair arm wall-time comparison.
- Remaining failures mix visual identification, source linkage and historical interpretation. The outputs do not isolate OCR as the cause.

| Arm | Prompt tokens | Generated tokens | Load seconds | Generation-eval seconds |
|---|---:|---:|---:|---:|
| control | 4,595 | 9,349 | 54.318 | 98.701 |
| zoom | 7,871 | 14,754 | 0.095 | 142.222 |

All8 calls produced finals, with0 errors/retries/placeholders. Whole operator wall371.452s; total12,466prompt +24,103generated tokens. The first control request bore54.292s cold load. Generation-eval time excludes load and prompt processing; per-arm complete wall times are not available in this summary.

This report only joins the previously frozen masked scores to the now-authorized arm key. Every answer string matches both public exports and the masked packet, and every UTF-8 answer hash matches the frozen grade. No score changed; no model calls or new grading were performed.

Frozen masked-grade SHA256: `c437b1c006a87a6919c15748601793d8247a9ec4f8c749be861c4ceb19d32b3f`. Public answer-only SHA256: `04d24f7ee234dc5394a27b1b782c029f322d82ed605a93866b3feb9a99ca18a6`. Public organizer-shaped answers SHA256: `61a778855fb462ff15336b847a6141cca53d6f3c57ea3adb405f2016b3ba50e4`. Complete provenance, per-answer hashes and metrics are in the adjacent JSON.
