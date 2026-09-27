# Matched coverage-prompt pair

`matched_pair.py` prepares two independent one-item packages with the same original item ID, metadata, template, source text and images. Only the candidate's question appends `coverage_suffix.py`; the shared generic essay suffix and runtime settings remain identical. The unchanged direct control is regenerated to avoid old-request parity assumptions.

The executable controller imports the reviewed branching `Operator`, stage declaration, ledger reconciliation and exact owned cleanup. It uses the same shell flock/absolute GNU-timeout guardian and sequential source-complete recovery CLI; it does not implement a model server. Eight attempts and294,912 requested-output tokens are the aggregate worst-case bound under one60-minute deadline. The first arm receives at most half the remaining stage wall time, leaving the second a useful window; both retain the original absolute deadline and600-second recovery reserve.

```powershell
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/essay-coverage-prep -p test_matched_pair.py -v
python -B -X utf8 agentsLog/kwiscion/essay-coverage-prep/matched_pair.py prepare --exam-dir EXACT_PRIVATE_ONE_ITEM_PACKAGE --item-id ACTUAL_ID --output FRESH_PROJECT_PRIVATE_DIRECTORY --execution-root EXACT_LINUX_DIRECTORY --cache-source PINNED_CACHE --binary PINNED_BINARY --host-lock SHARED_HOST_LOCK
```

Dry `check` is the default next step. `declare` requires an aware UTC start/deadline with at most six fractional digits, exact root authorization and immutable code/source pins. `execute` requires the guarded Linux path and inherited lock; a durable exclusive marker rejects replay. A failed cleanup/integrity assertion stops the next arm. Ordinary model failures remain explicit stage evidence, not claimed successful answers. Each stage preserves exact original-template answer files and all attempts; final scoring uses one masked pass on the two exact finals.

Focused tests:2/2 passed, exercising actual adapter/fake-provider sequence, source/image/ID preservation, common deadline, no replay and failure-before-second-worker behavior. Remote Python3.10.12 preparation/drypreflight also passed. The actual current run is declared on issue168 comment5852004326; its immutable remote package differs from this living source folder. No source edits may alter that package.
