"""Bounded essay-lab wave runner for issue #80 (one 90-minute wave on a dedicated host).

Stdlib only. Every bound is enforced here, not just declared:
  - one wave ledger (ledger.json, rewritten atomically) reloaded and checked before EVERY call:
    total calls (prior readiness/pilot calls included), requested output tokens (the stage cap
    reserved before sending), at most 4 mechanism families, and one wall deadline fixed at the
    first wave call (wave_start + wall_seconds);
  - per call timeout min(420 s, seconds left), no call starts with < MIN_START_S left;
  - each call runs in a worker thread; an overrun (+5 s grace) abandons it and stops the batch;
  - a global watchdog thread hard-exits the process 15 s after the deadline;
  - no retries: each (family, item, stage) is sent at most once per wave; a failed dependency
    leaves its dependants unsent (no fallback), and all attempted/failed/unsent are recorded;
  - a batch id can never be reused and a leftover run.lock blocks any new run (no silent resume).

Families (the final essay cap is the same for every family; the topic is fixed except in D):
  A  single     dedicated long-form single pass (essay-route-v1 prompt)
  B  facts      facts-first: fact bank per aspect, then argument built only on that bank
  C  critic     critic of family A's draft for the same item, then a full rewrite
  D  select     controlled topic selection (one short call), then the A prompt on that topic

  python scripts/Pewciu6/essay_wave_run.py init --wave-dir agentsLog/Pewciu6/essay/private/wave-X
  python scripts/Pewciu6/essay_wave_run.py run --wave-dir ... --batch b1 --families A,B,C,D \\
      --source agentsLog/Pewciu6/essay/dev_fixtures.jsonl --items dev-essay-001,... [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_route as er  # noqa: E402

WAVE_REVISION = "essay-wave-v1"
ENVELOPE = {
    "max_calls": 120, "max_tokens": 240_000, "max_families": 4, "wall_seconds": 5400,
    "per_call_max_s": 420, "retries": 0,
    # already spent before this wave: 3 smoke calls + 6 pilot calls; pilot reserved 7168 tokens
    "prior_calls": 9, "prior_tokens": 7168,
}
MIN_START_S = 30
TRANSPORT_ERRORS = {"URLError", "ConnectionRefusedError", "ConnectionResetError", "RemoteDisconnected", "OSError"}
GRACE_S = 5
CAPS = {"final": 2048, "facts": 768, "critic": 1024, "select": 128}
FAMILIES = {"A": ["final"], "B": ["facts", "final"], "C": ["critic", "final"], "D": ["select", "final"]}
FAMILY_NAMES = {"A": "single", "B": "facts-first", "C": "critic-rewrite", "D": "topic-select"}

FACTS_RULES = """\
Etap 1 z 2: przygotuj wyłącznie BANK FAKTÓW do wypracowania na temat nr {topic} (nie pisz jeszcze wypracowania ani tezy). Dla każdego aspektu wymienionego w temacie (jeśli temat nie wymienia aspektów, wybierz trzy) podaj 4–5 faktów, każdy w osobnej linii w formacie: rok – nazwa własna – co się stało (jedno zdanie). Uwzględnij tylko fakty, których jesteś całkowicie pewien; jeśli nie jesteś pewien daty albo nazwy, pomiń fakt. Maksymalnie 250 słów.
"""
WRITE_FROM_FACTS = """\
Etap 2 z 2: na podstawie poniższego banku faktów najpierw rozważ, jakie stanowisko najlepiej uzasadniają, a potem napisz pełne wypracowanie. Każdy argument oprzyj na konkretnych faktach z banku i wyjaśnij, jak potwierdzają tezę. Pomiń fakty błędne lub nieistotne; nie dodawaj faktów, których nie jesteś pewien.

BANK FAKTÓW:
{facts}
"""
CRITIC_RULES = """\
Jesteś surowym egzaminatorem maturalnym z historii. Oceń poniższe wypracowanie na temat nr {topic}. Wypisz zwięźle w punktach:
1. Błędy rzeczowe (daty, nazwy, terminy, związki przyczynowo-skutkowe) – każdy z poprawną wersją.
2. Aspekty tematu potraktowane powierzchownie i jakich konkretnych faktów z datami tam brakuje.
3. Miejsca, w których argument nie łączy się z tezą albo teza jest niejasna.
Nie przepisuj wypracowania. Maksymalnie 250 słów.

POLECENIE:
{body}

