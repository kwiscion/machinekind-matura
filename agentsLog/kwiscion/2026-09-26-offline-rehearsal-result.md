# Offline rehearsal result

**Successful two-item synthetic offline rehearsal; not a validation score.** Both package IDs produced nonempty answers with no errors, and the adapter validated the output JSON. No submission was performed.

| ID | Output | Characters | Prompt tokens | Completion tokens | Latency |
|---|---|---:|---:|---:|---:|
| `offline-text` | nonempty, `stop` | 6 | 140 | 3 | 55.79s |
| `offline-image` | nonempty, `stop` | 8 | 234 | 4 | 2.364s |

The two calls used 7 completion tokens under the 2,048-token total cap, at $0. Elapsed time was 68.891 seconds. The adapter reported two answers, zero empty outputs and no format failures.

The isolated runner and server used the same network namespace. Only loopback was present, and external IPv4 and IPv6 probes failed with network unreachable. Read-only WSL checks after cleanup found no rehearsal-owned process group or isolated namespace; the original host namespace and local daemon API remained available.

The configured model digest matched readiness, and the runner checks resident digest and 4,096-token context after both calls. Selected server-log evidence showed 35/49 layers offloaded to CUDA with a 5,191.72 MiB CUDA0 model buffer. The log also recorded an initial GPU-discovery watchdog warning before successful calls.

**Scope limit:** this validates only the two synthetic package items and adapter path. The generic final launcher remains CPU-only; this rehearsal does not validate its CUDA path. Nonempty answers and format validity do not establish correctness.

Evidence hashes are recorded in the accompanying JSON. Raw responses, answer text, prompts, provider envelopes and server log contents remain private.
