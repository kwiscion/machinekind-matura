# Actual single-Gemma cache staging — PASS

A fresh isolated native cache was staged from the verified development cache and checked on the actual files with both native-manifest discovery and the frozen inventory verifier. Only the pinned Gemma manifest and its referenced blobs were staged; no Qwen or other development model was included.

| Check | Result |
|---|---:|
| File entries | 6 |
| Model + projector | 7,556,497,632 bytes |
| Manifest and metadata | 11,669 bytes |
| Entire staged cache | **7,556,509,301 bytes** |
| Aggregate cap | 8,800,000,000 bytes |
| Remaining capacity | **1,243,490,699 bytes** |
| CPU staging and verification | 23.45 seconds |
| Inference / training calls | **0 / 0** |

All six entries were hardlinked on the same filesystem, with their **full bytes counted per entry**. Originals were neither moved nor deleted. Hardlinks share underlying data: this is a verified stage, not an immutable independent copy. Do not mutate either cache, and rerun verification before final use. Runtime code and reports remain outside the weights directory.

Exact evidence:

- Guard SHA256: `8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473`.
- Inventory SHA256: `cd00de981f52adeef9f2b09265fcfa382edc5e81352e652ebcb4432e37c8ec2c`.
- Remote/local evidence archive SHA256 matched: `90e45ebcecb80cf5516393768200594b20dd47dc51a359e841426e6389e05a57`.
- [Public inventory and aggregate evidence](2026-09-26-final-package-stage.json) records every relative filename, purpose, byte count and hash. The verified archive, execution declaration and process metadata are backed up privately.

The existing service was preserved. This proves **staged cache contents and aggregate size only**. It does not prove offline serving, final runner integration, inference quality, or a complete submission bundle. Any subsequently added weights or adapter require a new whole-package inventory.
