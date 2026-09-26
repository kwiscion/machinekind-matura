# Organizer-path May 2024 control — CPU preparation

**Ready for root to declare a fresh 40-item / 60-point organizer-rendered control. No model answers were generated.** The actual existing adapter and runner transport preserve all source-v2 question/source strings and ordered image bytes. No shared code was changed.

This is a **locally constructed May 2024 package in the organizer schema**, not an authentic organizer-issued May 2024 package. No such package was found in the local artifacts. The organizer guide provides the May 2023 mock and says the final package has its own future download/template. Thus this preparation proves and enables the real submission **code path**, not parity with an unavailable organizer transcription or final package. It is also not prompt parity with the previously scored runner.

## Frozen input and construction

Private root: `agentsLog/kwiscion/private/organizer-control-20260926/`.

- `package/`: `exam.json`, blank `answers-template.json`, and 21 original PNGs; exam ID `history-2024-source-v2-local-control-v1`.
- `prepared/input.jsonl` and its adapter manifest: 40 model-facing records prepared by the unchanged adapter.
- `id-mapping.json` / `verified-mapping.json`: printed task IDs (`1`, `3.1`, etc.) map bijectively to `val2024-hist-z<printed ID>`, in the original order. Each carries maximum points and text/image hashes. These are scoring-join metadata, not answer keys.
- `verification.json`, `launcher-preflight.json`, `adapter-dryrun/`: CPU evidence. `control-package.tar.gz` is a private transfer bundle containing package, mappings and verification; its hash is in the adjacent public JSON.
- `synthetic-format-only/`: artificial transport/format outputs, **never model answers or a scored control**. These are excluded from the transfer bundle.

The preserved source-v2 input SHA is `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`; question PDF SHA is `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`. I extracted only that question PDF using the existing local Poppler tool, verified its parsed task text equals all 40 frozen source-v2 bodies, and read item maxima directly from its task headings: **40 items, 60 points**. No evaluator keys, marking PDF or May 2025 files were read by this task. The build/verification script installs audit guards against those file accesses and socket operations.

The original harness header is removed by exact prefix match. Each remaining body is split at the printed active-subtask heading, or at its inspected instruction boundary for single tasks. All 40 boundaries were inspected. The essay is retained wholly as its question. **Concatenating source_text + question reproduces each complete original task body exactly**, including citations, options, tables, answer slots and all essay choices. Shared-source preambles remain repeated for every relevant subtask. No task body or answer semantics were reconstructed from keys.

The adapter renders the question before the source, as designed. Original task/group heading text remains where the lossless split placed it; this is not an attempt to reproduce an organizer's editorial cleanup. Images are the existing complete page PNGs, without cropping or re-encoding: **43 references, 30 image-bearing items, 21 unique files, 10,131,216 unique image bytes**, at most two images per item. The source-v2 correction for item 13 remains present. Existing image resolution, neighboring content visible on whole pages, and extraction artifacts remain inherited limitations.

Global `instructions` contain the complete instructions from page 2 of the question sheet, without page footer/code. This is a material difference from the old harness: the sheet limits reliance on outside knowledge unless the task says otherwise; the old header generally allowed it. Physical-paper directions are also retained. The field is not a newly optimized prompt.

`answer_format` is the same generic Polish text-response instruction for every item. All detailed task-specific requirements remain verbatim in `question`. There is no authentic organizer-authored May 2024 `answer_format` available to copy, so I did not invent choices, expected labels or answer examples. This representation is sufficient for the actual adapter control, but cannot test an unavailable organizer's exact format wording.

## Identity

| Artifact | SHA-256 |
|---|---|
| Package exam JSON | `907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471` |
| Blank answer template | `aa4451a853063e3f67d1b9d281ac063ee48c112e01c3cb8712ded433253b865f` |
| Ordered printed IDs | `517208a8952bdc53b209c55831dc2ab266699956072029eae551662628446086` |
| ID/source mapping | `2882518f4936a8191fb5bfc4e5f6267d6b86b9a3dd619c9a0a7c32a9e09e8dd0` |
| Verified mapping including rendered prompt hashes | `9ebc5706245a8638c3b0abb492a45ecaea962fe9d004fce793953144ce2dfdd1` |
| Prepared input at retained relative paths | `9600f00a473c0647de87030980425519b529b42df0ab6721b45c4da8f2b0c00f` |
| Bare config, actual CRLF bytes | `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa` |

