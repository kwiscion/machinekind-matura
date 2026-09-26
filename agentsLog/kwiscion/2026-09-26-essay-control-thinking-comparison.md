# Organizer control versus thinking essay: same-calibration audit

**Same-calibration central scores: control 7/15 [5–7] → thinking 8/15 [7–8].** The supported central change is +1, with a judgment envelope of 0–3. This is one known-validation pair, not a general improvement estimate or a blinded experiment.

The earlier historical control score is preserved. No prior per-item scorecard or adjudication file was opened. This reviewer knew the organizer aggregate 29 and current essay 8; inherited project context also mentioned the historical control essay 5. That exposure is disclosed rather than treating this as a blind regrade.

## Provenance

The control is the actual 40/40 original-template organizer-path run, not a laptop or another H100 arm. Its public handoff SHA256 is `0286692a89f2fdbfca2d87364c3e6eb0d827eafbb6f2a6d7a939fd17d79f0536`. Its exact essay matches recovered final `answers.json`, hash `b52e8981f967d3e1310ca8c53a11f7c80185ac724a81790708671145b02d97d9`; backup, raw and prepared-input hashes also verify against the published manifest. Only the essay was inspected semantically; no earlier grades were read.

| Property | Control | Thinking |
|---|---|---|
| Exact final essay SHA256 | `8b4b29d7e8604537d0fb7e1613eb1712838bb18f366de570bf20674c4a58f916` | `3f7561add3016ff2dbe830f24bdbb92d5bcfb74148d9bbdf5eb6e8261a678688` |
| Body words | 324; excludes five-token task heading | 384; all submitted words are body |
| Topic | One, topic 3 | One, topic 3 |
| Military argument | 3, borderline 1–3 | 3 |
| Diplomatic argument | 1 | 1 |
| Political-system argument | 1 | 1 |
| Factual deduction, central | −1 | 0 |
| Coherence | 3 | 3 |
| Total, central | 7 | 8 |

Both clear the official 300-word coherence threshold. The thinking essay misses its additional requested 400–500-word target; that is not a separate official penalty. Task headings alone do not lose coherence points.

## Evidence, errors and grading threshold

The control already explains that turning paramilitary organizations into an armed force enabled seizure of authority in 1918 and defense of sovereignty. This links a concrete formation to the thesis. Central grading awards satisfactory military argumentation, 3 points, under the same standard used for the newer essay. It is borderline because the remaining correct support is thin and lacks a specific operation or political transfer. A reviewer may place it at superficial 1, giving total 5. That is the principal adjudication question; neither a named battle nor a prescribed event list is automatically required for 3.

The control's claim of Legion fighting on Russian, German and Austrian fronts is false as a characterization of the campaign under Piłsudski. The [Sejm Library exhibition](https://biblioteka.sejm.gov.pl/file/czas_przelomu/m_pl.html) identifies fighting Russia alongside the Central Powers; the [Polish Army Museum](https://muzeumwp.pl/timeline/kryzys-przysiegowy-w-legionach-polskich/) distinguishes the subsequent oath crisis and breakdown of the formation. Isolated later conflicts involving former Legion elements do not validate the submitted regular three-front account. Count this as one factual error, deducting one point once. Do not count the three named fronts as three errors or automatically reduce the whole military aspect a second time.

The newer essay removes that claim and develops a more concrete 1920/Warsaw example with an explicit explanation of why victory preserved independence. That is a real evidential improvement within the satisfactory band. It does not yet reach rich argumentation. The previously documented uncertainty over collective Legion attribution and Versailles credit remains; the current 7–8 range is unchanged.

Both diplomatic paragraphs mainly assert prestige, alliances and international recognition. The new reference to Versailles is more concrete, but still supplies no demonstrated actor-action-consequence link. Both political-system paragraphs claim unity, stability and institution-building without identifying how a particular measure operated. Both therefore remain 1/1. Their organization is coherent: one thesis, three dimensions and a matching conclusion. Thin evidence is reflected in aspect grades, not an automatic second coherence penalty.

Consequently, a raw historical 5→8 subtraction cannot establish a three-point mechanism gain. Under this consistent central reading, two points can come from the military 1-versus-3 grading threshold and one from the removed factual deduction. Preserve both historical and new assessments for adjudication. Thinking, native transport, larger cap and the structural append changed together, so this pair does not isolate thinking causally.

## One mechanism for original DEV testing

Test one generic **aspect evidence-to-mechanism check before final prose**, after Paweł's frozen wave finishes. Append the following to the existing native-thinking essay prompt; it contains no benchmark facts or topic-specific examples:

> Opracuj dokładnie jeden wybrany temat. Przed napisaniem odpowiedzi sprawdź każdy aspekt wymagany w poleceniu: dobierz konkretny fakt, działanie osoby lub instytucji, które znasz dostatecznie pewnie; wyjaśnij mechanizm łączący ten przykład z ocenianym problemem; pokaż, dlaczego wspiera on Twoje stanowisko. Nie zastępuj przykładu ogólną pochwałą ani samym wymienieniem daty lub nazwy. Sprawdź, czy nie przypisujesz jednej osobie działań innych i czy przyczyna rzeczywiście poprzedza skutek. Jeśli nie jesteś pewien szczegółu, pomiń go lub zawęź twierdzenie zamiast go dopowiadać. Oddaj wyłącznie spójne wypracowanie liczące 400–500 słów: bez planu, tabeli kontrolnej, nagłówków aspektów i komentarza o wykonywaniu zadania.

Use the same model, runtime, thinking cap, temperature and source inputs on a fixed small panel of existing original DEV topics. Compare unchanged native-thinking prompt with this single append, one generation per arm/topic, without adding a rewrite chain. Freeze call/token/wall limits and topic IDs first. Assess supported argument development and new factual errors with blind labels and preserved independent scores; also retain length, one-topic compliance, coherence and cost. The instruction encourages checking, but does not provide external factual verification.

Do not copy this May 2024 question, either answer, or correction facts into the DEV prompt or training material. No model call, training write or Git mutation occurred. Companion JSON retains exact bindings, separate rubric components and the bounded test proposal.
