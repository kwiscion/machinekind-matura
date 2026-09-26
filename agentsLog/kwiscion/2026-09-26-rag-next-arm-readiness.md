# Possible later Gemma RAG arm — readiness only

26 September 2026. **Existing local retrieval works, but a later full arm is not yet declared or launch-ready.** Wait for the active question-policy result. No inference, new corpus, retrieval tuning, model download or prepared exam prompt file was produced by this review. The active process was not touched.

## Existing integration

`scripts/prepare_rag.py` already imports the merged retriever, defaults to `chrono`, top five, title weight1.0 and400 characters per hit. It queries the **entire supplied prompt**, adds reference text plus citation instructions to every row, retains IDs, and resolves original local image paths to absolute paths. Its trace records source/chunk IDs and index hash; corpus output contains only the selected excerpts for later citation audit. No answer/key fields enter its query or prompt construction.

With the policy input, the generic policy itself becomes part of each retrieval query. There is no automatic task-only query extraction or per-item routing. Choose and freeze whether the input is source-v2 alone or source-v2-plus-policy after reviewing the active arm; do not silently combine interventions. Current behavior is uniform across all40 cases, including essays and image cases. No exam-answer-informed selection is appropriate. The adapter's citation instruction is an additional response-policy change, so describe the treatment as the existing RAG package, not pure added facts.

## Local pins and checks

At reviewed main `a8f4c79a2c84f4b530db78e02701aa998a8ba613`:

- Local index matches `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`,8,514,642 bytes,3,481 chunks.
- All107 raw source files match the staging manifest. Source revisions/normalized-text hashes remain pinned; no fetch occurred.
- Graph semantic hash, excluding `built_at`, matches `9ed53bb99bf0599fa67535ec1a0b14d0869e6c62c210d81193fa9fd0093a004b`. Local raw graph hash differs from bundle bytes due timestamp; content is identical under the documented comparison.
- Local source-manifest and retriever bytes have Windows CRLF. LF-normalized identities match source manifest `8b77a63afd25317d783a3e511e3f1f99f09b6cec3c740bdf101a0d069aadfeed` and retriever `5ce9918fcc0151c8e15391781ace98deaf4b786977a69e6e773ccc9d7b0a51a3`.
- Three invented general-history queries ran under a socket-connect guard and each returned five hits. Union of Lublin and absolutism queries retrieved their corresponding articles first; a general Sejm query retrieved Sejm Wielki first, illustrating that successful loading does not prove question relevance.
- Licenses recorded:100 Polish Wikipedia pages under CC BY-SA4.0; seven Wikisource primary documents marked public domain with CC BY-SA4.0 transcription layers. Preserve staging `ATTRIBUTION.md`, revision permalinks and share-alike terms with any redistributed corpus bundle. Raw references and exam inputs remain ignored/private.

The possible model remains the same Gemma full digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, original config hash `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`, thinking off,1024 output tokens and4096 effective context. No weights or sampling defaults change is proposed; original sampling defaults were not fixed.

## Measured text expansion, not token-fit proof

Computed retrieval selections and lengths in memory over all40 current frozen policy inputs, without writing augmented prompts. Defaults were unchanged: chrono/top5/400chars. These are measured Unicode character counts:

| Quantity | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Current policy prompt |1859|2566.5|4899|
| RAG addition incl. headers/markers |2557|2686.5|2767|
| Combined text |4473|5250|7614|

Passage text alone is capped at2000 characters; titles, source markers and instructions add further overhead. A deliberately rough sensitivity estimate using2–4 characters/token makes the addition roughly640–1384 text tokens; this is **not a tokenizer measurement, confidence interval or context-fit guarantee**. At the largest combined text, that approximation spans1904–3807 text tokens before image/template overhead. Thus the existing2816-input-token ceiling cannot be assumed satisfied for every case. Actual tokenizer/image behavior is unproven; baseline usage does not prove the expanded input fits. Do not remove source text or lower retrieval limits after seeing scores. A later arm needs a declared context/overflow policy and bounded stopping behavior before calls.

## Does this require #54?

Existing `prepare_rag.py` can use this already verified local index on current main; #54 is not required merely to load/retrieve. However current staging is **not approved as a fresh-clone deployment path**: #54 records CRLF pin handling, protected destination replacement and validate-before-import fixes. Do not run staging/rebuild to resolve those issues during this preparation. Require Greg's reviewed #54 repair before declaring portable staging ready. This report verified the local retriever's LF identity before importing it; current generic adapter itself does not enforce the full source/graph/retriever pins, so a later launch preflight must record/check them explicitly.

Decision remains with the lead after the active policy arm. Training retrieval audits and successful loading are not evidence of Gemma exam gains. A prospective comparison must keep the same40 IDs and60-point denominator, original errors, frozen assets, runtime and independent grading. No additional laptop worker is authorized here.

Private aggregate measurements: `agentsLog/kwiscion/private/rag-readiness-aggregates.json` (no prompts, answers or reference excerpts).
