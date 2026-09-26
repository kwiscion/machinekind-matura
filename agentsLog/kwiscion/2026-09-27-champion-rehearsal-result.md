# Champion recovery rehearsal — terminal result

**Operator PASS; 40/40 complete nonblank final answers, zero placeholders.** This was one full organizer-path rehearsal with two declared faults, not a clean baseline benchmark. Quality grading is separate; no score or promotion is claimed here.

- 46 generation reservations/completions, including 6 recovery calls; no warmups or manual retries. The three failed initial attempts all recovered: one natural empty final and two injected faults. Item 13 actually returned `length` under cap 1; item 25 hit its declared 3-second timeout. Timeout usage is unknown, not zero. Owned server/backend processes were killed and verified absent before the next request; actual token generation before cancellation was not observed.
- 1,523,713 requested output tokens against the 5,898,240 ceiling.45 responses report 60,906 prompt and 88,611 generated tokens; the timed-out call has no usage receipt. Weighted generation throughput was 102.87 tokens/evaluation-second. First cold model-load duration was 54.51seconds; the 240-second cold allowance avoided a premature initial timeout.
- Declared 23:13:47.104702UTC; operator started 23:14:19.536904; first reservation 23:14:28.112261; terminal 23:33:36.795727 on 26 September. Operator wall time 19m17.26s; declaration-to-terminal 19m49.69s, leaving 40m10.31s before the hard deadline. Planning-rate estimate $1.084 at $3.28/hour; actual billing unverified.
- Pinned Gemma/Ollama 0.34.4 served with verified 65,536 context in an actual separate no-egress network namespace (only loopback; external IPv4/IPv6 attempts returned network-unreachable). All original source/image inputs were retained. Gemma model/projector total 7,556,497,632bytes; isolated six-file cache including metadata 7,556,509,301bytes, below the conservative 8,800,000,000 aggregate limit. Runtime VRAM allocation is not the saved-weight limit.
- Final owned cleanup and guardian completed successfully; post-terminal GPU process list was empty and the original idle service remained unchanged. All 36 early stable answers and the later 3 recovered answers equal the terminal strings exactly. All raw responses, interrupted thinking, requests and candidates remain private.

## Essay format behavior

| Attempt | Thinking | Whitespace words | Selected | Warning |
|---|---|---:|---|---|
|0|on|372|no|Outside requested 400–500 band|
|1|on|392|no|Outside requested 400–500 band|
|2|off|376|no|Outside requested 400–500 band|
|3|off|363|yes|Outside requested 400–500 band|

All four essays exceeded 300 words; no multiple-topic/plan warning was detected. The frozen latest-complete rule selected attempt 3. Thus repairs did **not** resolve the advisory400–500 band and replaced a longer complete candidate with a shorter one. All candidates are preserved; no post-hoc selection was made and no factual-quality ranking is implied.

## Exact artifacts

- Actual submission-shaped answers: `model-answers/champion-rehearsal-val40.answers.json`, SHA256 `eb70f42aa7706aa7a622d61b1378925914d025ea02c4bfa3a06a8bd544356ce8`.
- Answer-only evaluator JSONL: `model-answers/champion-rehearsal-val40-answer-only.jsonl`, SHA256 `c650744f4ca2360a3cf1cc6a17d42433e2866a76f20f36374472004faef26a20`.
- Machine-readable per-item flags, usage and timing: `2026-09-27-champion-rehearsal-result.json`.
- Complete private archive was downloaded and its local SHA256 matched remote: `e9c9729eee7266d0c2f94b92cd61a35723a161d7cce95e1acfaa3e4b4ad4e105`.
- Declared manifest SHA256 `3b7d63703189dff609e61a30538ae85f2be65c48755ef9067bab1235f4613356`; binding `4ee1ef11269ca47d3bacd8be56d36ee2ffedecb3987db42f4a7c432afd3018fd`; scheduler `17b153638574ba08c8239d8b5373fbf0039fe9034dea26848138e7204cc15506`.

The output contains all 40 original template IDs and passes the exact schema, nonblank, 100,000-codepoint-per-answer and 1 MiB-file checks. No FINAL access, organizer submission, May 2025 access, additional generation, or code change occurred during execution.
