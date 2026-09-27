# Autonomous route detection preparation

Status: CPU preparation only. `classify_item.py` is a small deterministic metadata utility, not an enabled runtime route or a quality claim. It introduces no prompt, model call, budget, network access, file I/O, topic choice or answer inference. All existing packages and preparers remain unchanged.

```python
from classify_item import classify_item
decision = classify_item(received_exam_item)  # raw organizer item, not merged prompt
# {route: essay|closed|open|unknown, visual: bool, reason: fixed label,
#  baseline_fallback: bool, explicit_override: bool, revision: ...}
```

The real organizer adapter validates separate string `question` and `answer_format` fields, with an image list. It merges `source_text` into the prompt only later in `build_prompt`. Classification must happen before that merge. The utility reads exactly those two instruction fields and image-list presence; it never reads IDs, points, source text, global instructions, keys or answers. It does not inspect image pixels. Returned reasons are fixed rule labels, not copied task text. Inputs remain untouched.

Detection is deliberately conservative. Explicit essay-writing directives or essay answer formats identify an essay; the older essay keyword plus topic/length structural principle remains supported. Closed detection requires finite-choice answer instructions, actual lettered options plus a selection directive, or explicit true/false instructions. Constructed-response instructions identify open items. Missing, conflicting or unsupported instructions return `unknown`, which requires unchanged baseline behavior. The visual flag is orthogonal: an essay/open/closed item can also have images. It does not enable zoom or claim the image is relevant. These are heuristic instruction rules, not a universal language parser; explicit overrides resolve unsupported phrasing.

## Existing implementation and minimal future integration

`agentsLog/kwiscion/prepare_question_policy.py` only prepends the historical fixed40 generic policy. It has no classifier and is neither imported nor re-enabled here. `scripts/Pewciu6/essay_route.py::detect_essay` provides the useful structural idea, but consumes a merged prompt and shares a module with historical prompt/budget logic. This small utility reuses that idea on raw instruction fields without importing its prompts, removing headers, fixing topic1 or changing response content.

Current `prepare_native_package.py` requires explicit `--essay-id` or `--no-essay`, then `build_routes` applies its declared route policy. Future integration can add an **opt-in mutually exclusive `--auto-routes`** alongside those existing flags. After `adapter.load_package`, classify each raw item; record route/visual/reason/revision and detector SHA in the new package manifest. Resolve only positive `essay` decisions into the current essay-ID list. `unknown` remains the baseline; open/closed/visual metadata must not activate an unqualified experiment. Existing explicit `--essay-id` and `--no-essay` keep their current authority and behavior. At a pure per-item API boundary, `override='essay'|'closed'|'open'|'unknown'` takes precedence; `unknown` explicitly requests baseline. The utility itself does not interpret IDs.

The executing preflight must independently recompute decisions from the unchanged copied `exam.json`, verify detector/policy pins and exact resolved routes, and reject drift. It must preserve the full original task/source/images in inference payloads, the same model, accounting, guardian, deadline and cleanup. Do not classify serialized prompts because that would expose source-text keywords to routing. Do not infer a particular historical answer, crop position or essay topic. Topic selection remains a separate future validated mechanism. No flag or runtime integration is implemented by this preparation.

Validation: `python -B -X utf8 agentsLog/kwiscion/route-detection-prep/test_classify_item.py` runs14 synthetic tests covering essay instructions/format, ambiguous essay mentions, finite options, true/false, open/unknown, visual metadata, forbidden source/ID access, input immutability, explicit override, conflicts, invalid fields and topic-list ambiguity. No benchmark pack or grading key is loaded. Public-safe source/code hashes are in `manifest.json`.
