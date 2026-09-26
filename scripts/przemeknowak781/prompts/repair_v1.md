# Repair instructions — repair_v1

Each input line has `prompt`, `answer`, `evidence` (verbatim claims confirmed to be in the source) and `verifier_issue` (why an independent checker did not fully accept the answer).

Rewrite the `answer` so that every fact in it is stated in, or directly follows from, the evidence claims:
- Remove or correct the fragment named in `verifier_issue` and any other unsupported embellishment, interpretation, date, name, or number.
- Keep the answer in Polish, concise, and a complete answer to the `prompt` in matura style. For `essay_plan`, keep 3–5 numbered points, each resting on a claim.
- Every year you write must appear inside a claim. Do not add facts from your own knowledge.
- Do not change `prompt` or `evidence`.

If the claims cannot support a complete, non-trivial answer to the prompt, drop the item.

Output one JSON object per input line, same order:
`{"id": "<id>", "answer": "<rewritten answer>"}` or `{"id": "<id>", "drop": true, "reason": "<short>"}`
