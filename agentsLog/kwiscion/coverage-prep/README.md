# Generic final coverage preparation

This additive CPU-only wrapper applies the **exact tested coverage suffix** to explicit essay IDs in any organizer package. It does not classify by historical content, item number or score. Choose one model; Gemma and Qwen together exceed the aggregate weight limit. No model calls or execution authorization are created by preparation.

```sh
python -X utf8 agentsLog/kwiscion/coverage-prep/prepare_coverage_exam.py --exam-dir PRIVATE_ORGANIZER_DIR --output agentsLog/kwiscion/private/final-coverage/package --model qwen --essay-id ACTUAL_ESSAY_ID --cache /fresh/private/qwen-only-cache --binary /owned/runtime/bin/ollama --lock /owned/offline.lock --minutes 60
python -X utf8 agentsLog/kwiscion/private/final-coverage/package/run_recovery_package.py agentsLog/kwiscion/private/final-coverage/package
```

Use `--model gemma` for the reviewed Gemma default, repeat `--essay-id` for multiple essays, or use `--no-essay` instead. `--minutes 120` is the explicit longer window. IDs/counts come solely from the supplied package. The unchanged recovery envelope is four attempts and147,456 maximum requested output tokens per item,65,536 context,600seconds recovery reserve, no injected faults. Gemma sampling remains omitted; Qwen uses the reviewed T1/p0.95/k64 profile.

The original source directory is never edited. A fresh sibling `package.coverage-source` contains only adapter-required files: the same template and complete images, and an exam where only selected `question` strings have the suffix appended. No keys or unrelated files are copied. `coverage-provenance.json` records original/derived file hashes, explicit IDs and exact suffix/preparation pins. The runtime copies these complete derived sources and pins every package file; unchanged runtime code retains its existing dependency checks. Existing destinations, duplicate/unknown essay IDs and changed preparation pins fail closed. Preserve failed preparation directories; choose a fresh output instead of overwriting them.

For execution, follow [the existing runtime guide](../final-package-prep/RECOVERY_RUNTIME.md): stage a fresh **single-model** cache with verified full manifest/blob inventory, transfer the frozen package, preserve its PREPARED manifest, and declare the actual finite budget/deadline using aware UTC with at most six fractional digits. Rerun dry preflight on the execution Python after declaration. Execute only once through the existing guardian:

```sh
python3 -B /fresh/private/package/run_recovery_package.py /fresh/private/package
python3 -B /fresh/private/package/run_recovery_package.py /fresh/private/package --execute
```

The existing owned-server isolation, timeout quiescence, retries, checkpoint preservation, nonblank fallback and final schema/byte-limit checks are unchanged. Final answers are `results/answers.json`; retain status, reservations and cleanup evidence. Requesting FINAL freezes team code/prompts/settings, so prepare and freeze the selected model and this wrapper beforehand. This wrapper adds no new quality claim; measured runs and CPU preparation checks are distinct.

Checks: `python -X utf8 agentsLog/kwiscion/coverage-prep/test_prepare_coverage_exam.py` — four tests pass, including arbitrary IDs/images, no-essay Qwen, invalid IDs/pin mutation, and all37 organizer DEV mock items through actual preparation/preflight. No GPU or network calls.
