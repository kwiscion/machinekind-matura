"""Issue #117: canonical source groups, deterministic essay checks, repair pairs and SFT export.

Subcommands (all deterministic, standard library only, no network):
  groups   build agentsLog/Bukareszt/essay_corpus/group_map.jsonl and check train/eval leakage
  check    run the output contract / schema / grounding / leakage gate on draft essays
  repairs  build original format-repair pairs from reviewer-ACCEPTED essays
  export   write the source-group-separated SFT export for accepted records only

Clusters (clusters.json) are the split unit: every source is canonicalized to a normalized
title key (aliases resolved), then to exactly one cluster; a cluster may appear in only one
partition. Review verdicts come from a different agent than the generator; this script
never marks anything accepted by itself.
"""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "przemeknowak781"))
from validate import norm  # noqa: E402  (reuse #4 strict quote normalization)

CORPUS = ROOT / "agentsLog" / "Bukareszt" / "essay_corpus"
RAW = ROOT / "agentsLog" / "Bukareszt" / "raw"
BK_SOURCES = ROOT / "agentsLog" / "Bukareszt" / "sources" / "sources.jsonl"
PN_SOURCES = ROOT / "data" / "przemeknowak781" / "sources.jsonl"
PN_RECORDS = [ROOT / "data" / "przemeknowak781" / "train.jsonl",
              ROOT / "data" / "przemeknowak781" / "train_strict.jsonl"]
PW_DEV = ROOT / "agentsLog" / "Pewciu6" / "essay" / "dev_fixtures.jsonl"
ROOT_DIRS = {"root_seed": ROOT / "agentsLog" / "kwiscion" / "essay-teacher-seed",
             "root_sol": ROOT / "agentsLog" / "kwiscion" / "essay-corpus-sol"}
EXAM_SOURCE_MANIFESTS = [ROOT / "agentsLog" / "Pewciu6" / "sources" / "validation_2024_sources.jsonl"]

MIN_WORDS, MAX_WORDS = 400, 500
NUMBER = re.compile(r"(?<![\w])\d+(?![\w])")
PREAMBLE = re.compile(
    r"^\s*(oto|poniżej|poniżej przedstawiam|oczywiście|jasne|jako model|chętnie|przedstawiam|"
    r"sure|here is|temat\s*\d|wypracowanie\s*:|#)", re.I)
CLOSING = re.compile(r"(mam nadzieję|daj znać|jeśli chcesz|czy chcesz|w razie pytań|"
                     r"jako model|powodzenia|liczba słów|słów:)", re.I)
FORBIDDEN_MARKUP = re.compile(r"(^|\n)\s*(#|\*|-\s|\d+\.\s|temat\s*\d)", re.I)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(title):
    t = unicodedata.normalize("NFKD", title.lower()).replace("ł", "l")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def load_clusters():
    cfg = json.loads((CORPUS / "clusters.json").read_text(encoding="utf-8"))
    k2c = {}
    for cid, c in cfg["clusters"].items():
        for m in c["members"]:
            if m in k2c:
                raise SystemExit(f"canonical key {m} in two clusters: {k2c[m]}, {cid}")
            k2c[m] = cid
    c2p = {}
    for part, cids in cfg["partitions"].items():
        for cid in cids:
            if cid not in cfg["clusters"]:
                raise SystemExit(f"partition {part} names unknown cluster {cid}")
            if cid in c2p:
                raise SystemExit(f"cluster {cid} declared in two partitions: {c2p[cid]}, {part}")
            c2p[cid] = part
    return cfg, k2c, c2p


def components(cfg):
    """Cluster -> connected-component id after merging declared cross-cluster dependencies."""
    parent = {c: c for c in cfg["clusters"]}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c
    for dep in cfg.get("dependencies", []) + root_dependency_edges(cfg):
        cs = dep["clusters"]
        for c in cs:
            if c not in parent:
                raise SystemExit(f"dependency names unknown cluster {c}")
        for c in cs[1:]:
            a, b = find(cs[0]), find(c)
            if a != b:
                parent[max(a, b)] = min(a, b)
    return {c: find(c) for c in parent}


