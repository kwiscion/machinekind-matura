# Corrected structural essay detection: CPU result

The narrow generic essay rule now detects the explicit essay task without an ID override. **20/20 synthetic tests PASS**; actual raw40 classification is33open,3closed,3unknown,1essay;30visual and0conflicts. Only item26 changes from unknown to essay. Unknown4/11.1/21 remain baseline, and the known multiline true/false19.1/20.2 limitation remains unchanged.

The added condition requires an explicit standalone essay heading, a minimum word count, an imperative choice referring to the offered topics, sequential numbered topics and topic vocabulary. It neither hardcodes IDs/topics/facts nor reads source_text. Six new synthetic tests cover two positive wording/numbering variants plus academic mention, absent heading, absent length and unrelated-source negatives. The original14 tests remain.

The failed v1 code/tests/docs/manifest are preserved byte-for-byte in `frozen-v1/`; the original failed-result JSON/Markdown remain unchanged. The original source exam hash remains `907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471`. IDs enter reporting only after classification. No exam text, images or keys are published here. Exact v2 pins and all decisions are in `known-validation-cpu-result-v2.json`.

This demonstrates the targeted generic structural correction on known validation only. It does not activate a prompt policy, replace explicit override support, select an essay topic or prove improved answer quality. No model/network/Git operations or changes to the shared runtime, running packages or teammate integration occurred.
