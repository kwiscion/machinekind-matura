# Essay cleaner independent review

Root inspected the merged PR119 controller at13d453921cad8e820b51138dbfc434dc6faee823 and reproduced two content-loss cases with CPU-only original fixtures. The author's17/17 fidelity packet did not cover these cases.

- A complete historical sentence formatted as a Markdown heading is deleted wholesale by clean_body, even when its removal stays below25% of words. Preserve substantive prose while stripping formatting, or reject ambiguity; remove only actual structural labels.
- parse_output accepts arbitrary short text outside JSON as a wrapper and discards it. A substantive dated conclusion of fewer than40words is therefore silently removed. Outside text must match an explicit non-substantive wrapper; otherwise regenerate.
- Aspect/source-word substring checks are semantic heuristics, not reliable hard requirements. An essay can address an aspect or use evidence without naming the generic label. Use these as critic diagnostics, with the independent factual reviewer assessing actual coverage.

Exact original synthetic examples and required regressions were sent to [#80](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848806894). Existing raw experiments remain immutable. The new larger-thinking wave is separately authorized, but its adopted cleaner must preserve content before freezing. This review reports specific defects, not a claim that previous live essays lost content.

The initial live contract probe's length-only expansion also added a factual error; reaching the soft400-word target no longer justifies a standalone repair. The hard300minimum and substantive argument quality remain separate.
