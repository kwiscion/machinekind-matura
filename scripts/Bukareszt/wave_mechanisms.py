"""Evidence mechanisms for the #96 H100 wave (used through wave_run.py module arms).

Every mechanism returns `[evidence block] + original prompt` (verbatim suffix) or the original prompt unchanged
(no-retrieval fallback). Auxiliary model calls are text-only and never see answers/keys. Retrieval uses the pinned
index, verified by prepare_bounded_rag.load_pinned_assets. The #57 untrusted-reference block frames all evidence.

  retrieve_verify   top-3 by the decontaminated query (#96 variant H); 1 aux call: the model marks which passages
                    contain information needed for the question (or BRAK); only those are inserted
  relation_query    1 aux call: the model writes a compact entity/relation/period search query (no answer);
                    top-2 compact windows for that query are inserted (no lexical gate)
  fact_card         no aux call: up to 5 verbatim sentences with a year or a question entity from the top-3 chunks
                    of the decontaminated query, as one compact card
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prepare_bounded_rag as pbr  # noqa: E402
import selective_rag as S  # noqa: E402

TASK_CHARS = 2500
BUDGET = 1000
_ASSETS = None


def assets():
    global _ASSETS
    if _ASSETS is None:
        root = pbr.DEFAULT_ROOT
        _ASSETS = pbr.load_pinned_assets(root, root / "staging" / "manifest.json", False)[:3]
    return _ASSETS


def task_text(prompt: str) -> str:
    return S.strip_templates(prompt)[:TASK_CHARS]


def compose(prompt: str, hits: list[dict]) -> tuple[str, dict]:
    if not hits:
        return prompt, {"inserted": []}
    block, stats = pbr.build_evidence(hits, BUDGET)
    return pbr.compose(prompt, block, None), {"inserted": stats["included"]}


def windows(retrieval, idx, hits, text, n):
    terms = S.distinctive_terms(retrieval, idx, text)
    return [{"title": h["title"], "chunk_id": h["chunk_id"],
             "text": S.compact_window(retrieval, h["text"], terms, terms)} for h in hits[:n]]


def retrieve_verify(case: dict, aux) -> str:
    retrieval, idx, graph = assets()
    q = S.build_query(retrieval, case["prompt"], S.SELECTED_VARIANT)
    cands = windows(retrieval, idx, S.rank(retrieval, idx, graph, q, k=3), q["text"], 3)
    listing = "\n\n".join(f"[{i}] {c['title']}: {c['text']}" for i, c in enumerate(cands, 1))
    verdict = aux(
        "Oceń, czy poniższe fragmenty encyklopedyczne zawierają informacje potrzebne do odpowiedzi na zadanie "
        "egzaminacyjne. Nie rozwiązuj zadania.\n\nZadanie:\n" + task_text(case["prompt"]) +
        "\n\nFragmenty:\n" + listing +
        "\n\nOdpowiedz wyłącznie numerami przydatnych fragmentów oddzielonymi przecinkami (np. 1,3) albo słowem BRAK.")
    keep = [] if re.search(r"\bBRAK\b", verdict, re.I) else sorted({int(n) for n in re.findall(r"\b([1-3])\b", verdict)})
    return compose(case["prompt"], [cands[i - 1] for i in keep])[0]


def relation_query(case: dict, aux) -> str:
    retrieval, idx, graph = assets()
    written = aux(
        "Napisz jedno krótkie zapytanie do wyszukiwarki encyklopedycznej (5–12 słów) zawierające kluczowe postacie, "
        "wydarzenia, pojęcia i okres, których dotyczy zadanie egzaminacyjne. Nie odpowiadaj na zadanie i nie "
        "dodawaj wyjaśnień.\n\nZadanie:\n" + task_text(case["prompt"]) + "\n\nZapytanie:")
    line = next((l.strip(" -*\"'") for l in written.splitlines() if l.strip()), "")[:200]
    if not line:
        return case["prompt"]
    q = {"text": line, "years": sorted(S.extract_years(retrieval, line, False)[0]), "bce_years": [], "bce_aware": False,
         "year_boost": True, "entity_boost": True}
    return compose(case["prompt"], windows(retrieval, idx, S.rank(retrieval, idx, graph, q, k=2), line, 2))[0]


def fact_card(case: dict, aux) -> str:
    retrieval, idx, graph = assets()
    q = S.build_query(retrieval, case["prompt"], S.SELECTED_VARIANT)
    hits = S.rank(retrieval, idx, graph, q, k=3)
    names = S.proper_name_terms(retrieval, task_text(case["prompt"]))
    terms = S.distinctive_terms(retrieval, idx, q["text"])
    facts, seen = [], set()
    for h in hits:
        for sent in re.split(r"(?<=[.!?])\s+", " ".join(h["text"].split())):
            toks = set(retrieval.tokenize(sent))
            dated = bool(re.search(r"(?<!\d)\d{3,4}(?!\d)", sent))
            if sent in seen or len(sent) > 260 or not (toks & terms):
                continue
            if dated or toks & names:
                facts.append(f"- {sent} ({h['title']})")
                seen.add(sent)
            if len(facts) == 5:
                break
        if len(facts) == 5:
            break
    if not facts:
        return case["prompt"]
    card = {"title": "Karta faktów (zdania z encyklopedii, mogą być nieistotne)", "chunk_id": "fact-card",
            "text": "\n".join(facts)}
    return compose(case["prompt"], [card])[0]
