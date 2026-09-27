# Qwen essay coverage diagnostic: prepared, not launched

Four cases use the same original corrected May2024 item26: free choice, then forced topic1,2,3. Each retains all offered topics, original source, answer format and instructions. The existing generic coverage suffix is identical; forced cases append only the numeric-choice instruction. No task-specific fact, key, grade or example enters any prompt. This is four repeated diagnostic essays, not a new60-point exam.

Actual CPU preflight and emitted initial payload checks PASS. Four synthetic tests PASS, including unchanged original source/image metadata and numeric-only differences between forced cases. All cases use the unchanged reviewed native/recovery binding and Qwen one-container profile: thinking=true, context65536, initial cap32768, T1/top_p0.95/top_k64. Up to3 recovery retries per case stay within16 total attempts/589824 requested output tokens/3600seconds/$3.28 proxy. Recovery and deadline accounting stay entirely in the shared runner. No selector or injected faults.

Prepared manifest: `0b8c2d0adf5895be2ad7504b9f0e2581ab0ac650489a6c7a835e717188aa5f73`. Private package: `agentsLog/kwiscion/private/qwen-essay-coverage-20260927-v2/package-v1`. Full runtime/prompt/builder pins and source-free mapping: [qwen-diagnostic-prepared.json](qwen-diagnostic-prepared.json).

Reproduce CPU preparation from the preserved terminal reference (choose a fresh private output):

```powershell
python -B -X utf8 agentsLog/kwiscion/essay-coverage-prep/prepare_qwen_diagnostic.py --reference agentsLog/kwiscion/private/corrected-qwen40-20260927/recovered/run/package-v1 --output agentsLog/kwiscion/private/qwen-essay-coverage-NEW --runtime-root /owned/project/qwen-essay-coverage-20260927
```

Root must review this exact manifest and declare fresh aware UTC start/deadline (at most6 fractional digits) before execution. Fresh eligible cache staging is still required: reuse only the five pinned native Qwen manifest/blob files, counting6594475420bytes; preserve the served old cache and runtime sidecars. Use the established owned lock/isolated server/guardian; never alter the original service. Preparation includes no remote write, GPU/model call or launch authorization. The ownership claim is [issue95](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5852021492).

Retain exact completed candidates and failures. Record whether each forced answer actually uses its requested topic; the unchanged shared essay validator does not enforce arm-specific topic choice. One later grading pass must judge actual submitted text and separate requested-topic adherence. A strict-ID selector could be prepared only as a separate declared follow-up; no answer rewriting or posthoc composite score is performed here.

The initial CPU-only directory is retained: importing the preparer from the archived package gave the wrong repository root and correctly failed its private-output guard. The builder now verifies the canonical source closure against that frozen archive before preparing fresh v2. No runtime guard was weakened.

Publish only the generic builder/test, this handoff and prepared JSON. The private source/package contain original exam text and must remain private. Existing suffix artifacts remain byte-identical and inactive until an explicit launch.
