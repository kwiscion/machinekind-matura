# Quick essay RAG result

The twenty-minute experiment produced **one complete essay, provisionally graded 9/15**: historical argument 6/12 after factual deduction, coherence 3/3. It contained 409 body words. The preserved direct essay was 8/15; this single result is a weak positive signal, not a full-exam improvement.

Three client trials were launched against one Qwen3.5:9b runtime. Its architecture accepted only one inference slot despite the requested parallelism. One 76.5-second writer blocked queued auxiliary requests, and two trials ended with transport timeouts. There were 88 calls, 16 failed attempts (14 quote-validation failures and two transport timeouts). Only one essay was scored. The serial recovery variant missed its start cutoff and made zero calls.

Runtime was approximately 2m33s, starting 09:20:12 Warsaw on 27 September 2026. Requested output-token total: 58,624. Known usage: 152,733 prompt and 13,772 generated tokens; two calls have unknown usage. The completed trial admitted three source passages. All raw records, unfinished trials and the isolated grade are backed up privately.

The grade identified weak socioeconomic development and two historical errors. Cleaning alone would not resolve these. The operational finding is decisive: final Qwen execution must be serial. Owned server/runner absence and an empty GPU were independently verified after shutdown. A redundant parent cleanup scan hit an unrelated `/proc` permission error; that path requires repair in the manual operator wrapper.

Provenance: terminal archive SHA256 `f92f187ef81d232062bb2fa85e14a198f933d35c604693bf4b6f0083a4dc068c`; run manifest `e4804fe7cc120ec339cad78eb471a84968224c9562dff1a36b83d5c55c5b9c97`; frozen grade `162430bac376d519444c5bb21044cb84c7f8315313d1d29450847f692115e44f`. No final exam was accessed.

The owner's subsequent decision selects both essay and ordinary RAG for the manual final workflow. That is a policy choice under limited evidence; it does not change or retroactively complete this experiment.
