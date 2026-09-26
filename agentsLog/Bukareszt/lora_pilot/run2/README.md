# #117 pilot-run2: stage 1 PASS (real 12B backward); stopped fail-closed at stage 2 on a mis-specified template criterion (false negative)

- **Driver:** root's PR #146 `586acd0b…`. **Wave:** start 22:11:20Z, deadline 23:11:10Z. It stopped at **22:12:15Z (55 s)**, rc 1. The backup verified (`evidence/` matches `BACKUP_SHA256SUMS`), the GPU is idle and no process is left.
- **Stage 1, probe: PASS.** 88 modules, 5,193,728 trainable parameters, 1 optimizer step, loss 0.0536 (finite), max parameter delta 1.0e-4. Peak CUDA memory 24,188,301,312 B allocated / 24,555,552,768 B reserved. Driver elapsed 24 s.
- **Stage 2, control serving: calls OK, report FAIL.** Both ledgered calls returned HTTP 200 with `stop`:
  - text: 80 completion tokens, on topic;
  - image: "Na obrazku widać czerwony kwadrat i niebieskie koło." (a red square and a blue circle), which is correct; 107 prompt tokens vs 32 for text.

  The server loaded in 3.1 s and exited cleanly with code 0. One predeclared criterion failed: `served_template_is_pinned_hf` compared the `/props` `chat_template` sha (`6a1015c4…`) with the raw HF `chat_template.jinja` sha (`ae53464b…`).
- **Root cause, my criterion rather than the model:**
  - llama.cpp `common_chat_template` stores `lexer_res.source`, and `/props` returns it (`common/chat.h` → `jinja/lexer.cpp tokenize()`). That source is normalized: CRLF → LF, and **a single trailing newline is stripped**.
  - Applying that normalization to the pinned HF template gives exactly `6a1015c47ccfcfa67c3b772385bccee357a4d37c3cda37bd202e9047f391ab82`. The control GGUF's `tokenizer.chat_template` KV is byte-identical to the pinned `ae53464b…` (18,681 chars).
  - So the server served the pinned template. The check should have compared against the lexer-normalized sha.
- **Not done, per the declaration:** no retry, no criterion edit mid-wave, no extension. Stages 3–6 (history, export, candidate calls) never ran.
- **Cumulative usage:**
  - run1: 0 steps, 0 calls;
  - run2: 1 synthetic step, 0 history steps, **2 of 4** generation calls (both control).
- **Proposed fix for any run3 (needs root):** in `serve_session.py`, compare `/props` against the lexer-normalized pinned sha `6a1015c4…`, or normalize `/props` and the raw template the same way before hashing. Nothing else changes.