def root_dependency_edges(cfg):
    """Edges declared by root datasets (additional_source_group_dependencies), mapped to clusters."""
    ext = cfg.get("external_group_map", {})
    edges = []
    for part, d in ROOT_DIRS.items():
        f = d / "repairs.jsonl"
        if not f.exists():
            continue
        for rec in load_jsonl(f):
            deps = rec.get("additional_source_group_dependencies") or []
            if not deps:
                continue
            groups = [rec["source_group_id"]] + list(deps)
            missing = [g for g in groups if g not in ext]
            if missing:
                raise SystemExit(f"{f}:{rec['id']} dependency groups not in external_group_map: {missing}")
            edges.append({"clusters": [ext[g] for g in groups], "reason": f"{part}:{rec['id']}"})
    return edges


def root_accepted_rows(cfg):
    """Root seed/Sol records whose prompt+response hashes match an independent 'accept' verdict."""
    ext = cfg.get("external_group_map", {})
    rows, rejected = [], []
    for part, d in ROOT_DIRS.items():
        rv = d / "independent-review.json"
        if not rv.exists():
            continue
        dec = {x["id"]: x for x in json.loads(rv.read_text(encoding="utf-8"))["records"]}
        for fname in ("essays.jsonl", "repairs.jsonl"):
            for rec in load_jsonl(d / fname):
                v = dec.get(rec["id"], {})
                ok = (v.get("decision") == "accept"
                      and v.get("response_sha256") == hashlib.sha256(rec["response"].encode()).hexdigest()
                      and v.get("prompt_sha256") == hashlib.sha256(rec["prompt"].encode()).hexdigest()
                      and not contract_errors(rec["response"]))
                if not ok:
                    rejected.append(rec["id"])
                    continue
                rows.append({"id": rec["id"], "task_type": rec["task_type"], "origin": part,
                             "source_group_id": ext[rec["source_group_id"]],
                             "root_source_group_id": rec["source_group_id"],
                             "messages": [{"role": "user", "content": rec["prompt"]},
                                          {"role": "assistant", "content": rec["response"]}]})
    return rows, rejected


def dev_pewciu6_clusters():
    rep = CORPUS / "leakage_report.json"
    return set(json.loads(rep.read_text(encoding="utf-8")).get("dev_pewciu6_clusters", [])) if rep.exists() else set()


def partition_family(part):
    if part in ("eval_bukareszt_16", "dev_pewciu6"):
        return "eval"
    if part.startswith(("train_", "reserved_root", "root_", "pn781_strict")):
        return "train"
    return "other"


def canon(cfg, title):
    k = key(title)
    return cfg["aliases"].get(k, k)


def wiki_title_from_url(url):
    m = re.search(r"wiki(?:pedia|source)\.org/wiki/([^?#]+)", url or "")
    if not m:
        return None
    from urllib.parse import unquote
    return unquote(m.group(1)).replace("_", " ")


def collect_sources(cfg):
    """Every known source across corpora -> canonical key. Returns list of rows."""
    rows = []
    for d in load_jsonl(BK_SOURCES):
        rows.append({"corpus": "bukareszt_107", "source_id": d["source_id"], "title": d["title"],
                     "url": d["url"], "revision": d.get("revision_id"), "sha256": d.get("sha256"),
                     "license": d["license"]})
    pn = {d["source_id"]: d for d in load_jsonl(PN_SOURCES)}
    for d in pn.values():
        rows.append({"corpus": "przemeknowak781_100", "source_id": d["source_id"], "title": d["title"],
                     "url": d["url"], "revision": d.get("revision_or_sha256"), "sha256": None,
                     "license": d["license"]})
    for r in rows:
        r["canonical_key"] = canon(cfg, r["title"])
    return rows, pn


def root_records():
    """Best-effort scan of root-owned folders (read-only). Yields (partition, record)."""
    for part, d in ROOT_DIRS.items():
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.suffix == ".jsonl":
                for rec in load_jsonl(p):
                    yield part, p, rec
            elif p.suffix == ".json":
                try:
                    obj = json.loads(p.read_text(encoding="utf-8"))
                except ValueError:
                    continue
                for rec in obj if isinstance(obj, list) else [obj]:
                    if isinstance(rec, dict):
                        yield part, p, rec


