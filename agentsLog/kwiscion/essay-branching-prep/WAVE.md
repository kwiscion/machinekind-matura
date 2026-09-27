# Executable staged wrapper — issue168

CPU implementation only; no model calls or execution authorization. `staged_wave.py` prepares a frozen portable mini-repository and uses the unchanged reviewed recovery CLI for two sequential stages. It does not implement another server, transport or retry policy. Independent review and a root queue declaration remain necessary before an actual run.

For three offered topics the first package contains four independent requests: unchanged direct control and one numerically forced draft per topic. The second package contains the complete original input plus all four explicitly fallible candidate views, and asks the same model to write one final essay. No rubric, grading or factual oracle is supplied. Every original string/image and complete candidate stays in private evidence. Only optional candidate views are capped at6000 characters, with exact length/excerpt and partial/placeholder status.

The whole wave is at most5 primary slots,20 attempts,737280 requested output tokens,3600 seconds and$3.28 proposed compute. These are ceilings, not expected usage. Two-topic inputs reduce the counts to4/16/589824. One aware-UTC start/deadline is copied into both stage declarations; the dynamic selector manifest hash is written before dispatch. The unchanged scheduler has the existing three-retry ladder and600-second recovery reserve. The controller limits the draft phase to the time remaining minus900seconds so a late selector still has an initial request window plus that recovery reserve. A phase cutoff is recorded as an operational failure, not successful retry completion.

## Prepare and dry-check

Run from the repository. All supplied sources, model envelopes and answers remain in the ignored private directory. Choose a fresh absolute destination on the eventual Linux host, the existing pinned Gemma native-cache source, pinned Ollama binary, and the **same shared host ownership lock used by other central workers**.

```sh
python -B agentsLog/kwiscion/essay-branching-prep/staged_wave.py prepare \
  --exam-dir PRIVATE_ORIGINAL_EXAM --item-id ACTUAL_ESSAY_ID \
  --output agentsLog/kwiscion/private/branching-wave/package \
  --execution-root /ABS/branching-wave \
  --cache-source /ABS/PINNED_GEMMA_MODELS \
  --binary /ABS/PINNED_RUNTIME/bin/ollama \
  --host-lock /ABS/SHARED_HOST_OWNERSHIP.lock
python -B agentsLog/kwiscion/private/branching-wave/package/staged_wave.py check \
  agentsLog/kwiscion/private/branching-wave/package
```

Preparation invokes the real adapter and qualified recovery preparation, snapshots its complete code closure and source hashes, and creates the first portable package. It performs no weight staging, network operation, namespace or model call. Ambiguous topic numbering fails preparation. Transfer the **whole** directory unchanged to the declared execution root using the existing project transfer mechanism.

## Only after root declaration and sole-worker ownership

These commands are a future recipe, not permission to run. Supply the actual root declaration reference and one current UTC interval no longer than3600seconds. Timestamps use `+00:00` and at most six fractional digits for compatibility with the host Python3.10. `declare` changes only the four declaration fields; `prepared-wave.json` remains unchanged. Freeze/hash `wave.json` after declaration.

```sh
python3 -B /ABS/branching-wave/staged_wave.py declare /ABS/branching-wave \
  --reference ROOT_DECLARATION_URL \
  --start YYYY-MM-DDTHH:MM:SS+00:00 --deadline YYYY-MM-DDTHH:MM:SS+00:00
python3 -B /ABS/branching-wave/staged_wave.py execute /ABS/branching-wave
```

The shell obtains the shared nonblocking host `flock` on inherited FD9 for the entire wave. The unchanged recovery packages retain a separate inner stage lock. An outer GNU `timeout` ends work15seconds before the absolute deadline, with5seconds kill grace and at most10seconds for owned cleanup. Each stage retains its existing guardian, namespace, source/context checks, exclusive server and recorded server/backend cleanup. The wrapper never overlaps stages. Its exclusive, fsynced `execution-once.json` prevents restart/replay; a failed wave requires a fresh declaration and fresh directory, not an automatic retry of the wrapper.

A durable exact-stage intent is written before process spawn; cleanup still works if interruption prevents PID capture. The outer interruption path stops only controllers whose arguments identify this exact frozen stage path, then invokes the existing recorded-identity cleanup CLI. It avoids protected cross-user-namespace `/proc/exe` and `/proc/ns` reads. Controller/session and backend cleanup errors are visible and prevent selection dispatch. The wrapper has not been runtime-qualified on an actual model; CPU fake operators establish orchestration, not H100 cleanup or throughput.

## Results and failure semantics

Each stage preserves the full qualified-runner ledger, raw candidate answers and statuses. `drafts-terminal.json` and `selector-terminal.json` bind the exact finals and reservation totals. `wave-terminal.json` independently recounts both durable ledgers; interrupted outer guardians write a separate `guardian-terminal.json` without claiming complete aggregate accounting. The public answer artifact is diagnostic, containing only the original exam ID, original item ID and one answer.

On a failed stage, invalid context, exhausted budget, malformed selector or partial/placeholder selector, `answers.json` preserves the exact direct control, not the retrospectively best draft. Its original partial/placeholder status is attached unchanged. If no verifiable terminal control exists, no answer is invented and the report states `no_terminal_control`. The existing runtime may already have supplied the owner's literal placeholder; that remains explicitly a placeholder, never successful recovery. Hard-interrupted stage exports are reconstructed using the existing CPU-only final-export routine from durable engine evidence.

Fresh per-stage cache views are staged only after prior quiescence, using the unchanged canonical Gemma cache helper. They contain the same pinned model/projector; no Qwen or alternative model is introduced. Hardlinks may share physical storage but every directory entry counts fully for packaging. These diagnostic cache views **must not be submitted together**: the final artifact remains one Gemma weight/projector set under8.8GB. No unowned cache is deleted or cleaned.

## CPU checks and next evidence

```sh
python -B -X utf8 -m unittest discover -s agentsLog/kwiscion/essay-branching-prep -p 'test_*.py' -v
bash -n agentsLog/kwiscion/essay-branching-prep/operator_wave.sh
```

The fake operator uses actual frozen adapter/preparation/scheduler/final-export code and synthetic400-word replies. Tests cover ordering and quiescence, shared deadlines, unchanged sources/images, exact candidate preservation, failed-stage and partial-selector fallback, no replay, reservation arithmetic and a POSIX duplicate-lock refusal. Production has no fake-provider CLI switch. No historical answer is generated during these checks.

After a declared real run, grade control, individual drafts and selector final once, masked. Report selector-versus-control and retrospective candidate oracle separately; oracle is diagnostic and cannot replace the submitted selector. Compare factual/argument/task fulfillment within the actual chosen branch; do not manufacture a common score denominator for different aspect requirements.
