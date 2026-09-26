#!/usr/bin/env python3
"""CPU-only, stdlib-only evaluation harness for machinekind-matura (issue #7).

Subcommands
-----------
score            Join model outputs (JSONL) to restricted eval keys (JSONL) by id,
                 grade each item with its item-level rubric, run the citation-support
                 audit, and emit a scorecard JSON plus optional item-level JSONL.
audit-citations  Run only the citation-support audit for outputs against a source corpus.
leakcheck        Check that runner (model-facing) input JSONL carries no key fields or
                 answer strings from eval_keys.jsonl.
validate         Light schema validation of keys / outputs / sources files.

Design rules (see docs/overnight/CONTRACTS.md):
* Scoring code is separate from answer keys; keys are only read from a path given
  on the command line and never copied into the scorecard or item-level output.
* All automatic grades are PROVISIONAL heuristics; a human or independent
  source-grounded review decides.
* SEALED_TEST keys are refused unless --sealed-release-ack is passed (lead release).
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import statistics
import sys
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone

GRADER_VERSION = "matura-harness-heuristic-v1"

ERROR_CATEGORIES = [
    "chronology",
    "entity_confusion",
    "essay_structure",
    "abstention",
    "citation_unsupported",
    "image_ocr",
    "content_incorrect",
]
EXCLUSION_REASONS = ["inference_error", "missing_output", "duplicate_output"]
TASK_TYPES = [
    "short_answer",
    "multiple_choice",
    "chronology",
    "source_analysis",
    "essay_plan",
    "essay",
    "vision_ocr",
]
SPLITS = ["TRAIN", "DEV", "VALIDATION", "SEALED_TEST"]
KEY_ONLY_FIELDS = {
    "answer", "answers", "accepted", "accepted_answers", "rubric", "rubric_criteria",
    "expected", "expected_order", "expected_choice", "expected_years", "distractors",
    "criteria", "key", "keys", "scoring", "reference_answer",
}

ABSTENTION_PATTERNS = [
    r"^\s*$",
    r"\bnie wiem\b",
    r"\bnie jestem w stanie\b",
    r"\bnie potrafie\b",
    r"\bbrak (mozliwosci|wystarczajacych|danych|odpowiedzi)\b",
    r"\bnie mozna (tego )?(ustalic|stwierdzic|okreslic)\b",
    r"\bi (do not|don't) know\b",
    r"\bi cannot (determine|answer)\b",
    r"\bi am (unable|not able) to\b",
    r"\binsufficient (information|evidence)\b",
    r"\b(abstain|abstaining)\b",
]
INLINE_CITATION_RE = re.compile(r"\[\[([A-Za-z0-9_.:\-]+)(?:#([^\]]+))?\]\]")
YEAR_RE = re.compile(r"(?<!\d)(\d{3,4})(?!\d)")
STOPWORDS = set(
    "a an and are as at be by for from in is it of on or that the this to was were with "
    "i w we z ze na do od po o u za przez oraz lub ale nie sie jest byl byla bylo byly "
    "to ten ta tego tej ktory ktora ktore jak czy co ich jego jej".split()
)


# ----------------------------------------------------------------------------- utils

def fold(text):
    """Casefold + strip diacritics (incl. Polish l-stroke) + collapse whitespace."""
    if text is None:
        return ""
    text = str(text).replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^\w\s#:\-\[\]]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_phrase(haystack_folded, phrase):
    p = fold(phrase)
    if not p:
        return False
    return re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", haystack_folded) is not None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit("%s:%d: invalid JSON (%s)" % (path, lineno, exc))
    return records


def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def machine_info():
    node = platform.node() or ""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "hostname_sha256_12": hashlib.sha256(node.encode()).hexdigest()[:12],
        "cpu_only": True,
    }


def response_text(out):
    for k in ("raw_response", "response", "output", "text"):
        v = out.get(k)
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            for kk in ("content", "text"):
                if isinstance(v.get(kk), str):
                    return v[kk]
    return ""


def model_revision(out):
    return {
        "backend": out.get("backend"),
        "model": out.get("model") or out.get("model_id"),
        "model_revision": out.get("model_revision") or out.get("revision"),
    }


# ------------------------------------------------------------------ citation audit

def load_corpus(paths):
    """Corpus JSONL: {source_id, locator, text} passages (retrieval corpus, NOT keys)."""
    corpus = defaultdict(dict)
    for p in paths or []:
        for rec in read_jsonl(p):
            sid = rec.get("source_id")
            if sid is None:
                continue
            corpus[sid][str(rec.get("locator", ""))] = rec.get("text", "")
    return corpus


def extract_citations(out):
    """Citations from an explicit `citations` field and inline [[source_id#locator]] markers."""
    cits = []
    for c in out.get("citations") or []:
        if isinstance(c, dict) and c.get("source_id"):
            cits.append({"source_id": c["source_id"], "locator": str(c.get("locator", "")),
                         "claim": c.get("claim", ""), "origin": "field"})
    for sent in re.split(r"(?<=[.!?])\s+", response_text(out)):
        for m in INLINE_CITATION_RE.finditer(sent):
            claim = INLINE_CITATION_RE.sub("", sent).strip()
            cits.append({"source_id": m.group(1), "locator": m.group(2) or "",
                         "claim": claim, "origin": "inline"})
    return cits


def content_tokens(text):
    return [t for t in fold(text).split() if len(t) > 2 and t not in STOPWORDS]


def audit_citation(cit, corpus, min_overlap=0.5):
    """Lexical, provisional check that the cited passage supports the claim.

    supported     : passage exists, >= min_overlap of claim content tokens present
                    (prefix-5 stems, to tolerate Polish inflection), and every year
                    in the claim appears in the passage.
    unsupported   : passage exists but the checks fail.
    source_missing / locator_missing : citation cannot be resolved (counts as unsupported).
    A recognised title is NOT evidence; only passage text counts.
    """
    sid, loc, claim = cit["source_id"], cit.get("locator", ""), cit.get("claim", "")
    if sid not in corpus:
        return {"status": "source_missing", "overlap": 0.0}
    passages = corpus[sid]
    if loc and loc not in passages:
        return {"status": "locator_missing", "overlap": 0.0}
    text = passages[loc] if loc else " ".join(passages.values())
    ctoks = content_tokens(claim)
    if not ctoks:
        return {"status": "unsupported", "overlap": 0.0, "note": "empty claim"}
    ptoks = set(t[:5] for t in content_tokens(text))
    overlap = sum(1 for t in ctoks if t[:5] in ptoks) / float(len(ctoks))
    claim_years = set(YEAR_RE.findall(claim))
    passage_years = set(YEAR_RE.findall(text))
    years_ok = claim_years.issubset(passage_years)
    res = {"status": "supported" if (overlap >= min_overlap and years_ok) else "unsupported",
           "overlap": round(overlap, 3)}
    if not years_ok:
        res["years_not_in_source"] = sorted(claim_years - passage_years)
    return res


# ------------------------------------------------------------------------- grading

def detect_abstention(text):
    f = fold(text)
    return any(re.search(p, f) for p in ABSTENTION_PATTERNS)


def extract_order(text, labels):
    """Return labels in the order they first appear in the response."""
    f = fold(text)
    alts = "|".join(re.escape(fold(l)) for l in sorted(labels, key=len, reverse=True))
    seen = []
    for m in re.finditer(r"(?<![\w])(" + alts + r")(?![\w])", f):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def grade_item(key, out, corpus):
    """Grade one joined (key, output) pair. Returns an item result without key content."""
    rub = key.get("rubric") or {}
    max_points = float(rub.get("max_points", key.get("max_points", 1)))
    text = response_text(out)
    f = fold(text)
    errors = []
    points = 0.0
    criteria_results = []
    abstained = detect_abstention(text)

    if abstained:
        if key.get("expect_abstention"):
            points = max_points
        else:
            errors.append("abstention")
    elif key.get("expect_abstention"):
        errors.append("content_incorrect")
    else:
        mode = rub.get("mode", "criteria")
        if mode == "choice":
            exp = sorted(set(c.upper() for c in rub.get("expected_choice", [])))
            # standalone capital letters A-F in the original (not upper-cased) text
            got = sorted(set(re.findall(r"(?<![^\W\d_])([A-F])(?![^\W\d_])", text)))
            ok = got == exp
            points = max_points if ok else 0.0
            criteria_results.append({"criterion_id": "choice", "met": ok})
            if not ok:
                errors.append(rub.get("error_on_fail", "content_incorrect"))
        elif mode == "order":
            exp = [fold(x) for x in rub.get("expected_order", [])]
            ok = extract_order(text, exp) == exp
            points = max_points if ok else 0.0
            criteria_results.append({"criterion_id": "order", "met": ok})
            if not ok:
                errors.append("chronology")
        else:  # criteria
            for crit in rub.get("criteria", []):
                any_of = crit.get("any_of") or []
                all_of = crit.get("all_of") or []
                met = ((not any_of) or any(contains_phrase(f, a) for a in any_of)) and \
                    all(contains_phrase(f, a) for a in all_of)
                kind = crit.get("kind", "content")
                if met:
                    points += float(crit.get("points", 1))
                criteria_results.append({"criterion_id": crit.get("criterion_id"),
                                         "kind": kind, "met": met})
                if not met:
                    if kind == "structure":
                        errors.append("essay_structure")
                    elif kind == "date":
                        errors.append("chronology")
                    elif kind == "entity" and any(contains_phrase(f, d)
                                                  for d in key.get("distractors") or []):
                        errors.append("entity_confusion")
                    else:
                        errors.append("content_incorrect")
            points = min(points, max_points)
        # wrong-year check (chronology) for any mode
        exp_years = set(str(y) for y in (key.get("expected_years") or []))
        if exp_years:
            said = set(YEAR_RE.findall(text))
            if said and not (said & exp_years):
                errors.append("chronology")

    # citation-support audit
    cits = extract_citations(out)
    cit_results = []
    for c in cits:
        r = audit_citation(c, corpus)
        row = {"source_id": c["source_id"], "locator": c.get("locator", ""), "origin": c["origin"]}
        row.update(r)
        cit_results.append(row)
    any_bad_cit = any(r["status"] != "supported" for r in cit_results)
    if key.get("requires_citation") and not abstained:
        if not cits or any_bad_cit:
            errors.append("citation_unsupported")
            if not cits:
                criteria_results.append({"criterion_id": "citation_present", "met": False})
            cap = rub.get("citation_fail_max_points")
            if cap is not None:
                points = min(points, float(cap))
    elif any_bad_cit:
        errors.append("citation_unsupported")

    if key.get("task_type") == "vision_ocr" and points < max_points and not abstained:
        errors.append("image_ocr")

    # dedupe in taxonomy order; content_incorrect only when nothing more specific applies
    errs = [e for e in ERROR_CATEGORIES if e in errors]
    if len(errs) > 1 and "content_incorrect" in errs:
        errs.remove("content_incorrect")

    if points >= max_points and not errs:
        status = "correct"
    elif points > 0:
        status = "partial"
    else:
        status = "incorrect"
    return {
        "id": key["id"],
        "status": status,
        "points": round(points, 3),
        "max_points": max_points,
        "abstained": abstained,
        "error_categories": errs,
        "criteria": criteria_results,
        "citations": cit_results,
        "task_type": key.get("task_type"),
        "era": key.get("era"),
        "topic": key.get("topic"),
        "latency_s": out.get("latency_s", out.get("latency")),
        "grader": GRADER_VERSION,
        "provisional": True,
    }


def _bucket():
    return {"n": 0, "correct": 0, "partial": 0, "incorrect": 0, "points": 0.0, "max_points": 0.0}


def _add(b, it):
    b["n"] += 1
    b[it["status"]] += 1
    b["points"] += it["points"]
    b["max_points"] += it["max_points"]


def _finalize(b):
    b = dict(b)
    b["points"] = round(b["points"], 3)
    b["max_points"] = round(b["max_points"], 3)
    b["accuracy"] = round(b["correct"] / b["n"], 4) if b["n"] else None
    b["points_rate"] = round(b["points"] / b["max_points"], 4) if b["max_points"] else None
    return b


def score(args):
    keys = read_jsonl(args.keys)
    outputs = read_jsonl(args.outputs)
    corpus = load_corpus(args.corpus)

    splits = sorted(set(k.get("split", "UNKNOWN") for k in keys))
    if "SEALED_TEST" in splits and not args.sealed_release_ack:
        raise SystemExit("Refusing SEALED_TEST keys without --sealed-release-ack (lead release only).")
    if args.split and any(s != args.split for s in splits):
        raise SystemExit("Key split(s) %s do not match --split %s" % (splits, args.split))

    key_by_id = OrderedDict()
    for k in keys:
        if k["id"] in key_by_id:
            raise SystemExit("duplicate key id: %s" % k["id"])
        key_by_id[k["id"]] = k

    out_by_id, exclusions, orphans = {}, [], []
    for o in outputs:
        oid = o.get("id")
        if oid not in key_by_id:
            orphans.append(oid)
        elif oid in out_by_id:
            exclusions.append({"id": oid, "reason": "duplicate_output", "note": "first record kept"})
        else:
            out_by_id[oid] = o

    items = []
    for kid, key in key_by_id.items():
        o = out_by_id.get(kid)
        if o is None:
            exclusions.append({"id": kid, "reason": "missing_output"})
        elif o.get("error"):
            exclusions.append({"id": kid, "reason": "inference_error", "error": str(o["error"])[:200]})
        else:
            items.append(grade_item(key, o, corpus))

    revisions = [json.loads(r) for r in
                 sorted(set(json.dumps(model_revision(o), sort_keys=True) for o in out_by_id.values()))]

    by = {"task_type": defaultdict(_bucket), "era": defaultdict(_bucket), "topic": defaultdict(_bucket)}
    overall = _bucket()
    err_counts, cit_counts = Counter(), Counter()
    for it in items:
        for dim in by:
            _add(by[dim][str(it.get(dim) or "unspecified")], it)
        _add(overall, it)
        err_counts.update(it["error_categories"])
        for c in it["citations"]:
            cit_counts[c["status"]] += 1

    def kmax(kid):
        k = key_by_id[kid]
        return float((k.get("rubric") or {}).get("max_points", k.get("max_points", 1)))

    counted_excl = [e for e in exclusions if e["reason"] != "duplicate_output"]
    strict_max = overall["max_points"] + sum(kmax(e["id"]) for e in counted_excl)
    latencies = [float(it["latency_s"]) for it in items if isinstance(it.get("latency_s"), (int, float))]
    usage = Counter()
    for o in out_by_id.values():
        for k2, v in (o.get("usage") or {}).items():
            if isinstance(v, (int, float)):
                usage[k2] += v

    now = datetime.now(timezone.utc)
    scorecard = OrderedDict([
        ("run_id", args.run_id or "run-" + now.strftime("%Y%m%dT%H%M%SZ")),
        ("provisional", True),
        ("grader", GRADER_VERSION),
        ("split", splits[0] if len(splits) == 1 else splits),
        ("model_revisions", revisions),
        ("model_manifest", args.model_manifest),
        ("command", shlex.join([os.path.basename(sys.executable)] + sys.argv)),
        ("timestamp_utc", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("machine", machine_info()),
        ("inputs", {
            "outputs_sha256": sha256_file(args.outputs),
            "keys_sha256": sha256_file(args.keys),
            "corpus_sha256": [sha256_file(p) for p in (args.corpus or [])],
            "n_keys": len(keys),
            "n_output_records": len(outputs),
        }),
        ("denominator", {
            "scored_items": overall["n"],
            "excluded_items": len(counted_excl),
            "orphan_outputs_ignored": len(orphans),
            "policy": "lenient = scored items only; strict = exclusions count as 0 points",
        }),
        ("overall", _finalize(overall)),
        ("strict_points_rate", round(overall["points"] / strict_max, 4) if strict_max else None),
        ("by_task_type", {k: _finalize(v) for k, v in sorted(by["task_type"].items())}),
        ("by_era", {k: _finalize(v) for k, v in sorted(by["era"].items())}),
        ("by_topic", {k: _finalize(v) for k, v in sorted(by["topic"].items())}),
        ("error_category_counts", {c: err_counts.get(c, 0) for c in ERROR_CATEGORIES}),
        ("abstentions", sum(1 for it in items if it["abstained"])),
        ("citation_audit_counts", dict(cit_counts)),
        ("latency_s", {
            "n": len(latencies),
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "median": round(statistics.median(latencies), 3) if latencies else None,
            "max": round(max(latencies), 3) if latencies else None,
        }),
        ("usage_totals", dict(usage)),
        ("exclusions", exclusions),
        ("orphan_output_ids", orphans),
    ])
    if args.scorecard:
        write_json(args.scorecard, scorecard)
    if args.items_out:
        write_jsonl(args.items_out, items)
    if not args.quiet:
        print(json.dumps({"run_id": scorecard["run_id"], "overall": scorecard["overall"],
                          "denominator": scorecard["denominator"],
                          "error_category_counts": scorecard["error_category_counts"]},
                         ensure_ascii=False, indent=2))
    return scorecard, items


def audit_citations_cmd(args):
    corpus = load_corpus(args.corpus)
    rows = []
    for o in read_jsonl(args.outputs):
        for c in extract_citations(o):
            row = {"id": o.get("id"), "source_id": c["source_id"], "locator": c["locator"],
                   "origin": c["origin"]}
            row.update(audit_citation(c, corpus, args.min_overlap))
            row["provisional"] = True
            rows.append(row)
    if args.out:
        write_jsonl(args.out, rows)
    print(json.dumps(Counter(r["status"] for r in rows), indent=2))
    return rows


def leakcheck(args):
    keys = read_jsonl(args.keys)
    inputs = read_jsonl(args.inputs)
    problems = []
    answer_strings = set()
    for k in keys:
        for crit in (k.get("rubric") or {}).get("criteria", []):
            for a in (crit.get("any_of") or []) + (crit.get("all_of") or []):
                if len(fold(a)) >= args.min_len:
                    answer_strings.add(fold(a))
        ref = k.get("reference_answer")
        for a in (ref if isinstance(ref, list) else [ref]):
            if a and len(fold(a)) >= args.min_len:
                answer_strings.add(fold(a))
    for rec in inputs:
        bad = sorted(set(rec) & KEY_ONLY_FIELDS)
        if bad:
            problems.append({"id": rec.get("id"), "severity": "error", "key_fields": bad})
        extra = sorted(set(rec) - {"id", "prompt", "images", "system", "meta"} - KEY_ONLY_FIELDS)
        if extra:
            problems.append({"id": rec.get("id"), "severity": "warning", "unexpected_fields": extra})
        p = fold(rec.get("prompt", ""))
        hits = [a for a in answer_strings if a in p]
        if hits:
            # count only; never print the key strings themselves
            problems.append({"id": rec.get("id"), "severity": "warning", "answer_string_hits": len(hits)})
    n_err = sum(1 for p in problems if p["severity"] == "error")
    print(json.dumps({"inputs": len(inputs), "problems": problems, "errors": n_err}, indent=2))
    return 1 if n_err else 0


def validate(args):
    required = {
        "keys": ["id", "split", "task_type", "rubric"],
        "outputs": ["id"],
        "sources": ["source_id", "url", "title", "publisher", "retrieved_at",
                    "revision_or_sha256", "license", "allowed_use"],
    }[args.kind]
    bad = 0
    for i, rec in enumerate(read_jsonl(args.path), 1):
        missing = [f for f in required if f not in rec]
        if args.kind == "keys":
            if rec.get("split") not in SPLITS:
                missing.append("split(enum)")
            if rec.get("task_type") not in TASK_TYPES:
                missing.append("task_type(enum)")
            rub = rec.get("rubric") or {}
            if rub.get("mode", "criteria") not in ("criteria", "choice", "order"):
                missing.append("rubric.mode(enum)")
        if args.kind == "outputs" and not any(k in rec for k in ("raw_response", "response", "error")):
            missing.append("raw_response|error")
        if args.kind == "sources" and not isinstance(rec.get("allowed_use"), list):
            missing.append("allowed_use(array)")
        if missing:
            bad += 1
            print("record %d (%s): missing/invalid %s" % (i, rec.get("id") or rec.get("source_id"), missing))
    print("validated %s: %s" % (args.path, "OK" if not bad else "%d bad record(s)" % bad))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.required = True

    s = sub.add_parser("score")
    s.add_argument("--outputs", required=True, help="model outputs JSONL (append-only raw)")
    s.add_argument("--keys", required=True, help="restricted eval_keys.jsonl")
    s.add_argument("--corpus", action="append", help="citation corpus JSONL (repeatable)")
    s.add_argument("--split", help="assert all keys are from this split")
    s.add_argument("--run-id")
    s.add_argument("--model-manifest", help="path/URL of the model candidate manifest")
    s.add_argument("--scorecard", help="write scorecard JSON here")
    s.add_argument("--items-out", help="write item-level results JSONL (no key content)")
    s.add_argument("--sealed-release-ack", action="store_true")
    s.add_argument("--quiet", action="store_true")

    a = sub.add_parser("audit-citations")
    a.add_argument("--outputs", required=True)
    a.add_argument("--corpus", action="append", required=True)
    a.add_argument("--min-overlap", type=float, default=0.5)
    a.add_argument("--out")

    l = sub.add_parser("leakcheck")
    l.add_argument("--inputs", required=True, help="runner input JSONL (model-facing)")
    l.add_argument("--keys", required=True)
    l.add_argument("--min-len", type=int, default=8)

    v = sub.add_parser("validate")
    v.add_argument("kind", choices=["keys", "outputs", "sources"])
    v.add_argument("path")

    args = ap.parse_args(argv)
    if args.cmd == "score":
        score(args)
        return 0
    if args.cmd == "audit-citations":
        audit_citations_cmd(args)
        return 0
    if args.cmd == "leakcheck":
        return leakcheck(args)
    return validate(args)


if __name__ == "__main__":
    sys.exit(main())
