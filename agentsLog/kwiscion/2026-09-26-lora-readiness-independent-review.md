# PR135 independent LoRA readiness review

**Data cleared; proceed only to a separately declared full-model compatibility step. Training, serving and release remain unqualified.**

Reviewed exact head `0aed5fd5a7d29cc3648ca3f2f516584df56779a7`, merge `e5a730ebe423751bfd4f632378878141c159d8a4`. Read exact Git blobs into ignored isolated copy; no checkout/fetch/Git mutation, GPU, inference, model download or remotehost access. Reviewed archived host evidence, not independently rerun model/conversion experiments.

## Verified scope

- Pinned tiny CPU attach/backward/one-optimizer-step/merge evidence passes: 5,248 trainable parameters, finite loss, numerical merge delta 4.17e-7. The archived probe/candidate/evidence-manifest hashes match root preparation exactly. This is synthetic optimizer training, with zero history or full-12B training.
- Canonical 90 training rows and 16 evaluation inputs retain the already reviewed hashes. The new attribution sidecar exactly reconstructs canonical attribution plus six required reference-only markings. Prior content/source/split audit remains authoritative; no broad regrade was repeated.
- Root preparation tests: **25/25 pass**. The issued real clearance validates all90 records,28 training components and16 disjoint evaluation components. Missing acceptance, a wrong train hash and an eval component collision each fail closed.
- Archived unmodified-base export + projector: **7,556,499,104 bytes**. Adding the synthetic adapter: **7,566,898,592 bytes**. Arithmetic fits8.8 billion bytes. Neither is an actual trained merged model; these figures do not certify candidate weight inventory or serving.

## Required corrections and gates

- **Full model and serving:** No full 12B attach/backward/memory, actual trained-adapter load/switch, offline text/image serving, or all-route regression is established. Tiny synthetic CPU success supports the next separately declared compatibility step only.
- **Tokenizer report missing:** README cites host_logs/tokenizer-control.json, but this file is absent from the exact PR135 tree. The implementation invokes unchanged tokenized_record on canonical90, but 90/90, max2510 and 86883 tokens are host claims without the committed result. Retrieve/hash the log or rerun local-base preparation with this real clearance before history training.
- **Training and merged-size wording:** runtime_probe.py does execute one backward and AdamW optimizer step on a random tiny model. Zero history training and zero full12B training is accurate; nothing was trained is not. The 7556499104-byte pair is the unmodified base control, not an actual LoRA-merged checkpoint. The 7566898592-byte layout contains a random untrained synthetic adapter. Recheck the actual candidate final inventory.
- **Matched export control:** Registry and new control have identical tensor metadata and338 F32 tensors, but all329 quantized tensors and embedded chat templates differ. This does not establish a quantizer-only cause or identical underlying full weights for the registry. Use matched newly exported untrained base vs candidate with identical serving template/settings, and separately compare strongest registry native-thinking baseline. Adapter on registry base needs explicit qualification too.
- **Fail-closed export:** host_scripts/export_control2.sh uses set -u and echoes conversion return codes while continuing. Historical file/hash evidence supports produced artifacts, but this script is not a safe future candidate export gate. Stop on each failed conversion/quantization, use a fresh directory, and require expected hashes/complete aggregate inventory.

## Exact data-only clearance

`agentsLog/kwiscion/essay-lora-prep/essay_lora_clearance_v1.json` SHA256 `9a31742306e1c37aa096ff9e16e128083b8fff8e83257658e21457f2b35921fd`.

Train SHA256 `83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5`; eval SHA256 `5979ee0b8e0e4f084cf6070f42d31892ee53c1f5485409b4fc5dac1266055a28`.

The sidecar binds every accepted exported row by canonical JSON hash, keeps Augsburg/Vienna and League/Marshall dependencies connected, and carries the prior independent-review references. Use canonical Git blob bytes, not stale CRLF checkouts. Retain the attribution sidecar. It authorizes no runtime job.

**Pilot accounting:** input-only eval16 means no evaluation loss or early stopping. Frozen three epochs with effective batch8 imply at most36 optimizer steps for90 rows under current prepare.py, inside the120-step outer cap;60 minutes remains a hard bound. No need to invent16 gold essays. Exclude overlapping old #80 DEV topics from clean posttraining claims. Compare against both matched nonthinking export control and strongest native-thinking base.

Next finite sequence: retrieve missing tokenizer evidence / run cleared preparation; declare one real-base synthetic backward with memory and exact module checks; qualify offline base/projector serving and selected export layout; only then declare a history pilot and retain matched base controls. Full40/all-route evidence and complete actual weight inventory remain promotion gates.
