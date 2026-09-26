# Native-thinking comparison bundle — run record — 2026-09-26 (owner semberecki / Piotr)

Authorized in [#95 comment 5849041941](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5849041941);
frozen launch record
[2026-09-26-rtx-native-thinking-launch.md](2026-09-26-rtx-native-thinking-launch.md)
(native Gemma thinking on the SAME six source-heavy items; fresh control
think:false/1024 total vs thinking arm think:true/10240 total; explicit
temperature 1.0 / top_p 0.95 / top_k 64 in both). Frozen before dispatch.

## Result: complete — 12/12 calls, 0 errors, 0 sampling failures, 0 unsent

- Stop reason `all_calls_dispatched`; wall **3 m 28 s**
  (start `20:41:56Z`, end `20:45:24Z`) vs the 30-minute absolute deadline.
- **Capability recorded in behavior**: every thinking-arm call produced
  nonempty thinking evidence (2,374–16,905 chars); **zero thinking appeared
  in any control call** despite explicit think:false (no violations in either
  direction); zero-generation metadata check (`/api/show` thinking levels)
  matched actual behavior.
- Native num_predict includes thinking: thinking-arm eval counts 791–5,214
  (all well under the 10,240 cap — the model stopped thinking early); control
  eval 78–473. **0 truncations, 0 length-stops, 0 empty finals** — the
  organizer's capped-thinking failure mode (ljaniec's z7 evidence) did not
  occur at this budget on these items.
- Prompt eval counts 754–1,609 (no truncation at context 32768); served
  digest `4eb23ef1…2b05c` + context 32768 asserted by the runner (fail closed)
  after first success; single response model.
- Latency: control 1.8–7.5 s; thinking 12.0–76.9 s; sum 214.0 s.
- Guards: 0 trips; no retries; $0 spent.
- Copied-source check: max 14 consecutive word overlap answer-vs-own prompt
  (2 answers, both z14.1 arms) — the flagged sequences are the "Zadanie 14.1"
  task-instruction echo ("Rozstrzygnij, czy rozkaz cytowany w źródle 1
  dotyczy…"), not source-passage copies; same classification as the
  transfer-run echoes. **0 thinking-content leaks**: all 12 published answers
  byte-equal the private final contents; no thinking field or reasoning text
  in the public handoff.

## Frozen hashes (verified before dispatch)

- Input v2 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`
  (enforced by the runner pre-dispatch; exact frozen hash).
- Question PDF `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`
  (re-verified this session after a private-dir restore; all prior raw
  artifacts intact — transfer 40 rows, multiscale 18 rows).
- Native bundle config `f06c570d6f1b09251264ebafd5c8cad4436f4a17c5a1486eb4504f8d71f9dd40`;
  native runner `61da9874d2c0ebc5d36b…` (full hash in the private manifest).
- Model blob `1278394b…895a606` + projector `675ad6e6…9842` verified
  pre-start; Ollama 0.34.4.

## Answer-only handoff (publication contract; NO reasoning)

[model-answers/gemma4-12b-val6panel-native-thinking-bundle.jsonl](model-answers/gemma4-12b-val6panel-native-thinking-bundle.jsonl)
— 12 rows (six known-validation diagnostic items × control/thinking), sha256
`ca9e92d2a341abbb4d18807b9ca557c82c93000523ee943112a977712c503321`; fields
`id`/`arm`/`answer`/`error`/`finish_reason`/`latency_seconds`. Final content
only — raw thinking is preserved privately per the authorization ("published
answer-only output should not include reasoning"). No source passages, keys,
question packs, credentials or envelopes.

## Reviewability

- Public runner copy: [native_thinking_run.py](native_thinking_run.py) (no
  exam material embedded; native payload shape + answer/usage validation
  reuse the reviewed native work, PR #133 semantics).
- Private traces (immutable): full raw responses including thinking, attempt
  ledger, manifest under the gitignored owner-private dir.
- The parked multiscale bundle and the RTX transfer control stay untouched.

## Limitations

- Six-item known-validation panel, DEV unavailable; automatic grades remain
  provisional pending root-arranged independent grading.
- A fixed 0.2-temperature multiscale baseline is not directly comparable —
  this bundle tests the organizer-inspired reasoning settings (temp 1.0 /
  top_p 0.95 / top_k 64) on both arms.
