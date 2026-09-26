# Organizer scoring patterns: verified public-site audit

**Prioritize factual/source reasoning and a working native-thinking path, with essay topic/length controls as guardrails. Do not treat these results as evidence that removing preambles alone will recover points.** The site contains **27 full-run pages, 19 distinct models and 951 scored item records with 951 grading explanations**. Every extracted total reconciles with its page headline. These are organizer AI assessments of **18 May 2023 history (DEV)**, not official examiner grades or our May 2024 scores. [Method and input formats](https://warsaw-matura-method.ania-olchowik.chatgpt.site/#input-formats)

## Relevant models and actual coverage

| Model actually published | Input | Items | Total | Essay |
|---|---|---:|---:|---:|
| [Gemma 4 12B IT](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html) | Original pages | 37 | **46/60** | **12/15** |
| [Qwen3.5-9B](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen-3-5-9b-vision.html) | Original pages | 37 | **36/60** | **8/15** |
| [Bielik-4.5B-v3.0-Instruct](https://warsaw-matura-method.ania-olchowik.chatgpt.site/bielik-4-5b.html) | Descriptions | 34 | **23/55** | **2/15** |
| [LLaVA-Bielik-11b-v2.6-instruct](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-vision.html) | Original pages | 37 | **14/60** | **0/15** |
| [Same LLaVA-Bielik checkpoint](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-text.html) | Descriptions | 34 | **29/55** | **3/15** |
| [Qwen3-4B-Instruct-2507](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen3-4b-instruct-2507.html) | Descriptions | 34 | **22/55** | **3/15** |

**Coverage gaps:** no indexed Qwen3.5-4B or text-only Bielik11B-v3 result. The similarly named Qwen3-4B and LLaVA-Bielik11B are different checkpoints. No completed linked description run for Gemma4-12B or Qwen3.5-9B was present in this snapshot.

Full coverage ledger (each score is separately labeled; dash means no linked completed run):

| Model | Images /60 | Descriptions /55 |
|---|---:|---:|
| gemma-3-1b-it | — | 8 |
| Bielik-1.5B-v3.0-Instruct | — | 15 |
| Qwen3-1.7B | — | 13 |
| SmolLM3-3B | — | 10 |
| Llama-3.2-3B-Instruct | — | 10 |
| Phi-4-mini-instruct | — | 10 |
| Qwen3-4B-Instruct-2507 | — | 22 |
| Bielik-4.5B-v3.0-Instruct | — | 23 |
| Qwen3-VL-2B-Thinking | 4 | 7 |
| Qwen3-VL-2B-Instruct | 9 | 6 |
| PLLuM-4B-instruct-2512 | 13 | 17 |
| gemma-3-4b-it | 16 | 20 |
| InternVL3_5-8B-Instruct | 22 | — |
| Qwen3.5-9B | 36 | — |
| LLaVA-Bielik-11b-v2.6-instruct | 14 | 29 |
| gemma-4-12B-it | 46 | — |
| LLaVA-PLLuM-12b-nc-instruct | 14 | 19 |
| Ministral-3-14B-Instruct-2512 | 29 | 33 |
| GPT Astra | 60 | 55 |

The companion JSON includes exact links, per-item scores, denominators and explanation hashes for every run.

Descriptions replace images with fixed written observations; tasks 7, 8, 15 are excluded, reducing 60 to 55. Original-image runs retain all 37 items and require reading complete page pixels, with only the target question typed separately. Compare shared items when assessing mode differences; neither the raw totals nor their percentages isolate vision quality. [Input contract](https://warsaw-matura-method.ania-olchowik.chatgpt.site/#input-formats)

## Exact settings that matter for our comparison

Both relevant vision pages report **BF16, no quantization, A100 80GB, batch 1, no system instruction, Transformers5.17.0 and PyTorch2.8.0+cu128**. They use sampling and native thinking. This differs materially from our Q4, thinking-off, 1024-final-token Ollama control. Seed is not stated on these pages; a seed from another pilot must not be assumed.

| Setting | Gemma4-12B | Qwen3.5-9B |
|---|---|---|
| Model revision | `707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7` | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Sampling | temperature1.0, top_p0.95, top_k64 | temperature1.0, top_p0.95, top_k20, min_p0, repetition_penalty1, presence_penalty1.5 |
| Allowed thinking per short / essay | 8,192 /16,384 | 8,192 /16,384 |
| Allowed final per short / essay | 2,048 /4,096 | 2,048 /4,096 |
| **Observed stored thinking tokens, whole run** | **55,242** | **92,684** |
| **Observed stored final tokens, whole run** | **6,946** | **7,438** |
| Missing final answers | 0 | 3, worth4availablepoints |
| Thinking / final generation seconds | 3867.9 /521.0 | 4632.4 /347.9 |

These are generation times, not billing or elapsed orchestration time. Shared dataset SHA-256: `989ca67f9a6417e3daecc15be864d130ac470016d7718092d0359b59e6b1a37a`. The observed totals are **not** requested caps. Exact settings are in each page's reproducibility section: [Gemma](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html), [Qwen](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen-3-5-9b-vision.html). Quantization, input construction, decoding, thinking and output budgets all differ from our controls; no single cause of the score gap is established.

## Failure taxonomy with linked examples

| Pattern | What the organizer actually awards or rejects | Example |
|---|---|---|
| Missing selection / format | Copying choices or restating descriptions without selecting the requested answer loses credit. Parser-ambiguous format is reviewed, not automatically zeroed. | [LLaVA-Bielik image2.2](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-vision.html#task-2-2) |
| Conflicting commitments | A correct sentence does not silently replace an incompatible explicit decision; multiple incompatible alternatives are not cherry-picked. | [LLaVA-Bielik text22](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-text.html#task-22) |
| Multiple essay topics | Only the first explicitly selected topic and its words are counted under the organizers' stated interpretation. | [Bielik4.5B26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/bielik-4-5b.html#task-26) |
| Underlength | Historical credit can survive while coherence becomes0. The reported first-topic count is 291 for Bielik4.5B; LLaVA-Bielik text has 193 body words. | [Bielik4.5B26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/bielik-4-5b.html#task-26), [LLaVA-Bielik text26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-text.html#task-26) |
| Preamble / non-answer | No blanket preamble penalty found. A topic placeholder alone is not an essay; irrelevant material can disrupt coherence. | [LLaVA-Bielik image26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-vision.html#task-26) |
| Truncation / absent final | Stored reasoning is not graded as final output. A repeated unfinished response can consume the cap without answering. | [Qwen9B13.1](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen-3-5-9b-vision.html#task-13-1), [Qwen3-4B14.2](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen3-4b-instruct-2507.html#task-14-2) |
| Visual/source grounding | Plausible generic interpretation is insufficient when the actual visual relation is wrong. Bibliographic publication dates can be confused with event dates. | [Gemma8](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html#task-8), [LLaVA-Bielik image24](https://warsaw-matura-method.ania-olchowik.chatgpt.site/llava-bielik-11b-vision.html#task-24) |
| Factual relations | An incorrect genealogy is central when genealogy is the explanation requested; a correct broad topic cannot rescue it. | [Gemma5.2](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html#task-5-2) |
| Argument quality | Headings, length and fluent organization cannot replace valid historical examples and causal comparison. | [Qwen3-4B26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen3-4b-instruct-2507.html#task-26) |
| Rubric uncertainty / extra facts | The organizer sometimes keeps credit when the required core is sufficient despite an irrelevant extra error. Closed-task selections may score independently of unsolicited explanations. | [Gemma5.3](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html#task-5-3), [Bielik4.5B10](https://warsaw-matura-method.ania-olchowik.chatgpt.site/bielik-4-5b.html#task-10) |

This taxonomy is a manually checked set of representative mechanisms, not automated causal-frequency estimates. No claim is made that all951 answers were independently regraded.

## Essay lessons and the boundary between CKE and organizer policy

Gemma's essay receives 12: three satisfactory component arguments plus coherence; generality prevents richer argument credit. Qwen9B receives 8: a weaker political comparison and factual deductions reduce narrative credit, while its 325-word body earns coherence. These are separate constraints: expanding a weak essay is insufficient. [Gemma26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/gemma-4-12b-vision.html#task-26), [Qwen26](https://warsaw-matura-method.ania-olchowik.chatgpt.site/qwen-3-5-9b-vision.html#task-26)

Bielik4.5B's score is not merely a format penalty: its first essay gets 3 raw historical points for superficial argument, loses 1 for factual errors, and receives 0 coherence for underlength. The other topics do not increase its count under the benchmark policy. [Organizer explanation](https://warsaw-matura-method.ania-olchowik.chatgpt.site/bielik-4-5b.html#task-26)

**Directly verified CKE 2023 rules:** pages 25–26 require at least300 words for coherence credit, assess logical organization separately, and require historical knowledge to support the thesis and specified components functionally. Underlength alone does not automatically erase historical narrative points. Irrelevant digressions can impair coherence; there is no standalone automatic penalty for a polite preamble in the inspected rubric. [Official CKE scheme](https://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2023/Arkusze_egzaminacyjne/2023/Historia/MHIP-R0-100-2305-zasady.pdf)

**Organizer interpretation:** grading only the first explicitly selected topic is expressly identified as their policy, not a quoted CKE rule. Their word-count preprocessing, phase extraction and AI judgments also remain benchmark procedures. Do not present these as universal examination law. [Methodology](https://warsaw-matura-method.ania-olchowik.chatgpt.site/methodology.md)

## Prioritized bounded experiments — proposals, not launches

1. **Native thinking with a reliable final channel:** Łukasz's decision lab should test a matched source-preserving subset, with explicit thinking and final caps and no hidden-reasoning substitution. Example envelope: six items × two arms, one call per item/arm; thinking arm 4096+1024, control 0+1024, total 36,864 requested output tokens, 30-minute outer stop. Check actual backend support first. This tests a named configuration bundle, not temperature alone; preserve the existing no-thinking control.
2. **Evidence-to-answer relation checks:** keep full sources, identify the needed person/event/relation or visible feature, then verify that the final claim is supported. Score core identification and justification together. Use generic fixtures or authorized evaluation-only slices; never inject these benchmark solutions into retrieval or training.
3. **Essay factual ledger before prose:** compare single-pass with actor/event/date/consequence verification on three independent multi-era DEV topics. One selected topic, three supported components, actual body-word count with a modest margin above 300, and separate factual/argument/coherence review. Topic locking can prevent wasted output; it cannot manufacture the missing historical evidence.
4. **Final commitment check for closed/decision items:** require one explicit answer per requested slot and make the decision agree with its justification. Test correct controls as well as misses. Do not repair answers by reading the key or rely on the grader choosing a favorable alternative.
5. **Quantization/runtime parity only after a promising route is reproducible:** the BF16 site results justify a measurement question, not a switch from the eligible saved-model artifact. Compare the actual compliant quantized deployment under identical inputs/settings before attributing gains to a checkpoint.

## Collection, provenance and limits

Read the actual index links; downloaded30 linked documents through ordinary HTTPS after the web reader failed. Parsed `article.review-task`, `.task-score` and `.grade-explanation`; verified unique item IDs, all explanations present and27 headline sums/denominators. The benchmark summary, five-question pilot and methodology are not counted as full runs. No recursive external crawl, May 2025 access, GPU/model calls or training writes.

Raw HTML and extracted explanations stay in ignored `outputs/organizers-model-method/`. Public JSON contains score facts, links and explanation hashes, plus original analytical summaries. The owned standard-library parser `agentsLog/kwiscion/organizer_method_collect.py` reproduces951 records from the cached pages. Run: `python -X utf8 agentsLog/kwiscion/organizer_method_collect.py`.

Official 2023 rubric SHA-256: `64acaefce9554c67434bca06045224154fc8079e84cc557f0a3a42d30eb5f9ae`. Each model page hash is in the JSON. The local index was supplied as a cached snapshot; model pages and the official rubric were fetched during this audit. All material is DEV evaluation evidence only: **question, answer, grade and rubric content must never enter TRAIN or retrieval.**
