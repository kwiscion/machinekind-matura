# Generic Qwen preparation and inactive essay policy review

Root reviewed both additive paths; neither changes the running experiments or activates a policy.

`qwen-thinking-prep/prepare_qwen_exam.py` delegates arbitrary organizer IDs, source/image copying, template checks and explicit essay mapping to the qualified generic preparer, then freezes the reviewed closed Qwen profile and reruns actual package preflight. The fresh-output and profile-hash checks fail closed. It supports 60/120 minutes with the existing recovery accounting; no benchmark IDs or runtime implementation are introduced.

Root independently ran both actual-adapter synthetic tests: 2/2 PASS, including a four-item package with an image and custom essay ID, one-item no-essay input, source-byte equality, profile mutation and fresh-output refusal. Author also verified the resulting synthetic package with actual remote Python3.10.12: 4items/16attempts/589824requested tokens, zero model calls/server starts. This qualifies preparation, not Qwen promotion.

`essay-coverage-prep/coverage_suffix.py` appends original generic Polish instructions without changing any original item fields or clipping source text/images. It asks for evidence and causal explanation for every requested aspect, using the existing400–500-word mechanics. Root independently ran2/2 real-adapter synthetic preservation/duplicate-application tests. No historical answers or rubric excerpts are embedded. Quality still needs a separately frozen experiment.

Reviewed code hashes: Qwen wrapper `a3134927353b28d71d75187c5c3820a8b65e77d45b5874568f7ef71fb84c0873`; essay policy `298d383edcd03cf1cc0a4b6ffaa1d97941b60c0e48090667b7861418ae836bae`; exact suffix `236e9ee6d23168b817b144a706d86a8f204fe133af568ba27c08c88c4727d763`.