WYPRACOWANIE:
{draft}
"""
REWRITE_RULES = """\
Poniżej masz pierwszą wersję wypracowania i uwagi egzaminatora. Napisz poprawioną, pełną wersję: popraw błędy rzeczowe, pogłęb słabo uzasadnione aspekty konkretnymi faktami i powiąż każdy argument z tezą. Nie wprowadzaj faktów, których nie jesteś pewien; jeśli któraś uwaga egzaminatora jest błędna, pomiń ją.

PIERWSZA WERSJA:
{draft}

UWAGI EGZAMINATORA:
{critique}
"""
SELECT_RULES = """\
Przeczytaj polecenie poniżej. Dla każdego tematu oceń, ile pewnych faktów z datami i nazwami własnymi znasz, i wybierz temat, na który napiszesz najlepiej udokumentowane wypracowanie. Odpowiedz wyłącznie jedną linią w formacie „Temat: N”, bez uzasadnienia.

POLECENIE:
{body}
"""
SELECTION = re.compile(r"Temat\s*(?:nr\s*)?:?\s*(?:nr\s*)?(\d{1,2})", re.I)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def template_sha256() -> str:
    parts = [WAVE_REVISION, er.template_sha256(), FACTS_RULES, WRITE_FROM_FACTS, CRITIC_RULES,
             REWRITE_RULES, SELECT_RULES, json.dumps(CAPS, sort_keys=True)]
    return sha256_text("\x00".join(parts))


def write_json_atomic(path: Path, data) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def append_jsonl(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------- prompts

def base_prompt(info: dict, topic: int) -> str:
    return er.single_prompt(info, topic)


def facts_prompt(info: dict, topic: int) -> str:
    return FACTS_RULES.format(topic=topic) + er.topic_directive(topic) + "\nPOLECENIE:\n" + info["body"]


def write_from_facts_prompt(info: dict, topic: int, facts: str) -> str:
    return (er.COMMON_RULES.format(topic_label=topic) + er.topic_directive(topic)
            + WRITE_FROM_FACTS.format(facts=facts.strip()) + "\nPOLECENIE:\n" + info["body"])


def critic_prompt(info: dict, topic: int, draft: str) -> str:
    return CRITIC_RULES.format(topic=topic, body=info["body"], draft=draft.strip())


def rewrite_prompt(info: dict, topic: int, draft: str, critique: str) -> str:
    return (er.COMMON_RULES.format(topic_label=topic) + er.topic_directive(topic)
            + REWRITE_RULES.format(draft=draft.strip(), critique=critique.strip())
            + "\nPOLECENIE:\n" + info["body"])


def select_prompt(info: dict) -> str:
    return SELECT_RULES.format(body=info["body"])


def parse_selection(text: str, topics: list[int]) -> int | None:
    match = SELECTION.search(text or "")
    if match and int(match.group(1)) in topics:
        return int(match.group(1))
    return None


# ---------------------------------------------------------------- backend

def ollama_backend(base_url: str, model: str, num_ctx: int):
    url = base_url.rstrip("/") + "/api/chat"

    def call(prompt: str, cap: int, timeout: float) -> dict:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                "think": False, "options": {"num_predict": cap, "num_ctx": num_ctx}}
        request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {"error": f"http_{exc.code}"}
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
            return {"error": type(exc).__name__}
        text = (data.get("message") or {}).get("content") or ""
        out = {"text": text, "done_reason": data.get("done_reason"), "eval_count": data.get("eval_count"),
               "prompt_eval_count": data.get("prompt_eval_count"), "model": data.get("model")}
        if data.get("done_reason") == "length":
            out["error"] = "truncated"
        elif not text.strip():
            out["error"] = "empty"
        return out

    return call


def call_with_timeout(backend, prompt: str, cap: int, timeout: float) -> tuple[dict, bool]:
    box: dict = {}

    def target():
        try:
            box["result"] = backend(prompt, cap, timeout)
        except Exception as exc:  # noqa: BLE001 - recorded, never retried
            box["result"] = {"error": f"exception:{type(exc).__name__}"}

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout + GRACE_S)
    if worker.is_alive():
        return {"error": "call_overran"}, True
    return box["result"], False


# ---------------------------------------------------------------- ledger

class StopWave(Exception):
    pass


class Wave:
    def __init__(self, wave_dir: Path, backend=None, clock=time.time):
        self.dir = wave_dir
        self.ledger_path = wave_dir / "ledger.json"
        self.backend = backend
        self.clock = clock

    def load(self) -> dict:
        return json.loads(self.ledger_path.read_text(encoding="utf-8"))

    def save(self, ledger: dict) -> None:
        write_json_atomic(self.ledger_path, ledger)

    @staticmethod
    def totals(ledger: dict) -> tuple[int, int]:
        calls = ledger["envelope"]["prior_calls"] + len(ledger["entries"])
        tokens = ledger["envelope"]["prior_tokens"] + sum(e["cap"] for e in ledger["entries"])
        return calls, tokens

    def seconds_left(self, ledger: dict) -> float:
        if ledger["wave_start"] is None:
            return float(ledger["envelope"]["wall_seconds"])
        return ledger["deadline"] - self.clock()

    def reserve(self, batch: str, family: str, item: str, stage: str, cap: int, prompt: str) -> tuple[dict, float]:
        """Reload the ledger, check every bound, persist the reservation, return (entry, timeout)."""
        ledger = self.load()
        env = ledger["envelope"]
        calls, tokens = self.totals(ledger)
        if calls + 1 > env["max_calls"]:
            raise StopWave("call_limit")
        if tokens + cap > env["max_tokens"]:
            raise StopWave("token_limit")
        if family not in ledger["families"] and len(ledger["families"]) >= env["max_families"]:
            raise StopWave("family_limit")
        key = f"{family}|{item}|{stage}"
        if any(e["key"] == key for e in ledger["entries"]):
            raise StopWave(f"duplicate_call:{key}")
        now = self.clock()
        if ledger["wave_start"] is None:
            ledger["wave_start"] = now
            ledger["deadline"] = now + env["wall_seconds"]
            ledger["wave_start_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            ledger["deadline_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ledger["deadline"]))
        left = ledger["deadline"] - now
        if left < MIN_START_S:
            raise StopWave("deadline")
        if family not in ledger["families"]:
            ledger["families"].append(family)
        entry = {"seq": len(ledger["entries"]) + 1, "key": key, "batch": batch, "family": family, "item": item,
                 "stage": stage, "cap": cap, "prompt_sha256": sha256_text(prompt), "status": "reserved",
                 "t_reserved": now}
        ledger["entries"].append(entry)
        self.save(ledger)
        return entry, min(env["per_call_max_s"], left)

    def settle(self, seq: int, status: str, **fields) -> None:
        ledger = self.load()
        entry = ledger["entries"][seq - 1]
        entry.update(status=status, **fields)
        self.save(ledger)


def start_watchdog(wave: Wave, stop_event: threading.Event) -> None:
    def watch():
        while not stop_event.wait(1.0):
            try:
                ledger = wave.load()
            except (OSError, ValueError):
                continue
            if ledger.get("deadline") and wave.clock() > ledger["deadline"] + 15:
                sys.stderr.write("watchdog: wave deadline passed, hard exit\n")
                append_jsonl(wave.dir / "watchdog.jsonl", {"t": wave.clock(), "event": "hard_exit"})
                os._exit(3)

    threading.Thread(target=watch, daemon=True).start()


# ---------------------------------------------------------------- batch

def load_items(source: Path, ids: list[str]) -> list[tuple[dict, dict]]:
    rows = {row["id"]: row for row in er.read_jsonl(source)}
    out = []
    for item_id in ids:
        if item_id not in rows:
            raise SystemExit(f"unknown item {item_id} in {source}")
        info = er.detect_essay(rows[item_id]["prompt"])
        if not info["is_essay"]:
            raise SystemExit(f"{item_id} is not routed as an essay; refusing")
        out.append((rows[item_id], info))
    return out


def prior_answers(wave_dir: Path, family: str) -> dict:
    """Final answers of a family from earlier (or the current) batches, keyed by item id."""
    found = {}
    for path in sorted((wave_dir / "batches").glob("*/answers.jsonl")):
        for row in read_jsonl(path):
            if row["family"] == family and not row.get("error_type") and row.get("answer"):
                found[row["item"]] = row
    return found


def plan_calls(families: list[str], items: list) -> list[tuple[str, str, str, int]]:
    plan = []
    for family in families:
        for row, _info in items:
            for stage in FAMILIES[family]:
                plan.append((family, row["id"], stage, CAPS[stage]))
    return plan


def run_batch(wave: Wave, batch: str, families: list[str], items: list, topic: int, source: Path) -> dict:
    batch_dir = wave.dir / "batches" / batch
    batch_dir.mkdir(parents=True, exist_ok=False)  # never reuse a batch id
    raw_path, answers_path = batch_dir / "raw.jsonl", batch_dir / "answers.jsonl"
    manifest = {"batch": batch, "families": families, "items": [r["id"] for r, _ in items], "topic": topic,
                "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "template_sha256": template_sha256(), "caps": CAPS, "status": "running", "stop_reason": None,
                "attempted": 0, "failed": [], "unsent": [], "started": wave.clock()}
    write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    stop_reason = None

    def send(family, item_id, stage, prompt):
        nonlocal stop_reason
        cap = CAPS[stage]
        entry, timeout = wave.reserve(batch, family, item_id, stage, cap, prompt)
        manifest["attempted"] += 1
        started = wave.clock()
        result, overran = call_with_timeout(wave.backend, prompt, cap, timeout)
        elapsed = round(wave.clock() - started, 2)
        status = "error" if result.get("error") else "ok"
        wave.settle(entry["seq"], status, elapsed_s=elapsed, timeout_s=round(timeout, 1),
                    error=result.get("error"), eval_count=result.get("eval_count"),
                    prompt_eval_count=result.get("prompt_eval_count"), done_reason=result.get("done_reason"))
        append_jsonl(raw_path, {"batch": batch, "family": family, "item": item_id, "stage": stage, "cap": cap,
                                "prompt": prompt, "prompt_sha256": entry["prompt_sha256"], **result,
                                "elapsed_s": elapsed, "timeout_s": round(timeout, 1)})
        if result.get("error"):
            manifest["failed"].append({"family": family, "item": item_id, "stage": stage, "error": result["error"]})
        if overran:
            raise StopWave("call_overran")
        if result.get("error") in TRANSPORT_ERRORS:
            raise StopWave(f"transport_error:{result['error']}")  # e.g. tunnel down: stop, do not burn calls
        return result

    try:
        for family in families:
            drafts = prior_answers(wave.dir, "A") if family == "C" else {}
            for row, info in items:
                item_id = row["id"]
                answer, error_type, chosen = None, None, topic
                if family == "A":
                    r = send(family, item_id, "final", base_prompt(info, topic))
                elif family == "B":
                    f = send(family, item_id, "facts", facts_prompt(info, topic))
                    if f.get("error"):
                        manifest["unsent"].append({"family": family, "item": item_id, "stage": "final",
                                                   "reason": f"failed_facts:{f['error']}"})
                        r = {"error": f"unsent_after_facts_{f['error']}"}
                    else:
                        r = send(family, item_id, "final", write_from_facts_prompt(info, topic, f["text"]))
                elif family == "C":
                    draft = drafts.get(item_id)
                    if not draft:
                        for stage in ("critic", "final"):
                            manifest["unsent"].append({"family": family, "item": item_id, "stage": stage,
                                                       "reason": "no_A_draft"})
                        r = {"error": "unsent_no_A_draft"}
                    else:
                        c = send(family, item_id, "critic", critic_prompt(info, topic, draft["answer"]))
                        if c.get("error"):
                            manifest["unsent"].append({"family": family, "item": item_id, "stage": "final",
                                                       "reason": f"failed_critic:{c['error']}"})
                            r = {"error": f"unsent_after_critic_{c['error']}"}
                        else:
                            r = send(family, item_id, "final",
                                     rewrite_prompt(info, topic, draft["answer"], c["text"]))
                elif family == "D":
                    s = send(family, item_id, "select", select_prompt(info))
                    chosen = None if s.get("error") else parse_selection(s.get("text", ""), info["topics"])
                    if chosen is None:
                        manifest["unsent"].append({"family": family, "item": item_id, "stage": "final",
                                                   "reason": "bad_selection"})
                        r = {"error": "unsent_bad_selection"}
                    else:
                        r = send(family, item_id, "final", base_prompt(info, chosen))
                else:
                    raise SystemExit(f"unknown family {family}")
                if r.get("error"):
                    error_type = r["error"]
                else:
                    answer = r["text"]
                append_jsonl(answers_path, {"id": f"{item_id}__{family}", "item": item_id, "family": family,
                                            "family_name": FAMILY_NAMES[family], "topic": chosen,
                                            "answer": answer, "error_type": error_type, "batch": batch})
    except StopWave as exc:
        stop_reason = str(exc)
        done = {(e["family"], e["item"], e["stage"]) for e in wave.load()["entries"] if e["batch"] == batch}
        recorded = {(u["family"], u["item"], u["stage"]) for u in manifest["unsent"]}
        for family, item_id, stage, _cap in plan_calls(families, items):
            if (family, item_id, stage) not in done and (family, item_id, stage) not in recorded:
                manifest["unsent"].append({"family": family, "item": item_id, "stage": stage, "reason": stop_reason})
    manifest.update(status="stopped" if stop_reason else "complete", stop_reason=stop_reason,
                    finished=wave.clock())
    if answers_path.exists():
        manifest["answers_sha256"] = hashlib.sha256(answers_path.read_bytes()).hexdigest()
    write_json_atomic(batch_dir / "batch_manifest.json", manifest)
    return manifest


# ---------------------------------------------------------------- cli

def cmd_init(args) -> int:
    wave_dir = Path(args.wave_dir)
    er.require_private_dir(wave_dir)
    wave_dir.mkdir(parents=True, exist_ok=False)
    ledger = {"revision": WAVE_REVISION, "wave_id": wave_dir.name, "envelope": ENVELOPE, "caps": CAPS,
              "template_sha256": template_sha256(), "model": args.model, "num_ctx": args.num_ctx,
              "think": False, "temperature": None, "base_url": args.base_url, "wave_start": None,
              "deadline": None, "families": [], "entries": [], "created": time.time()}
    write_json_atomic(wave_dir / "ledger.json", ledger)
    print(json.dumps({"wave_dir": str(wave_dir), "template_sha256": ledger["template_sha256"]}, indent=1))
    return 0


def cmd_run(args) -> int:
    wave_dir = Path(args.wave_dir)
    families = [f.strip() for f in args.families.split(",") if f.strip()]
    items = load_items(Path(args.source), [i.strip() for i in args.items.split(",") if i.strip()])
    wave = Wave(wave_dir)
    ledger = wave.load()
    plan = plan_calls(families, items)
    calls, tokens = Wave.totals(ledger)
    need_tokens = sum(p[3] for p in plan)
    env = ledger["envelope"]
    summary = {"planned_calls": len(plan), "planned_tokens": need_tokens, "used_calls": calls,
               "used_tokens": tokens, "after_calls": calls + len(plan), "after_tokens": tokens + need_tokens,
               "families_after": sorted(set(ledger["families"]) | set(families)),
               "seconds_left": round(wave.seconds_left(ledger), 1)}
    summary["fits"] = (summary["after_calls"] <= env["max_calls"] and summary["after_tokens"] <= env["max_tokens"]
                       and len(summary["families_after"]) <= env["max_families"])
    print(json.dumps(summary, indent=1))
    if args.check:
        return 0 if summary["fits"] else 2
    if not summary["fits"]:
        print("refusing: planned batch exceeds the envelope", file=sys.stderr)
        return 2
    lock = wave_dir / "run.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print("refusing: run.lock exists (another run, or an interrupted one to inspect first)", file=sys.stderr)
        return 2
    os.write(fd, f"{os.getpid()} {args.batch}\n".encode())
    os.close(fd)
    stop = threading.Event()
    wave.backend = ollama_backend(args.base_url, ledger["model"], ledger["num_ctx"])
    start_watchdog(wave, stop)
    try:
        manifest = run_batch(wave, args.batch, families, items, args.topic, Path(args.source))
    finally:
        stop.set()
        lock.unlink()
    ledger = wave.load()
    calls, tokens = Wave.totals(ledger)
    print(json.dumps({"batch": args.batch, "status": manifest["status"], "stop_reason": manifest["stop_reason"],
                      "attempted": manifest["attempted"], "failed": len(manifest["failed"]),
                      "unsent": len(manifest["unsent"]), "ledger_calls": calls, "ledger_tokens": tokens,
                      "seconds_left": round(wave.seconds_left(ledger), 1)}, indent=1))
    return 0 if manifest["status"] == "complete" else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--wave-dir", required=True)
    p.add_argument("--model", default="gemma4:12b-it-q4_K_M")
    p.add_argument("--num-ctx", type=int, default=32768)
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("run")
    p.add_argument("--wave-dir", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--families", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--items", required=True)
    p.add_argument("--topic", type=int, default=1)
    p.add_argument("--base-url", default="http://127.0.0.1:11434")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
