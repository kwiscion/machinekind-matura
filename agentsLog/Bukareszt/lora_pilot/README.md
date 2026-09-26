# #117 finite LoRA pilot, run1: BLOCKED at stage 1 (driver bug). 0 steps, 0 calls.

- **Declaration:** root, #117, 21:07Z plus the window set at 21:24Z.
- **Preparation:** 23:35:12 → 23:52 CEST, within the 40-minute bound, with 0 calls and 0 training steps. It covered the CUDA serving build, this operator, the fixtures, the ledger and the manifest generator.
- **Review:** an independent agent reviewed the flow three times, read-only: FAIL (3 blocking), FAIL (1 blocking), then PASS. Every defect was fixed before launch. The hashes and the start and deadline were posted on #117 before dispatch.
- **Wave:** start 21:53:25Z, deadline 22:53:15Z. It ended at **21:54:09Z (44 s) with a fail-closed stop in the `probe` stage**, rc 1.
- **Evidence:** the terminal line was written and the backup was verified (`run1_evidence/`, checked against `BACKUP_SHA256SUMS`). The GPU is idle afterwards and no process is left.
- **Counts:** synthetic optimizer steps 0, history steps 0, generation calls 0 (no ledger was created), peak CUDA memory 0 (the model was never loaded).

## Cause: root's driver `run_real_pilot.py` (`3d466395…`) at line 88

In the synthetic-probe branch, `tokenizer.apply_chat_template(..., tokenize=True, ...)` returns a `BatchEncoding` under the pinned transformers 5.18.0.dev0 (`96331a9f`), not a list. As a result, `prefix + answer` raises `TypeError: unsupported operand type(s) for +: 'BatchEncoding' and 'list'`.

The mocked tokenizer in `test_real_pilot.py` returns a list, so the tests did not catch this.

A tokenizer-only CPU check on the pinned base confirms the fix: `apply_chat_template(..., tokenize=True, add_generation_prompt=True, enable_thinking=False, return_dict=False)` returns a list. Its 30 ids are identical to `prepare.py`'s path (`tokenizer(apply_chat_template(..., tokenize=False), add_special_tokens=False)['input_ids']`) and to `BatchEncoding['input_ids']`.

The history branch uses `prepare.tokenized_record` and is not affected.

## Not done, per the declaration

There was no retry, no local patch of root's driver and no extension. Stages 2–6 never ran. Root owns the driver fix and any new declaration. The frozen operator, fixtures and pins can be reused unchanged, apart from the new driver hash in `make_manifest.py` `EXPECT` and in `pins.sha256`.
