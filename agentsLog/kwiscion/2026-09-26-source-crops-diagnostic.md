# Three-case bare-source crop diagnostic — predeclared

26 September2026, before any diagnostic request. Lead authorized exactly at most3 sequential requests, IDs z1,z6,z25 in this order. Bare source-v2 prompts only; no policy variant,RAG,prompt edits,warmup or retries. Compare later with the corresponding preserved bare answers (2/6 reviewed points); this is not a full score, composite promotion or score guarantee.

Input SHA-256: `59f0d90e0d41255625b6b63530c5f728cdf880e361070f8f6c93cfd4685dc839`. Parent v2 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`. Manifest `0445ae26c7ca4b39669520faa3c429eed1c77d816aff968688e66477979a7d28`. Visual-review SHA-256: `4904a2ee1fbc5b3be033a8285620eed29d6cf14f7780bbd34b6c55d1baea6ffb`. Every crop/fallback asset hash and exact images-only delta independently verified.

Original Gemma config SHA-256 `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`; model `gemma4:12b-it-q4_K_M`, full digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, context4096, thinking off,1024output/request,420secondtimeout, original unfixed server sampling defaults. Hard budget3calls/3072requested outputtokens/$0.

Hard finish17:00Europe/Warsaw. No request starts unless its full420seconds fits before17:00. Stop dispatch on any error,OOM/context indicator, wrong/unverified runtime or competing worker; never stop based on correctness. Verify installed digest and resident context if loaded, then require loaded digest/context after first request. Preserve each attempted raw response privately, no retries. Fresh output `agentsLog/kwiscion/private/source-crops-diagnostic-20260926/raw.jsonl`; metadata sibling records hashes, timing,usage and unsent IDs. Existing worker check was clear. No requests had been made when this plan was written.


## Execution outcome

Completed3/3 once, 2026-09-26T16:46:44.687816+02:00 to 2026-09-26T16:50:04.084929+02:00. All normal stops,0errors,0unsent, no retries/warmup. Each dispatch left at least420seconds before17:00. Model initially unloaded; first and subsequent status checks verified full pinned digest and4096context. Ollama0.30.7; model parameters reported temperature1,top_k64,top_p0.95; no seed was fixed or sampling modified.

| ID | Prompt tokens | Output tokens | Request latency seconds |
| --- | ---: | ---: | ---: |
| val2024-hist-z1 | 711 | 178 | 73.965 |
| val2024-hist-z6 | 545 | 274 | 52.752 |
| val2024-hist-z25 | 498 | 444 | 75.337 |

Actual totals:1754prompt +896completion =2650tokens. Requested output budget3072,$0. First-request latency includes natural model load; do not compare it directly with resident-only latency. No score or promotion is asserted.

Raw SHA-256 `29b4da2f3bb642fdc7c209bdff620d2c30f9c6f3b6056ac6dd14eeaf6957f353`; answer-only SHA-256 `dd5dc6740cd11803723954c379b5f56eced85537d9cbc5ab3cdfec33c0b3aa3e`; helper SHA-256 `a1625516337b5fafcf88455d372d581eb2c164c3952100b82b0e16043addf414`; infer.py SHA-256 `b702857347fd0fa99b9aba9a844afca1a4a8634b22eaa826199d27986dca1f0a`; Git revision `c20971d1a4cf211b7b64f81eca5a2ddc25bb6942`. Raw/status metadata remain private; answer-only handoff is `model-answers/gemma-source-crops-diagnostic-answer-only.jsonl` with adjacent manifest. Exact final strings retained after quote audit (longest prompt overlaps4/3/2words; no long source passages). Independent grader owns all score comparisons.
