# Winning plan

**Latest owner decision: use full-Wikipedia RAG for both ordinary questions and essays, and deliver a frozen manual workflow that finishes within65minutes without agent involvement.** Prepare locally and on the Pawel H100, where the complete corpus is present. Do not access final questions; the owner will start the final run manually after all code is frozen.

## Deliver now

1. One local PowerShell command accepts the real organizer exam directory or ZIP, preserves every text/image/ID, prepares and uploads a frozen package, starts the remote worker once, and downloads validated answers.json plus status/logs. Provide a resume/fetch command for connection loss; never duplicate inference.
2. One Qwen3.5:9b weight set,65536context, serial model calls (installed Qwen runtime has one inference slot). Obtain a complete direct answer sheet first, then essay RAG and ordinary-question RAG within explicit optional budgets. Essay: chooseone topic, sixqueries, fivepassages/query, strict independent evidence checks, evidence-backed writer. Ordinary: query, topfive, strict checks, evidence-backed final. Preserve direct answers for failed, unsupported or unfinished improvements.
3. Hard timing from local command start: remote work ends byT0+55minutes, with tenminutes within that window reserved for recovery/export; local retrieval/validation targetsT0+60, leaving five minutes for manual submission within65. Bound optional RAG to available time, give essays a reserved opportunity, and stop cleanly. All required entries nonblank; three recovery retries before emergency fallback when time permits. Report deadlines/placeholders/skipped RAG explicitly.
4. Verify the local-to-remote manual path on synthetic/DEV inputs and a bounded real mixed question/essay smoke before final access. Review at exact source hashes, stage clean eligible weights and a frozen full index, document exact commands and freeze Git. No code, prompts or settings change after final acquisition.

## Evidence and limits

Preserved direct baseline:40/60 (32nonessay+8essay),40complete answers in27m58s. Nonessay full-corpus Qwen diagnostic4/6→4/6. One completed essay-RAG diagnostic9/15; two other tries failed operationally because concurrent clients were serialized. These are limited results, not proof of full-exam improvement. The owner explicitly selects both RAG routes despite this uncertainty. Preserve all original results; no posthoc composed full score.

## Constraints

Aggregate saved model weights at most8,800,000,000bytes; Qwen6,594,475,420bytes. Final inference offline; one owner/controller per GPU, no concurrent queued model calls. Full Polish Wikipedia:1,587,721articles/2,729,746passages. No held-out training/retrieval, new compute purchases, reset credits or unrelated credentials. May2025 remains sealed. Heartbeat remains paused. Final questions and submission are performed manually by the owner; our job is to leave a tested runnable package and instructions.