def titles_in(rec):
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("url", "canonical_url", "source_url") and isinstance(v, str):
                    t = wiki_title_from_url(v)
                    if t:
                        out.add(t)
                elif k in ("title", "source_title") and isinstance(v, str) and len(v) < 120:
                    out.add(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(rec)
    return out


def cmd_groups(args):
    cfg, k2c, c2p = load_clusters()
    rows, pn = collect_sources(cfg)
    usage = defaultdict(set)   # cluster -> partitions using it
    unmapped = []
    for r in rows:
        r["cluster_id"] = k2c.get(r["canonical_key"])
        if r["cluster_id"] is None:
            unmapped.append(f'{r["corpus"]}:{r["source_id"]} ({r["canonical_key"]})')
    by_id = {(r["corpus"], r["source_id"]): r for r in rows}
    pn_key = {sid: canon(cfg, d["title"]) for sid, d in pn.items()}

    for cid, part in c2p.items():
        usage[cid].add(part)
    # Paweł's #80 DEV fixtures (evaluation-only for #80).
    pw_rows = load_jsonl(PW_DEV) if PW_DEV.exists() else []
    for rec in pw_rows:
        for sid in rec.get("source_ids", []):
            ck = pn_key.get(sid) or canon(cfg, sid.removeprefix("src-plwiki-"))
            cid = k2c.get(ck)
            if cid is None:
                unmapped.append(f"pewciu6_dev:{sid}")
            else:
                usage[cid].add("dev_pewciu6")
    # #4 legacy/strict records: inventory only (training-candidate drafts).
    pn_usage = defaultdict(int)
    for path in PN_RECORDS:
        for rec in load_jsonl(path):
            for sid in rec.get("source_ids", []):
                cid = k2c.get(pn_key.get(sid, ""))
                if cid:
                    pn_usage[(path.name, cid)] += 1
                    usage[cid].add("pn781_" + ("strict" if "strict" in path.name else "legacy_draft"))
    # Root folders.
    root_found = defaultdict(set)
    ext = cfg.get("external_group_map", {})
    for part, p, rec in root_records():
        gid = rec.get("source_group_id")
        if isinstance(gid, str) and gid:
            if gid in ext:
                root_found[part].add(ext[gid])
                usage[ext[gid]].add(part)
            else:
                unmapped.append(f"{part}:source_group_id={gid} (add to external_group_map)")
        for t in titles_in(rec):
            cid = k2c.get(canon(cfg, t))
            if cid:
                root_found[part].add(cid)
                usage[cid].add(part)
    # Exam source manifests: only titles/URLs are compared; nothing is printed.
    exam_hits = 0
    for m in EXAM_SOURCE_MANIFESTS:
        if m.exists():
            for rec in load_jsonl(m):
                for t in titles_in(rec):
                    cid = k2c.get(canon(cfg, t))
                    if cid and c2p.get(cid, "").startswith(("eval_bukareszt", "train_bukareszt")):
                        exam_hits += 1

    for r in rows:
        r["partitions"] = sorted(usage.get(r["cluster_id"], ()))
    write_jsonl(CORPUS / "group_map.jsonl", sorted(rows, key=lambda r: (r["cluster_id"] or "~", r["corpus"], r["source_id"])))

    # Leakage rules.
    fails, warns = [], []
    eval_parts = {"eval_bukareszt_16", "dev_pewciu6"}
    for cid, parts in sorted(usage.items()):
        mine_eval = "eval_bukareszt_16" in parts
        trainish = {p for p in parts if p.startswith(("train_", "reserved_root_seed", "root_", "pn781_strict"))}
        if mine_eval and "pn781_legacy_draft" in parts:
            warns.append(f"{cid}: eval_bukareszt_16 shares a cluster with #4 legacy DRAFT records (not export-eligible; keep excluded)")
        if mine_eval and (trainish or "dev_pewciu6" in parts):
            fails.append(f"{cid}: eval_bukareszt_16 overlaps {sorted(trainish | (parts & {'dev_pewciu6'}))}")
        mine_train = {p for p in parts if p.startswith("train_bukareszt")}
        if mine_train and parts & eval_parts:
            fails.append(f"{cid}: {sorted(mine_train)} overlaps eval {sorted(parts & eval_parts)}")
        other_train = {p for p in parts if p.startswith(("reserved_root_seed", "root_"))}
        if other_train and "dev_pewciu6" in parts:
            warns.append(f"{cid}: root training material overlaps Paweł #80 DEV fixtures")
        if "pn781_strict" in parts and "dev_pewciu6" in parts:
            warns.append(f"{cid}: #4 strict training records overlap Paweł #80 DEV fixtures")
    # Source-connected components: dependent clusters must share one partition family.
    comp = components(cfg)
    comp_parts = defaultdict(set)
    for cid, parts in usage.items():
        comp_parts[comp[cid]] |= {(cid, p) for p in parts}
    for root, cps in sorted(comp_parts.items()):
        fams = {partition_family(p) for _, p in cps} - {"other"}
        if len({c for c, _ in cps}) > 1 and len(fams) > 1:
            fails.append(f"component {root} spans eval and train via declared dependency: {sorted(cps)}")
        if len({c for c, _ in cps}) > 1:
            declared = {c2p.get(c) for c, _ in cps if c2p.get(c)}
            if len(declared) > 1 and len({partition_family(x) for x in declared}) > 1:
                fails.append(f"component {root} declared across partitions {sorted(declared)}")
    if exam_hits:
        fails.append(f"{exam_hits} validation-2024 source titles map to Bukareszt eval/train clusters")
    # Eval file must match partition.
    ev = load_jsonl(CORPUS / "eval16_topics.jsonl")
    ev_c = [e["cluster_id"] for e in ev]
    if sorted(ev_c) != sorted(cfg["partitions"]["eval_bukareszt_16"]) or len(set(ev_c)) != 16:
        fails.append("eval16_topics.jsonl clusters differ from partition eval_bukareszt_16")
    src_ids = {r["source_id"]: r for r in rows if r["corpus"] == "bukareszt_107"}
    for e in ev:
        for sid in e["source_ids"]:
            if sid not in src_ids or src_ids[sid]["cluster_id"] != e["cluster_id"]:
                fails.append(f'{e["id"]}: source {sid} not in cluster {e["cluster_id"]}')

    report = {
        "sources": len(rows), "canonical_keys": len({r["canonical_key"] for r in rows}),
        "clusters": len(cfg["clusters"]), "clusters_used": len(usage),
        "partitions": {p: len(v) for p, v in cfg["partitions"].items()},
        "dev_pewciu6_clusters": sorted(c for c, p in usage.items() if "dev_pewciu6" in p),
        "pn781_records_by_cluster": {f"{f}:{c}": n for (f, c), n in sorted(pn_usage.items())},
        "root_folders_present": {k: v.is_dir() for k, v in ROOT_DIRS.items()},
        "root_clusters_found": {k: sorted(v) for k, v in root_found.items()},
        "exam_source_title_hits": exam_hits,
        "root_dependency_edges": root_dependency_edges(cfg),
        "unmapped": sorted(set(unmapped)), "fails": fails, "warnings": sorted(set(warns)),
        "group_map_sha256": sha256_file(CORPUS / "group_map.jsonl"),
        "clusters_sha256": sha256_file(CORPUS / "clusters.json"),
    }
    (CORPUS / "leakage_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("sources", "canonical_keys", "clusters", "unmapped", "fails", "warnings", "exam_source_title_hits")}, ensure_ascii=False, indent=1))
    return 1 if fails else 0


# ---------------------------------------------------------------- essay contract

def body_words(text):
    return len(text.split())


def contract_errors(text):
    errs = []
    n = body_words(text)
    if not MIN_WORDS <= n <= MAX_WORDS:
        errs.append(f"word_count {n} outside {MIN_WORDS}-{MAX_WORDS}")
    if PREAMBLE.search(text):
        errs.append("assistant preamble / heading at start")
    if CLOSING.search(text):
        errs.append("assistant closing or meta remark")
    if FORBIDDEN_MARKUP.search(text):
        errs.append("markdown/list/topic label in body")
    if re.search(r"temat\s*[12]\b", text, re.I):
        errs.append("mentions a topic number (multi-topic risk)")
    if text != text.strip() or "\n\n\n" in text:
        errs.append("untrimmed whitespace")
    if len([p for p in text.split("\n\n") if p.strip()]) < 3:
        errs.append("fewer than 3 paragraphs")
    return errs


def source_text(sid):
    p = RAW / f"{sid}.txt"
    return norm(p.read_text(encoding="utf-8")) if p.exists() else None


def cmd_check(args):
    cfg, k2c, c2p = load_clusters()
    rows, _ = collect_sources(cfg)
    s_cluster = {r["source_id"]: k2c.get(r["canonical_key"]) for r in rows if r["corpus"] == "bukareszt_107"}
    manifest = {d["source_id"]: d for d in load_jsonl(BK_SOURCES)}
    cards = {c["fact_id"]: c for f in args.factcards for c in load_jsonl(f)}
    texts, results = {}, []
    card_errs = {}
    for fid, c in cards.items():
        e = []
        sid = c["source_id"]
        if sid not in texts:
            texts[sid] = source_text(sid)
            if texts[sid] is not None and manifest.get(sid, {}).get("sha256") != sha256_file(RAW / f"{sid}.txt"):
                e.append("raw source hash differs from pinned manifest")
        if texts[sid] is None:
            e.append(f"no pinned raw text for {sid}")
        elif norm(c["quote"]) not in texts[sid]:
            e.append("quote not verbatim in pinned source")
        if s_cluster.get(sid) != c["cluster_id"]:
            e.append(f"source {sid} not in cluster {c['cluster_id']}")
        card_errs[fid] = e
    for rec in load_jsonl(args.essays):
        e = []
        for f in ("id", "cluster_id", "era", "source_ids", "topics", "selected_topic", "required_aspects",
                  "essay", "fact_ids_used", "off_topic_paragraph", "teacher"):
            if f not in rec:
                e.append(f"missing field {f}")
        if e:
            results.append({"id": rec.get("id"), "pass": False, "errors": e})
            continue
        part = c2p.get(rec["cluster_id"], "")
        if not part.startswith("train_bukareszt"):
            e.append(f"cluster {rec['cluster_id']} is not a Bukareszt training cluster ({part or 'undeclared'})")
        for sid in rec["source_ids"]:
            if s_cluster.get(sid) != rec["cluster_id"]:
                e.append(f"source {sid} outside cluster")
        if len(rec["topics"]) != 2 or rec["selected_topic"] not in (1, 2):
            e.append("need two topics and selected_topic in {1,2}")
        e += contract_errors(rec["essay"])
        used = rec["fact_ids_used"] + rec.get("off_topic_fact_ids", [])
        missing = [f for f in used if f not in cards]
        if missing:
            e.append(f"unknown fact ids {missing}")
        bad = [f for f in used if card_errs.get(f)]
        if bad:
            e.append(f"fact cards failing verbatim/cluster check: {bad}")
        if any(cards[f]["cluster_id"] != rec["cluster_id"] for f in used if f in cards):
            e.append("fact card from another cluster")
        if len(rec["fact_ids_used"]) < 8:
            e.append("fewer than 8 fact cards used")
        support = " ".join(norm(cards[f]["quote"]) + " " + norm(cards[f]["fact"]) for f in rec["fact_ids_used"] if f in cards)
        ungrounded = sorted({n for n in NUMBER.findall(rec["essay"]) if n not in NUMBER.findall(support)})
        if ungrounded:
            e.append(f"numbers not in used fact cards: {ungrounded}")
        otw = body_words(rec["off_topic_paragraph"])
        if not 40 <= otw <= 160:
            e.append(f"off_topic_paragraph {otw} words")
        results.append({"id": rec["id"], "cluster_id": rec["cluster_id"], "words": body_words(rec["essay"]),
                        "essay_sha256": hashlib.sha256(rec["essay"].encode()).hexdigest(),
                        "pass": not e, "errors": e})
    out = {"essays": args.essays, "essays_sha256": sha256_file(args.essays),
           "factcards": args.factcards, "factcards_sha256": [sha256_file(f) for f in args.factcards],
           "factcards_total": len(cards), "factcards_failing": {k: v for k, v in card_errs.items() if v},
           "results": results, "passed": sum(r["pass"] for r in results), "total": len(results)}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "total": out["total"], "factcards_failing": len(out["factcards_failing"]),
                      "failures": {r["id"]: r["errors"] for r in results if not r["pass"]}}, ensure_ascii=False, indent=1))
    return 0


