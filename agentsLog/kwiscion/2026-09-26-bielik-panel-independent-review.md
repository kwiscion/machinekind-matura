# Independent Bielik / Gemma text-panel review

**Bielik: 7/11 [6,8]. Fresh matched Gemma: 8/11 [8,8].** Nine items per arm; the denominator is eleven points. Bielik minus Gemma is -1 point, with descriptive adjudication bounds [-2,0]. This is a provisional independent Sol review of known validation, not organizer adjudication or a full-exam promotion result. Model labels were visible; the reviewer did not generate the answers.

The first pass used the original source-v2 panel and official May 2024 marking rules, without earlier model grades. Exact answer hashes match the supplied manifest, and all nine IDs are unique and in matched order. The panel was selected by zero-image, non-essay structure before grading. Both length-failed Bielik outputs remain blank and zero. Uncertainty ranges express rubric interpretation, not statistical confidence.

| Item | Max | Bielik central [low,high] | Gemma | Rationale |
|---|---:|---:|---:|---|
| z3.1 | 1 | 1 [1,1] | 1 | Correct requested identity; unnecessary commentary does not change that identification. Gemma: Correct requested identity. |
| z3.2 | 1 | 0 [0,0] | 0 | Length failure exported blank; partial completion is not graded. Gemma: An incorrect primary office plus incompatible alternatives fails the requirement for two correct office names. |
| z7 | 1 | 0 [0,1] | 0 | Correct selection and references to both excerpts, but ordering is asserted rather than historically demonstrated; generous rubric reading could accept. Gemma: A later correction of the selected letter cannot repair invented rulers, dates and events in the justification. |
| z15.1 | 1 | 0 [0,0] | 1 | Length failure exported blank; partial completion is not graded. Gemma: Correct requested event identification. |
| z15.2 | 1 | 1 [1,1] | 0 | Correct selection supported by the shared evaluative stance and evidence from both sources. Gemma: Wrong selection and reversed interpretation of the source evaluation. |
| z20.1 | 1 | 1 [1,1] | 1 | Correct source selection with relevant concrete economic evidence. Gemma: Correct source selection with relevant concrete economic evidence. |
| z20.2 | 2 | 1 [1,1] | 2 | Two of three statement judgments are correct; the third remains wrong despite its explanation acknowledging the contrary fact. Gemma: All three judgments are correct and map unambiguously to the ordered statements. |
| z22.1 | 1 | 1 [1,1] | 1 | Correct required day and month. Gemma: Correct required day and month. |
| z22.2 | 2 | 2 [1,2] | 2 | Both requested comparison dimensions have a valid shared core; extra claims are misattributed to both texts, creating a stricter one-point interpretation. Gemma: Supplies a supported similarity in each requested comparison dimension. |

Two judgments need adjudication: Bielik z7 selects correctly and refers to both excerpts, but does not establish the chronology convincingly; z22.2 contains two valid comparison cores alongside unsupported shared attributions. For z20.2, both models use labels 0–2. Explicitly repeated statement content and order make their mapping unambiguous, so no literal numbering penalty is imposed. Correct alternatives embedded among incompatible answers do not rescue z3.2.

## Failure diagnosis after scoring

The scores above were frozen before inspecting the two private Bielik partials. Each consumed its full 1,024-token cap and ended with `length`:

- **z3.2: semantic repetition and indecision.** It cycles through incompatible candidates, repeatedly revises them and does not converge. More space alone has no clear repair hypothesis.
- **z15.1: task-boundary failure.** It supplies the requested short answer early, then invents further numbered tasks and continues answering them until the cap. This is not a shortage of space for the active task. No points are recovered from the partial.

**Park a cap-only Bielik extension.** A separately declared generic one-active-task/answer-boundary repair is a concrete hypothesis, initially testable on original DEV examples. The saved evidence does not establish a template or EOS defect. Factual selection and source interpretation also contribute to errors, so format repair alone is not established as sufficient.

## Scope and provenance

The paired run used the same full source prompts, 1,024-token output caps, context 32,768 and omitted temperature. Gemma used thinking off; Bielik has no thinking capability. Different tokenizers, model templates and native defaults remain potential confounds. Nine selected known-validation items cannot establish general superiority or justify promotion. No new model calls were made for this review.

- Bielik answers SHA-256: `aae8a0c0fe0549bde136dd77a688f220fa3d74e6d55fca64c8467350160a5587`
- Gemma answers SHA-256: `95e332d8383e96f6f60a82c76273fccce699155e313d910322a837025a350a71`
- Panel SHA-256: `213197cc40570123d52d90e3c5609675f4d2f36f050704a042475bba418614d0`
- Official rubric PDF SHA-256: `95c275b9546611c1f8cd45b7973c436625fd0ee5643b778dcc8bb566db56cd4c`
- Private raw paired trace SHA-256: `2bdf49086ea14b707ae7c6c55e3b7999b7b874c6c7f2729956150a6d31b84760`

Structured item scores and diagnostic categories are in `2026-09-26-bielik-panel-independent-review.json`. Public reasons contain no copied question, source or official-key passages.
