# Known-validation route detection check

**Not ready to replace explicit essay routing.** The frozen detector passes14/14 synthetic tests but misses essay26 and two multiline true/false tasks on the actual raw40-item metadata. No implementation changes or runtime integration were made.

Counts:33open,3closed,4unknown,0essay;30items have images;0conflicting-rule results. Unknowns:4,11.1,21,26. The closed detections10,14.2,16.2 correspond to explicit lettered-option tasks. Items19.1/20.2 contain multiline true/false instructions but were labelled open;4/21 use unsupported argument-formulation wording, and11.1 is a matching task. Essay26 uses a choose-one-of-them construction plus numbered topics, length requirement and essay marker that the current narrow topic regex misses.

The detector received only question, answer_format and images. Item IDs were attached afterwards for audit; neither source_text nor keys were read for classification. Manual inspection concerned instruction structure only, with no historical answer inference. Existing known-validation input is not unseen data. Counts are diagnostic output, not a measured gold-label accuracy score.

Classifier SHA256: `2f91f6c657da087ef16d611e804ee30ad2c699b098ebd7a3107c361a65fd101c`. Raw organizer exam SHA256: `907976be94f848fc3415ca0e4b1ba473e9dd08caa66984245a63e73d0fa27471`. Detailed public-safe ID/rule output is in `known-validation-cpu-result.json`; no exam text or images are reproduced. Independent rerun within this validation:14synthetic tests PASS in0.002seconds. Zero inference, network or Git operations.

Recommendation: keep explicit --essay-id/--no-essay behavior. A later generic fix should cover choice-pronoun/numbered-topic essay structures and multiline finite-choice instructions with new synthetic regression tests; preserve this pre-fix result. Unknown cases continue safely through baseline. This optional preparation must not interfere with the separate structured-stage integration.