def cmd_evalcards(args):
    """Verbatim/cluster check for eval fact cards (grading reference only, never training)."""
    ev = {e["id"]: e for e in load_jsonl(CORPUS / "eval16_topics.jsonl")}
    cards = load_jsonl(CORPUS / "eval16_factcards.jsonl")
    errs, per = [], defaultdict(int)
    for c in cards:
        e = ev.get(c.get("eval_id"))
        if e is None or c["cluster_id"] != e["cluster_id"] or c["source_id"] not in e["source_ids"]:
            errs.append(f'{c["fact_id"]}: eval id/cluster/source mismatch')
            continue
        t = source_text(c["source_id"])
        if t is None or norm(c["quote"]) not in t:
            errs.append(f'{c["fact_id"]}: quote not verbatim')
        per[c["eval_id"]] += 1
    thin = sorted(i for i in ev if per[i] < 5)
    rep = {"cards": len(cards), "per_eval": dict(sorted(per.items())), "errors": errs, "thin_items": thin,
           "sha256": sha256_file(CORPUS / "eval16_factcards.jsonl")}
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 1 if errs or thin else 0


# ---------------------------------------------------------------- repair pairs

WRAPPERS = [
    ("Oczywiście! Oto wypracowanie na wybrany temat:\n\n", "\n\nMam nadzieję, że to wypracowanie spełnia Twoje oczekiwania. Jeśli chcesz, mogę je skrócić lub rozwinąć."),
    ("Poniżej przedstawiam moją odpowiedź.\n\n**Wypracowanie**\n\n", "\n\n(Liczba słów: około 450)"),
    ("Jako model językowy przygotowałem następujący tekst:\n\n", "\n\nDaj znać, czy potrzebujesz poprawek."),
    ("# Wypracowanie\n\n", "\n\n---\nPowodzenia na egzaminie!"),
]
REPAIR_INSTRUCTION = (
    "Poniżej znajdują się tematy wypracowania oraz wadliwa wersja odpowiedzi. Popraw ją: wybierz "
    "dokładnie jeden temat (ten, na który odpowiada szkic), usuń wszystko, co nie jest wypracowaniem "
    "(wstępy, komentarze, nagłówki, fragmenty na inny temat), a jeśli tekst jest za krótki, uzupełnij go "
    "rzetelną wiedzą historyczną. Zwróć wyłącznie czysty tekst wypracowania o długości 400–500 słów.")


