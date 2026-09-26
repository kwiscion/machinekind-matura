# Winning plan

Owner: @kwiscion. Current decision: **26 September 2026, evening acceleration (18:30 Europe/Warsaw)**. Consult this before dispatch, scope changes, accepting results and reporting progress. GitHub issues are the live scheduling authority; newer explicit owner decisions prevail. [Earlier checkpoints](agentsLog/kwiscion/2026-09-26-plan-history-through-1608.md) remain historical.

## Strategy: central diagnosis, parallel experiments

**Keep one central failure audit and distribute distinct improvement experiments across the available GPUs.** Do not spend every teammate's budget repeating the same full audit. Each experiment owner adds evidence from their own slice; an independent reviewer grades the resulting answers. Root integrates the findings and protects the unchanged fallback. The owner has explicitly resumed intensive work.

The Astra [40-case audit](agentsLog/kwiscion/2026-09-26-failure-audit-astra.md) is the shared diagnosis. Missing-point opportunity accounts: visual recognition/localization 5, independent source comparison 3, historical entities/relations 7, contradictory commitments 3, essay quality 7. These are observed symptoms, not additive guaranteed gains. [Routing and retrieval diagnostics](agentsLog/kwiscion/2026-09-26-routing-evidence.md) identify bibliography-year contamination in the current whole-prompt retrieval query. There are no guaranteed free formatting points.

Route by **answer form AND evidence needed**: choice/PF, short identification, decision+justification, essay; supplied-source, external-fact, or mixed evidence. Derive routes only from question/source structure, never evaluation keys or validation IDs. Ambiguous cases retain the bare fallback. Exclude essays from initial RAG experiments; first test an essay-specific prompt, then an independently trained essay-only adapter if feasible. Keep the base model for other tasks.

## Objective and honest current result

Deliver the strongest measured offline system for Sunday's exam. **48/60 (80%) remains the target; the Saturday 18:00 target was missed.** Final freeze: Sunday 27 September at 11:00 Europe/Warsaw. Highest final score is the only competition track.

| Arm | Provisional independent score | What it establishes |
| --- | ---: | --- |
| Laptop bare Gemma 4 12B Q4 | **35/60 [28,40]** | Best observed fallback; corrected source-v2 evidence is a labeled 39+1 composite |
| RTX bare Gemma, source-v2, Ollama 0.34.4/context 32768 | **34/60 [25,39]** | Fresh 40/40 control in **146.6 seconds**; fast iteration is practical, formal quality equivalence is not established |
| Qwen 3.5 9B |25/60 [16,29]|36 complete, four truncated |
| Blanket format / generic policy |35/60 [28,39] / 32/60 [22,35]|Neither promoted |
| Full bounded RAG |27/60 [22,33]|Not promoted; essay degradation and irrelevant retrieval |
| Three source crops |3/6 [1,3] versus bare 2/6 [1,2]|Selected diagnostic only; gain disputed |

All scores are agent rubric reviews, not organizer grades. A qualifying result covers all 40 items/60 points; errors and unsent items stay in the denominator. Preserve exact answers and gains AND regressions. Hypothetical RAG-short/bare-essay routing reaches only 33/60. Perfecting the baseline essay alone reaches at most 42/60: source/factual improvements are also necessary.

## Parallel ownership and next deliverables

| Owner | Worker / track | First concrete deliverable |
| --- | --- | --- |
| @kwiscion, Sol workers | Existing **central H100**; common control, sampling and integration | Freeze source-v2/prompt/runtime provenance; run matched bare control and explicit temperature 0.2 arm; independent review before promotion. Audit organizer-versus-evaluation prompt parity on CPU in parallel. |
| @semberecki | Existing **RTX 5090 Laptop**; source grounding | Independent observation of each supplied source before comparison. Compare one-pass versus observation+answer on a small fixed panel, then a frozen full candidate if useful. Keep image resolution unchanged in the first arm. |
| @Bukareszt | CPU initially; **additional H100 offered, not provisioned**; selective retrieval | Finish portable-runtime PR #93, then query/date ablations, relevance gate allowing zero hits, external-fact/mixed routing. Preserve the existing licensed index and unchanged solver sources. |
| @Pewciu6 | CPU initially; **additional H100 offered, not provisioned**; essay specialist | Dedicated essay prompt and matched-cap plan/write pilot; prepare one bounded essay-only LoRA feasibility path with independent data. Root/other reviewers grade this track, not its author alone. Existing scoring work remains on #11. |
| @przemeknowak781 | CPU; essay data and factual QA | First 12 independent, rights-cleared, multi-era essay examples plus provenance/source-group splits and factual checks; expand only after review. Never use fixed exam-derived topics or rubrics. Preserve existing alias-repair WIP. |
| @ljaniec | CPU; runtime, export and cross-review | Review PR #93 at exact head; verify prompt/runtime parity and plan offline qualification on each actual deployment runtime. Check adapter/export feasibility and model size independently. |

