# Full-Wikipedia filtered RAG v2: completed

**The pipeline now works; the selected-panel grade improves from direct3/6 to RAG4/6, with one regression. No full-exam promotion.** The direct score has a2–3/6 terminology interval. Grades were frozen before the arm key was opened; the grader knew the implementation, so this was arm-masked, not fully blind.

| Item | Direct | RAG | Admitted passages | Finding |
|---|---:|---:|---:|---|
|3.2|1*|1|3|Stable; RAG gives more explicit terminology.|
|11.2|0|1|3|Retrieved evidence supplies the missing causal explanation.|
|12.1|0|0|2|Namesake/generic material was falsely admitted; identification remains wrong.|
|17.2|1|0|1|Incorrect query hypothesis and article-title association overrode a relevant clue in the admitted quotation.|
|5.2|1|1|3|Stable correct response.|
|19.2|0|1|1|Retrieved evidence resolves the requested identification.|

\*The direct office nouns are centrally accepted in their Roman context; a stricter demand for the omitted qualifier could remove this point. This judgment was frozen before unmasking. The lexical distinction was checked against [Arct's dictionary entry](https://pl.wikisource.org/wiki/M._Arcta_S%C5%82ownik_ilustrowany_j%C4%99zyka_polskiego/Trybunat); it does not replace the official CKE criterion.

The four auxiliary probes passed on their first attempts: two typed queries and two valid negative judgments. All six main queries were valid, all thirty judgments reached valid finals, and thirteen literal quotations were admitted. Two nonverbatim quotations were rejected and recovered **before** final answers. One final-answer timeout also recovered. All twelve submitted answer slots are complete, without placeholders or control-fallback substitution.

Execution used55 attempts and1,835,008 reserved output tokens. Known usage was86,287 prompt and148,508 generated tokens, plus one timeout with unknown usage. The pinned Gemma model loaded with65,536 context; complete original text/image payloads and request hashes were verified for all55 requests. The fresh single-model cache counted7,556,509,301 bytes. Actual isolated-network and owned-cleanup evidence is retained privately; the GPU was empty afterward.

Declared04:20:24.076268UTC; dispatched04:24:15.720228UTC; terminal04:56:06.821245UTC. Execution wall time was1,911.10seconds, approximatelyUSD1.74 at the suppliedUSD3.28/hour planning rate; actual billing is unverified. The05:20UTC deadline was not extended. A pre-call CRLF/LF metadata hash failure was preserved and corrected using the exact original bytes, before any reservation or service start.

Verified local/remote backup SHA256: `d59750782952887d1b66cf9c403b85210c476df1b6f3a3ce093c199e84c4e926`.
Masked grade freeze: `50b924e3826f2c21f0ab95025bdf72d4062519ec832cf23221f7a8c8ead4fe95`.
See the adjacent result/grade JSON files for exact answer-export hashes, item flags and provenance.

This is a known, selected six-item diagnostic with unfixed sampling defaults. Faithful quotation is not sufficient for correct relevance or source interpretation. The earlier v1 run admitted no evidence because its auxiliary task framing failed; it remains a separate preserved negative engineering result.
