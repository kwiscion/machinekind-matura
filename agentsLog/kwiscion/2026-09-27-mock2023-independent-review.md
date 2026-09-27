# Independent review: organizer mock compatibility (#170)

**PASS for the exact CPU implementation below. No remaining blocking finding.** This is package/request/export compatibility, not inference quality, throughput, GPU, network isolation or submission evidence. No model/server calls, remote mutation, submission, keys or final-exam access occurred.

The actual organizer README requires all 37 string IDs, complete question/source text and every linked PNG, one chosen essay topic number plus the essay, and exact answer-only schema. Independently reran the real package preparation, dry preflight, fake-provider execution and final export: 37 replies / 37 nonblank entries, 60 points, all 29 linked references to 19 PNGs byte/hash-equal, all original question/source/format strings preserved. Output is explicitly synthetic and private. Dynamic bounds are 148 attempts and 5,455,872 requested tokens; no hardcoded 40-item runtime assumption was introduced.

## Findings resolved before this approval

- A valid `2. body` prefix and Markdown topic headers were initially misclassified as missing a number. Leading blank lines also caused a standalone heading to inflate the essay body count. The final parser recognizes plain, inline, leading-blank and conventional Markdown labels without transforming stored/submitted answer strings. Independently checked all four forms at the consequential 299-word boundary; each reports 299 body words and the under-300 warning. Tests also cover 400 body words, multiple distinct topics, and a four-digit year that must not become a topic number.
- An explicit optional topic number could previously trigger required-number repair. Narrow negative/optional-format handling now passes; the existing May2024 generic answer format remains false and the actual 2023 required format true. Detection reads the adapter answer-format section, and nonessay diagnostics remain unchanged. This remains a conservative Polish-format heuristic, not a general natural-language contract parser or factual grader.
- Whole-file newline churn in the native runner was removed. Its semantic diff is just the conditional instruction to retain the required chosen-topic number; native runner diff is now 2 insertions / 1 deletion. Existing source newline conventions are preserved.

Mechanical ranking, repair warnings and durable replay all use the same topic-number requirement. A selected essay number remains in the exact final string. Minimum 300 body words and advisory requested 400–500 range remain distinct. Attempt count, model caps, absolute deadline, source/image preservation, ownership and cleanup mechanisms were not expanded. The updated selection-policy binding prevents silent replay across policy versions. The new CPU-check script is deliberately a fixture-specific 37-item check; its hardcoded assertions are not runtime constraints on arbitrary organizer packages.

## Independent checks and retained failure

- Final scheduler suite: **25/25 PASS**. Native package suite: **14/14 PASS**. Recovery binding suite: **8/8 PASS**. Additional independent heading-boundary and optional/other-exam probes: PASS.
- Fresh successful actual mock check: `agentsLog/kwiscion/private/mock2023-independent-cpu-fixed-20260927/package`. Prepared manifest SHA `1c7aa5f7e21474e06e9251bd9ee546aee5528269d86a69165d7808e90996791c`; final synthetic answer SHA `27db851068eca04de86eeffa21160ecd150bc4df8f6b249caf59961c5b483e91` (19,525 bytes). Essay retains `Temat 2.` and 400 body words. The real runtime validator and adapter validator accepted the exported file.
- Initial independent fake-provider attempt at `agentsLog/kwiscion/private/mock2023-independent-cpu-20260927/package` stopped after 18 completed synthetic replies with Windows `PermissionError: [WinError 5]` during `os.replace(answer-status.json.tmp, answer-status.json)`. Its files are preserved. The fresh run passed without a code workaround or escalation. The cause of that OS permission failure is **not established**; contention is not a confirmed diagnosis.
- Reviewer inspected current report and code; site-JavaScript-validator success is the author's preserved evidence, not a separately rerun independent browser check. No live exam solutions were generated or read for this review.

## Frozen reviewed files

| File under `agentsLog/kwiscion/` | SHA-256 |
|---|---|
| `final-package-prep/recovery_harness.py` | `628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0` |
| `final-package-prep/run_native_package.py` | `60393fc61705efb8bdeaf8348ac6fd754bc8a4c0ad1efe142b7c6c39846cda6f` |
| `final-package-prep/test_native_package.py` | `90eacd5223c41f00aa8842cd4b91335e98e7b3304b19ce2ebd876d58525e38bb` |
| `final-package-prep/test_recovery_harness.py` | `5397960a146619b2a945606f0fcb3e9f134c9fcfb7e5078fb578cd5765357231` |
| `mock_package_cpu_check.py` | `d9d3533dadf31d98d47280e062a9a5e8112ffa15f464ba8e988b567242468b75` |

Hashes are exact reviewed file bytes. Frozen existing inference packages remain unchanged. Root owns publication and any subsequent execution declaration.
