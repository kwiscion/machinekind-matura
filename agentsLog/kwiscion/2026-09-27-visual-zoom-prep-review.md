# Visual zoom preparation: independent CPU/payload review

**PASS, no material blocker.** Scope is the prepared four-item mechanism test, not a quality result or execution authorization. No GPU, Brev, Git mutation, new source acquisition or model call was used.

| Artifact | Exact SHA256 |
|---|---|
| prepared-v2/package-v1/launch.json | d14ef2394d2511e87708e0e4b7f1c3680f225b11131939afd93bf973f9a3a96d |
| visual-zoom-prep/prepare_zoom.py | 3c2b68227c085086c53b7e9c07a2a4ac6ebf5f321d65b6de047aae1a137d4999 |
| visual-zoom-prep/test_zoom.py | b34293d57f5c403d8adef10706da376c6c11c1fd2a69f0248a60c7e7e431fc6c |
| visual-zoom-prep/preparation-manifest.json | 9e04a477c32344f5e06eb33babde721a8af35b9f9906a941d0c7593ba293af6c |
| embedded recovery_harness.py | d99d9271d6cc589f0e9caccfee3d1387c4695d0fd9cd33db97bcd3efba54a521 |
| original source exam.json | 907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471 |

Compared actual prepared payloads against the preserved original organizer exam in the prior champion package. All original item fields, including complete question, source text, answer format and points, remain exact; global instructions remain exact. Only arm IDs/image additions/generic layout note and paired exam metadata differ. The eight slots alternate arm order by item:5.1 control/zoom,18 zoom/control,23.2 control/zoom,25 zoom/control. There are four distinct original pages and sixteen generic tiles.

Every control contains its byte-identical complete original image. Each zoom case contains that same original first, followed by all four corresponding tiles in TL/TR/BL/BR order. Independently compared every tile's mode, dimensions and decoded pixel bytes with the specified crop of its original page; all16 match. The55%-dimension crops overlap centrally and cover the whole page, with no resampling. Every image/code/input file pin in the prepared launch manifest matches. A visual contact sheet was unnecessary for this exact byte/pixel mapping check; no historical image interpretation or grading was performed.

The generic Polish note correctly describes full originals first, then four views per page, warns against treating overlap as extra evidence, and introduces no key, grading hint or historical assertion. The actual package adapter preserves that note in model-facing metadata; dry preflight validates the exact generated input mapping. Complete original pages remain available in the same request. This tests additional image views rather than a new-resolution source scan.

Budget/configuration:8slots times4attempts =32calls;8 times(32768+49152+32768+32768) =1179648 requested-token ceiling;60-minute operation,420-second request ceiling,65536context, omitted temperature, no injected faults, no essay route. The prepared declaration/deadline/authorization remain null. Embedded scheduler is the reviewed d99d9271 version; cleanup and runtime file pins pass unchanged package preflight. Canonical Gemma model plus projector is7556497632bytes, below the aggregate8800000000byte cap; no additional weight set is introduced. This is a pin/accounting check, not a new remote-cache inspection.

Independent checks: `test_zoom.py` **3/3 PASS** in0.123seconds; packaged `run_recovery_package.py PACKAGE` default dry check **PASS**,32calls/1179648tokens/model_calls0; all original fields, original image bytes,16tile pixel comparisons and complete launch-file hashes **PASS**. No source text or exam images are copied into this public report. The original prepared/frozen packages were read only. A fresh declaration remains the execution owner's responsibility; selected-panel results cannot establish whole-exam improvement.
