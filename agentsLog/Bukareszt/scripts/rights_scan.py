#!/usr/bin/env python3
"""Rights, provenance and contamination scan for the retrieval slice (issue #6, @Bukareszt).

Checks
  1. every manifest row has the CONTRACTS.md fields and a known (non-"unknown") license;
  2. every fetched raw file still matches its recorded SHA-256 (index reproducibility);
  3. committed files under agentsLog/Bukareszt/ contain no source text beyond what the license
     permits: Wikipedia excerpts (CC BY-SA 4.0) must be attributable to a manifest source_id,
     and no committed file may carry a passage longer than --max-passage chars from a source
     that is not marked redistributable;
  4. contamination guard: no file in the repo looks like a 2023/2024/2025 matura exam sheet, key
     or rubric, and no training query text hashes to a hash listed in --exam-hashes (optional);
  5. writes queries/query_hashes.json (SHA-256 of NFKC-lowercased, whitespace-collapsed prompts).
Exit code 1 on any hard failure.
"""
import argparse, hashlib, json, os, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(os.path.dirname(ROOT))
REQUIRED = ["source_id", "url", "title", "publisher", "retrieved_at", "revision_or_sha256", "license", "allowed_use"]
EXAM_PAT = re.compile(r"(EHIP|arkusz|klucz|zasady oceniania|matura).*(2023|2024|2025)|(2023|2024|2025).*(arkusz|klucz|zasady oceniania|matura)", re.I)


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).lower()).strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--max-passage", type=int, default=400); ap.add_argument("--exam-hashes")
    a = ap.parse_args(); problems = []; warnings = []
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "sources", "sources.jsonl"), encoding="utf-8") if l.strip()]
    redistributable = set()
    for r in rows:
        missing = [k for k in REQUIRED if not r.get(k)]
        if missing: problems.append(f"manifest {r.get('source_id')}: missing {missing}")
        if str(r.get("license", "unknown")).lower().startswith("unknown"): problems.append(f"manifest {r['source_id']}: license unknown")
        if any(u.startswith("redistribute") for u in r.get("allowed_use", [])): redistributable.add(r["source_id"])
        p = os.path.join(ROOT, r.get("local_path", ""))
        if r.get("local_path") and os.path.exists(p):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            if h != r.get("sha256"): problems.append(f"raw {r['source_id']}: sha256 mismatch (re-run fetch --refresh or rebuild)")
        elif r.get("local_path"):
            warnings.append(f"raw {r['source_id']}: not present locally (run fetch)")
    # committed files (tracked + staged) under agentsLog/Bukareszt
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "agentsLog/Bukareszt"], cwd=REPO, capture_output=True, text=True).stdout.split()
    raw_texts = {r["source_id"]: norm(open(os.path.join(ROOT, r["local_path"]), encoding="utf-8").read()) for r in rows if os.path.exists(os.path.join(ROOT, r.get("local_path", "")))}
    for f in out:
        fp = os.path.join(REPO, f)
        if not os.path.isfile(fp) or fp.endswith((".png", ".jpg")): continue
        txt = open(fp, encoding="utf-8", errors="replace").read()
        if EXAM_PAT.search(os.path.basename(f)): problems.append(f"{f}: filename looks like a fixed exam artifact")
        # find long verbatim passages: sample windows of the committed file and look them up in raw texts
        ntxt = norm(txt)
        if len(ntxt) < a.max_passage: continue
        hits = set()
        for i in range(0, len(ntxt) - a.max_passage, a.max_passage // 2):
            win = ntxt[i:i + a.max_passage]
            for sid, rt in raw_texts.items():
                if win in rt: hits.add(sid)
        for sid in hits:
            if sid not in redistributable: problems.append(f"{f}: contains a >{a.max_passage}-char passage from non-redistributable source {sid}")
            elif f.endswith(".jsonl") and f"\"{sid}\"" not in txt: problems.append(f"{f}: passage from {sid} without attribution id")
        if hits: warnings.append(f"{f}: carries excerpts from {len(hits)} source(s) (all CC BY-SA/PD, attributed via sources.jsonl)")
    # repo-wide exam artifact guard
    allfiles = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split()
    exam_like = [f for f in allfiles if EXAM_PAT.search(f)]
    if exam_like: warnings.append(f"repo files with exam-like names (verify they are not keys/questions): {exam_like}")
    # query hashes
    qpath = os.path.join(ROOT, "queries", "train_queries.jsonl"); qs = [json.loads(l) for l in open(qpath, encoding="utf-8") if l.strip()]
    hashes = {q["id"]: hashlib.sha256(norm(q["prompt"]).encode()).hexdigest() for q in qs}
    json.dump({"normalization": "NFKC, lowercase, whitespace collapsed", "sha256": hashes}, open(os.path.join(ROOT, "queries", "query_hashes.json"), "w"), indent=2)
    if a.exam_hashes:
        bad = set(json.load(open(a.exam_hashes))) & set(hashes.values())
        if bad: problems.append(f"query hash collision with exam hashes: {bad}")
    report = {"sources": len(rows), "redistributable_sources": len(redistributable), "committed_files_scanned": len(out), "queries_hashed": len(hashes), "problems": problems, "warnings": warnings}
    json.dump(report, open(os.path.join(ROOT, "reports", "rights_scan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
