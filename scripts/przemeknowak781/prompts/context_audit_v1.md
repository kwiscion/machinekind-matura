# Context audit — context_audit_v1

Earlier judges saw only the cited claims. You check each record against the full article, which is available in the JSON files listed in `article_files` (`sections[].heading`, `sections[].text`). For every evidence claim, find it in the article and read the surrounding paragraph.

Flag a record only for one of these defects:
- `context_distortion`: the surrounding text changes the meaning of the claim, and the answer relies on the distorted reading. Examples: the article presents it as a refuted or disputed view ("niesłusznie", "według legendy", "część historyków"), as a plan that was not carried out, as a different person's or period's action, or with a qualifier the answer drops ("prawdopodobnie", "ok.", "według źródeł rosyjskich").
- `contradicted_by_article`: the article contradicts a fact in the answer or the prompt.
- `misattributed_subject`: the claim is about a different subject than the answer assumes (e.g., a date that belongs to another event in the same section).

Do not flag a record just because the answer omits article details, or because the claims are short; that was checked already. Be concrete: quote the article passage that shows the defect.

Output per record: `{"id": "...", "flag": true|false, "defect": "<code or empty>", "evidence": "<quoted article passage and short explanation, or empty>"}`

## Confirmation (second agent)
A second, independent agent receives only the flagged records and the first agent's finding. It re-reads the article passage and tries to refute the finding. It returns `confirmed: true` only if the defect is clearly real; if the finding is wrong or doubtful, `confirmed: false`. A record is excluded only when the defect is confirmed.
