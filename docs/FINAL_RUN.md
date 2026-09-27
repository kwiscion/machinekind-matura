# Final run: Qwen with essay coverage

Decision prepared27September2026, before final-question access. The exact Git commit and verified cache receipt in the freeze record complete this decision. No final questions have been used for this selection.

## Selected system

Use **one Qwen3.5:9b native multimodal model**, the exact closed profile tested in the corrected full40 coverage run. It scored40/60 (32/45 nonessay,8/15 essay), completed40/40 answers in27m58s, and recovered all four initial timeouts autonomously. Gemma39/60 is retained as development evidence, outside the submitted weight set. The48/60 target was not reached; a one-point validation advantage is uncertain.

The final policy is the qualified recovery runner plus the exact generic essay coverage suffix. No RAG, image-description ensemble, factual referee, LoRA or external-model selection is enabled. The generic preparer's40 initial payloads were independently shown identical to the measured run, and its arbitrary-ID/image tests and37-item organizer mock preparation passed.

| Pin | Value |
|---|---|
| Model | `qwen3.5:9b` |
| Native manifest SHA256 | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| Closed profile SHA256 | `953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d` |
| Aggregate model/cache bytes | 6,594,475,420 across5 declared files; cap8,800,000,000 |
| Ollama | 0.34.4; executable SHA256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Initial request | context65,536; output32,768; thinking on; temperature1, top_p0.95, top_k64 |
| Essay policy SHA256 | `236e9ee6d23168b817b144a706d86a8f204fe133af568ba27c08c88c4727d763` |
| Recovery code SHA256 | `628aa6b92b76e10540d8f43bf7f186bc5c6178eae526d296c149483051f292b0` |

Retain the installed runtime/backend libraries, not merely the main executable. The central project H100 is the intended worker. Verify its idle state and the fresh Qwen-only cache; never copy the mixed development cache into the submission.

## Freeze and obtain input

Before requesting FINAL, merge the reviewed code, record the exact commit and configuration, and post the team-wide freeze on issue3. All team model/prompt/code experimentation stops. Do not open May2025 as an extra selection set.

Use the actual organizer package with its `exam.json`, linked PNGs and `answers-template.json`. Identify essay IDs from the package's explicit task type/instructions; do not hardcode26 or assume37/40 items. Preserve every original source and image. Do not manually edit answers or introduce question-specific hints.

## Prepare and run

The planned final window is **120minutes**, with the existing600-second recovery/export reserve. Start early enough to finish by10:40Warsaw, leaving time to submit before11:00. If the organizer supplies a shorter window, use the already qualified60-minute mode and record that choice before dispatch. Budget: at most4N requests and147,456N requested output tokens for N actual items; maximum120minutes is approximatelyUSD6.56 at the suppliedUSD3.28/hour rate. This is a cost ceiling estimate, not an invoice or compute purchase.

Use the [generic coverage CLI](../agentsLog/kwiscion/coverage-prep/README.md) with `--model qwen`, explicit received essay IDs and `--minutes 120`. The output path must be a fresh project-private directory. Preparation preserves the source, creates a derived package with only the tested essay suffix appended, and records both sets of hashes. Keep `PREPARED` evidence before the runtime declaration.

Declare only the actual aware-UTC start/deadline and the finite authorization envelope already stated above. Timestamp precision must be at most six fractional digits. Rerun preflight on the actual execution Python, then execute the existing `run_recovery_package.py ... --execute` exactly once through its guardian. Complete runtime commands are in the [coverage guide](../agentsLog/kwiscion/coverage-prep/README.md) and [recovery guide](../agentsLog/kwiscion/final-package-prep/RECOVERY_RUNTIME.md).

Inference runs inside the verified no-egress network namespace. Recovery, essay form checks and cleanup are autonomous. The controller preserves usable candidates, attempts up to three recovery retries, and reports any deadline-limited shortfall. Exhausted failures or explicit deadline/global-stop shortfalls use the emergency `Tadeusz Kościuszko` fallback when no usable answer exists; placeholders and unmet retry attempts remain distinguishable from recovered answers. No external agent writes, cleans or chooses model answers during the run.

## Validate and submit

Back up `results/answers.json`, status, request/reservation ledger, pins and cleanup evidence locally. The runtime checks the actual template: every ID exactly once, all answer values nonempty strings, unchanged exam_id, only permitted JSON fields, UTF-8, at most1MiB and100,000characters per answer. Review status for placeholders and unfinished recovery; preserve the exact model export.

Submit only `answers.json` through the organizer page using the team's existing account/code. Keep the returned receipt. Do not claim submission until the site confirms it. Final questions, official keys and raw reasoning stay outside public Git; our model answers and result reports may be published under the owner's sharing decision.
