"""Fetch pinned plwiki revisions, split them into sections, and write sources.jsonl.

Usage: python scripts/przemeknowak781/fetch_sources.py [--topics PATH] [--out-dir PATH]
Raw section text goes to <out-dir>/cache/ (git-ignored); only the manifest is committed.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

API = "https://pl.wikipedia.org/w/api.php"
USER_AGENT = "machinekind-matura-data/0.1 (https://github.com/kwiscion/machinekind-matura)"
SKIP_CLASSES = {"reference", "mw-editsection", "navbox", "reflist", "references",
                "noprint", "metadata", "ambox", "mw-empty-elt", "toc", "hatnote"}
SKIP_TAGS = {"style", "script", "sup"}
VOID_TAGS = {"br", "img", "meta", "link", "hr", "input", "wbr", "area", "source", "col"}
BLOCK_TAGS = {"p", "li", "div", "tr", "dd", "dt", "caption", "figcaption", "table", "ul", "ol"}
DROP_SECTIONS = {"przypisy", "bibliografia", "linki zewnętrzne", "zobacz też", "uwagi"}


def api_get(params):
    params = {**params, "format": "json", "formatversion": "2"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def slugify(text):
    text = text.replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class SectionExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.skip_depth = 0
        self.sections = [{"heading": "lead", "parts": []}]
        self.in_heading = False
        self.heading_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            if tag == "br" and not self.skip_depth:
                self.sections[-1]["parts"].append("\n")
            return
        classes = set((dict(attrs).get("class") or "").split())
        skip = tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        self.stack.append((tag, skip))
        if skip:
            self.skip_depth += 1
        elif tag in ("h2", "h3") and not self.skip_depth:
            self.in_heading = True
            self.heading_parts = []
        elif tag in BLOCK_TAGS and not self.skip_depth:
            self.sections[-1]["parts"].append("\n")
        elif tag in ("td", "th") and not self.skip_depth:
            self.sections[-1]["parts"].append(" ")

    def handle_endtag(self, tag):
        while self.stack:
            open_tag, skip = self.stack.pop()
            if skip:
                self.skip_depth -= 1
            if open_tag in ("h2", "h3") and self.in_heading:
                self.in_heading = False
                heading = " ".join("".join(self.heading_parts).split())
                self.sections.append({"heading": heading, "parts": []})
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.in_heading:
            self.heading_parts.append(data)
        else:
            self.sections[-1]["parts"].append(data)


def clean(text):
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def parse_topics(path):
    topics = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = [f.strip() for f in raw.split("|")] + [""] * 5
        title, oldid, source_id, group, era = fields[:5]
        slug = slugify(title)
        topics.append({"title": title, "oldid": oldid or None,
                       "source_id": source_id or f"src-plwiki-{slug}",
                       "source_group_id": group or f"grp-{slug}", "era": era})
    return topics


def resolve_oldid(title):
    data = api_get({"action": "query", "titles": title, "redirects": 1,
                    "prop": "revisions", "rvprop": "ids|timestamp"})
    page = data["query"]["pages"][0]
    if page.get("missing"):
        return None, None, None
    rev = page["revisions"][0]
    return page["title"], rev["revid"], rev["timestamp"]


def main():
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics", default=root / "data/przemeknowak781/topics.txt")
    ap.add_argument("--out-dir", default=root / "data/przemeknowak781")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    cache = out_dir / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    manifest = out_dir / "sources.jsonl"
    pinned = {}
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                pinned[rec["source_id"]] = (rec["title"], int(rec["url"].rsplit("oldid=", 1)[1]))

    records, missing = [], []
    for t in parse_topics(args.topics):
        if t["oldid"] or t["source_id"] in pinned:
            title, oldid = pinned.get(t["source_id"], (t["title"], None))
            oldid = int(t["oldid"]) if t["oldid"] else oldid
            rev_ts = None
        else:
            title, oldid, rev_ts = resolve_oldid(t["title"])
            if oldid is None:
                missing.append(t["title"])
                print(f"MISSING {t['title']}", file=sys.stderr)
                continue
        parsed = api_get({"action": "parse", "oldid": oldid, "prop": "text|revid"})["parse"]
        extractor = SectionExtractor()
        extractor.feed(parsed["text"])
        sections = []
        for sec in extractor.sections:
            text = clean("".join(sec["parts"]))
            if text and sec["heading"].lower() not in DROP_SECTIONS:
                sections.append({"idx": len(sections), "heading": sec["heading"], "text": text})
        if sections and sections[0]["text"].startswith("To jest strona ujednoznaczniająca"):
            missing.append(f"{t['title']} (disambiguation)")
            print(f"DISAMBIGUATION {t['title']}", file=sys.stderr)
            continue
        doc = {"source_id": t["source_id"], "title": title, "oldid": oldid,
               "era": t["era"], "sections": sections}
        body = json.dumps(doc, ensure_ascii=False, indent=1)
        (cache / f"{t['source_id']}.json").write_text(body, encoding="utf-8")
        digest = hashlib.sha256("\n".join(s["text"] for s in sections).encode("utf-8")).hexdigest()
        revision = f"oldid:{oldid}" + (f" ({rev_ts})" if rev_ts else "") + f"; extracted_text_sha256:{digest}"
        records.append({
            "source_id": t["source_id"],
            "url": f"https://pl.wikipedia.org/w/index.php?oldid={oldid}",
            "title": title,
            "publisher": "Wikipedia (pl)",
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "revision_or_sha256": revision,
            "license": "CC BY-SA 4.0",
            "allowed_use": ["reference", "train"],
            "local_path": f"cache/{t['source_id']}.json",
            "source_group_id": t["source_group_id"],
            "notes": f"era={t['era']}; {len(sections)} sections; raw text kept locally, not committed.",
        })
        print(f"ok {t['source_id']} oldid={oldid} sections={len(sections)}")
        time.sleep(0.3)

    with open(out_dir / "sources.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"sources={len(records)} missing={len(missing)} {missing}")


if __name__ == "__main__":
    main()
