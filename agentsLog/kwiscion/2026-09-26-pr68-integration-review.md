# PR68 integration review

Lead reviewed exact head `a286b8b0e0638f2ccb72d645c74c2b3737672af0` at17:24 Europe/Warsaw. **PASS for opt-in submission integration; no RAG score promotion.**

The80-line integration change invokes the already reviewed preparation script in a subprocess, preserving the parent transport from its socket guard. It retains the bare prepared input/manifest, verifies IDs, unchanged image/other fields, original prompt suffixes and trace/hash bindings before transport, and finalizes against the original package manifest. Default bare behavior remains unchanged. Retrieval remains opt-in; final selection depends on the pending complete score.

An isolated checkout at the exact reviewed head ran `python3 -B -m unittest scripts.Bukareszt.test_matura_package scripts.Bukareszt.test_matura_package_rag scripts.Bukareszt.test_prepare_bounded_rag -q`: **84 tests passed** in32.977s under WSL. This includes15 new tests with arbitrary IDs/template order, preserved image bytes, pinned-index refusal before transport, call-budget refusal, remote-endpoint refusal, dry paths and inference-failure blanks. Existing synthetic retriever code emits unclosed-file ResourceWarnings; no test failed. The previously reviewed staging helper is unchanged and was not retested in this invocation. Repository CI also passed at this exact head.

No real model/server calls, exam output changes or index changes occurred during review. New options do not establish offline runtime isolation or token fit. The generic isolated launcher remains a separate #66 task.
