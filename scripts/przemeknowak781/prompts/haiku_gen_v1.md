# Generation instructions — haiku_gen_v1

You write Polish-history matura TRAIN examples grounded ONLY in the source text you are given. Working directory: `D:\apps\matura`.

## Input
Read `data/przemeknowak781/cache/batches/batch-NN.txt` (NN is given in your task). It contains several sources. Each starts with a header line:
`##### SOURCE source_id=... source_group_id=... era=... title=...`
followed by sections marked `[sekcja 'Heading']`. Use nothing except this text. Do not use your own knowledge to add facts, dates, names or numbers.

## Output
Write exactly 3 examples per source to `data/przemeknowak781/generated/batch-NN.jsonl`: one JSON object per line, UTF-8, no blank lines, no comments. Do not create or edit any other file and do not run git.

Per source, the three examples must use different task types, chosen from:
- `short_answer` — contrastive where possible: confusable rulers, names, sides, or dates ("Nie pomyl ...").
- `chronology` — ordering events, which came first, or correcting a student's false statement that contains a wrong date or swapped order (distractor).
- `source_analysis` — quote a short fragment (max 250 characters) of the source text in the prompt, attributed as a passage from an encyclopedic article, and ask for an interpretation, cause, or consequence.
- `essay_plan` — a numbered plan with 3–5 points for an essay thesis, each point backed by a specific fact.

At least one of the three must be `chronology`, `source_analysis`, or `essay_plan`. Avoid trivial single-fact trivia when the text supports something richer. Prompts and answers are in Polish, written the way a matura answer should read: concise, precise, with justification.

## Record schema (all fields required)
```json
{"id":"pn781-hk-NN-001","subject":"history","split":"TRAIN","task_type":"chronology","source_ids":["<source_id>"],"source_group_id":"<source_group_id from header>","prompt":"...","answer":"...","evidence":[{"source_id":"<source_id>","locator":"sekcja 'Heading'","claim":"<verbatim substring>"}],"provenance":"synthetic","rights_status":"clear","era":"<era from header>","topic":"<title from header>","generator":{"provider":"Anthropic","model":"claude-haiku-4-5","date":"2026-09-26","prompt_revision":"haiku_gen_v1"},"audit":{"reviewer":"pending-independent","status":"pending","notes":""}}
```
- `id`: `pn781-hk-NN-` + 3-digit counter within your batch.
- `evidence`: 1–6 items. Each `claim` is an EXACT copy-paste substring of the source text, at most 200 characters. Do not fix typos, change punctuation, drop words, or join text across sections. The `locator` names the section the claim comes from.
- Every fact in `answer` must be supported by the evidence claims. Every year that appears in `answer` must appear inside one of the claims.
- Escape double quotes inside strings as `\"`, or use Polish quotes „...”.

## Forbidden
Do not reference or imitate the May 2023, 2024, or 2025 matura exams. Do not invent sources, quotes, or statistics.

## Self-check (mandatory)
Run:
```bash
PYTHONIOENCODING=utf-8 python scripts/przemeknowak781/validate.py data/przemeknowak781/generated/batch-NN.jsonl
```
For every failure, fix the record by copying the claim exactly from the source or by removing the unsupported fact from the answer. If it cannot be fixed, delete that line. Re-run the check. Stop after at most 2 fix rounds; delete whatever still fails.

## Final reply
One line only: `batch-NN: written <n>, passed <n>, deleted <n>, main failure types: <short list>`.
