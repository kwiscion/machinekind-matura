# Manual final workflow dispatch

Owner decision at 09:38 Warsaw: use full-Wikipedia RAG for both ordinary questions and essays. Prepare the complete manual workflow locally and on the Pawel H100; the owner will obtain the final package and start it after the code freeze.

- Lead: integration, exact-head review, frozen commands and operator handoff.
- Implementation Sol: extend the existing deadline RAG package with the essay route, preserving direct answers and all original sources.
- Operations Sol: sole Pawel worker; stage a clean eligible cache and frozen index, deliver a one-command local launcher with automatic fetch and resume.
- Review Sol: independent deadline, input/output and failure tests, plus a bounded mixed-route smoke through the manual path.

No final questions may be requested during this preparation. All agents and teammates must stop development before the owner accesses them. Existing experimental issues remain historical evidence; this manual integration is the only active lead dispatch.

Timing starts at the local command: remote deadline 55 minutes, local answers target 60 minutes, 5 minutes left for manual submission. Optional RAG cannot consume the 10-minute recovery/export reserve. The runtime is serial. Both RAG routes are enabled; unfinished improvements retain complete direct answers. The policy bounds execution, but external transfer outages cannot be guaranteed away; retain outputs remotely and provide resume/fetch.

Use only the existing H100 allocation. At the reported $3.28/hour, 65 minutes costs approximately $3.56 of already provisioned compute. Exact finite model-call and requested-token ceilings must be written into each generated run declaration before launch.
