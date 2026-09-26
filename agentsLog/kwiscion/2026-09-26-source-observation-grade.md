# Independent source-observation review — 26 September 2026

**Decision: no promotion. Bare3/6 versus observation/fallback3/6.** Root Astra independently reviewed the exact six answer pairs against the local May2024 evaluator after the Sol generator finished. These are provisional agent grades on a deliberately selected known-validation panel, not organizer grades or a full exam score. Conservative wording interpretations give2–3/6 for each arm; these ranges are judgment bounds, not statistical confidence intervals.

All six items are worth one point. A correct decision alone does not earn the point when the required source-based justification is wrong. No evaluator keys or source passages are reproduced here. Inputs, methods, runtime and answer hashes are in the [execution report](2026-09-26-source-observation-result.md).

| Item | Bare | Final | Observation completed? | Independent diagnosis |
|---|---:|---:|---|---|
| z1 |0|0|Yes|Both choose the wrong visual alternative. The final answer rationalizes a familiar historical narrative instead of grounding the decisive symbol in the image. Separating an observation pass did not fix this case.|
| z2 |1|1|Yes|Both correctly distinguish the historical periods represented by the two sources and justify the distinction. Minor wording imprecision does not reverse the explanation.|
| z4 |1|1|Yes|Both identify a relevant Greek architectural feature and a Roman feature. The final answer adds wording, without a new point.|
| z5.1 |0|1|No: capped|Bare invents the map's historical identity and gives an impossible chronology. The second bare draw identifies the contrasting migrations and the appeal correctly. Its malformed crusade terminology could be treated more strictly; central credit1, conservative0.|
| z14.1 |0|0|No: capped|Both justify the otherwise correct decision using a misidentified map and invented map details. The required comparison is therefore unsupported.|
| z15.2 |1|0|No: capped|Bare recognizes the shared criticism of leadership; imprecise attribution/quotation supports conservative0 rather than central1. The second draw chooses the opposite alternative and treats criticism as praise.|
| **Total** |**3/6**|**3/6**|3/6 assisted|One gain and one regression occur only in unchanged-input fallback draws.|

## What the experiment actually teaches

The successfully assisted path scores **2/3 in both arms**. The fallback path scores1/3 in each arm centrally, with different items credited. For the three failed observations, the final request was byte-identical to its bare control; its differences are unseeded sampling variation, **not evidence for or against observation assistance**. Six answers completing does not mean six assisted answers were tested.

Half the observation calls exhausted their768-token allowance. That gives a concrete completion defect, but the fully completed difficult visual case still failed through unsupported interpretation. We do not infer from this tiny experiment that all source decomposition is useless. We also do not spend another round merely polishing the same long observation narrative.

**Next family:** prepare an independently verified, eligible alternative visual observer feeding a concise evidence record to the unchanged Gemma solver, with all original sources retained. This changes the model evidence path and tests complementary grounding rather than temperature. It is a named mechanism bundle, not an isolated causal test of one prompt sentence. Root owns its CPU preparation; a new manifest and runtime/artifact checks precede any generation. Piotrek retains a distinct crop/multiscale lane when he claims it.

No full-system score changes. The35/60 historical laptop fallback remains preserved. Exact outputs and failed observations remain attributable; no lucky per-item answer splice is promoted.
