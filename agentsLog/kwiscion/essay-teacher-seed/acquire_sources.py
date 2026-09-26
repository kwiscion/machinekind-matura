"""Acquire only the four independently chosen general-history reference pages."""
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ("wiki-solon", "Solon", "history-solon-reforms"),
    ("wiki-casimir", "Casimir_III_the_Great", "history-casimir-iii-statebuilding"),
    ("wiki-lublin", "Union_of_Lublin", "history-lublin-union-1569"),
    ("wiki-january", "January_Uprising", "history-january-uprising-peasant-policy"),
]

def main():
    directory = ROOT / "sources"
    directory.mkdir(exist_ok=True)
    records = []
    for source_id, title, group in SOURCES:
        url = "https://en.wikipedia.org/wiki/" + title
        request = urllib.request.Request(url, headers={"User-Agent": "MaturaTeacherSeed/1.0 (reference attribution audit)"})
        with urllib.request.urlopen(request, timeout=40) as response:
            content = response.read()
        path = directory / (source_id + ".html")
        path.write_bytes(content)
        html = content.decode("utf-8")
        match = re.search(r'"wgRevisionId"\s*:\s*(\d+)', html) or re.search(r'oldid=(\d+)', html)
        revision = match.group(1) if match else None
        records.append({
            "source_id": source_id, "source_group_id": group,
            "url": url, "title": title.replace("_", " "),
            "publisher": "Wikipedia contributors; Wikimedia Foundation host",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "revision_or_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "revision_id": revision,
            "permalink": "https://en.wikipedia.org/w/index.php?title=" + title + "&oldid=" + revision if revision else None,
            "license": "CC-BY-SA-4.0 for article text, except separately credited material",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "attribution": "Wikipedia contributors, " + title.replace("_", " ") + ", linked revision and page history",
            "history_url": "https://en.wikipedia.org/w/index.php?title=" + title + "&action=history",
            "allowed_use": ["reference", "train_subject_to_independent_review_and_license_compliance", "redistribute_text_with_attribution_and_sharealike"],
            "local_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "notes": "Licensed secondary source. No images downloaded. HTML includes navigation/third-party references; snapshot is review evidence, not a ready public dataset. Prose in essays is newly composed; original analysis is labeled in evidence cards."
        })
    (ROOT / "sources.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    print(json.dumps({"sources": len(records), "revision_ids": [r["revision_id"] for r in records]}))

if __name__ == "__main__":
    main()
