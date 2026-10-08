# Matura hackathon post-mortem

**Warsaw Model Trainers, 25–27 September 2026**

Retrospective completed 8 October 2026.

## Outcome and purpose

The team delivered an offline history-exam solution and, according to the human owner, scored **46/60**, versus **54/60** for the winner, placing in the lower half of the scoreboard. The project also tested whether a heterogeneous team of agents could conduct research and development with little human direction.

The technical outcome was useful. The autonomy outcome fell short: the human owner expected to handle resource provisioning and submission, but repeatedly had to challenge assumptions, reopen alternatives, and redirect research.

The central finding is **owner-dependent research direction, compounded by weak task-level qualification, experiments that did not always resolve the important uncertainty, and incomplete planning through to usable results**.

The agents demonstrated valuable implementation, review, and recovery capabilities. Those successes must not be mistaken for independent initiation of the strategic changes that enabled them.

## Scope and evidence

The investigation covered **38 linked cases and two context records**, using GitHub issues, PRs, run receipts, two historical coordination/audit chats, and the owner's account. Related failures and repairs are not independent observations.

The [evidence register](RETROSPECTIVE_CASE_RECORD.md) and [case details](CASE_DETAILS.md) preserve sources, attribution, mixed effects, uncertainty, and corrections to early interpretations. Repository-file citations are pinned to a commit. No exam questions, official keys, private images, credentials, or raw model reasoning are reproduced.

The final competition score is owner-reported. The strongest preserved full validation result was **40/60 on a different exam**. Comparing it with the final 46/60 cannot establish the contribution of RAG or any other individual change.

## What went wrong

### 1. Research direction remained dependent on the owner

The lead agent had an explicit objective, authority to coordinate research, and instructions to pivot after uninformative results. The problem cannot be explained simply by missing ownership or a vague request to make progress.

The owner identifies **reconsidering Qwen and increasing reasoning budgets** as their interventions. The crop correction and late decision to include both ordinary and essay RAG are also directly visible in the lead-agent chat. Exact original messages for the budget/Qwen interventions were not recovered, so their attribution is retained as firsthand owner evidence.