def exam_prompt(rec):
    return ("Wybierz jeden z podanych tematów i napisz wypracowanie. Sformułuj stanowisko (tezę) i "
            "uzasadnij je, odwołując się do wiedzy historycznej. Wypracowanie powinno liczyć 400–500 słów.\n\n"
            + "\n\n".join(rec["topics"]))


def make_defect(rec, kind, variant):
    essay = rec["essay"]
    if kind == "wrapper":
        pre, post = WRAPPERS[variant % len(WRAPPERS)]
        return pre + essay + post
    if kind == "extra_topic":
        other = 2 if rec["selected_topic"] == 1 else 1
        return (f"Temat {rec['selected_topic']}\n\n{essay}\n\nTemat {other}\n\n{rec['off_topic_paragraph']}")
    if kind == "underlength":
        paras = [p for p in essay.split("\n\n") if p.strip()]
        keep = [paras[0], paras[-1]] if len(paras) > 2 else paras[:1]
        return "\n\n".join(keep)
    raise ValueError(kind)


KINDS = ["wrapper", "extra_topic", "underlength"]


def cmd_repairs(args):
    essays = {r["id"]: r for r in sorted((r for f in args.essays for r in load_jsonl(f)), key=lambda r: r.get("repair_round", 0))}
    cfg, _, _ = load_clusters()
    accepted = {k: v for k, v in load_accepted(args.reviews, essays).items()
                if k not in cfg.get("withdrawn_essays", {})}
    pairs = []
    for i, eid in enumerate(sorted(accepted)):
        rec = essays[eid]
        # A reviewer-flagged off-topic paragraph must not be propagated even as a defect.
        kinds = [k for k in KINDS if not (k == "extra_topic" and accepted[eid].get("off_topic_issues"))]
        for j in range(args.per_essay):
            kind = kinds[(i + j) % len(kinds)]
            draft = make_defect(rec, kind, i + j)
            if not contract_errors(draft) or contract_errors(rec["essay"]):
                raise SystemExit(f"{eid}/{kind}: defect must fail and target must pass the contract")
            pairs.append({
                "id": f"{eid}-repair-{kind}", "cluster_id": rec["cluster_id"], "source_ids": rec["source_ids"],
                "task_type": "essay_repair", "defect": kind,
                "prompt": REPAIR_INSTRUCTION + "\n\nTEMATY:\n" + "\n".join(rec["topics"]) + "\n\nSZKIC:\n" + draft,
                "answer": rec["essay"],
                "transformation": {"from_essay_id": eid, "essay_sha256": hashlib.sha256(rec["essay"].encode()).hexdigest(),
                                   "kind": kind, "variant": (i + j) % len(WRAPPERS), "script": "scripts/Bukareszt/essay_corpus.py repairs"},
                "draft_words": body_words(draft),
            })
    write_jsonl(Path(args.out), pairs)
    print(json.dumps({"accepted_essays": len(accepted), "pairs": len(pairs)}))
    return 0


