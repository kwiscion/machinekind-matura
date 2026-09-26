# Failure-only answer recovery — terminal paired diagnostic

Both arms completed3/3 planned items (6calls total), with zero generation errors, unsent items, retries or extra smokes. Selection used only the parent run's actual `length` errors, yielding printed IDs12.1,19.1,25; no key, score or content routing. Independent grading now gives A1/6 and B0/6; see the [decision](2026-09-26-answer-recovery-decision.md). **These are separate recovery results, not a new full40 score or a composed candidate.** Any later full-score arithmetic using them is posthoc until a fresh integration run.

ArmA requests a fresh nonthinking final answer from the original complete sources. ArmB uses the same complete sources plus the full interrupted thinking string, explicitly framed as fallible notes rather than instructions or historical evidence. Notes were neither clipped nor replaced by a partial prior final answer. Captured payloads verified all original text, ordered image bytes and the full decoded note string. Final exported strings exactly match the actual organizer adapter outputs and native final content.

| Arm | Planned/completed | Prompt tokens | Generated tokens |
|---|---:|---:|---:|
| A — fresh final | 3/3 | 4,011 | 401 |
| B — fallible notes to final | 3/3 | 35,873 | 545 |

All six responses ended with `stop` and no returned thinking. Both arms used the same pinned Gemma4 12B Q4_K_M, Ollama0.34.4, context32768, `think:false`, `truncate:false`, `shift:false`, output cap2048, temperature omitted, and180second request timeout. Original sampling defaults remain unfixed. Actual prompt usage plus output reserve, both explicit truncation flags, model/runtime identity and sole-worker guards passed. Notes fit screening was an estimate, not a claim of exact pre-dispatch tokenization. No namespace isolation was performed or claimed.

Declared2026-09-26T20:38:16.711526UTC; first durable reservation20:38:53.427685UTC; last native response20:39:18.943936949UTC. Worker wall33.985seconds. Declared maximum6calls/12288 requested output tokens/20minutes, deadline20:58:16.711526UTC; actual946 generated tokens. Execution-time estimate$0.0310 at the supplied$3.28/hour rate, below the declared$1.10 ceiling. Actual billing remains unverified and unrelated idle-instance time is excluded.

## Exact handoffs and provenance

- `model-answers/answer-recovery-A-three.jsonl`: SHA256 `ad93976a5361179d209e67e4ed6573849bfaf0e6b829b1c13549727ae0e7b56c`.
- `model-answers/answer-recovery-B-three.jsonl`: SHA256 `fcc745275a65969ec04e54a0c4ed649d97c7da8c20e31ba3db7eeb96b2e31f5a`.
- `model-answers/answer-recovery-three.manifest.json`: SHA256 `673b90c349a7cbf92e785b4d8b6c17c4e9bc7099ed98f0da43dd7bd8f5cc4cb3`.

Each arm preserves all three source-v2 IDs and exact answers/errors. A15-word source-overlap screen found no matches; no answer text was edited. Full original-template per-arm artifacts remain privately retained, with all nonselected rows blank; they are not full40 candidate submissions.

Parent output: [full-thinking-gemma-val40.jsonl](model-answers/full-thinking-gemma-val40.jsonl), SHA256 `fdbf288a3deb276d9600a353403ac8c1aa10fc37df11ec6f0524c0d76a12bde9`. Parent raw SHA256 `8b814e4f0cd9d35a7b0635d0b62c81ef16d2694b3743373cc68af8d504e4ab78`; parent launch `2c17a930e89d0f7eb0e4f18b068aa0faf5167e72893116807869d6c8bcf0e4d5`. These artifacts remain unchanged.

Recovery runner `810773fd7ebdec581012124d4ac2f80ff93533c8ecb010f210c7d1ddec27f551`; prepared manifest `cd215325c6e80468b33907305610eb665275890d5e50ecc267e7cc130e230c2e`; actual declared manifest `d51e724ea2dedab5b4da921edc9b4546f7d4979805bd966d471bf902fd767825`. Independent review passed13 tests plus source/image and runtime-failure probes before launch.

The remote/local archive hashes match `b79503545d7690750fbb3fb3145eadabb28f7e247aefdcadd6b802385856c91d`. Raw response SHA256 `f9562485c6b36652623cca56358cc35a4601209005fcc026fc11423a70e0d67e`. All frozen code/input/image/parent hashes and request controls matched. Requests, original sources, interrupted notes and raw/provider evidence stay private.

Only one Gemma model/projector is used:7,556,497,632bytes against the explicitly assumed8,800,000,000-byte aggregate allowance. Final eligibility still requires the final packed-weight inventory. The worker exited0; existing runtime was preserved. No further inference or full40 composition was performed.
