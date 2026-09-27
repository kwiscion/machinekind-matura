# Full-page plus generic zoom diagnostic

The separately declared run completed eight of eight slots with verified local backup; see [terminal result](../2026-09-27-visual-zoom-result.md). Preparation instructions below do not authorize another run. Four deliberately selected known-validation source items (5.1,18,23.2,25), each with a full-page control and full-page-plus-tiles arm. Eight slots alternate arm order by item. Each original page remains present and byte-identical. Every page receives the same four crops: top-left, top-right, bottom-left, bottom-right, each55% of page width/height with10% central overlap, rounded outward using integer arithmetic. No resizing, source-specific boxes, answer hints, historical facts, keys or handpicked regions.

The zoom arm adds only a generic image-order/repeated-region clarification. Original question, source text, answer format and global instructions remain exact. Distinct slot IDs and the adapter's generated image list necessarily differ; total experiment points are the sum of the duplicated slots. Original source images/crops remain private.

`prepare_zoom.py` requires Pillow for CPU raster cropping. It prepares an ordinary organizer package, then invokes the unchanged shared `prepare_recovery_package.py`. No custom runner, guardian or model API was added. `test_zoom.py` checks full coverage/overlap, matched source/image preservation, alternating order, generic note only, fresh output refusal and canonical Gemma weight size.

```sh
python prepare_zoom.py --source PRIVATE_ORIGINAL_ORGANIZER_PACKAGE --output PRIVATE_FRESH_OUTPUT --runtime-reference PRIVATE_RUNTIME_MANIFEST
python PRIVATE_FRESH_OUTPUT/package-v1/run_recovery_package.py PRIVATE_FRESH_OUTPUT/package-v1
```

Frozen current preparation:4 original PNGs +16 tiles;24 image references across8 slots. Native Gemma, thinking on, context65,536, initial cap32,768, omitted temperature; shared recovery ladder maximum32calls/1,179,648requested tokens/60minutes. No injected faults or warmup. The first scored request performs actual runtime/context qualification. The canonical model/projector7,556,497,632bytes remains below the8,800,000,000aggregate limit; fresh cache includes only its exact metadata/blobs.

`preparation-manifest.json` records safe generic settings, slot mapping, question/source hashes and exact code/package pins. Detailed pixel boxes and all file hashes are in the private source-provenance and shared launch manifests. Prepared state is not execution authorization. Root must declare the fresh UTC deadline and budget before invoking the existing reviewed operator; no call is authorized by this document. All8slots remain in the result denominator, including failures. This selected panel cannot establish whole-exam improvement.