def load_accepted(review_paths, essays):
    """Essay ids whose LATEST independent verdict is accept, from a reviewer != generator."""
    latest = {}
    for p in review_paths:
        for v in load_jsonl(p):
            latest[v["id"]] = v
    ok = {}
    for eid, v in latest.items():
        rec = essays.get(eid)
        if rec is None or v.get("verdict") != "accept":
            continue
        if v.get("reviewer", {}).get("agent") == rec["teacher"].get("agent"):
            continue
        if v.get("essay_sha256") != hashlib.sha256(rec["essay"].encode()).hexdigest():
            continue  # verdict is for a different text
        ok[eid] = v
    return ok


def cmd_ledger(args):
    """Per-essay status ledger: generation hash, deterministic check, every verdict, final status.
    Rule: an essay gets at most one repair round; a non-accept verdict after the repair drops it."""
    cfg, _, _ = load_clusters()
    withdrawn = cfg.get("withdrawn_essays", {})
    versions = defaultdict(list)          # id -> [(round, record, file)]
    for f in args.essays:
        for r in load_jsonl(f):
            versions[r["id"]].append((r.get("repair_round", 0), r, f))
    verdicts = defaultdict(list)
    for f in args.reviews:
        for v in load_jsonl(f):
            verdicts[v["id"]].append(v)
    checks = {}
    for f in args.checks:
        for r in json.loads(Path(f).read_text(encoding="utf-8"))["results"]:
            checks[(r["id"], f)] = r
    rows = []
    for eid in sorted(versions):
        vs = sorted(versions[eid], key=lambda x: x[0])
        hist = []
        for rnd, rec, f in vs:
            h = hashlib.sha256(rec["essay"].encode()).hexdigest()
            vv = [v for v in verdicts[eid] if v.get("essay_sha256") == h]
            chk = [c for (i, cf), c in checks.items() if i == eid and c.get("essay_sha256", h) == h]
            hist.append({"round": rnd, "file": f, "essay_sha256": h, "words": body_words(rec["essay"]),
                         "teacher": rec["teacher"], "check_pass": [c["pass"] for c in chk],
                         "verdicts": [{"verdict": v["verdict"], "issues": len(v.get("issues", [])),
                                       "reviewer": v.get("reviewer", {}).get("agent")} for v in vv]})
        last = hist[-1]
        lv = last["verdicts"][-1]["verdict"] if last["verdicts"] else None
        if eid in withdrawn:
            status, reason = "withdrawn", withdrawn[eid]
        elif lv == "accept" and all(last["check_pass"] or [False]):
            status, reason = "accepted", ""
        elif lv is None:
            status, reason = "pending_review", ""
        elif last["round"] >= 1 or lv == "reject":
            status, reason = "dropped", f"{lv} after {last['round']} repair round(s)"
        else:
            status, reason = "repair_pending", ""
        rows.append({"id": eid, "status": status, "reason": reason, "history": hist})
    write_jsonl(Path(args.out), rows)
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
    print(json.dumps(dict(counts)))
    return 0


