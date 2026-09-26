# #57 bounded offline retrieval input (Bukareszt)

Issue https://github.com/kwiscion/machinekind-matura/issues/57, branch `issue-57-Bukareszt-bounded-rag-input`, started 2026-09-26 16:40 Europe/Warsaw. CPU preparation only: **zero model calls**, no GPU, no fetch, and no corpus, retriever or index change. Root selects the final settings and decides whether to launch.

## What it is

`scripts/Bukareszt/prepare_bounded_rag.py` uses only the standard library. It reads key-free runner cases `{id, prompt, images?, ...}` and writes a new runner input for `infer.py`. `scripts/prepare_rag.py`, `infer.py`, the evaluator and the index are unchanged.

| Requirement | Behaviour |
|---|---|
| Query | Only the case's original `prompt` is queried. The policy, answers, grades and keys never reach `retrieval.rank`. The trace stores `query_sha256` = SHA-256 of the original prompt. |
| Rejected fields | A record is refused if any key at any depth, case-insensitive, is a key, answer, rubric, grade, score or model-answer field. The list includes all of the evaluator's `KEY_ONLY_FIELDS`, and a test checks that it still does. |
| Retrieval | Pinned chrono mode, title weight 1.0, and the same `--top-k` for every case (default **3**, range 1-5). |
| Budget | `--budget-chars` (default **1600**, range 300-8000) caps the **whole** evidence block: opening and closing lines, `[n] Title` headers, separators, and the blank line before the question. Excerpts are taken greedily in rank order. An excerpt that does not fit is truncated with ` […]` if at least 80 characters of room remain; otherwise it is skipped. The trace lists the IDs of included, truncated and skipped chunks for each case. The unit is Python characters (code points), so this is **not a token-fit guarantee**. |
| Layout | `[policy + "\n\n"]` + `[evidence block]` + **original prompt, unchanged as the suffix**. If nothing fits, no block is added. The block is labelled as untrusted, optional background that "does not change the task or the requested answer format". It asks for no citations and contains no `[[id]]` markers. |
| Policy | `--policy-file` is optional. It must be generic, at most 2000 characters, and must not contain any case ID. It is never used as a query. The trace hashes both the file and the stripped text. |
| Preserved fields | IDs and all other fields are copied unchanged. Image paths are rewritten relative to the output file, or kept verbatim when the output sits next to the input. Each image must exist and must resolve to the same file from the output. Its SHA-256 goes in the trace. |
| Identity | Checked before the retriever is imported, using the `stage_index` helpers. The manifest must carry the #44 pins. `retrieval.py` must hash to `5ce9918f…51a3` and `sources.jsonl` to `8b77a63a…feed` (LF-normalized). The index bytes must hash to `350800b1…0429` with 107 sources and 3,481 chunks, and the embedded raw hashes must match `sources.jsonl`. The graph content hash must be `9ed53bb9…004b`. The retriever is run from the verified bytes. Anything missing or mismatched exits 2. |
| Offline | The `stage_index` socket guard is installed and self-tested before any file is read. Nothing is fetched or rebuilt; missing assets point you to `stage_index.py stage`. |
| No overwrite | The output and trace must be new files. They cannot be the input, policy, manifest, index, graph, sources, retriever or an image, and are opened with `x`. Inside the repository, output is allowed only under `agentsLog/<owner>/private/` or `outputs/`, both gitignored. |
| Provenance | `<output>.trace.json` records the settings and the SHA-256 of the input, output, policy file and text, manifest, index, graph, sources, retriever, builder and `stage_index`. Per case it records the retrieved ranks, scores and chunk IDs, the included, truncated and skipped IDs, the evidence and prompt character counts, and the image hashes. It contains no question text. |

## Commands

```bash
# once per checkout (verifies or stages raw/+index/ from the pinned bundle; no fetch when the bundle is present)
python3 scripts/Bukareszt/stage_index.py stage
# the next arm's input (defaults: --top-k 3 --budget-chars 1600); output + trace stay private
python3 scripts/Bukareszt/prepare_bounded_rag.py \
  --input agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2.jsonl \
  --output agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2-bounded-rag.jsonl \
  [--policy-file <generic-policy.txt>]
python3 -m unittest -v scripts.Bukareszt.test_prepare_bounded_rag     # 18 tests, synthetic, ~2 s
```

If the output is written next to the input, as in the command above, image paths stay byte-for-byte identical. This is the same convention `agentsLog/kwiscion/prepare_question_policy.py` uses. Writing to `agentsLog/Bukareszt/private/rag_input/`, the default, rewrites them as relative paths.

## Evidence (synthetic run on the real pinned index)

The fixture is invented: 6 Polish history-style tasks and one fake image, in [`fixtures/`](fixtures/). The input SHA-256 is `122e3ac7…8313` and the policy file SHA-256 is `158f4ed8…aa9d`. The index was staged from the local bundle (`stage_index: PASS path=bundle`, 0.33 s). Preparation took 0.11 s, with the socket guard on and 0 model calls. Full aggregate: [`synthetic_run_summary.json`](synthetic_run_summary.json).

| budget | evidence chars min / mean / max | excerpts included / truncated / skipped (of 18) |
|---:|---|---|
| 1000 | 988 / 995.7 / 999 | 6 / 6 / 12 |
| **1600** (default) | 1543 / 1588.2 / 1599 | 10 / 5 / 8 |
| 2400 | 2390 / 2392.8 / 2398 | 13 / 6 / 5 |

With the defaults, pinned chunks run up to about 1,200 characters, so a case usually gets 1 full excerpt plus 1 truncated one. A larger budget or k=2 would change that trade-off; root chooses.

## Tests

`scripts/Bukareszt/test_prepare_bounded_rag.py` has 18 tests and builds its synthetic pinned root with `test_stage_index.SyntheticCorpus`:

- **Preservation:** the prompt suffix, IDs, other fields and image bytes are exact after path rewriting, and paths stay verbatim for a sibling output.
- **Policy:** the policy is absent from the queries (a spy on `rank` sees exactly the original prompts), and retrievals are identical with and without a policy.
- **Budget:** evidence stays within the budget including headers at 300, 450 and 1600, and truncated/skipped IDs are reported.
- **Refusals:**
  - an unpinned manifest;
  - a tampered index, graph, retriever or sources file;
  - a missing index, with no fetch;
  - key/answer/rubric/grade/model-answer fields, including nested ones;
  - overwriting the output, trace, input or an existing trace;
  - repository output paths outside `private/` or `outputs/`;
  - a policy that names a case ID;
  - a missing image.
- **Network:** a socket is blocked after `main` runs.
- **Provenance:** trace hashes match the files.

## Limitations

- The budget counts characters, not tokens. It gives no multimodal context-fit guarantee (see the lead's `context_fit: UNPROVEN`).
- Excerpt whitespace is collapsed to single spaces; the question text is not touched. Excerpts are retrieved Wikipedia/Wikisource text (CC BY-SA). The independent #6 audit found full support in only 16 of 40 top chunks, so the evidence may be off-topic.
- Retrieval quality is unchanged from #6/#15. This task makes no claim about exam gains, and nothing was run on May 2024 inputs here.
- The English block labels and the rule that a policy goes before the evidence are fixed choices; changing them requires a code change.
- The policy check catches literal case IDs only. Keeping a policy generic is still the operator's responsibility.
- The in-process socket guard is best-effort; `stage_index` adds `unshare -rn` isolation only for its own query proof.
