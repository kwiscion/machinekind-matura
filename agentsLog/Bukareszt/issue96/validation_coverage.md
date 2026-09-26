# #96 corrected selective RAG: coverage on May 2024 question-only source-v2 (CPU, zero calls)

Built locally at 2026-09-26T19:20:11+0200 by the #96 worker, as root allowed on #96 (17:14Z):
- `bootstrap.py` produced v1 `f4df6bcb…03c7` (Poppler 26.09.0 via Homebrew, `answer_key_access: false`);
- `repair-v2.py` produced **v2 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`**, identical to the canonical hash.
The generated exam files stay in gitignored `agentsLog/Bukareszt/private/`. No keys, answers or scores were read. The router and gate see prompt text only.

Command (head of PR #104 at the time of this report):
```bash
python3 scripts/Bukareszt/selective_rag.py prepare \
  --input agentsLog/Bukareszt/private/validation_2024_keyfree/runner_input.v2.jsonl \
  --output agentsLog/Bukareszt/private/selective-rag-96/selective.jsonl --pairs 12
```

**Outputs (SHA-256):**

| file | SHA-256 |
|---|---|
| `selective.jsonl` | `b8af80f90768d7d8276bc4b184119f83fa0641f8d6c16a742ac6dfecaf02a1cd` |
| `selective.pairs-bare.jsonl` | `b083dc8f8cab5462bcdcc70bcff637ec3063fbac24e1c29f644b114b6971b203` |
| `selective.pairs-selective.jsonl` | `673eec56961da6d25f825df5136e78f6ca8e15117c9c9b79d0779f51998b4240` |

The trace is kept privately.

**Routes:** {'mixed': 20, 'ambiguous': 11, 'external_fact': 6, 'supplied_source': 2, 'essay': 1}. **Changed: 5 / 40**; the other 35 prompts are unchanged.
Pair IDs, in hash order: val2024-hist-z18, val2024-hist-z2, val2024-hist-z5.1, val2024-hist-z24, val2024-hist-z7. That makes **5 pairs = 10 calls**, not 24.

| id | route | passage inserted | gate reason | chunk |
|---|---|---|---|---|
| val2024-hist-z1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z2 | mixed | **yes** | described entity supported in passage | plwiki-aleksander-macedonski#0064 |
| val2024-hist-z3.1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z3.2 | ambiguous | no | – | – |
| val2024-hist-z4 | ambiguous | no | – | – |
| val2024-hist-z5.1 | mixed | **yes** | relation+entity in passage | plwiki-wyprawy-krzyzowe#0174 |
| val2024-hist-z5.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z6 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z7 | mixed | **yes** | relation+entity in passage | plwiki-chrzest-polski#0264 |
| val2024-hist-z8.1 | supplied_source | no | – | – |
| val2024-hist-z8.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z9 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z10 | ambiguous | no | – | – |
| val2024-hist-z11.1 | ambiguous | no | – | – |
| val2024-hist-z11.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z12.1 | ambiguous | no | – | – |
| val2024-hist-z12.2 | ambiguous | no | – | – |
| val2024-hist-z12.3 | mixed | no | too little of the question supported | – |
| val2024-hist-z13 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z14.1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z14.2 | ambiguous | no | – | – |
| val2024-hist-z15.1 | ambiguous | no | – | – |
| val2024-hist-z15.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z16.1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z16.2 | ambiguous | no | – | – |
| val2024-hist-z17.1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z17.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z18 | mixed | **yes** | relation+entity in passage | plwiki-i-wojna-swiatowa#1553 |
| val2024-hist-z19.1 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z19.2 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z20.1 | mixed | no | weak support in passage | – |
| val2024-hist-z20.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z21 | ambiguous | no | – | – |
| val2024-hist-z22.1 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z22.2 | supplied_source | no | – | – |
| val2024-hist-z23.1 | ambiguous | no | – | – |
| val2024-hist-z23.2 | mixed | no | requested relation absent from passage | – |
| val2024-hist-z24 | mixed | **yes** | described entity supported in passage | plwiki-zimna-wojna#3182 |
| val2024-hist-z25 | external_fact | no | requested relation absent from passage | – |
| val2024-hist-z26 | essay | no | – | – |

## Findings

1. **Coverage is the binding constraint.** The corrected, relation-aware lexical gate inserts evidence for only 5 items.
   - **Why most abstain:** most mixed items fail on "requested relation absent from passage".
   - **Terms that are not relations:** several of the missing "relation" terms are exam instruction or source-description vocabulary (`cytowany`, `poniższe`, `prawdziwe`, `stwierdzenie`, `załączony`, `zilustrowany`, `rysunek`), not historical relations.
   - **Terms the corpus lacks:** others are relations the pinned 107-article corpus probably does not cover.
   - **No tuning on validation:** per root's instruction I did **not** tune the lexical lists or thresholds on this validation input.
2. **One essay fix, prompted by validation structure.** Before this report, the router labelled 3 items as essays. Two of them (z4, z21) are short thesis/argument tasks. The long-form rule now also needs a composition cue (`zakończenie`/`wstęp`), and only z26 remains an essay. This is a generic structural fix, but it was noticed on validation question text, so disclose it.
3. **Recommendation for the dedicated-H100 wave:** don't spend more rounds on lexical thresholds. Better next mechanisms (question-structure-selected subsets, not answer-selected):
   - question-to-relation queries (the model rewrites the question into a compact entity/relation query);
   - retrieve-verify-answer with a model relevance check, replacing the lexical gate;
   - compact entity/date fact cards.
   The corrected selective arm is only a 5-pair control.
