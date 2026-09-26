# Final single-Gemma weight guard

CPU-only preparation; this does not launch inference, qualify offline isolation, or replace live process ownership checks. Historical two-model experiments remain unchanged.

Stage a fresh **Ollama models directory** containing only `manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M` and the `blobs/sha256-*` files referenced by that manifest. Copy from the verified project cache into a separate final-package directory; do not copy the complete development cache. Keep runtime binaries, scripts, reports and the inventory outside this weights directory. Never point staging or a later server at the development cache by accident. Hardlinks are allowed but every file entry counts its full size; symlinks, junctions and other reparse points are rejected.

From the repository root:

```sh
python agentsLog/kwiscion/final-package-prep/guard.py native STAGE/models --write-inventory STAGE/weight-inventory.json
python agentsLog/kwiscion/final-package-prep/guard.py inventory STAGE/models STAGE/weight-inventory.json
python -X utf8 agentsLog/kwiscion/final-package-prep/test_guard.py
```

The native command defaults to the verified Gemma model/projector/manifest pins embedded in `guard.py`. It requires exactly that manifest and all its referenced blobs, including configuration/template/license metadata, with no extra files or Qwen dependency. The inventory records each relative path, purpose, actual bytes and SHA256. The inventory output must be fresh and outside the cache. The generic inventory command verifies an already frozen inventory; it does not establish a new model's suitability from a caller-supplied label.

The canonical model and projector total **7,556,497,632 bytes**. **All staged cache files count**, including tiny metadata and the native manifest, so the reported aggregate is slightly larger. The conservative cap is **8,800,000,000 actual bytes**. Missing, changed, unlisted, duplicate/case-colliding paths, unreadable directories, outside paths and executable binaries in the weight directory fail verification. No hardlink deduplication discount applies. Do not modify the stage during or after verification; reverify at final use.

A future trained Gemma pair needs a separately reviewed explicit JSON pins file with the same `single_gemma_pins_v1` fields as `CANONICAL`, passed through `--pins PINS.json`. Both weight hashes/sizes and the native manifest hash must be replaced explicitly; there is no automatic alternative-weight allowlist. Keep its matched export control separate.

Optional saved runtime evidence can be checked without contacting a server:

```sh
python agentsLog/kwiscion/final-package-prep/guard.py snapshot SNAPSHOT.json --runtime-binary RUNTIME/bin/ollama --require-loaded
```

`SNAPSHOT.json` contains `version`, `tags` and `ps` objects from the corresponding read-only Ollama APIs. The command verifies the separately located runtime binary hash, version, single Gemma identity and loaded context. Omit `--require-loaded` to allow an unloaded cache. A saved snapshot cannot prove current server ownership, environment, freshness or network isolation; those remain required in the separately declared final runner proof. No runtime binary bytes are misreported as model weights.

Validation: 14 small fixture tests pass in WSL/Linux; Windows passes 13 with the symlink-privilege test skipped. Linux exercises that test. No full model allocation, downloads, GPU calls or staged production cache were used for these checks.
