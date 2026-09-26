# Independent native attempt/restage evidence review

**PASS for the accuracy of the failed-attempt and CPU-restage reports. No material discrepancy found.** This is a local evidence audit, not a new remote verification or a successful generic-runtime qualification.

The failed attempt's 26 archived file members match their recovered copies. Archive SHA256 is `eb640320e92b04089db3702b4a6b777217455c566f345b502956c24f5a0b8b92`. Declared/prepared manifests, dependency pins, terminal receipt, stderr and pre/post host checks match the public report's hashes. The exact stderr records rejection of the two unlisted runtime metadata files; the unchanged runner reaches this check before creating results, a namespace, server or reservation ledger. No results directory exists in the recovered evidence. **Zero actual calls and zero requested/output tokens are supported.** Operator exit 2 is preserved separately from the transport's deliberate exit 0.

The terminal postcheck succeeded and matches the precheck's server PID/start ticks, environment and runtime snapshots. Both show no project workers, GPU processes or resident models. This verifies the terminal idle state; the owned-server cleanup path was never reached and remains unqualified. No cleanup success is inferred from a pre-server failure. The report correctly distinguishes the time-based cost proxy from measured billing.

The fresh stage's evidence archive, `a3ecaa39f66f6c37b6d8f79fc4b339e13e209904ad436a6af1c8e04d4250e2f3`, contains exactly the preserved report and inventory; both match their local copies and the public JSON. All six original file paths, purposes, sizes and hashes match the previously verified stage inventory. Their full logical sizes total **7,556,509,301 bytes**: **7,556,497,632 model/projector bytes plus 11,669 metadata bytes**, leaving **1,243,490,699 bytes** under the 8,800,000,000-byte cap. All six hardlinked entries count fully. They are not immutable independent copies.

The inspected restage script performs only filesystem staging, hashing and evidence creation under its finite CPU timeout. It preserves the old cache and its two generated sidecars. It does not weaken the guard, start services or make model calls. The backed-up artifacts establish what that script verified; they contain no local backup of the large model weights.

The fresh package archive `98f66c21eb6dd979be417138d35271f487d792fb9d9b2e9470ab1c2dea719a5a` has 16 file members, each matching the prepared package. Manifest SHA256 **`2e53c8580eb3356366eccccc1a9e580b6307eb3271992554d37b2a71e6957b30`** is correct. Compared with the prior prepared manifest, **only `cache` changes**. Every code, guard, prompt, template, route and image pin and byte is unchanged. Status is `PREPARED`; authorization and declaration/deadline timestamps are null. The guard remains `8ec6a7cf2f75615c2713c9db9e1cae408087be251b9b0e11437fe31e4c230473`.

Reviewed public report SHA256 values:

- Attempt Markdown: `1c44661fb6ad83c6ce9f9123854a4cb6219a09e393e35d561f8a61c40afd864c`
- Attempt JSON: `878959185c3de0826a0bc6b53328cd994fa5f3070d1ef52607698d7eab368155`
- Restage Markdown: `f0f39d964f785f1e03b018a21091a40ae8d50369b8ade971f640955db2f2dbf0`
- Restage JSON: `5e852bd20ab8c6b0d9c1cd95405f663520fac8ed151b9adfffa634209da14673`

A fresh root declaration and prior-worker cleanup verification are still required before another attempt. Future runtime-created metadata must be handled by a fresh exact stage or separately reviewed inventory policy. No runtime/code test suite was repeated because the reviewed code is unchanged.

Reviewer: independent Sol `/root/essay_corpus_sol`; CPU/local evidence only, no remote/service/model calls, no frozen-artifact changes and no Git mutation.