Code snapshot: `outputs/organizer-control-code-1eb8849`, commit `1eb8849902cf64c1afdd50b0d85c4c370a5f8aec`. Its infer/adapter/launcher/helper are unchanged in the shared checkout at final comparison. Exact file hashes and all 40 ID/point mappings are in [public provenance](2026-09-26-organizer-control-preparation.json). Prepared image references are relative; preparing in a different directory can change JSONL path bytes. Recompute and freeze the actual execution input hash rather than assuming it remains identical after relocation.

## CPU evidence

- Actual `matura_package.load_package/prepare` accepted the package and every source string. `infer.load_cases` encoded all images.
- **40 `infer.run_case` requests went only to an in-memory capture stub**, with socket operations forbidden. Every request retained its exact question, source and global instruction strings; decoded image bytes/order matched source-v2. One user message, output cap 1024, reasoning setting `none`, temperature omitted. All 40 prompt strings differ from the old runner by construction.
- Actual adapter `run --dry-run` invoked the existing infer CLI dry-run successfully for all 40 cases. No raw generation output was produced.
- Actual final-launcher default CPU preflight passed under Linux/WSL, without `--execute`. Its future run directory remains absent. Native Windows preflight first rejected Linux absolute runtime paths; the intended Linux execution passed. An earlier out-of-owner output path was also correctly refused before writing.
- **51 existing adapter tests passed** under Linux. Additional full-package synthetic finalization produced 40 valid entries; a truncated row plus an unsent essay yielded 38 synthetic nonempty strings and two blanks while preserving all 40 IDs. Duplicate and unknown output IDs were rejected without writing an answer file.
- Total prepared prompt text is 94,507 characters; largest is 4,515. These are character counts, not model-token/context estimates. Runtime context fit, real completion, throughput and offline H100 execution remain unproven by CPU checks.

## Commands and root handoff

From repository root, use existing code with the frozen package. These commands perform preparation/validation only; the first prepare/run directory must be fresh:

```bash
PKG=agentsLog/kwiscion/private/organizer-control-20260926/package
CFG=agentsLog/kwiscion/gemma4-12b-val40-1024.config.json
RUN=agentsLog/kwiscion/private/organizer-control-20260926/new-control
python3 scripts/Bukareszt/matura_package.py check --exam-dir "$PKG" --expect-items 40 --expect-points 60 --expect-images 21
python3 scripts/Bukareszt/matura_package.py run --exam-dir "$PKG" --config "$CFG" --workdir "$RUN" --max-calls-total 40 --dry-run
```

Do not remove `--dry-run` from that same populated work directory: the adapter correctly refuses reuse. Root's actual run declaration should use a fresh directory, freeze runtime/model/context/config and actual prepared bytes, and reserve at most **40 calls / 40,960 output tokens** for this unchanged-1024-cap control, with an enforced aggregate wall stop, cost estimate and no retries. A higher essay cap or winning route is a separately named candidate, not this control.

The existing bounded final launcher can consume this package directly:

```bash
# CPU preflight only. PROFILE must be the independently verified target-host profile.
python3 agentsLog/kwiscion/run_gemma_package.py \
  --exam-dir "$PKG" --config "$CFG" \
  --output agentsLog/kwiscion/private/organizer-control-20260926/fresh-launch \
  --runtime-profile "$PROFILE" \
  --max-calls 40 --max-output-tokens-total 40960 --wall-seconds 3600
```

The demonstrated preflight used the qualified laptop default profile only to validate CPU behavior. **Do not execute that default on H100.** Root chooses the real profile, wall bound and declared execution after host review. The unchanged launcher still has a 2,816 prompt-token acceptance guard even for a larger-context profile; CPU preparation cannot predict image-token consumption. Report any resulting failures/unsent items as zero, not a smaller denominator. The generic launcher's zero-cost field is a local-runtime assumption, not an H100 billing estimate. These existing limitations are not silently relaxed here.

After actual generation, use the adapter's `finalize` with the matching prepared manifest, then `validate` against this package. The scoring join maps each returned printed ID through `id-mapping.json`; keep the complete 40-item/60-point denominator, failed/unsent blanks, raw attempts and independent essay grading. Do not use the synthetic format-check files. No submission, organizer receipt, accuracy gain or final candidate is claimed.

The official [organizer guide](https://matura-json-guide.ania-olchowik.chatgpt.site/) was inaccessible to the web tool during this review. Its existing cached HTML was read instead (`outputs/organizers-testing-guide.html`, SHA `d2d3b0535747e8b9bf536ab8ff3e83e5eb64f74b70ab02700249ee6eb48ee859`), alongside the merged PR101 parity report, current adapter and operator runbook. No final-package assumptions were inferred from the mock's item count or identity.
