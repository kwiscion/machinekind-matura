# Recommended next Gemma arm

**Recommend one question-compliant response-policy arm on the existing laptop.** Root decides and dispatches; this note does not authorize or launch inference. Keep retrieval, thinking, weights and output budget unchanged.

The full first pass is provisionally **35/60**, with a **27-40/60** adjudication range and **40 complete outputs**. The 25 provisionally lost points comprise approximately 7 in visual interpretation, 1 in the omitted-image case, 10 in factual/chronological identification or conflicting alternatives, and 7 in the essay. Two conflicting-alternative losses, visual grounding and essay discipline give this policy a plausible mechanism. A **3-6 point gain is a planning hypothesis, not a measured or promised result**; it would not close the current 13-point gap by itself.

Choose this before RAG: the pinned corpus has no image understanding, its TRAIN audit found fully supporting passages in only 22/40 top-three sets, and the earlier five-item Qwen RAG diagnostic scored 1/5 with one incomplete response. That diagnostic does not establish Gemma's RAG effect, but it does not justify treating retrieval as a reliable immediate gain. Turning thinking on also changes completion/latency risk without measured Gemma evidence.

## The only new model-facing policy

Prepend the following identical generic text to every unchanged task prompt. Do not add exam facts, answer examples, evaluator annotations or topic-specific hints.

> Answer in Polish. Solve only the requested task or subtask; neighboring material on a page supplies context, not additional assignments. Follow the question's exact requested form, number of answers, comparisons and justifications. Give one final answer; remove competing alternatives, draft corrections and conversational introductions. For a decision task, make the decision and its required justification agree. Preserve statement labels; if none are present, number the statements consecutively in their presented order. Explain every requested reason using the requested sources. For visual material, ground your interpretation in features actually visible; do not invent inscriptions, dates, uniforms or objects. Add historical details only when relevant and well supported. For an essay, choose one permitted topic without asking for clarification, state your position, address every aspect specified by that topic with relevant facts, and conclude. Meet the question's minimum length with a modest margin of about ten percent. Return only the finished answer, including all explanations the question requests.

## Frozen execution envelope

| Control | Fixed choice |
|---|---|
| Model/runtime | Existing `gemma4:12b-it-q4_K_M`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; existing Ollama 0.30.7; one laptop worker |
| Context/thinking | Effective context 4096; `reasoning_effort: none`; no thinking-template change |
| Output/timeout | `max_output_tokens: 1024`, `timeout_seconds: 420`, matching baseline |
| Sampling | Preserve and record actual existing server defaults. `infer.py` does not send temperature or seed; adding ignored config fields would not fix them. |
| Calls | Exactly 40 planned original-item calls, `--max-calls 40`, sequential, no retries, regeneration, extra judge calls or dropped failures; maximum 40,960 requested output tokens; paid API budget $0 |
| Input | Already-versioned source-v2 assets; preserve all IDs, question text and images. Hash the policy, prepared input, image manifest, model identity and config before launch. |

Use the preserved v1 answers plus the separately declared single-item v2 correction as the comparison anchor if that correction is complete. Label that anchor as reused results. Otherwise disclose that one point also has an input repair; do not attribute that item's change solely to the policy.

Before dispatch, require the entire rendered input, including image tokens, plus 1024 output tokens and a 256-token reserve to fit 4096: **input at most 2816 tokens**. Baseline reported prompt maximum was 1485, which is encouraging but does not prove the revised multimodal fit. Verify effective counting/template behavior without new inference; no character-count claim or silent truncation. If unavailable, resolve that preflight rather than silently shrinking sources. Do not wait for or migrate to an unclaimed RTX worker for this arm.

## Time, stopping and acceptance

Launch by **16:10 Warsaw**, target completion by **17:10**, reserve the remainder for adjudication and the 17:30 selection gate. Baseline requests totaled 25 minutes; observed end-to-end wall time was about 37 minutes. Budget **60 minutes**, without claiming unchanged speed.

After five recorded responses, project completion from observed latency. Stop new requests if the projection exceeds 17:10, after two consecutive infrastructure failures, on OOM/context truncation, or at the 60-minute wall limit. Allow at most the current 420-second request to finish; retain every attempt and missing-item IDs on the fixed 40-item/60-point denominator. No settings changes or continuation under the same arm name. Stop decisions must not depend on interim correctness.

Check final-content completeness, decision consistency and essay body word count offline. An underlength essay is flagged for the official criterion-specific rule, not automatically zeroed in full and never regenerated. Compare all item deltas with independent rubric review; keep the baseline if improvement is absent or grading remains unresolved. This policy cannot establish new factual knowledge or guaranteed recovery of visual errors.

Evidence: [full provisional review](2026-09-26-gemma-review-full.json), [second-half review](2026-09-26-gemma-review-second20.md), [retrieval audit](../Bukareszt/README.md), [earlier RAG diagnostic](2026-09-26-rag-validation-audit.md), and local baseline config/raw usage. Current GitHub comments could not be refreshed in this bounded analysis: CLI config access was denied and public fetch failed. Root must reconcile the current issue owner and absence of another worker before dispatch.
