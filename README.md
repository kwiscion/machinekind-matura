# Matura: small offline exam assistant

Overnight hackathon working assumption: **Polish history matura**. The lead must confirm the final subject before promotion; all records carry a `subject` field so other work can proceed. The final system may use local retrieval and tools, and each saved model's weights must fit within **8 GB**. Closed models and synthetic data are allowed during development; the final inference path must run offline.

The handoff package is in [docs/overnight/PLAN.md](docs/overnight/PLAN.md). Start with [SETUP.md](docs/overnight/SETUP.md), then read [CONTRACTS.md](docs/overnight/CONTRACTS.md) and your assigned issue. Source and publication rules are in [SOURCE.md](SOURCE.md). GitHub issues are the overnight scheduling authority; live assignments are recorded in [ISSUE_LINKS.md](docs/overnight/ISSUE_LINKS.md); local issue bodies preserve the original briefs.

| Issue | Owner | Local brief | GitHub lookup |
| --- | --- | --- | --- |
| Lead, integration and freeze | @kwiscion | [Lead](docs/overnight/issues/lead.md) | [Search](https://github.com/kwiscion/machinekind-matura/issues/3) |
| Grounded training data | @przemeknowak781 | [Data](docs/overnight/issues/data.md) | [Search](https://github.com/kwiscion/machinekind-matura/issues/4) |
| Compact model experiments | @ljaniec | [Spark](docs/overnight/issues/spark.md) | [Search](https://github.com/kwiscion/machinekind-matura/issues/5) |
| Historical retrieval | @Bukareszt | [Retrieval](docs/overnight/issues/retrieval.md) | [Search](https://github.com/kwiscion/machinekind-matura/issues/6) |
| Evaluation and rubric audit | @Pewciu6 | [Evaluation](docs/overnight/issues/eval.md) | [Search](https://github.com/kwiscion/machinekind-matura/issues/7) |

The canonical input is JSONL with `{ "id", "prompt", "images"? }`; each task supplies its own standalone script or adapter. A small `infer.py` prototype exists locally but is not yet published or required on a fresh clone. Hosted development endpoints need explicit configuration; keep credentials out of Git.

No repository-wide code or dataset license has been selected. Original code could later use MIT if the owner approves; each third-party dataset subset needs its own source/license review.