Issues contain the executable scope, acceptance conditions and start claim. One active parent worker per owner and one inference/training worker per GPU. An assignment is not proof of execution. Claim with host, session, start and ETA. Extra H100 names/access must be supplied before scheduling them; never infer that an offered machine exists. Blackwells remain unavailable.

## Fast experimental loop

1. Freeze each arm's hypothesis, exact input/config/prompt hashes, comparator, runtime/model/projector, owner, call/token/time/cost cap and stop rule in a launch record. Read the current GPU claim before launch.
2. Use independent DEV or original synthetic fixtures for prompt/router preparation. A small diagnostic panel must include previously correct controls as well as failures. Known-validation diagnostics must be labeled as such; do not turn them into training examples or item-specific rules.
3. Test one main change per arm. Record intermediate observation/plan artifacts privately. Keep the final-answer cap comparable; account separately for extra reasoning calls. Permit empty retrieval and baseline fallback.
4. Freeze the generic implementation, then execute all 40 known-validation items. Independent reviewers grade exact answers, blind to arm where feasible; split grading across reviewers and adjudicate uncertain/changed cases. A one-point fluctuation is a replication candidate, not proof of improvement.
5. Combine only supported components and execute the combined system end-to-end, including its actual organizer-package prompt path. A sum of component gains is not the combined score. Preserve the original fallback and an immediate rollback command.

First wave: CPU artifacts and start claims within 30 minutes; first bounded GPU diagnostics within 60 minutes of a ready worker. Review the first wave around **19:30**, choose/replicate candidates around **20:30**, and aim for a complete combined validation plus offline qualification by **22:00**. These are coordination targets, not permission to exceed a run's envelope. Overnight training is limited to declared experiments with an unattended stop and local backup; Sunday 11:00 freeze remains binding.

Second-wave options, selected by findings: minimal per-form output slots; statement-wise PF voting; selective thinking with a verified runtime flag; triggered decision/explanation consistency checks; separate visual-resolution/token-budget ablation; essay-only LoRA. Do not launch all options or build a specialist fleet by default.

## Compute and deployment gates

The existing H100 readiness result (retained locally) verifies text/image inference on Ollama 0.34.4/context 32768 and a locally backed-up evidence archive. The initial two-call readiness envelope is complete. **No full H100 exam batch or remote offline qualification has yet passed.** Each new run needs its own bounded declaration. Record the owner-supplied hourly rate and bounded estimate in the private launch record; billing is unverified and an idle instance still costs money. Additional-instance prices are unknown until supplied. No new purchases or resource provisioning by agents.

Keep the existing Gemma model/projector hashes pinned: combined **7,556,497,632 bytes**. Root owns the central H100; Piotrek retains his RTX. Preserve local backups of remote outputs/configs/logs after every completed bounded run. Stop only a freshly identified owned process; never disrupt another worker.

The laptop generic organizer-package launcher passed actual isolated CPU/CUDA synthetic qualification. Remote portability is separate: PR #93 adds frozen runtime profiles but does not by itself prove H100 offline execution. The organizer adapter and scored validation runner currently construct different prompts; resolve or measure that difference before final deployment. The [operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md) remains the verified laptop fallback.

## Non-negotiable boundaries and final handoff

- Final inference is offline; each saved model including vision/projector components is at most **8,000,000,000 bytes**. Report adapters separately under the event rule. Validate the actual final export and runtime, not merely training success.
- Follow [SOURCE.md](SOURCE.md) and [contracts](docs/overnight/CONTRACTS.md). Fixed 2023/2024/2025 questions, answers, rubrics, source packs and paraphrases never enter training or retrieval. Independently licensed general history material is allowed. May 2025 remains sealed until a separate lead release after candidate freeze.
- Public sharing is limited to checked exact final model answers, IDs/errors and provenance. Keep official keys, questions/source packs, reasoning/provider envelopes and credentials private. Do not edit answers to make publication or grading easier.
- User authorizes project Git/GitHub, HF and bounded paid inference through normal existing/project credentials. No unrelated-project credentials, purchases, reset credits or HF publication on the current path. Record estimated and actual usage separately.
- Preserve attributable dirty work. Merge only scoped passing changes at the exact reviewed head; no admin merge, force push or broad reset. Use Sol/Luna for implementation and review; reserve Astra for central diagnosis and decisions.
- While active, reconcile changed GitHub state approximately every 15 minutes; stay quiet on unchanged checks. The old morning heartbeat remains paused to avoid duplicate dispatchers.

Final handoff: model/projector hashes and sizes; frozen prompts/router/retrieval/adapters; runnable offline environment; exact organizer-package command; valid answers.json covering every ID; complete independent scorecard, latency/cost evidence and limitations. The [organizer guide](https://matura-json-guide.ania-olchowik.chatgpt.site/) defines the input package and answer template. Schema acceptance is separate from model quality and an actual submission receipt.
