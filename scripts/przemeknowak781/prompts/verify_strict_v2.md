# Strict verification rubric — verify_strict_v2

Two independent judges review each record, each through ONE lens. A record is accepted only if both lenses pass. Input records contain `task_type`, `topic` (article title), `prompt`, `answer`, and `evidence` (verbatim claims already confirmed to be substrings of the pinned source revision, with section locators). Judge only against the claims; the article itself is not provided. Do not approve anything because you know it to be historically true.

## Lens S — evidence support
Pass only if ALL of these hold:
1. Every date, number, name, title, place, office, causal link, and sequence in the answer is stated in the claims, or follows from them without any added knowledge.
2. No interpretation, evaluation, motive, or consequence goes beyond what the claims say. Evaluative adjectives ("katastrofalny", "największy") count as unsupported unless a claim says so.
3. Nothing in the claims is misread, swapped, or merged incorrectly (e.g., two simultaneous titles presented as a sequence).
4. The prompt does not presuppose a false or unsupported fact.
Output `unsupported`: list each offending fragment verbatim from the answer or prompt.

## Lens Q — exam quality
Pass only if ALL of these hold:
1. The prompt is a complete, grammatical Polish question or instruction that a student could answer without seeing the claims: it names the event, person, or period it asks about (not "Kto dowodził wojskami polskimi?" with no battle named). A quoted passage in `source_analysis` counts as context.
2. The answer fully answers the prompt (all requested parts; an `essay_plan` asking for N points has N points; a chronology item gives the order asked for).
3. The answer is correct, fluent Polish: no stray non-Latin characters, no garbled or telegraphic fragments, no English.
4. The `task_type` fits (a `source_analysis` item analyses a passage; an `essay_plan` has a thesis-driven numbered plan with a fact in each point; `chronology` is about order or dates).
5. It is not trivial echo (the answer just repeats the quoted passage) and not a question whose answer is the prompt's own text.
Output `issues` as short codes from: `prompt_not_standalone`, `prompt_garbled`, `answer_incomplete`, `language_error`, `wrong_task_type`, `trivial_echo`, `other:<note>`.

## Amendment 2.1 (applies from round B)
Round 1 judges failed answers only because a claim fragment did not repeat its subject (e.g., "Bitwa rozpoczęła się 13 sierpnia 1920" taken from the article „Bitwa Warszawska”). From round B, the record's `source_titles` (the titles of the cited articles) count as evidence for WHICH event, person, or institution the claims describe. It does not support any other fact: dates, numbers, actors, causes, and evaluations must still come from the claims.

## Output per record
`{"id": "...", "pass": true|false, "notes": "<fragments or issue codes; empty if pass>"}`
