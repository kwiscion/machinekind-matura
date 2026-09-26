"""Verify frozen evaluation evidence locally; no network or model calls."""
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[2]
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    source_input = root / manifest["input_path"]
    assert digest(source_input) == manifest["input_sha256"], "input bytes changed"
    inputs = {r["id"]: r for r in map(json.loads, source_input.read_text(encoding="utf-8").splitlines())}
    records = []
    for name, expected in manifest["files_sha256"].items():
        assert digest(folder / name) == expected, f"frozen file changed: {name}"
        if name.startswith("topics-"):
            records.extend(json.loads((folder / name).read_text(encoding="utf-8")))
    assert len(records) == 16 and len({r["id"] for r in records}) == 16
    assert {r["id"] for r in records} == set(inputs)
    aspects = 0
    for record in records:
        original = inputs[record["id"]]
        assert record["source_group_id"] == original["source_group_id"]
        assert record["prompt_sha256"] == hashlib.sha256(original["prompt"].encode()).hexdigest()
        assert sorted(t["number"] for t in record["topics"]) == [1, 2]
        sources = {s["source_id"]: s for s in record["sources"]}
        assert len(sources) == len(record["sources"])
        for topic in record["topics"]:
            assert topic["requirements"] and topic["interpretive_flexibility"]
            assert topic["aspects"]
            for aspect in topic["aspects"]:
                assert aspect["name"] and aspect["facts"] and aspect["causal_explanation"]
                aspects += 1
                for fact in aspect["facts"]:
                    assert fact["claim"] and fact["locator"] and fact["source_id"] in sources
            for trap in topic["traps"]:
                assert all(s in sources for s in trap["source_ids"])
    source_rows = list(map(json.loads, (folder / "sources.jsonl").read_text(encoding="utf-8").splitlines()))
    assert len({s["source_id"] for s in source_rows}) == len(source_rows)
    for source in source_rows:
        assert all(source.get(k) for k in ["source_id", "url", "title", "publisher",
                   "retrieved_at", "revision_or_sha256", "license", "allowed_use"])
        assert source["allowed_use"] == ["reference"]
    assert manifest["candidate_answers_inspected"] is False
    assert manifest["existing_eval16_fact_cards_inspected"] is False
    assert manifest["model_api_calls"] == manifest["gpu_calls"] == manifest["purchases"] == 0
    print(f"PASS: 16 inputs, 32 alternatives, {aspects} evidence dimensions, "
          f"{len(source_rows)} reference records; frozen bytes and references match.")


if __name__ == "__main__":
    main()
