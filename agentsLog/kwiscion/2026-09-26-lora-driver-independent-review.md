# Independent review: bounded real-base LoRA pilot preparation

**Approve the frozen driver and development envelope. No blocking driver defect remains after the reviewed fixes. This is not launch authorization or a claim of full-model runtime success.** The runtime-specific operator/serving script and instantiated stage manifests remain the explicitly declared final launch review, not an additional research prerequisite.

Reviewer: independent Sol `/root/essay_corpus_sol`, 26 September 2026. Read-only review of implementation and plan, plus CPU contract tests. No model import, GPU, inference, remote-host operation, Git mutation, or training occurred during this review.

## Exact reviewed files

| File under `agentsLog/kwiscion/essay-lora-prep/` | SHA256 |
|---|---|
| `run_real_pilot.py` | `3d466395cad9a2d596a356f15904024e2102b655c79fdc6319942d17bd1443dd` |
| `test_real_pilot.py` | `54e724d14c42c5d79b7853ade36dbef51ce493252d059e34fc73ead5ceb3b2c3` |
| `NEXT_EXECUTION.md` | `773222a7e43052bd3aed79f9f93d0e60f5f162bf9481586a568a2633009125ef` |
| `next-execution-plan.json` | `fb65536b25330224f5875da413624caad03af752d936ee3359ee5f30e478fc56` |
| `prepare.py` | `0d3a0452ef9caf514c713766e81b3fc1f21ecfcb85db8d2b89072a9a75cf115e` |
| `candidate.json` | `fc3b61de8cd061617ed5351cac441b8610cca19fff6a0b8827feb767cd617707` |
| `evidence-manifest.json` | `2ffac97f62bc12db94277e6cc2d3d30e876f4eb5ebb2731ada1ebee91c2db5cd` |
| `essay_lora_clearance_v1.json` | `9a31742306e1c37aa096ff9e16e128083b8fff8e83257658e21457f2b35921fd` |

## Correctness findings

- **Data isolation and reset:** history accepts only the exact cleared 90 rows and disjoint input-only eval16. The driver revalidates the clearance and actual token boundaries, masks prompt labels, rejects truncation, and never optimizes evaluation inputs. Each stage is a separate invocation loading the hash-verified pristine base, creating fresh LoRA tensors and a new optimizer. Synthetic updates are discarded; there is no synthetic checkpoint loaded into history.
- **Finite optimization:** the probe has one step and a 600-second stage cap. History has 36 steps and a 1,500-second cap, within the 120-step outer ceiling. Three passes cover each of 90 rows exactly three times: 33 eight-row groups plus three two-row groups. Loss is divided by the actual group length, so final partial groups are accumulated correctly. No retry, early stopping, hyperparameter search, or evaluation generation is hidden in the driver.
- **Identity and trainability:** full base and tokenizer SHA256, pinned metadata, four installed Transformers/PEFT source files, Torch 2.8.0/CUDA 12.8 and BF16 support are checked. Explicit built-in model loading uses local files only and disables remote code. The target regex must match 88 text q/v modules and exactly 5,193,728 trainable parameters; every trainable parameter must be a text-layer LoRA tensor. Finite loss, finite/nonzero gradients, finite updated parameters and a nonzero actual parameter delta are enforced.
- **Evidence and failure accounting:** reports bind manifest, base, tokenizer, driver, candidate and pinned inputs; history checks the probe's matching identity. Completed steps are flushed/fsynced with loss, group size and parameter delta. Allocated and reserved CUDA peaks are recorded, including handled failures after CUDA initialization. OOM/nonfinite/deadline failure raises; no silent fallback or automatic rerun occurs. An OS kill can prevent the final report, so absence of a complete PASS report must fail closed. The ledgers and partial directories remain diagnostic evidence only.
- **Base and merge preservation:** writes target a fresh output directory. History saves an adapter and one merged candidate without overwriting the development base. Safe merge is checked against original full state keys/shapes and exact hashes of unified vision/audio embedding tensors. The hash set must be nonempty, and both before/after dictionaries are retained in the report. Processor, template and generation metadata are copied from the pinned base. These checks still require actual execution; the CPU tests do not establish successful 12B merge or export.
- **Whole-wave bound and ownership:** the runbook requires an outer orchestration lock and `timeout` of 3,590 seconds plus a 10-second kill grace, covering all stages within 3,600 seconds. Stage locks are distinct; GPU ownership is checked before loading and before each optimizer step. SIGALRM is secondary because native CUDA calls can delay Python signal handling. The outer script must keep children in its process group and clean up only proven-owned servers. This is specified correctly but awaits the actual operator script review.
- **Calls and comparison:** the fixed plan permits exactly at most four synthetic serving calls, 512 output tokens each, with no retries/warmups: unmodified export text/image, then candidate on the identical text/image fixtures/settings. No history evaluation is included. The same converter, quantizer, serving implementation and template interpretation are required; registry equivalence is not assumed. Candidate conversion uses fresh files and fail-closed commands. The final declared candidate/projector inventory must satisfy the aggregate 8,800,000,000-byte limit.

## Checks executed

`python -B agentsLog/kwiscion/essay-lora-prep/test_real_pilot.py`: **6/6 PASS**. Covers all-row three-epoch accounting, partial accumulation, separate synthetic bound, rejection of a 120-step history override, missing qualification/data pins, invalid model/call/time/row limits, and rejection of an empty multimodal inventory.

`python -B agentsLog/kwiscion/essay-lora-prep/test_prepare.py`: **25/25 PASS**. Covers exact data/acceptance binding, grouping, evaluation isolation, token boundaries/labels and aggregate artifact gates. The actual canonical data was separately validated with the issued clearance during the readiness review; this review did not repeat historical content grading.

All plan file hashes, the clearance hash, four-call/2,048-token arithmetic and the 3,590+10-second envelope were also checked. These are contract checks, not GPU/runtime tests.

## Final execution prerequisites and limits

Greg/root must freeze and review the actual foreground-only `operator-stages.sh`, serving commands, fixture hashes, model/template/quantizer identity, call reservations, owned-server cleanup, absolute UTC deadline and stage manifests. The final plan uses unique normalized POSIX inventory paths; stage manifests must use actual host absolute paths. An initial stale duplicate driver pin was caught by the final hash gate and corrected before approval. The driver checks only the pinned control report's PASS/scope fields; an independent agent may establish and freeze that report's two actual control calls and matching runtime/artifacts inside the predeclared one-hour window before history starts; no additional root approval pause is required.

No additional gold essays, broad data regrade or final full-exam regression is required to begin this bounded development pilot. A 12B runtime failure is a legitimate pilot outcome. A completed pilot still does not establish essay gain or promotion: later independently declared eval16 and all-route/full40 comparisons remain separate. The one-hour planning cost is an unverified estimate, not a billing guarantee.
