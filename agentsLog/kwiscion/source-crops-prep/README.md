# May 2024 source-region input correction

**CPU and visual QA PASS; no inference or score claim.** This prepares the known May 2024 VALIDATION exam in the organizer's separate-text-and-cropped-illustrations style. It is not the four-tile zoom experiment. The organizer's May 2023 mock has 37 items; this package correctly retains all **40 May 2024 items / 60 points**.

The new private package is `agentsLog/kwiscion/private/may2024-source-crops-v1/package-v1/`. Original files, previous runs and live packages are preserved. The original `exam_id` is intentionally unchanged, along with every other non-image field and the exact answer-template bytes; the version is identified by the directory and provenance manifest.

## Result and checks

- 21 lossless source-region PNGs, 32 image references across the same 30 image-bearing items; 10 text-only items remain text-only. Original full-page inputs had 43 references to 21 pages.
- Visually inspected all 21 original pages and every extracted region on four private contact sheets. No unresolved boundary ambiguities. The full family tree, map legends, external callouts/arrows, translations, panel letters and captions are retained. All multi-panel sources remain complete. Task 23 retains both its poster and table as separate images for both subitems.
- Source groups spanning pages retain the associated illustration and unchanged text transcription. The inspected package contains no visual diagram itself divided across page images. Removed image links point to text-only continuations or unrelated adjacent tasks; they are documented in the complete old/new mapping. Related subitems share complete sources, even when one subitem could be answered from text alone.
- Every PNG is the exact parent-pixel rectangle in the spec: no resize, redraw, recoloring, interpolation or generative editing. Only the private QA contact sheets use thumbnail scaling; they are never input images.
- The actual `scripts/Bukareszt/matura_package.py` adapter validates the package and prepares all 40 inputs. Each non-image field is exactly equal; adapter prompts are identical after excluding the generated image list. The template is byte-identical.
- A second fresh build produced byte-identical `exam.json`, template and all 21 PNGs: **23/23 reproduction checks PASS**. Pixel equality and bounds checks pass on all crops. Source-file hashes remain unchanged.

## Reproduce

Requires Python 3 with Pillow; no new installation was needed. The existing bundled Windows interpreter used here is `C:/Users/kwisc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Use that interpreter if the project `.venv` or `uv` environment lacks Pillow.

```powershell
& C:/Users/kwisc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -B -X utf8 agentsLog/kwiscion/source-crops-prep/build_source_crops.py --source agentsLog/kwiscion/private/champion-rehearsal-20260927/recovered-v2/package-v2/exam --output agentsLog/kwiscion/private/may2024-source-crops-v1/new-reproduction
```

The destination must be fresh and private. The builder pins the original exam/template/pages and refuses changes. It produces the package, adapter input, provenance manifest and private QA contact sheets. A new build intentionally starts at `CPU_BUILT_VISUAL_QA_PENDING`; the published manifest records the completed visual review of the exact delivered pixels. It does not automatically certify a future review.

| Artifact | SHA-256 |
|---|---|
| Original exam | `907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471` |
| New exam | `e93b7488da7dfcf4044c906af9b28c1275a1b295838455ec3d88dcc2344aaac6` |
| Unchanged answer template | `aa4451a853063e3f67d1b9d281ac063ee48c112e01c3cb8712ded433253b865f` |
| Prepared adapter input | `ffb4be546dd9726f8603372f99cfb90428262516abca03cf0b4d29d20c9e3503` |
| Reviewed crop manifest | `6af937748b4e9bc169f4df9f257e42f9e95a00639c11029b07caba96bfc454f3` |
| Crop spec | `92025640327a7c91e55a7c98623a683c59e634580fb72f1b42af848ca640790e` |
| Builder | `ece0ba27b12e83b36825443f9e0debde724f2f362c77766dd94d194ad603d3a8` |

The 21 model-input PNGs total 8,124,416 bytes. The whole private directory including adapter text, manifest and QA sheets is 14,969,638 bytes. These are input artifacts, not model weights.

Root independently reviewed all four contact sheets / 21 source units and reran pixel equality for every crop, exact non-image-field equality for all 40 items, file hashes for all 32 image references, and template byte identity: **PASS**. This independent review did not change the frozen builder, spec, manifest or package.

## Publication and limits

Publish only this README, `build_source_crops.py`, `crop-spec-v1.json`, and `crop-manifest-v1.json`. The manifest contains coordinates, hashes, item/source links and QA notes, not exam passages or image payloads. All exam JSON, transcriptions, templates, PNGs, contact sheets and reproduction outputs remain private under existing evaluation rights; publication permission for our code does not grant redistribution rights to exam sources.

Selection used source associations and source boundaries only, with no keys, rubrics or current model answers. No GPU, service, remote host or Git operations were performed. This changes model inputs; previous full-page scores are not an identical-input comparison. Root must freeze and separately declare any subsequent inference.
