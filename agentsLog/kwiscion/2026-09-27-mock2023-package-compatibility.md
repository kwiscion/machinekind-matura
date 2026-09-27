# Supplied2023 mock: verified CPU package compatibility

**PASS for preparation, request construction and exact answer export.** The actual supplied `data/history-2023-mock-v1` passed the real organizer adapter, current recovery preparation, portable dry preflight, a37-reply synthetic-provider run, qualified final validation and the saved site JavaScript validator. No model/server/GPU/network call, upload, submission or FINAL access occurred. Synthetic answers are unmistakably marked and remain private; they are not exam solutions or quality evidence.

## Exact package and evidence

- Exam ID `history-2023-mock-v1`;37 string IDs,60points;19 unique PNGs,29 linked image references on23 items. Every original question, source text, answer-format field and linked image byte/hash reaches the constructed request. The syntax-only warning accompanies format examples.
- `exam.json` SHA256 `0d4559be6ffae26304b102d8cec14814849caec879fd53d8be0196f24116354c`; template SHA256 `35675b9a7766d2b5314188796b5d26fc97c75d9cd65a0bd8612cb74bdf81d9c0`. All19 image hashes and the README hash are recorded in the adjacent JSON, without source text/images.
- Both CLI preparation and dry preflight report148 maximum attempts and5,455,872 worst-case requested output tokens for37 items. This is derived from item count, not hardcoded40. The envelope is preparation metadata, not generation authorization.
- Prepared manifest SHA256 `0740821095a577ff5cf7618944ab1c226da35b6d0954601f4ee7c57977d2b366`. Actual fake-provider export is19,525bytes, all37 entries nonblank, exact original exam ID and template order. It contains only `exam_id`/`answers`, each entry only string `id`/`answer`. Export SHA256 `27db851068eca04de86eeffa21160ecd150bc4df8f6b249caf59961c5b483e91`.
- The saved site validator returned0 errors and0 blanks, with actual file size also checked against1MiB. Current qualified runtime validation counts Unicode codepoints, allows at most100,000 per answer and checks actual UTF-8 file bytes. The older standalone adapter validator is more conservative for astral Unicode because it counts UTF16 units; the qualified runtime export does not inherit that mismatch.

## Small generic correction

There was no code stripping a topic number. The material bug was that a valid single `Temat2.` or `Temat3.` heading triggered a multiple-topic warning, so mechanical repair could prefer removing required content. Current-source diagnostics now accept one selected-topic heading, detect distinct multiple headings, and count body words without a standalone topic label. When the original adapter answer-format field explicitly requires a topic number, its absence triggers repair and affects mechanical retention. The initial essay instruction and repair instruction explicitly preserve the required number. No historical facts or exam-specific topic choice were added.

The synthetic essay retains `Temat2.` plus400 body words through retry, replay and final export. The official task minimum300 and the user's stricter400–500 target remain distinct; the latter is an advisory repair target. A deadline-limited partial/fallback may still fail essay length, with status preserved honestly rather than inventing content.

Edits were coordinated with the active runtime owner. Only current source and tests changed: `final-package-prep/recovery_harness.py`, `test_recovery_harness.py`, `run_native_package.py`, `test_native_package.py`; plus the new owned CPU check script. Existing frozen packages and current binding/Qwen profile files were not changed.

## Reproduce the CPU evidence

Run from the repository root; outputs must be fresh. The first command validates the supplied package. The second executes the actual preparation/export path with a local Python fake provider; it never invokes a model executable.

```powershell
python -B -X utf8 scripts/Bukareszt/matura_package.py check --exam-dir data/history-2023-mock-v1
python -B -X utf8 agentsLog/kwiscion/mock_package_cpu_check.py --exam-dir data/history-2023-mock-v1 --output agentsLog/kwiscion/private/mock2023-cpu-check-fresh/package
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/final-package-prep -p test_recovery_harness.py -q
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/final-package-prep -p test_recovery_binding.py -q
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/final-package-prep -p test_native_package.py -q
```

Results:23 scheduler tests,8 binding tests and14 native-package tests passed. The new tests exercise accepted topic2/3 headings, multiple-topic detection, missing-required-number repair, exact final number preservation and replay. Existing binding tests cover100,000-codepoint strings and file-size/schema limits.

The preserved CPU run is `agentsLog/kwiscion/private/mock2023-cpu-compatibility-20260927/package`; its synthetic output is `results/answers.json`. A separate `package-dry` retains the equivalent PREPARED package without results, and its actual CLI dry preflight passed.

## Later live CLI, after root queue declaration only

Use a reviewed fresh eligible Gemma cache and actual pinned runtime paths. Do not use CPU-placeholder paths or synthetic answers. On the preparation host:

```sh
python -B -X utf8 agentsLog/kwiscion/final-package-prep/prepare_recovery_package.py --exam-dir data/history-2023-mock-v1 --output agentsLog/kwiscion/private/mock2023-live/package --essay-id 26 --cache /ABS/FRESH_ELIGIBLE_CACHE --binary /ABS/PINNED_RUNTIME/bin/ollama --lock /ABS/OWNED/offline.lock --minutes 60
python -B -X utf8 agentsLog/kwiscion/private/mock2023-live/package/run_recovery_package.py agentsLog/kwiscion/private/mock2023-live/package
```

Transfer the frozen prepared package by the established project mechanism. Root must declare exact148calls/5,455,872requested-token/60-minute bounds, common aware-UTC start/deadline and authorization before execution. Only then, on the Linux runtime host:

```sh
python3 -B /ABS/FROZEN_PACKAGE/run_recovery_package.py /ABS/FROZEN_PACKAGE --execute
```

The unchanged guarded runtime writes the actual final file to `/ABS/FROZEN_PACKAGE/results/answers.json`, with separate status/ledger/cleanup evidence. The number in `--essay-id26` is read from this supplied package; arbitrary package IDs continue to be explicitly operator-mapped. No live37-item throughput, history accuracy or visual interpretation was tested here. This report authorizes no execution or submission.

## Independent-review follow-up

The narrow parser follow-up accepts a leading inline `2. body`, blank lines before a heading, `**Temat 2.**`, and `# Temat 2`, without modifying answer strings. The heading is excluded from body words, including the299/300 boundary. Explicit optional/not-required topic-number formats do not trigger a repair. All four edited source files retain their HEAD newline convention; the native runner diff is three lines.

Current validation:25 scheduler tests pass; the earlier8 binding and14 native tests remain applicable. A fresh actual37-item CPU-only adapter/preparation/export check passes at `private/mock2023-cpu-compatibility-20260927/review-final2/package`, manifest `1c7aa5f7e21474e06e9251bd9ee546aee5528269d86a69165d7808e90996791c`. All29 image references and original prompt/format strings are preserved; synthetic output bytes/hash remain unchanged. One preceding CPU attempt (`review-final`) hit Windows WinError5 during atomic status-file replacement and is preserved; the separate fresh rerun passed without a code workaround. Frozen prior packages are unchanged. The JSON report binds current source hashes.
