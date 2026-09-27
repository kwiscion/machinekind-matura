# #178 three-perspective visual strategy: implementation and diagnostic result

**Scope:** a known-failure diagnostic on panel 6, 14.1, 18, 25, 1, 23.2. It is NOT a representative exam estimate. Everything runs on the same eligible registry Gemma weights (`1278394b…` + projector `675ad6e6…`), served by one owned pinned llama.cpp `fcb3074f` server with greedy temp 0, nonthinking and 65,536 context. The inputs are root's verified six-item source crops (`8d458388…`), normalized by `matura_package.py prepare` into `b8171f4f…`. They stay private on the host.

**Code:** `perspectives_session.py` (v2 `55d2cbf3…`), `settings.json` (wave 1), `settings-v2.json` (wave 2), `operator-stages*.sh`, `launch*.sh` and `test_perspectives.py` (focused fake-server test, 17/17 PASS). Per item:
1. A direct call: the unchanged prompt plus the images.
2. Three independent views of the images only: text, details and context.
3. A final call: the complete prompt, all images and the three views marked fallible.

Only the direct and final answers are exported.

## Waves

- **Wave 1** (`settings.json`, full 32768 → 49152 → 32768 → 32768 ladder for every call): started 03:55:12Z.
  - Item 6 completed. Item 14.1's text view looped to the 32768 cap under greedy decoding (315 s) and then began retry 2.
  - Stopped early by me at 04:06:41Z through the designed TERM path (rc 143, owned server exited, verified backup), because the loop would have consumed the window and starved the later items' direct calls.
- **Wave 2 (v2)** (`settings-v2.json`): identical, except each view gets **one 2048-token attempt**.
  - 04:09:45 → **04:12:05Z (2 min 20 s)**, rc 0, backup verified.
  - **30/30 calls; direct 6/6 and perspectives 6/6 complete; 0 blanks and 0 placeholders.** Only 14.1's text view truncated at 2048 (a labelled partial, a "Lwów Lwów…" repetition).
  - Cost ≈ wave 1 (11 min) plus wave 2 (2.3 min), about 0.25 h, ≈ $0.8 at the unverified $3.28/h proxy.

## Per-item comparison (answers only; correctness is left to root's single grade pass)

| ID | Direct vs perspectives |
|---|---|
| 6 | **Changed.** Direct maps the three slogans to clergy, knights and peasants. Final replaces the knights with "the central figure of Christ" and "townspeople", following views that claim "Christ on the cross". **Likely false view detail propagated.** |
| 14.1 | Same decision ("nie"). Final cites map dates "1.01.1914, 1.07.1914", which are **unverified and possibly invented**. Direct placed the map "after WWI". |
| 18 | Same decision ("Ententa"). Final adds four uniformed Allied soldiers, "one in Polish dress with a cape". Direct cites "a crown with a cross". Details need image verification. |
| 25 | **Changed interpretation.** Direct: a critique of system/bureaucracy, "S.O.N.D.A.". Final: "SONDA" as probing/surveying, "pre-war". Needs grading. |
| 1 | Same decision ("B"). Final adds Narmer and a "two figures holding crowns" description. |
| 23.2 | Same decision ("Nie") and the same table figures. The view transcription matches the direct reading. |

**Overhead:** 5× the calls per image item (30 vs 6). Wall time is about 2.3 min for both arms together, with views 1–20 s each; final prompts are about 1.5–4.3k tokens.

**Descriptions and false facts:** the views contain transcription errors ("ZNIEŚWIENIEM", "Zdrojó 2", "Gródzki/Grodździ"), repetition degeneration (the 14.1 text view) and plausibly invented details. At least item 6's final appears to adopt a false view detail. The view texts stay private on the host (`perspectives-raw.jsonl` `73bc264a…`, and the backup), because they transcribe third-party source content.

**Status:** answer-only exports are in `evidence/wave2/answers-{direct,perspectives}.jsonl` (`cff0352e…` / `0a2d5aeb…`) for root's single grading pass. No promotion claim: decisions are unchanged on the 4 decision-style items, and the open items changed in ways that include introduced errors.