# ---------------------------------------------------------------- export

def cmd_export(args):
    cfg, k2c, c2p = load_clusters()
    essays = {r["id"]: r for r in sorted((r for f in args.essays for r in load_jsonl(f)), key=lambda r: r.get("repair_round", 0))}
    accepted = load_accepted(args.reviews, essays)
    pairs = load_jsonl(args.repairs) if args.repairs else []
    out = Path(args.out_dir)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty")
    withdrawn = cfg.get("withdrawn_essays", {})
    accepted = {k: v for k, v in accepted.items() if k not in withdrawn}
    train = []
    for eid in sorted(accepted):
        r = essays[eid]
        train.append({"id": eid, "task_type": "essay", "source_group_id": r["cluster_id"],
                      "messages": [{"role": "user", "content": exam_prompt(r)},
                                   {"role": "assistant", "content": r["essay"]}]})
    for p in pairs:
        if p["transformation"]["from_essay_id"] in withdrawn:
            continue
        if p["transformation"]["from_essay_id"] not in accepted:
            raise SystemExit(f"repair {p['id']} built from non-accepted essay")
        train.append({"id": p["id"], "task_type": "essay_repair", "source_group_id": p["cluster_id"],
                      "messages": [{"role": "user", "content": p["prompt"]},
                                   {"role": "assistant", "content": p["answer"]}]})
    for r in train:
        r["origin"] = "bukareszt"
    root_rows, root_rejected = root_accepted_rows(cfg)
    train += root_rows
    ev = load_jsonl(CORPUS / "eval16_topics.jsonl")
    evrows = [{"id": e["id"], "prompt": exam_prompt(e), "source_group_id": e["cluster_id"]} for e in ev]
    comp = components(cfg)
    tg = {r["source_group_id"] for r in train}
    eg = {r["source_group_id"] for r in evrows}
    leak = sorted({comp[g] for g in tg} & {comp[g] for g in eg})
    bad_part = sorted(g for g in tg if partition_family(c2p.get(g, "")) != "train")
    if leak or bad_part:
        raise SystemExit(f"leakage: shared={leak} non-train-partition={bad_part}")
    for r in train:
        errs = contract_errors(r["messages"][1]["content"])
        if errs:
            raise SystemExit(f"{r['id']}: {errs}")
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "train_sft.jsonl", train)
    write_jsonl(out / "eval16_input.jsonl", evrows)
    man = {"train_rows": len(train), "essays": sum(r["task_type"] == "essay" for r in train),
           "bukareszt_accepted_essays": len(accepted),
           "repair_pairs": sum(r["task_type"] == "essay_repair" for r in train),
           "by_origin": {o: sum(r["origin"] == o for r in train) for o in sorted({r["origin"] for r in train})},
           "root_rows_rejected": root_rejected,
           "component_of_group": {g: comp[g] for g in sorted(tg | eg) if comp[g] != g},
           "train_groups_overlapping_pewciu6_dev": sorted(g for g in tg if g in dev_pewciu6_clusters()),
           "train_groups": sorted(tg), "eval_groups": sorted(eg), "shared_groups": leak,
           "train_sha256": sha256_file(out / "train_sft.jsonl"), "eval_sha256": sha256_file(out / "eval16_input.jsonl"),
           "format": "chat messages (user/assistant), no system prompt; eval rows are runner input {id,prompt}"}
    (out / "export_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("groups")
    sub.add_parser("evalcards")
    lg = sub.add_parser("ledger")
    lg.add_argument("--essays", nargs="+", required=True)
    lg.add_argument("--reviews", nargs="+", required=True)
    lg.add_argument("--checks", nargs="+", required=True)
    lg.add_argument("--out", required=True)
    c = sub.add_parser("check")
    c.add_argument("--essays", required=True)
    c.add_argument("--factcards", nargs="+", required=True)
    c.add_argument("--out", required=True)
    r = sub.add_parser("repairs")
    r.add_argument("--essays", nargs="+", required=True)
    r.add_argument("--reviews", nargs="+", required=True)
    r.add_argument("--per-essay", type=int, default=2)
    r.add_argument("--out", required=True)
    e = sub.add_parser("export")
    e.add_argument("--essays", nargs="+", required=True)
    e.add_argument("--reviews", nargs="+", required=True)
    e.add_argument("--repairs")
    e.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    return {"groups": cmd_groups, "evalcards": cmd_evalcards, "ledger": cmd_ledger, "check": cmd_check, "repairs": cmd_repairs, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
