# Final launcher prompt budget follows the verified context

The generic launcher previously rejected any response reporting over 2,816 prompt tokens, including runs using a frozen and runtime-verified 32,768-token profile. The request loop now receives `context_length` explicitly from the validated inner profile and accepts at most `context_length - 1024 - 256` prompt tokens. The output reservation remains 1,024; headroom remains 256. No context, sampling or profile default changes.

The default 4,096 context still accepts 2,816 and rejects 2,817. A verified 32,768 context accepts 31,488 and rejects 31,489. Invalid context arguments fail before any request reservation. Runtime digest/context verification, malformed usage checks, truncation flags, call/time limits, raw-error retention and blank failed/unsent output handling remain in force. The case-local error classifier is unchanged.

CPU verification in an isolated worktree:

```bash
PYTHONPATH=agentsLog/kwiscion python3 -B -m unittest \
  test_final_offline test_runtime_profile test_offline_rehearsal
```

**38 tests passed in 92.163 seconds** under local Linux/WSL. Added checks cover both exact boundaries and one-token overflow, invalid contexts, and larger-context failures for malformed/negative usage, truncation and runtime mismatch. Existing mocked inside-launch tests now assert the profile context is explicitly threaded to the loop; actual-server context mismatch remains rejected. `git diff --check` passed.

This is CPU correctness evidence, not H100 context-fit or offline runtime qualification. No model, GPU or remote-host calls, exam material, training writes or shared-checkout changes. Independent exact-head review is required before root merges or launches the new organizer control. The earlier organizer preparation remains frozen at its original revision.
