"""Structural/provenance checks only; this is not historical or independent review."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(name):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines() if line.strip()]

essays, repairs = read("essays.jsonl"), read("repairs.jsonl")
sources = read("sources.jsonl") + read("crosscheck-sources.jsonl")
cards, groups = read("evidence-cards.jsonl"), read("source-groups.jsonl")
assert len(essays) == len(repairs) == len(groups) == 4
assert len({r["response"] for r in essays + repairs}) == 4
assert len({r["id"] for r in essays + repairs}) == 8
assert len({r["normalized_prompt_sha256"] for r in essays + repairs}) == 8
source_map = {r["source_id"]: r for r in sources}
essay_map = {r["id"]: r for r in essays}
required = {"id", "source_group_id", "prompt", "response", "body_word_count", "fact_claims", "source_ids", "synthetic_model", "generation_date", "status"}
for row in essays + repairs:
    assert required <= row.keys()
    count = len(re.findall(r"\S+", row["response"]))
    assert 400 <= count <= 500 and count == row["body_word_count"]
    assert row["split"] is None and row["status"] == "synthetic_draft_pending_independent_review"
    assert not any(s in row["response"] for s in ["Oczywiście!", "Temat 1:", "Temat 2:", "Mam nadzieję", "Dalszą część mogę", "```", "# "])
    assert "\ufffd" not in row["response"]
    assert all(sid in source_map and source_map[sid]["source_group_id"] == row["source_group_id"] for sid in row["source_ids"])
    for claim in row["fact_claims"]:
        assert claim["source_group_id"] == row["source_group_id"]
        assert all(1 <= p <= 6 for p in claim["essay_paragraphs"])
        assert set(claim["source_ids"]) <= set(row["source_ids"])
    if row["task_type"] == "essay_repair":
        parent = essay_map[row["parent_essay_id"]]
        assert parent["response"] == row["response"] and parent["source_group_id"] == row["source_group_id"]
        assert row["corrupted_response"] != row["response"]
        if "underlength" in row["defects"]:
            assert len(row["corrupted_response"].split()) < 300
        if "multiple_topic_answers" in row["defects"]:
            assert "Temat 1:" in row["corrupted_response"] and "Temat 2:" in row["corrupted_response"]

for source in sources:
    path = ROOT / source["local_path"]
    assert source["revision_or_sha256"] == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    assert source["license"] and source["url"] and source["retrieved_at"]
for group in groups:
    assert group["split"] is None
    assert len(group["example_ids"]) == 2
    assert len(group["aliases"]) == len(set(a.casefold() for a in group["aliases"]))

review_path = ROOT / "independent-review.json"
review_state = "pending"
if review_path.exists():
    review = json.loads(review_path.read_text(encoding="utf-8"))
    audited = {r["id"]: r for r in review["records"]}
    for row in essays + repairs:
        assert hashlib.sha256(row["response"].encode()).hexdigest() == audited[row["id"]]["response_sha256"]
        assert hashlib.sha256(row["prompt"].encode()).hexdigest() == audited[row["id"]]["prompt_sha256"]
    review_state = "accepted_with_limitations; canonical export and exclusion review pending"

summary = {
    "result": "pass", "verification_type": "local_structural_and_provenance_only",
    "essays": 4, "repair_pairs": 4, "unique_target_essays": 4, "source_groups": 4,
    "licensed_reference_sources": 5, "institutional_primary_crosschecks": 5,
    "evidence_cards": len(cards), "verified_training_examples": 0,
    "word_counts": {r["id"]: r["body_word_count"] for r in essays},
    "negative_input_word_counts_including_wrappers": {r["id"]: len(r["corrupted_response"].split()) for r in repairs},
    "source_hashes_verified": len(sources),
    "benchmark_contamination_check": "not performed by this benchmark-blind generator; isolated custodian review required",
    "independent_factual_review": review_state,
    "semantic_single_topic_check": "generator inspection only; no claim of automated semantic validation"
}
(ROOT / "validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
tracked_payloads = sorted(p for p in ROOT.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
(ROOT / "SHA256SUMS.txt").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in tracked_payloads), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
