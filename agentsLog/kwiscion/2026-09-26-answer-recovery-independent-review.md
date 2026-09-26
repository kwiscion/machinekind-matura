# Answer-recovery preparation — independent review

**PASS for the exact frozen v2 candidate below; no execution authorized by this review.** The initial control mismatch was repaired before freezing: a nonempty returned thinking field now causes systemic stop/blanking when both arms declare `think:false`. Absence or an empty thinking field remains valid. No other blocking finding remains in the reviewed scope.

| Artifact | SHA256 |
|---|---|
| Runner | `810773fd7ebdec581012124d4ac2f80ff93533c8ecb010f210c7d1ddec27f551` |
| Preparation | `5fafccc11e2cccabe9e92abd7313ae0cf3ca182583921cfd309a94ac4660be10` |
| Tests | `b9e0da3e8de184d45b0a9c73c2e466f914c7495c73fc73387a150c658efbcd19` |
| Prepared private v2 manifest | `cd215325c6e80468b33907305610eb665275890d5e50ecc267e7cc130e230c2e` |

Selection recomputes the three eligible rows from actual terminal `length`/`empty_final` errors in original input order. It does not route by known ID, question content, score or key. Parent raw/launch/code/source hashes are pinned, and selected inputs are compared structurally for exact equality. Original text and ordered encoded images remain present in both arms. ArmA is a fresh nonthinking answer; armB adds complete original thinking as an explicitly fallible JSON-framed note message. Partial prior final answers are not substituted for notes.

Malformed or conservatively over-budget notes retain an armB failed zero without clipping or a replacement call. Notes screening is clearly an estimate; native no-truncation controls and actual returned prompt count plus2048 provide runtime rejection gates, not a proof of tokenization fit before dispatch. Both explicit truncation flags and malformed flag types stop. Identity, usage, completion state and unexpected thinking failures cannot become a successful answer.

The actual organizer adapter finalizes each arm against the original full template; each selected-arm handoff retains all three planned IDs, including failed/unsent blanks. Unselected template rows remain blank and are not additional experimental successes. Synthetic tests confirm these exact behaviors.

Bounds are fixed at6calls,12288 requested output tokens,20minutes,180second per-request timeout, no retries/smokes, one pinned Gemma. Every dispatch requires the remaining full timeout plus5seconds. The existing owned lock, process/executable/environment/GPU checks, cold native-worker detection, full Gemma/model-projector blob hashing, runtime context/identity snapshots, hard alarm and killable HTTP subprocess remain enforced. Reservations are fsynced before transport. Returned runtime failure preserves the raw response but exports a blank and stops later dispatch. Single Gemma plus projector is7,556,497,632bytes against the explicitly assumed8,800,000,000-byte aggregate allowance; final packed inventory is still a separate release check.

Evidence:

- 13 supplied tests independently passed on Windows and WSL Linux.
- Exact private package-v2 default file-only preflight passed (`PREPARED_NOT_AUTHORIZED`, executefalse).
- Independent network-prohibited probe used actual `infer.load_cases` and native image serialization to verify original Unicode text, decoded image bytes/order, full decoded notes, a durable reservation before send, and post-response runtime failure blanking/stopping while retaining raw content.
- The original unexpected-thinking acceptance was independently reproduced, then the final regression and production condition were checked at the stated hash.

Commands: `python -X utf8 agentsLog/kwiscion/answer-recovery-prep/test_recovery.py`; Linux equivalent with `python3 -B`; independent probe `python3 -B outputs/reviews/answer-recovery/probe.py`. No model call, service change, key access, teammate-file edit or Git mutation occurred during review. Root must freeze actual runtime identity/deadline and authorize any future launch; this review does not change prior full40 outputs.