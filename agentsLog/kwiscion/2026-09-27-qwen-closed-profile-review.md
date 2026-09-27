# Closed Qwen profile: independent focused CPU review

**PASS for the prepared closed profile/shared binding delta.** No material code blocker found. No inference, remote access, cache mutation, Git mutation or broad framework rewrite was performed by this review. Fresh staging, one shared absolute declaration deadline and live loaded-model qualification remain execution gates.

| Exact artifact | SHA256 |
|---|---|
| final-package-prep/run_recovery_package.py | 54983970c8bc9bd8b84bc878383b254af8cb192be313320b793317e86b4aa392 |
| qwen-thinking-prep/closed_profile.py | 953bc792cb6d553b84d58398b0261e333799737e5f94fc5fd77fadf527b8367d |
| qwen-thinking-prep/prepare_recovery_pair.py | dd93305578aa3fd24a42b479075049365298e63d0288784ebf88d7400812e8c2 |
| qwen-thinking-prep/test_closed_profile.py | d45b95f80b1b53e6457864087fe8c92ddfe20f37fe66cd5fac3c04035a8d877e |
| qwen-thinking-prep/recovery-pair-manifest.json | 7317a0f2e979a3db605f66296cdde107d6850019b5acec6ad8cfa5af9b93a438 |
| unchanged recovery_harness.py | d99d9271d6cc589f0e9caccfee3d1387c4695d0fd9cd33db97bcd3efba54a521 |
| prepared Gemma launch.json | f231722e6e3bed5649689ad17e310f9829911cd35de8cf86b7d9d360c85677a7 |
| prepared Qwen launch.json | 0c0211744265457475205094581249749f1b443725e53cab492f2173de6bdfa4 |

The shared binding resets model/step state before choosing a profile. Default manifests retain exact Gemma model and omitted sampling; a closed hash-pinned profile permits only the declared Qwen identity and T1/top_p0.95/top_k64. Profile switching was independently exercised in Gemma→Qwen→Gemma order; final Gemma request defaults were restored. This is an opt-in model profile, not a question-ID router or arbitrary model override.

The Qwen guard requires exact native manifest digest6488c96f…93ea7 and exactly one pinned model container6594462816bytes, rejecting extra model/projector layers. Existing verify_inventory still checks every listed file size/hash, rejects missing/unlisted files and applies the aggregate8.8GB cap, including metadata. The native manifest pin binds the referenced metadata too. Runtime snapshots reject wrong tag/digest, extra or missing loaded model and wrong65536context. Existing runtime binary pin, isolated cache/server, namespace proof, owned identity, cancellation/quiescence, cleanup and default-dry-execution path remain shared and unchanged. No combined Gemma+Qwen submission is permitted; each arm uses a separate cache and sequential owned service.

Both actual prepared packages pass dry preflight. All six complete input cases and image bytes compare equal between arms; each first request retains the exact source and images with truncate/shift false. Qwen changes only model identity and the explicitly fixed sampling fields. Context and cap checks remain in the existing scheduler; no source shortening or guessed image-token fit was introduced. A synthetic Qwen length-failure/recovery exercised the real shared scheduler: two durable reservations/two callback calls,32768→49152 ceilings, correct Qwen identity/sampling and accepted final. No actual model request was made.

Independent tests:5/5 profile tests PASS in0.014seconds;8/8 existing binding tests PASS in1.768seconds; both prepared dry preflights and explicit input/reset/fake-ledger assertions PASS. The unchanged21-test scheduler suite was not needlessly repeated; prior reviewed scheduler pin is preserved.

Each prepared arm has6items,24maximum attempts,884736requested tokens, no injected faults, and null execution authorization. The paired proposal totals48calls/1769472tokens. The common60minute deadline is an operator declaration invariant: both manifests must receive the same start/deadline, the second arm starts only after verified first-arm cleanup, and systemic failure stops the pair. CPU approval does not prove fresh cache contents, Qwen loaded context, memory use, throughput or answer quality. Read-only model metadata recorded by the author is architectural evidence only. The next allowed runtime qualification requires root's fresh exact declaration; no extra warmup is required by this review.