Agents could generate interesting directions when prompted and could execute substantial work. They did not reliably initiate the consequential reassessment the owner had delegated. Useful pivots elsewhere in the record do not cancel that gap. [C01](CASE_DETAILS.md#c01), [C04](CASE_DETAILS.md#c04), [C15](CASE_DETAILS.md#c15), [C20](CASE_DETAILS.md#c20), [C35](CASE_DETAILS.md#c35)

The underlying cause is less certain than the failure itself. Strategic attention, context management, role design, and feedback quality may all have contributed. The retrospective does not isolate one universal cause.

### 2. Verification often established a narrower property than the task required

Several checks were mechanically correct but insufficient for the conclusion drawn from them.

| Episode | What passed | What remained wrong |
|---|---|---|
| Spark smoke | Requests returned records without transport errors | 16 of 20 GPU responses were empty; the usable-answer success and speedup claims were invalid |
| Evaluation images | Required visual material was present; later tiles matched their pixel specification | Full pages included unrelated material; generic quadrants did not extract coherent source illustrations |
| Filter and referee | CPU tests, preparation, provenance, and nonempty answer checks | The actual models did not reliably return the structured judgments or candidate IDs those stages required |

The image records contradict the early impression that no agent looked: a visual audit noticed neighboring content but treated it as nonblocking. The failure was partly **what inspection was intended to establish**, not merely its absence. [C05](CASE_DETAILS.md#c05), [C17](CASE_DETAILS.md#c17), [C19](CASE_DETAILS.md#c19), [C24](CASE_DETAILS.md#c24), [C27](CASE_DETAILS.md#c27)

The same distinction explains why synthetic-provider tests were useful for deterministic package plumbing but insufficient to qualify a new model behavior.

### 3. Some experiments could not answer the research question used to justify them

The 107-source retrieval configurations failed under their tested conditions. Several variants were tried, but they retained the same coverage limitation. Their results did not establish that full-Wikipedia retrieval was ineffective.

Other comparisons changed inputs, prompts, runtime budgets, or recovery behavior together. They could screen a combined candidate but could not cleanly explain which mechanism helped or hurt.

Grading added uncertainty. On the same four essays, one grader estimated a critic/rewrite gain of **14 to 27 out of 60**; independent review estimated **35 to 39**. These were four-essay totals, not the full exam. Calibration reduced the claimed benefit and exposed a regression before deployment. [C03](CASE_DETAILS.md#c03), [C12](CASE_DETAILS.md#c12), [C13](CASE_DETAILS.md#c13), [C31](CASE_DETAILS.md#c31)

A broken test, an inconclusive comparison, and a functioning negative experiment require different interpretations. Stopping can be rational under a deadline, but the stop should explicitly weigh remaining time, repair cost, and alternatives.

### 4. Planning did not consistently cover the full path to useful evidence

Individual runs had detailed limits, while the complete sequence through preparation, qualification, execution, grading, and integration was less reliably managed.

- A structured-route study remained unrun after integration delays and supporting-agent usage limits. The blocker reached coordination late; extending the launch window did not establish a recovery plan.
- Essay RAG preparation was explicitly stopped at its cutoff to protect final integration. This was a documented trade-off, not a negative essay-RAG result.
- Three reopened essay trials assumed parallel serving capacity that the runtime did not provide. Only one essay completed.
- A filter was repaired successfully, but repair and requalification left little downstream integration time. [C22](CASE_DETAILS.md#c22), [C23](CASE_DETAILS.md#c23), [C24](CASE_DETAILS.md#c24), [C25](CASE_DETAILS.md#c25), [C36](CASE_DETAILS.md#c36)

These episodes support specific dependency and readiness failures. They do not establish that all agents were slow coders or that all review and coordination were unnecessary.

## What worked and should be retained

| Practice | Demonstrated value | Limit |
|---|---|---|
| **Bounded real execution with a complete path** | Full Qwen confirmation launched about 98 seconds after declaration and completed in 27m58s | Available inputs and a qualified runtime made this a less novel integration task |
| **Recovery tested against actual failures** | A full rehearsal produced 40 nonblank answers, including recovery from injected and natural failures | Its score remained 38/60; completion was not correctness |
| **Independent inspection with decision authority** | Unsafe data export was blocked before merge; a failing LoRA candidate was rejected and work reassigned | Repairs and reviews still consumed time and did not catch every defect at once |
| **Preserved evidence and candidate answers** | Original grades and outputs allowed claims to be corrected; saved drafts could be recovered without regeneration | Preservation alone does not ensure useful interpretation |
| **Concrete delivery contracts** | The organizer mock passed the real adapter/export path; the final two-item smoke and no-new-calls resume passed | Neither test established full-exam quality or final end-to-end runtime |

The successful local loop was:

**Specific uncertainty → relevant checks → available inputs and compatible execution → measured result → a decision that actually changes work.**

The Qwen confirmation is particularly useful: it replaced an attractive but unmeasured 44-point composite with an actual 40/60 run. It answered the selection question rather than merely confirming a desired story. [C09](CASE_DETAILS.md#c09), [C30](CASE_DETAILS.md#c30), [C34](CASE_DETAILS.md#c34), [C35](CASE_DETAILS.md#c35), [C37](CASE_DETAILS.md#c37)

## What we can say about time

Nine sampled batches account for approximately **3h22m of summed run durations**. They overlap and are an incomplete, selected sample. They are not total GPU utilization, staff-hours, or project delay.

Concrete costs include a **28m48s** filter batch whose intended mechanism failed, a **33m46s** mixed A/B/referee batch whose selections all failed, and **45m49s from the first missed latest-start deadline to final expiry**, with no experiment calls. The referee also generated useful candidate comparisons, so its entire duration cannot be classified as wasted.

We cannot responsibly assign a percentage of the project to bureaucracy, repair, or waiting. Comments, commits, issue lifetimes, and idle snapshots do not supply a complete active-time ledger. The [time ledger](retrospective_time_ledger.csv) keeps run durations, correction latency, and preparation windows separate.

## Agreed operating model for future projects

These are agreed changes for future work, not experimentally proved remedies. No same-project trial or test-design stage is planned.

### 1. Separate research direction from execution management

| Role | Responsibility |
|---|---|
| **Research expert** | Own the cross-project explanation of the bottleneck; choose hypotheses, priorities, and approaches to continue or stop |
| **Manager** | Check feasibility, allocate resources, resolve dependencies, verify actual execution, and deliver results into the shared notebook |
| **Workers** | Implement and execute bounded tasks; report local evidence, validity limits, and unresolved issues |

The manager should not silently replace scientific priorities with easier work. It can reorder independent tasks and resolve routine implementation details within the agreed plan. Changes that alter the experiment's meaning return to the expert. Hard resource limits can stop execution immediately under the agreed envelope.

The expert reassesses after consequential results, invalidated assumptions, material scope changes, or stalled experiments. For a short project, **an hourly cross-project review is an initial default**, not an evidence-derived optimum. Already-justified work continues during review.

Every strategic review asks:
- What happened to the previous decisions?
- What changed in our understanding?
- What is now the important uncertainty?
- What should run next, and what should stop?
- What outcome would change that choice?

### 2. Qualify suitability and actual behavior before scaling

Two distinct questions must be answered:

1. **Task suitability:** do the inputs and proposed comparison represent the question we intend to answer?
2. **Actual behavior:** does the real model/runtime perform the required stage?

Use the smallest meaningful qualification and retain its results within the experiment where possible. A selector must demonstrate selection, a filter must demonstrate filtering, and image preparation must produce relevant visual units. A failed qualification leads to repair or an explicit stop; it is not automatically evidence against the research hypothesis.

This replaces broad ready declarations with concrete evidence. It does not require real-model calls for purely deterministic checks or another general approval committee.

### 3. Make experiments feed decisions through one compact notebook

Before execution, record:
- The uncertainty being resolved.
- What changes and what stays fixed.
- How different outcomes would change the next action.

After execution, record:
- Whether the intended test actually happened.
- What the evidence supports and leaves unresolved.
- The expert's cross-project consequence: continue, revise, expand, or stop.

Workers supply local results. The expert synthesizes across experiments. The manager makes sure the resulting decision becomes actual work.

**All experiment records and strategic decisions live in one authoritative project notebook.** Raw logs, outputs, and detailed evidence remain linked artifacts.

| Notebook section | Content | Initial size discipline |
|---|---|---|
| Current position | Objective, best verified result, main uncertainty, active priorities, remaining resources | About 300 words, updated in place |
| Experiment records | Question, comparison, validity, finding, next decision, evidence links | About 75 words per completed experiment |
| Major decisions | What changed, why, and the supporting experiment IDs | Only consequential changes |

These limits must not erase essential uncertainty or evidence. Update existing entries instead of appending routine status reports; retain meaningful changes of direction while removing superseded drafting and duplication. Avoid competing planning, status, and research-summary documents.

Workers return compact results; the manager integrates them and controls bloat; the expert owns their strategic interpretation.

### 4. Manage delivery through to a usable result

Before committing, account for preparation, qualification, execution, grading, and integration—not only model-call runtime.

| Trigger | Required response |
|---|---|
| Dispatch | Confirm the worker has inputs, access, capacity, and a real execution path |
| Blocker or missed milestone | Repair, reassign, simplify, or stop; return scientific scope changes to the expert |
| Proposed extension | State a credible recovery plan and the trade-off against remaining work |
| Completion | Put the compact result in the notebook and trigger the appropriate expert decision |
| Stop | Preserve the reason: negative result, invalid test, unavailable resource, or deliberate deprioritization |

Assignments and PR merges do not prove execution. No silent abandonment, automatic deadline extension, or repeated permission loop should substitute for a concrete decision. Routine work proceeds within its authorized scope and resource envelope.

## Conclusions and remaining uncertainty

The project demonstrated that agents can implement, review, recover, and deliver substantial work. It did not demonstrate the intended autonomy in sustained research leadership.

The response is to give strategic reasoning a continuing owner while improving the connection between the actual task, the evidence produced, and the next action. The agreed notebook and delivery rules are intended to make that connection visible without multiplying documents or approvals.

The final report deliberately leaves some questions open:
- Exact total coordination and human-supervision effort.
- Complete human-versus-agent attribution for every idea.
- The score a different experimental portfolio would have achieved.
- The causal contribution of each model, prompt, budget, image, recovery, or retrieval change.
- Whether the agreed operating model will improve future outcomes.

The detailed record preserves those limits and the successful counterexamples. It should remain the reference when this account is shortened for presentations or reused in another project.
