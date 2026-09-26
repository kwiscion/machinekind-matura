# Generation instructions — haiku_gen_v2

Follow `haiku_gen_v1.md` in full, with these overrides (they come from the round-1 audit, where 29% of gated items were not fully supported):

- Input `data/przemeknowak781/cache/batches/r2-NN.txt`; output `data/przemeknowak781/generated/r2-NN.jsonl`; ids `pn781-hk-r2NN-001`, ...; `prompt_revision` is `haiku_gen_v2`.
- Exactly 3 examples for EVERY source in the file; check the source count at the end.
- Per source: one `essay_plan`, one `source_analysis`, and one `chronology` or contrastive `short_answer`.
- The answer may contain ONLY what the claims say. Round-1 rejections were mostly: interpretations or consequences not in the text ("symbolizowało...", "świadczy o..."), an added place, month, or title, a sequence ("najpierw..., następnie...") the text does not state, and essay plans whose points were bare headings without facts.
- In `source_analysis`, ask about something the passage states (cause, actor, consequence, date), not about its symbolic meaning.
- In `essay_plan`, every point must contain a concrete fact taken from a claim; cite 3–6 claims.
- If a source cannot support 3 good examples, write fewer for it rather than padding.
