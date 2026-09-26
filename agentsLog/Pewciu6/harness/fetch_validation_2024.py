#!/usr/bin/env python3
"""Re-acquire (or verify) the May 2024 history formula-2023 VALIDATION PDFs listed in
agentsLog/Pewciu6/sources/validation_2024_sources.jsonl.

Downloads go to each record's git-ignored `local_path` (agentsLog/Pewciu6/private/...).
Never commit the PDFs. The zasady (marking rules) file is a RESTRICTED answer key.

  python3 agentsLog/Pewciu6/harness/fetch_validation_2024.py            # verify existing, fetch missing
  python3 agentsLog/Pewciu6/harness/fetch_validation_2024.py --refetch  # force re-download
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MANIFEST = os.path.join(REPO, "agentsLog", "Pewciu6", "sources", "validation_2024_sources.jsonl")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--manifest", default=MANIFEST)
    args = ap.parse_args()
    rc = 0
    with open(args.manifest, encoding="utf-8") as fh:
        recs = [json.loads(l) for l in fh if l.strip()]
    for r in recs:
        lp = r.get("local_path")
        if not lp:
            continue
        dest = os.path.join(REPO, lp)
        if "/private/" not in dest.replace(os.sep, "/"):
            sys.exit("refusing to write outside a git-ignored private/ path: %s" % lp)
        if args.refetch or not os.path.exists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            req = urllib.request.Request(r["url"], headers={"User-Agent": "Mozilla/5.0 (matura-eval-audit)"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        got = sha256(dest)
        want = r["revision_or_sha256"].split(":", 1)[-1]
        status = "OK" if got == want else "MISMATCH (upstream revision changed?)"
        if got != want:
            rc = 1
        print("%-24s %s %s" % (r["source_id"], got, status))
    return rc


if __name__ == "__main__":
    sys.exit(main())
