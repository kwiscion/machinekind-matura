# Source-blind Sol essay corpus (DRAFT)

Owned additive batch for issue #117. These are original Polish teacher targets, not accepted training data. Topic selection used general curriculum coverage, independently of fixed exam content. No exam question, key, rubric, model answer, source pack, benchmark site or user attachment was opened for this task. No inference API, GPU, training, purchase or git operation was used.

Each target has an explicit thesis, three developed argumentative paragraphs and a conclusion. Repairs are deterministic corruptions of this batch's own prose. All variants retain their parent source group and `split: null`. Multitopic negatives additionally declare the other essay's source-group dependency; these groups must be connected before any split assignment.

Sources are licensed Wikipedia secondary reference articles, read from local hash-pinned snapshots. `sources.jsonl` records revision URLs, retrieval timestamps, hashes, attribution, history links and the article-text CC BY-SA 4.0 license. The footer license was checked automatically. Images and separately credited passages are excluded. Snapshots and extracted source text are under ignored `source-private/`; they are review evidence, not publication artifacts. Article reliability varies: the Augsburg page requests citations and some Vienna/investiture details have citation-needed flags. Historical correctness requires independent review; this batch does not claim a primary-source audit.

`revision_or_sha256` hashes actual raw HTML bytes. `text_sha256` hashes UTF-8 extracted text with LF-normalized newlines, as read by Python's universal-newline handling; `text_file_sha256` separately hashes actual extracted-text file bytes (CRLF on this Windows run). Record `response_sha256` likewise hashes the decoded JSON response's UTF-8 bytes; `SHA256SUMS.txt` hashes actual artifact file bytes.

**Independent content review is complete:** all8essay targets,8repairpairs and32evidencecards are accepted with limitations. See independent-review.md/json. Target prose and prompts are unchanged; validator verifies their hashes against that review. Canonical records stay DRAFT until Greg completes corpus-wide integration.

Original prose synthesizes facts with explicitly marked causal interpretation in `evidence-cards.jsonl`. Conservative downstream treatment: preserve Wikipedia attribution, linked revision/history and share-alike obligations where applicable. Final dataset license/export review remains outstanding; no blanket MIT claim is made for data.

Run from the repository root:

```powershell
python agentsLog/kwiscion/essay-corpus-sol/build_corpus.py
python agentsLog/kwiscion/essay-corpus-sol/validate_corpus.py
```

Acquisition is explicit and network-dependent; running `acquire_sources.py` again replaces snapshots and requires rebuilding and re-reviewing the manifest. `validate_corpus.py` checks structure, length, pairing, draft gates and hashes only. It does not certify truth, coherence, novelty, rights or contamination absence.

Outstanding gates: cross-corpus source/alias and near-duplicate audit; connected source-group evaluation split; final rights/export check. Keep every status DRAFT and accepted count zero until those gates pass. No claims about pretrained-model exposure are made.
