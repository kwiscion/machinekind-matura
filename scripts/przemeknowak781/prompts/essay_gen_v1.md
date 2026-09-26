# Essay-plan generation — essay_gen_v1

Write `essay_plan` TRAIN examples for the Polish history matura, grounded only in the provided source text.

## Input
A batch file with several sources. Each starts with `##### SOURCE source_id=... source_group_id=... era=... title=...`, followed by sections marked `[sekcja 'Heading']`. Use nothing but this text.

## Per source
Write 2 essay-plan examples with different theses, for example:
- evaluative: „Oceń, czy ... było ...”, „Czy ... można uznać za ...? Uzasadnij.”;
- causes and consequences: „Wyjaśnij przyczyny i skutki ...”;
- change and continuity, or comparison within the same article: „Scharakteryzuj zmiany ...”.

The prompt names the event, person, or period and the time frame, stated in the text, and asks for a plan of a matura essay.

The answer, in Polish:
1. **Teza**: one sentence answering the question, supported by the claims.
2. **Argumenty**: 3–5 numbered points; each point states a concrete fact (date, actor, decision, number) taken from a claim, followed by one short phrase linking it to the thesis. The linking phrase must not add new facts.
3. If the text supports it, one **kontrargument** or limitation, also from a claim.
4. **Wniosek**: one sentence that follows from the points. No new facts.

## Evidence
4–8 evidence items. Each `claim` is an EXACT character-for-character substring of the source text (max 200 characters, within one section), with `locator` `sekcja '<Heading>'`. Every year in the answer must appear inside a claim. Do not use your own knowledge for any fact, date, name, or number.

## Record
```json
{"id":"pn781-es-NN-001","subject":"history","split":"TRAIN","task_type":"essay_plan","source_ids":["<source_id>"],"source_group_id":"<source_group_id>","prompt":"...","answer":"...","evidence":[{"source_id":"<source_id>","locator":"sekcja '...'","claim":"..."}],"provenance":"synthetic","rights_status":"clear","era":"<era>","topic":"<title>","generator":{"provider":"Anthropic","model":"claude-opus-5-5","date":"2026-09-26","prompt_revision":"essay_gen_v1"},"audit":{"reviewer":"pending-independent","status":"pending","notes":""}}
```

## Self-check (mandatory)
Run from `D:\apps\matura`:
`PYTHONIOENCODING=utf-8 python scripts/przemeknowak781/validate.py <your output file>`
Fix every failure by copying claims exactly from the batch file or removing unsupported facts; delete records that still fail after 2 rounds. Do not create any other file and do not run git.
