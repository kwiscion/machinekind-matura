# Independent answer-recovery second review

**Result: arm A 1/6 [1,1]; arm B 0/6 [0,0].** These are selected-subset scores, not full-exam scores.

Arm labels A/B were visible. Reviewer previously graded the full-thinking last20 and knows aggregate evidence from assignment/plan. No interrupted notes, recovery request envelopes, root recovery grades, or other recovery assessments were read. This is independent scoring, not a fully blinded evaluation.

Original source-v2 prompts and full page images 14, 15, 22 and 28 were inspected. Official item rules were applied manually. Exact answer SHA256 uses decoded answer string encoded UTF-8 without normalization; file SHA256 uses raw bytes.

| Arm | Item | Central | Low | High | Maximum |
|---|---|---:|---:|---:|---:|
| A | val2024-hist-z12.1 | 0 | 0 | 0 | 1 |
| A | val2024-hist-z19.1 | 1 | 1 | 1 | 2 |
| A | val2024-hist-z25 | 0 | 0 | 0 | 3 |
| B | val2024-hist-z12.1 | 0 | 0 | 0 | 1 |
| B | val2024-hist-z19.1 | 0 | 0 | 0 | 2 |
| B | val2024-hist-z25 | 0 | 0 | 0 | 3 |

## Item evidence

- **A / val2024-hist-z12.1:** The response names Ludwik Maria and Wladyslaw IV, neither the ruler supported by the abdication narrative and Paris monument. The supplied evidence identifies Jan Kazimierz. No correct identification is present. Answer SHA256: `62478762e64cd72e2e894e35124dcef82f171c476f87cec9fa0f1a55c602a825`.
- **A / val2024-hist-z19.1:** Two of three selections are correct (positions 1 and 3); position 2 is wrong. The Cieszyn stamp concerns a planned plebiscite that did not take place. The official rule awards one point for exactly two correct selections. Answer SHA256: `db9fc7fcd2dd98e5090f480ffdc23eaed8fc5145870a85b076423e9b4be98986`.
- **A / val2024-hist-z25:** The response interprets the scene as alcohol prohibition in the USA and misreads the inscription as SOAKER. The observed uniform, broom and bars are attached to the wrong political event. It misses the Solidarity suppression / concealment and externally controlled Polish communist leadership message. An isolated visual noun does not satisfy the minimum correct-message-plus-interpreted-element requirement. Answer SHA256: `cd296834bc9a3c9661fd86b42defa72bbaddae7d677267c5f4dd3945661e2b9e`.
- **B / val2024-hist-z12.1:** Jan III Sobieski is the wrong ruler. The abdication narrative after the death of Ludwika Maria and the Paris monument support Jan Kazimierz. No partial identification credit is available. Answer SHA256: `11627d48a9598e1cbdc7a685ce64b4ae7a4037495a28415e04fde95b1cfa8912`.
- **B / val2024-hist-z19.1:** Only selection 1 is correct; selections 2 and 3 are wrong. The Cieszyn plebiscite was not held, and Poland received the smaller territorial portion of the Upper Silesian plebiscite area. The official two-point item awards no point for only one correct selection. Answer SHA256: `89290644b6d09a570b25c4cdacce278727131f34f13dcd96da0d83d06bbd2388`.
- **B / val2024-hist-z25:** The response places a supposedly German soldier in the First World War and treats the inscription as SODADA and the sweeping as German military collapse. That is an incorrect message and historical setting. It does not interpret the Solidarity inscription, sweeping under the carpet, or puppet strings in the relevant Polish communist context. Broom/uniform recognition alone earns no point. Answer SHA256: `7e48a3c5c83298b0457656a7b0cab396ab07be995a2f110ca8caf41b8dd0a420`.

The cartoon rubric requires a correct message even at its lowest nonzero level. Neither response meets that requirement; there is no discretionary point merely for naming an object visible in the drawing. These judgments concern failed interpretation, not a blanket penalty for incidental extra detail.

## Provenance and limits

- Arm A: `agentsLog/kwiscion/model-answers/answer-recovery-A-three.jsonl`, SHA256 `ad93976a5361179d209e67e4ed6573849bfaf0e6b829b1c13549727ae0e7b56c`; all three finals nonempty, error null, finish reason stop.
- Arm B: `agentsLog/kwiscion/model-answers/answer-recovery-B-three.jsonl`, SHA256 `fcc745275a65969ec04e54a0c4ed649d97c7da8c20e31ba3db7eeb96b2e31f5a`; all three finals nonempty, error null, finish reason stop.
- Original source/key content is retained privately; this report contains assessment rationale, not copied source passages or a reproduced official key. Evidence file hashes and all response hashes are in the companion JSON.
- Original source images were inspected directly, including the two-page ruler task. No scoring interval is needed for the six unambiguous decisions.
- No interrupted notes, request envelopes or other recovery grades were read. No model call, Git mutation, training write, or full-exam-score extrapolation occurred.
