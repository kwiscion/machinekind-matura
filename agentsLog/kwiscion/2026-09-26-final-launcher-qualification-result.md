# Generic final-launcher runtime qualification

**Passed for two synthetic items only.** The generic launcher completed two calls with two nonempty outputs, no errors or unsent items, `stop` finish reasons, and $0 cost. This verifies the isolated runtime and answer-file packaging path; it is not a correctness score or real-exam qualification.

The private evidence records 374 prompt tokens, 7 completion tokens (381 total), and 15.628 seconds summed request latency. Model digest: `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; Ollama `0.30.7`; loaded context 4096. CUDA was active on the laptop RTX 2000 Ada, with 35/49 layers offloaded. The multimodal projector stayed on CPU because projector offload was disabled for limited VRAM. The configured model plus projector is 7,556,497,632 bytes, below the 8,000,000,000-byte limit.

The runner and server shared isolated namespace `net:[4026532228]` with loopback only. External IPv4 and IPv6 connection attempts failed with errno 101. A read-only post-run WSL check found no owned process group or remaining isolated-namespace holder. The host Ollama API remained available at version 0.30.7; the host namespace recorded at launch was `net:[4026531833]` and the current WSL process remained in that namespace.

This qualification covers two synthetic fixtures only. The real 40-item package, source and image completeness, full-run context fit, event time window, correctness, final candidate and submission acceptance remain unproven. It used the laptop RTX 2000 Ada, not the separate RTX 5090 control.

The earlier [fixed two-item offline rehearsal](2026-09-26-offline-rehearsal-result.md) is a separate successful run. Neither rehearsal is a real-exam result.

Private evidence hashes: launch `166d7098453ddda2d1ab391e5372a150d227d9c23caef619c46db5378601b5f0`, raw JSONL `75a2a70580945aef3260981687657d0c00a1d47369eb003afd5d872a8ca684b1`, answers `4e62aaee0315e6d411bc37c75c9e910e2add10ab2020959b7ab1e752fd25e037`, network proof `ffd11ac7edccbf3a0ca3d094f95eec210f1ccbf2614cd3a9636d0ebdf262034d`, cleanup `315cfc042dbc31199d2ded2bad2367ee1d960f2cfe3834c3f51f03add6cebb5a`, selected server log `069e9e4b6c5a73015e2545aecc1b3647074bf105cd0d066b49ae46c5ec93a47f`. No raw provider records or answer strings are reproduced here.
