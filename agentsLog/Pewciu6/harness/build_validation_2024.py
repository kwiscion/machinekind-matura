#!/usr/bin/env python3
"""Build RESTRICTED May 2024 history (formula 2023) VALIDATION artifacts from the CKE PDFs.

Inputs (git-ignored, fetched by fetch_validation_2024.py):
  agentsLog/Pewciu6/private/validation_2024/MHIP-R0-100-A-2405-arkusz.pdf   (exam sheet)
  agentsLog/Pewciu6/private/validation_2024/MHIP-R0-100-2405-zasady.pdf     (marking rules = KEY)

Outputs (all under private/, never commit):
  private/validation_2024/eval_keys.jsonl     restricted keys + item rubrics (for `matura_harness.py score`)
  private/validation_2024/runner_input.jsonl  model-facing input {id, prompt, images} -- NO key content
  private/validation_2024/pages/page-NN.png   rendered sheet pages referenced by runner_input images
Public output (aggregate counts + hashes only, no key or question text):
  agentsLog/Pewciu6/results/validation_2024_build_stats.json

Requires poppler (pdftotext, pdftoppm). Rubrics are a heuristic translation of the official rules:
closed items are auto-scorable; decision+justification items auto-check only the decision (gate)
and route the justification to review; open/essay items are manual_only with auto diagnostics.

  python3 agentsLog/Pewciu6/harness/build_validation_2024.py [--no-images]
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OWNER = os.path.dirname(HERE)
PRIV = os.path.join(OWNER, "private", "validation_2024")
ARKUSZ = os.path.join(PRIV, "MHIP-R0-100-A-2405-arkusz.pdf")
ZASADY = os.path.join(PRIV, "MHIP-R0-100-2405-zasady.pdf")
STATS = os.path.join(OWNER, "results", "validation_2024_build_stats.json")
PROMPT_REVISION = "val2024-prompt-v1"
BUILDER_REVISION = "build-validation-2024-v1"

PROMPT_HEADER = (
    "Rozwiąż poniższe zadanie z egzaminu maturalnego z historii (poziom rozszerzony). "
    "Odpowiadaj po polsku, zwięźle i na podstawie źródeł zamieszczonych w zadaniu oraz własnej wiedzy. "
    "Jeżeli zadanie wymaga rozstrzygnięcia, zacznij odpowiedź od linii 'Rozstrzygnięcie: ...', "
    "a następnie podaj 'Uzasadnienie: ...'. W zadaniach typu prawda/fałsz podaj numer zdania i literę P albo F. "
    "W zadaniach zamkniętych podaj literę wybranej odpowiedzi. Obrazy stron arkusza są dołączone, jeśli zadanie "
    "zawiera materiał ikonograficzny lub kartograficzny.\n\n"
)
IMAGE_WORDS = ["fotografi", "relief", "mapa", "mapy", "ilustracj", "rysun", "plakat", "karykatur",
               "drzeworyt", "tablica genealogiczna", "kadr", "obraz", "grafik", "schemat", "wykres",
               "znaczek", "moneta", "medal", "pomnik", "miniatur", "fresk", "rzezb", "rzeźb"]
NUM_WORDS = {"jedno": 1, "jeden": 1, "dwa": 2, "dwie": 2, "trzy": 3, "cztery": 4, "piec": 5, "pięć": 5}


def assert_private(path):
    if "/private/" not in os.path.abspath(path).replace(os.sep, "/"):
        sys.exit("refusing to write restricted artifact outside private/: %s" % path)


def pdftotext(pdf, layout=False):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + [pdf, "-"]
    return subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout.decode("utf-8")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def era_from_section(n):
    """Approximate era from the curriculum section number of the 2022 core curriculum (PP history)."""
    if n is None:
        return "unspecified"
    if n <= 4:
        return "ancient"
    if n <= 14:
        return "medieval"
    if n <= 27:
        return "early_modern"
    if n <= 37:
        return "19th_century"
    if n <= 46:
        return "1914_1939"
    if n <= 52:
        return "ww2"
    if n <= 58:
        return "1945_1989"
    return "post_1989"


GENERAL_REQ = ("Chronologia historyczna", "Analiza i interpretacja", "Tworzenie narracji")


def clean_lines(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if re.match(r"^Strona \d+ z \d+$", s) or s in ("MHIP-R0_100", "Zasady oceniania rozwiązań zadań") \
                or s.startswith("Egzamin maturalny z historii") or re.match(r"^\d+(\.\d+)*\.$", s) \
                or re.match(r"^0[–-]\d+$", s):
            continue
        out.append(ln.rstrip())
    return out


# ------------------------------------------------------------------------------ zasady (KEY)

HDR = re.compile(r"^Zadanie (\d+(?:\.\d+)?)\. \(0[–-](\d+)\)\s*$")


def parse_zasady(text):
    lines = clean_lines(text)
    blocks, cur = [], None
    for ln in lines:
        m = HDR.match(ln.strip())
        if m:
            cur = {"num": m.group(1), "max": int(m.group(2)), "lines": []}
            blocks.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    items = []
    for b in blocks:
        body = "\n".join(b["lines"])
        req, _, rest = body.partition("Zasady oceniania")
        m = re.search(r"\n(Rozwiązanie|Przykładowe rozwiązani[ea])\s*\n", rest)
        rules, sol = (rest[:m.start()], rest[m.end():]) if m else (rest, "")
        sol_label = m.group(1) if m else ""
        sections = []
        for ln in req.split("\n"):
            for chunk in re.split(r"\s{3,}", ln.strip()):
                sm = re.match(r"^([IVXL]{1,7})\. ([A-ZĄĆĘŁŃÓŚŹŻ].{3,80})$", chunk.strip())
                if sm and not any(g in sm.group(2) for g in GENERAL_REQ):
                    sections.append((roman_to_int(sm.group(1)), sm.group(1), sm.group(2).strip()))
        # footnotes/leftovers
        sol = re.split(r"\n\s*\d+ Rozporządzenie", sol)[0]
        items.append({"num": b["num"], "max": b["max"], "rules": rules.strip(), "solution": sol.strip(),
                      "solution_label": sol_label, "sections": sections})
    return items


def variants(ans):
    """Synthetic example: 'Kazimierz [III] Wielki / Kazimierz' -> ['Kazimierz III Wielki', 'Kazimierz Wielki',
    'Kazimierz']; splits ' / ' alternatives, optional [..]/(..) parts kept and dropped."""
    out = []
    for alt in re.split(r"\s+/\s+", ans):
        alt = alt.strip().strip(".;,")
        if not alt:
            continue
        keep = re.sub(r"[\[\]()]", "", alt)
        drop = re.sub(r"\s*[\[(][^\])]*[\])]\s*", " ", alt)
        for v in (keep, drop):
            v = re.sub(r"\s+", " ", v).strip()
            if v and v not in out:
                out.append(v)
    return out


def build_rubric(it):
    n, sol, rules = it["max"], it["solution"], it["rules"]
    sol_lines = [l.strip() for l in sol.split("\n") if l.strip()]
    first = sol_lines[0] if sol_lines else ""
    rid = "val2024-r-%s" % it["num"]
    if n >= 10:
        return "essay", {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": [
            {"criterion_id": "min-words-300", "kind": "structure", "points": 0, "min_words": 300,
             "zeroes": ["B-coherence"], "description": "CKE: under 300 words -> criterion B = 0"},
            {"criterion_id": "stance", "kind": "structure", "points": 0,
             "any_of": ["teza", "stanowisko", "uwazam", "zgadzam sie", "nie zgadzam sie", "moim zdaniem",
                        "podsumowujac", "podsumowanie", "wnioski"],
             "description": "diagnostic: explicit stance/conclusion marker"},
            {"criterion_id": "A-narrative", "kind": "content", "points": 12, "manual_only": True,
             "description": "CKE A: argumentation per topic element (rich 4 / satisfactory 3 / superficial 1)"},
            {"criterion_id": "B-coherence", "kind": "structure", "points": n - 12, "manual_only": True,
             "description": "CKE B: coherence with >=300 words"}]}, "manual"
    if first.startswith("Rozstrzygnięcie"):
        val = first.split(":", 1)[1].strip().rstrip(".") if ":" in first else ""
        vals = variants(val) or [val]
        low = [v.lower() for v in vals]
        options = ["Tak", "Nie"] if low[0] in ("tak", "nie") else (
            ["A", "B", "C", "D"] if re.match(r"^[a-d]$", low[0]) else [])
        return "source_analysis", {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": [
            {"criterion_id": "decision", "kind": "decision", "gate": True, "points": 0, "any_of": vals,
             "options": options},
            {"criterion_id": "justification", "kind": "content", "points": n, "manual_only": True,
             "description": "justification per official rules"}]}, "gate+manual"
    if it["solution_label"].startswith("Przykładow") or "Przykładowe" in sol:
        return "short_answer", {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": [
            {"criterion_id": "open", "kind": "content", "points": n, "manual_only": True,
             "description": "open response; see official example answer"}]}, "manual"
    pf = [re.match(r"^(\d+)\s*[–-]\s*([PF])$", l) for l in sol_lines]
    if sol_lines and all(pf):
        counts = {}
        for pm in re.finditer(r"(\d) pkt – za odpowiedź zawierającą (\w+) prawidłow", rules):
            k = NUM_WORDS.get(pm.group(2).lower())
            if k:
                counts[str(k)] = int(pm.group(1))
        crit = [{"criterion_id": "s%s" % m.group(1), "points": 0, "pair": [m.group(1), m.group(2)]} for m in pf]
        rub = {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": crit}
        if counts:
            rub["points_by_met_count"] = counts
        else:
            rub["all_or_nothing"] = True
        return "multiple_choice", rub, "auto"
    if len(sol_lines) == 1 and re.match(r"^[A-F]\.?$", first):
        return "multiple_choice", {"rubric_id": rid, "max_points": n, "mode": "choice",
                                   "expected_choice": [first[0]]}, "auto"
    if 1 <= len(sol_lines) <= 4 and all(len(l) <= 100 for l in sol_lines):
        crit = []
        for i, l in enumerate(sol_lines, 1):
            ans = l.split(" – ", 1)[1] if " – " in l else l
            kind = "date" if re.search(r"\d{3,4}|\d+ [a-ząćęłńóśźż]+", ans) else (
                "entity" if ans[:1].isupper() or ans[:1] == "[" else "content")
            crit.append({"criterion_id": "a%d" % i, "kind": kind, "points": n / float(len(sol_lines)),
                         "any_of": variants(ans), "review_on_fail": True})
        rub = {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": crit}
        if n == 1 and len(crit) > 1:
            rub["all_or_nothing"] = True
        return "short_answer", rub, "auto"
    return "short_answer", {"rubric_id": rid, "max_points": n, "mode": "criteria", "criteria": [
        {"criterion_id": "open", "kind": "content", "points": n, "manual_only": True}]}, "manual"


# ------------------------------------------------------------------------------ arkusz (prompts)

SHEET_HDR = re.compile(r"^\s*Zadanie (\d+)(?:\.(\d+))?\.?\s*(?:\((0[–-]\d+)\))?\s*$")


def parse_arkusz(text):
    """Return {item_num: {"text": str, "pages": set}} with group preambles prepended to sub-items."""
    pages = text.split("\f")
    segs = []  # (group, sub, has_points, page, lines)
    cur = None
    started = False
    for pno, page in enumerate(pages, 1):
        for ln in clean_lines(page):
            m = SHEET_HDR.match(ln)
            if m:
                started = True
                cur = {"group": m.group(1), "sub": m.group(2), "pts": m.group(3), "pages": {pno}, "lines": []}
                segs.append(cur)
                continue
            if not started or cur is None:
                continue
            s = ln.strip()
            if s.upper().startswith("BRUDNOPIS"):
                cur = None
                continue
            if s.startswith("Wypełnia") or s.startswith("egzaminator"):
                continue
            if re.match(r"^[\.…\s]{8,}$", s):
                if cur["lines"] and cur["lines"][-1] == "[miejsce na odpowiedź]":
                    continue
                s = "[miejsce na odpowiedź]"
            s = re.sub(r"\.{6,}", "…", s)
            cur["lines"].append(s)
            cur["pages"].add(pno)
    items, preamble = {}, {}
    for sg in segs:
        body = "\n".join(sg["lines"]).strip()
        if sg["sub"] is None and sg["pts"] is None:          # group header with shared sources
            preamble[sg["group"]] = (body, set(sg["pages"]))
            continue
        num = sg["group"] if sg["sub"] is None else "%s.%s" % (sg["group"], sg["sub"])
        pre, pre_pages = preamble.get(sg["group"], ("", set())) if sg["sub"] else ("", set())
        text = ("Zadanie %s.\n%s\n\n" % (sg["group"], pre) if pre else "") + \
               "Zadanie %s.\n%s" % (num, body)
        items[num] = {"text": text.strip(), "pages": sorted(pre_pages | set(sg["pages"]))}
    return items


def modality(text):
    f = text.lower()
    hits = sorted(set(w for w in IMAGE_WORDS if re.search(r"(?<!\w)" + re.escape(w), f)))
    return ("image" if hits else "text"), hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args()
    for p in (ARKUSZ, ZASADY):
        if not os.path.exists(p):
            sys.exit("missing %s; run fetch_validation_2024.py first" % p)
    zas = parse_zasady(pdftotext(ZASADY, layout=True))
    ark = parse_arkusz(pdftotext(ARKUSZ))
    keys, inputs = [], []
    stats = Counter()
    per_type, per_mod, per_era, per_scoring = Counter(), Counter(), Counter(), Counter()
    points_by = Counter()
    missing_prompt = []
    for it in zas:
        num = it["num"]
        iid = "val2024-hist-z%s" % num
        ttype, rub, scoring = build_rubric(it)
        sheet = ark.get(num)
        if sheet is None:
            missing_prompt.append(num)
            sheet = {"text": "", "pages": []}
        mod, mod_hits = modality(sheet["text"])
        if ttype == "essay":
            mod = "text"
        sec = max(it["sections"]) if it["sections"] else (None, None, None)
        era = "multi" if ttype == "essay" else era_from_section(sec[0])
        page_imgs = ["pages/page-%02d.png" % p for p in sheet["pages"]] if mod == "image" else []
        keys.append({
            "id": iid, "split": "VALIDATION", "task_type": ttype, "era": era,
            "topic": sec[2] or "unspecified", "curriculum_section": sec[1], "modality": mod,
            "modality_evidence": mod_hits, "source_ids": ["cke-2024-mhip-arkusz", "cke-2024-mhip-zasady"],
            "source_group_id": "exam-2024-05-history-f2023", "max_points": it["max"],
            "reference_answer": it["solution"], "official_rules": it["rules"],
            "official_points_ref": "MHIP-R0-100-2405-zasady Zadanie %s" % num,
            "scoring_mode": scoring, "rubric": rub, "builder": BUILDER_REVISION,
        })
        inputs.append({"id": iid, "prompt": PROMPT_HEADER + sheet["text"], "images": page_imgs})
        per_type[ttype] += 1
        per_mod[mod] += 1
        per_era[era] += 1
        per_scoring[scoring] += 1
        points_by[scoring] += it["max"]
    os.makedirs(PRIV, exist_ok=True)
    kp, ip = os.path.join(PRIV, "eval_keys.jsonl"), os.path.join(PRIV, "runner_input.jsonl")
    for p, rows in ((kp, keys), (ip, inputs)):
        assert_private(p)
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    rendered = 0
    if not args.no_images:
        need = sorted(set(int(x[11:13]) for r in inputs for x in r["images"]))
        pdir = os.path.join(PRIV, "pages")
        os.makedirs(pdir, exist_ok=True)
        assert_private(pdir)
        for p in need:
            outbase = os.path.join(pdir, "page-%02d" % p)
            if not os.path.exists(outbase + ".png"):
                subprocess.run(["pdftoppm", "-r", str(args.dpi), "-png", "-f", str(p), "-l", str(p),
                                "-singlefile", ARKUSZ, outbase], check=True)
            rendered += 1
    with open(kp, "rb") as fh:
        kh = sha256_bytes(fh.read())
    with open(ip, "rb") as fh:
        ih = sha256_bytes(fh.read())
    summary = {
        "builder": BUILDER_REVISION, "prompt_revision": PROMPT_REVISION, "split": "VALIDATION",
        "exam": "May 2024 history, extended level, formula 2023 (MHIP-R0-100-2405)",
        "items": len(keys), "total_points": sum(k["max_points"] for k in keys),
        "by_task_type": dict(per_type), "by_modality": dict(per_mod), "by_era_approx": dict(per_era),
        "by_scoring_mode": dict(per_scoring), "points_by_scoring_mode": dict(points_by),
        "items_missing_prompt": missing_prompt, "rendered_pages": rendered,
        "restricted_outputs_sha256": {"private/validation_2024/eval_keys.jsonl": kh,
                                      "private/validation_2024/runner_input.jsonl": ih},
        "note": "Aggregate counts only. Keys, rules, and question text stay in git-ignored private/.",
    }
    os.makedirs(os.path.dirname(STATS), exist_ok=True)
    with open(STATS, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
