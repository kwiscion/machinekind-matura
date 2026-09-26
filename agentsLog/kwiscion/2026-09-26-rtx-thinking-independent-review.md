# RTX native-thinking panel: independent review

**Control 3/8 [2,3]; thinking 3/8 [2,3]. Paired central delta: 0. No secure gain or regression.** All six items and all eight possible points remain in each arm. The only scoring uncertainty is z13, where both answers combine a correct core with false visual description. The conservative paired judgment interval is [-1,+1]; it is not a statistical confidence interval.

The exact 12-row Git artifact from merged [PR136](https://github.com/kwiscion/machinekind-matura/pull/136), commit `b346b86ee63643a47f5c62fc89a8de73f9e2d841`, matches SHA256 `ca9e92d2a341abbb4d18807b9ca557c82c93000523ee943112a977712c503321`. Every exact decoded answer has a UTF-8 SHA256 in the companion JSON.

The first pass was frozen before reading launch/run-record text or any other grading of this bundle. Arm labels were visible, and I already know this validation set from earlier work. I read full source-v2 prompts, official task-specific rules and freshly viewed original pages 5,7,8,16,17,28. I did not read raw thinking.

| Item | Control | Thinking | Finding |
|---|---:|---:|---|
| z2 |1/1|1/1|Both establish the required contrast using both sources.|
| z4 |1/1|1/1|Both give the required architectural argument; control adds unnecessary specificity without negating its valid core.|
| z5.1 |0/1|0/1|Both identify the map through the prose and reach the wrong decision.|
| z13 |1/1 [0,1]|1/1 [0,1]|Correct event plus a real visible date; both add an invented literal scene, and control adds further fabricated details.|
| z14.1 |0/1|0/1|Both conflate distinct campaigns; thinking changes the incorrect date/story without fixing the map identification.|
| z25 |0/3|0/3|Different wrong historical contexts and unsupported visual interpretations; neither establishes the cartoon message required for partial credit.|

z13 is not treated as an automatic zero merely because an extra detail is invented. The event/date connection independently satisfies a defensible core reading. Conversely, the false scene descriptions are part of the justification and may lead a stricter examiner to reject either answer. This is the same uncertainty treatment for both arms; a selective acceptance difference must not be presented as a secure thinking gain.

Lightweight provenance audit: 12 unique item-arm rows, all nonempty stop completions with no reported errors; six calls at 1024 plus six at 10240 equals67,584 requested generation tokens. Both arms declare context 32768, temperature 1.0, top_p 0.95 and top_k 64. The published runner matches its recorded hash prefix and enforces these two caps. The reported 208-second run is below the 1800-second dispatch window. That window permits an in-flight call to finish within 420 seconds, so it is not a hard process deadline.

Two evidence limits: published row latencies sum to 207.415 seconds (control 28.156; thinking 179.259), whereas the run record says 214.0. Also, the full source-v2 file hash and all six prompt hashes match locally, but local PNG byte hashes differ from the owner’s reported image hashes. Thus grading used the same official pages, while exact cross-machine raster parity remains unverified. Individual native usage/truncation/runtime claims were not re-audited from private reasoning envelopes.

**Implication:** longer native thinking did not repair source identification on this panel. The next mechanism needs evidence that it improves reading and checking the original image, not simply a larger reasoning budget. Verify image ingestion and test a generic source-supported claim check on a predeclared panel; keep item-specific answers/corrections out of prompts and do not assume another observer stage will help. This is one known-validation sample per arm, not a full-system result.
