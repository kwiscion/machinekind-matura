# CPU dependency retry — 26 September2026

**Blocked at the new eight-minute setup deadline; synthetic probe not run.** This is incomplete dependency installation, not a LoRA compatibility failure. The expired original attempt and frozen scripts were left untouched.

New authorization clock:19:59:34UTC. Installer ran20:00:39.762–20:07:34.011UTC and was killed at the absolute20:07:34 deadline. It downloaded the two exact-commit archives, built both wheels, and reached package installation. A subsequent scoped process query found no remaining installer Python processes.

Torch remains2.8.0+cpu with CUDA buildNone. Transformers/PEFT distribution state: `{'torch': '2.8.0+cpu', 'transformers': None, 'peft': None}`. `pip check` reports no broken requirements, which does **not** imply an absent package is installed. The partial freeze and installed-source hashes/missing-file state are recorded separately. No pretrained weights, GPU use, generation, history training, purchase or other environment modification occurred.

## Exact archive provenance

| Package | Commit | Archive SHA256 |
|---|---|---|
| peft | `b8674c86183a5dee38d0c3ede392e189593025e5` | `05a70e1ef6ac1633da4d2ca3b90db5df7cb5f24d9b9b123ce0763e9e83b42dd2` |
| transformers | `96331a9f93b72697f160a958d2883d4b49a56739` | `c97fdf3bfb260db12b4fecf1a7647f51ca0e2b52cc75a947ca1a3d6cc4f4ed8c` |

Both archive root directories match the full requested commit. Copies are retained inside the isolated cpu-venv retry-archives directory. Package install logs and any retained wheels are recorded in the JSON report. The retry used a separate cache/tmp directory inside cpu-venv, so it re-downloaded the exact archives rather than relying on the original global cache.

Next minimal step is another separately bounded missing-dependency install using these already built artifacts, followed by exact installed provenance/source-hash checks and complete freeze, then the unchanged120-second synthetic probe. No compatibility fix is proposed because runtime was never reached. Do not extend this attempt's elapsed deadline or label a partial install a passing probe.

The new aggregate submitted-weight limit is8,800,000,000bytes. Existing Gemma plus projector occupies7,556,497,632bytes, leaving1,243,502,368. Two full model copies are ineligible; future export needs one merged all-route model or verified small-adapter reuse. Current frozen probe/configuration was not changed.
