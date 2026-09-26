#!/usr/bin/env python3
"""Rubric sanity checks on the restricted May 2024 VALIDATION keys (no model involved).

oracle : every item answered with the official reference answer from the key.
         Every auto-scored item should get full credit and no item should score 0
         with upper bound 0. Any miss points to a rubric-translation bug.
null   : every item answered with an empty string (floor; all abstentions, 0 points).

Oracle/null outputs are key-derived, so they are written only to private/. Only aggregates
(no item text) go to results/validation_2024_sanity.json.

  python3 agentsLog/Pewciu6/harness/sanity_validation_2024.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matura_harness as mh  # noqa: E402

OWNER = os.path.dirname(HERE)
PRIV = os.path.join(OWNER, "private", "validation_2024")
KEYS = os.path.join(PRIV, "eval_keys.jsonl")
OUT = os.path.join(OWNER, "results", "validation_2024_sanity.json")


class A(object):
    def __init__(self, **kw):
        self.__dict__.update(dict(corpus=None, split="VALIDATION", model_manifest=None, scorecard=None,
                                  items_out=None, sealed_release_ack=False, quiet=True))
        self.__dict__.update(kw)


def run(name, make):
    # items without an official example answer (the essay) cannot be oracle-tested; excluded + counted
    keys = [k for k in mh.read_jsonl(KEYS) if (k.get("reference_answer") or "").strip() or not name.startswith("oracle")]
    path = os.path.join(PRIV, "sanity_%s_outputs.jsonl" % name)
    mh.write_jsonl(path, [{"id": k["id"], "backend": "sanity", "model": name, "model_revision": "n/a",
                           "raw_response": make(k), "usage": {}, "latency_s": 0.0, "error": None}
                          for k in keys])
    sc, items = mh.score(A(outputs=path, keys=KEYS, run_id="sanity-" + name,
                           items_out=os.path.join(PRIV, "sanity_%s_items.jsonl" % name)))
    by_mode = {}
    kmode = {k["id"]: k.get("scoring_mode") for k in keys}
    for it in items:
        b = by_mode.setdefault(kmode[it["id"]], {"n": 0, "points": 0.0, "upper": 0.0, "max": 0.0,
                                                 "full_credit": 0, "status": {}})
        b["n"] += 1
        b["points"] += it["points"]
        b["upper"] += it["points_upper_bound"]
        b["max"] += it["max_points"]
        b["full_credit"] += int(it["points"] >= it["max_points"])
        b["status"][it["status"]] = b["status"].get(it["status"], 0) + 1
    auto_misses = sum(1 for it in items if kmode[it["id"]] == "auto" and it["points"] < it["max_points"])
    return {"items_tested": len(keys), "items_excluded_no_reference": sc["denominator"]["excluded_items"],
            "overall": sc["overall"], "by_scoring_mode": by_mode,
            "auto_items_not_full_credit": auto_misses,
            "error_category_counts": sc["error_category_counts"]}


def main():
    if not os.path.exists(KEYS):
        sys.exit("run build_validation_2024.py first")
    res = {"provisional": True, "keys_sha256": mh.sha256_file(KEYS),
           "oracle": run("oracle", lambda k: k.get("reference_answer") or ""),
           # format robustness: same answers embedded in a sentence with newlines flattened
           "oracle_wrapped": run("oracle_wrapped", lambda k: "Moja odpowiedź na to zadanie jest taka: " +
                                 " ; ".join(l.strip() for l in (k.get("reference_answer") or "").split("\n")
                                            if l.strip()) + ". To wszystko."),
           # adversarial: hedge every option; auto/gate credit here = rubric false positive
           "shotgun": run("shotgun", lambda k: "Rozstrzygnięcie: Tak / Nie / A / B / C / D\n"
                                                "A B C D\n1 P F 2 P F 3 P F"),
           "null": run("null", lambda k: "")}
    mh.write_json(OUT, res)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["oracle"]["auto_items_not_full_credit"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
