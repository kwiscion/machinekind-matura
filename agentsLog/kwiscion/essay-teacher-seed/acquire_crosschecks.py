"""Optional primary/institutional crosschecks; raw pages remain local and ignored."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = [
    ("mit-aristotle", "https://classics.mit.edu/Aristotle/athenian_const.1.1.html", "Athenian Constitution, parts 2, 5-9, 11-14", "Aristotle or his school; F. G. Kenyon translation; Internet Classics Archive at MIT", "history-solon-reforms"),
    ("uj-archive", "https://archiwum.uj.edu.pl/historia-auj", "Historia", "Archiwum Uniwersytetu Jagiellońskiego", "history-casimir-iii-statebuilding"),
    ("agad-lublin", "https://agad.gov.pl/Unia%20Lubelska/uni_lub.html", "Unia Lubelska (1569)", "Archiwum Główne Akt Dawnych", "history-lublin-union-1569"),
    ("mhp-peasants", "https://powstanie1863-64.pl/artykul/uwlaszczenie-chlopow-w-optyce-tymczasowego-rzadu-narodowego/index.htm", "Uwłaszczenie chłopów w optyce Tymczasowego Rządu Narodowego", "Piotr Niziołek; Muzeum Historii Polski", "history-january-uprising-peasant-policy"),
    ("radom-peasants", "https://muzeum-radom.pl/wydarzenia/uwlaszczenie-chlopow-w-krolestwie-polskim-w-dobie-powstania-styczniowego/3139", "Uwłaszczenie chłopów w Królestwie Polskim w dobie powstania styczniowego", "Magdalena Grosiak; Muzeum Wsi Radomskiej; 2023-02-03", "history-january-uprising-peasant-policy"),
]
directory = ROOT / "source-private"
directory.mkdir(exist_ok=True)
records = []
for source_id, url, title, publisher, group in ITEMS:
    existing_path = ROOT / "crosscheck-sources.jsonl"
    existing = {r["source_id"]: r for r in (json.loads(line) for line in existing_path.read_text(encoding="utf-8").splitlines())} if existing_path.exists() else {}
    if source_id in existing:
        records.append(existing[source_id])
        continue
    req = urllib.request.Request(url, headers={"User-Agent": "MaturaTeacherSeed/1.0 reference check"})
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read()
    path = directory / (source_id + ".html")
    path.write_bytes(content)
    records.append({"source_id": source_id, "source_group_id": group, "url": url,
                    "title": title, "publisher": publisher,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "revision_or_sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
                    "license": "unknown for website presentation; not licensed for corpus redistribution by this seed",
                    "allowed_use": ["reference_fact_check_only"],
                    "local_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "notes": "Institutional/primary corroboration only. No quotations or copied prose enter examples. Do not publish local HTML. Canonical source group matches related licensed reference."})
for record in records:
    if record["source_id"] == "mhp-peasants":
        record.update({"license": "CC-BY-4.0 for article text; separately credited illustrations excluded",
                       "license_url": "https://creativecommons.org/licenses/by/4.0/",
                       "license_evidence": "Article declares CC-BY; its footer license link resolves to CC BY 4.0 legalcode.pl.",
                       "allowed_use": ["reference", "train_subject_to_independent_review", "redistribute_article_text_with_attribution"],
                       "attribution": "Piotr Niziołek, Uwłaszczenie chłopów w optyce Tymczasowego Rządu Narodowego, Muzeum Historii Polski, linked URL, CC BY 4.0",
                       "notes": "Licensed institutional corroboration added after target freeze. See supplementary-review-notes.md. No article quotations included in targets."})
(ROOT / "crosscheck-sources.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
print(json.dumps({"crosscheck_sources": len(records)}))
