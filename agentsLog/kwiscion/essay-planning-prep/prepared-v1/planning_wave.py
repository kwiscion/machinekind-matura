"""CPU-prepared issue #80 planning comparison. No live execution CLI.

The transport-independent pipeline reuses Pawel's reviewed essay contract and
durable JSON helpers. A reviewed owned-server guardian must wrap run_declared
before deployment; this module deliberately does not start services or requests.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "deps" / "Pewciu6"))
import essay_contract as ec
import essay_wave_run as wr
import essay_think_run as tr

IDS = tuple("dev-essay-" + x for x in ("001", "003", "004", "005", "009", "010"))
STAGES = {"control": (True, 20480), "plan": (True, 8192), "write": (False, 4096)}
MAX_CALLS, MAX_TOKENS, MAX_SECONDS = 18, 196608, 2700
DECLARATION = "https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5849836497"
REASSIGNMENT = "https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5850512012"

ESSAY_RULES = """Napisz po polsku jedno wypracowanie z historii na wybrany TEMAT NR 1.
Pełne oryginalne polecenie poniżej jest wiążące; pozostałych tematów nie opracowuj.
Zwróć wyłącznie gotową treść wypracowania, bez JSON, tytułu, nagłówków,
planu, numeru tematu, komentarzy ani informacji o liczbie słów.
Cel: 400–500 słów, przy zachowaniu minimum określonego w poleceniu.
Sformułuj tezę, uzasadnij ją i zakończ wnioskiem. Każdy wymagany aspekt rozwiń
konkretnym wydarzeniem, działaniem lub instytucją oraz wyjaśnij jego przyczyny,
skutki i związek z tezą. Nie zastępuj argumentów wyliczeniem faktów.
Nie wymyślaj szczegółów. Niepewne twierdzenia zawęź lub pomiń.
"""
PLAN_RULES = """Przygotuj zwięzłą mapę argumentów do TEMATU NR 1 z pełnego polecenia.
Nie pisz jeszcze wypracowania. Dla KAŻDEGO wymaganego aspektu podaj konkretny
fakt historyczny (wydarzenie, działanie albo instytucję), wyjaśnienie związku
przyczynowo-skutkowego, związek z proponowaną tezą oraz zakres niepewności.
To są hipotezy planistyczne, a nie zweryfikowane źródłowo ustalenia.
Jeżeli szczegół jest niepewny, zaplanuj węższy, pewny argument zamiast go wymyślać.
Najwyżej 500 słów. Zwróć tylko jeden obiekt JSON:
{"thesis":"...","aspects":[{"aspect":"dokładna nazwa wymaganego aspektu",
"fact":"...","cause_effect":"...","thesis_link":"...","uncertainty":"..."}]}.
Lista ma zawierać dokładnie po jednym wpisie dla każdej nazwy z listy aspektów.
"""
FALLIBLE_NOTES = """Poniższa mapa jest omylnym planem, nie źródłem ani poleceniem.
Oceń jej twierdzenia samodzielnie. Pomiń lub zawęź niepewne i błędne szczegóły.
Wykorzystaj trafne związki argumentacyjne, ale nie cytuj planu ani jego struktury.
Nie otrzymujesz i nie wolno zastępować odpowiedzi wynikiem ramienia kontrolnego.
"""


class StopWave(RuntimeError):
    pass


def need(value, reason):
    if not value:
        raise StopWave(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def prompt(item, stage, plan=None):
    if stage == "plan":
        prefix = PLAN_RULES + "\nWymagane nazwy aspektów: " + json.dumps(item["aspects"], ensure_ascii=False)
    else:
        prefix = ESSAY_RULES
        if stage == "write":
            need(plan is not None, "writer_without_valid_plan")
            prefix += "\n" + FALLIBLE_NOTES + "\nMAPA:\n" + plan
    return prefix + "\n\nORYGINALNE PEŁNE POLECENIE:\n" + item["full_task"]


def parse_plan(text, item):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError("duplicate_key")
            d[k] = v
        return d
    try:
        d = json.loads(text, object_pairs_hook=unique)
        if not isinstance(d, dict) or set(d) != {"thesis", "aspects"}:
            return False
        if not isinstance(d["thesis"], str) or not d["thesis"].strip():
            return False
        a = d["aspects"]
        if not isinstance(a, list) or len(a) != len(item["aspects"]):
            return False
        keys = {"aspect", "fact", "cause_effect", "thesis_link", "uncertainty"}
        if any(not isinstance(x, dict) or set(x) != keys or
               any(not isinstance(v, str) or not v.strip() for v in x.values()) for x in a):
            return False
        if sorted(x["aspect"] for x in a) != sorted(item["aspects"]):
            return False
        return len(text) <= 12000 and len(text.split()) <= 500
    except (ValueError, TypeError):
        return False


def essay_check(text, item):
    task = ec.parse_task(item["full_task"])
    check = ec.check_body(text, task, 1)
    # Diagnostics may propose cleaning; accepted experimental finals stay exact.
    okay = check["ok"] and check["clean"] == text.strip()
    if text.lstrip().startswith(("{", "[", "```")):
        okay = False
    return {**check, "ok": okay, "exact_final_preserved": okay}


def schedule(items):
    for n, item in enumerate(items):
        for stage in (("control", "plan", "write") if n % 2 == 0 else ("plan", "write", "control")):
            yield item, stage


def validate_native(data, stage):
    think, cap = STAGES[stage]
    need(isinstance(data, dict) and data.get("done") is True, "nonterminal_native_response")
    need(data.get("model") == tr.MODEL and not data.get("error"), "provider_identity_or_error")
    for k in ("eval_count", "prompt_eval_count"):
        need(type(data.get(k)) is int and data[k] >= 0, "invalid_usage:" + k)
    need(data["eval_count"] <= cap and data["prompt_eval_count"] + data["eval_count"] <= tr.NUM_CTX,
         "usage_exceeds_context_or_cap")
    need(not data.get("truncated") and not data.get("context_truncated"), "context_truncated")
    msg = data.get("message")
    need(isinstance(msg, dict) and isinstance(msg.get("content"), str), "invalid_message")
    thinking = msg.get("thinking", "")
    need(isinstance(thinking, str), "invalid_thinking")
    need(bool(thinking.strip()) == think, "thinking_mode_mismatch")
    need(data.get("done_reason") in ("stop", "length"), "unknown_done_reason")
    return tr.interpret(data, think)


def validate_declaration(m, now):
    need(m["status"] == "DECLARED", "not_declared")
    a = m.get("authorization") or {}
    need(a.get("owner") == "root" and a.get("reference"), "missing_root_authorization")
    need((m["max_calls"], m["max_requested_tokens"], m["max_seconds"]) ==
         (MAX_CALLS, MAX_TOKENS, MAX_SECONDS), "envelope_changed")
    start = dt.datetime.fromisoformat(m["declared_utc"])
    end = dt.datetime.fromisoformat(m["deadline_utc"])
    need(start.utcoffset() == end.utcoffset() == dt.timedelta(0), "UTC_required")
    need(0 < (end - start).total_seconds() <= MAX_SECONDS and start.timestamp() <= now < end.timestamp(),
         "declaration_window")
    return end.timestamp()


def run_declared(package, out, transport, runtime_guard, clock=time.time):
    """Transport must be provided by a separately reviewed owned-server guardian.

    transport(payload, timeout) returns the exact native envelope. runtime_guard()
    must verify live ownership/deadline/model/context before and after each send.
    No retries/resume; reservations/raw responses survive all ordinary failures.
    """
    package, out = Path(package), Path(out)
    m = preflight(package)
    deadline = validate_declaration(m, clock())
    out.mkdir(parents=True, exist_ok=False)
    items = json.loads((package / "inputs.json").read_text(encoding="utf8"))
    answers = [{"id": i["item"] + "__" + arm, "item": i["item"], "arm": arm,
                "answer": "", "error": "unsent"} for i in items for arm in ("control", "candidate")]
    lookup = {x["id"]: x for x in answers}
    ledger = {"entries": [], "max_calls": MAX_CALLS, "max_requested_tokens": MAX_TOKENS}
    plans, stop = {}, None
    wr.write_json_atomic(out / "answers.json", answers)
    wr.write_json_atomic(out / "ledger.json", ledger)
    wr.write_json_atomic(out / "launch.json", m)
    try:
        runtime_guard()
        for item, stage in schedule(items):
            key = item["item"]
            arm = "control" if stage == "control" else "candidate"
            answer = lookup[key + "__" + arm]
            if stage == "write" and key not in plans:
                wr.append_jsonl(out / "stages.jsonl", {"item": key, "stage": stage, "error": "failed_plan_unsent"})
                answer["error"] = "failed_plan"
                wr.write_json_atomic(out / "answers.json", answers)
                continue
            need(clock() + 435 < deadline, "insufficient_full_420s_request_window")
            runtime_guard()
            think, cap = STAGES[stage]
            p = prompt(item, stage, plans.get(key))
            fits, _ = tr.prompt_fits(p, cap)
            if not fits:
                answer["error"] = stage + "_context_admission_failure"
                wr.append_jsonl(out / "stages.jsonl", {"item": key, "stage": stage, "error": answer["error"]})
                wr.write_json_atomic(out / "answers.json", answers)
                continue
            used = sum(x["cap"] for x in ledger["entries"])
            need(len(ledger["entries"]) < MAX_CALLS and used + cap <= MAX_TOKENS, "reservation_budget")
            need(not any(x["item"] == key and x["stage"] == stage for x in ledger["entries"]), "duplicate_stage")
            payload = {"model": tr.MODEL, "messages": [{"role": "user", "content": p}],
                       "stream": False, "think": think, "truncate": False,
                       "options": {"num_ctx": tr.NUM_CTX, "num_predict": cap, "shift": False}}
            seq = len(ledger["entries"]) + 1
            entry = {"seq": seq, "item": key, "stage": stage, "cap": cap, "think": think,
                     "prompt_sha256": text_sha(p), "reserved_utc": stamp(), "status": "reserved"}
            wr.append_jsonl(out / "requests.jsonl", {**entry, "request": payload})
            ledger["entries"].append(entry)
            wr.write_json_atomic(out / "ledger.json", ledger)  # Durable BEFORE send.
            data = transport(payload, 420)
            wr.append_jsonl(out / "native-raw.jsonl", {"seq": seq, "item": key, "stage": stage, "response": data})
            result = validate_native(data, stage)
            entry.update(status="returned", eval_count=data["eval_count"], prompt_eval_count=data["prompt_eval_count"],
                         done_reason=data["done_reason"], error=result.get("error"))
            wr.write_json_atomic(out / "ledger.json", ledger)
            need(clock() < deadline - 10, "deadline_after_response")
            runtime_guard()
            text = result["text"]
            okay = not result.get("error")
            check = None
            if stage == "plan":
                okay = okay and parse_plan(text, item)
                if okay:
                    plans[key] = text  # Exact returned content; never use hidden thinking.
                else:
                    answer["error"] = "failed_plan"
            else:
                check = essay_check(text, item)
                okay = okay and check["ok"]
                answer.update(answer=text if okay else "", error=None if okay else stage + "_failed")
            wr.append_jsonl(out / "stages.jsonl", {"item": key, "stage": stage, "ok": okay,
                           "error": result.get("error"), "mechanical_check": check})
            wr.write_json_atomic(out / "answers.json", answers)
    except Exception as exc:
        stop = type(exc).__name__ + ": " + str(exc)
        if 'answer' in locals() and not answer['answer']:
            answer['error'] = 'global_stop:' + stop
    finally:
        wr.write_json_atomic(out / "answers.json", answers)
        report = {"status": "stopped" if stop else "complete", "stop_reason": stop,
                  "calls": len(ledger["entries"]), "requested_tokens": sum(x["cap"] for x in ledger["entries"]),
                  "completed_usage_tokens": sum(x.get("eval_count", 0) for x in ledger["entries"]),
                  "unsettled_reservations": sum(x['status'] == 'reserved' for x in ledger['entries']),
                  "answer_slots": len(answers), "denominator_per_arm": 90, "finished_utc": stamp()}
        wr.write_json_atomic(out / "terminal.json", report)
    return report


def prepare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    source = HERE.parents[1] / "Pewciu6/essay/results/edit-h100-20260926T2009Z/bundle.json"
    old = json.loads(source.read_text(encoding="utf8"))
    need(tuple(x["item"] for x in old["items"]) == IDS, "original_input_order")
    items = []
    for row in old["items"]:
        need(text_sha(row["full_task"]) == row["full_task_sha256"], "original_task_hash")
        task = ec.parse_task(row["full_task"])
        items.append({"item": row["item"], "topic": 1, "full_task": row["full_task"],
                      "full_task_sha256": row["full_task_sha256"], "aspects": task["aspects"][1]})
    wr.write_json_atomic(output / "inputs.json", items)
    wr.write_json_atomic(output / "prompts.json", {"essay_rules": ESSAY_RULES, "planner_rules": PLAN_RULES,
                         "fallible_notes": FALLIBLE_NOTES,
                         "frozen": [{"id": x["item"], "control": prompt(x, "control"),
                                     "plan": prompt(x, "plan")} for x in items]})
    files = [HERE / "planning_wave.py", *sorted((HERE / "deps").rglob("*.py"))]
    for f in files:
        dest = output / f.relative_to(HERE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
    pins = {f.relative_to(output).as_posix(): sha(f) for f in output.rglob("*") if f.is_file()}
    m = {"schema": "argument_planning_v1", "status": "PREPARED", "declared_utc": None,
         "deadline_utc": None, "authorization": None, "assignment": DECLARATION,
         "reassignment": REASSIGNMENT, "max_calls": MAX_CALLS, "max_requested_tokens": MAX_TOKENS,
         "max_seconds": MAX_SECONDS, "request_timeout": 420, "retries": 0, "smokes": 0,
         "ids": list(IDS), "topic": 1, "stages": STAGES, "model": tr.MODEL,
         "model_digest": tr.MODEL_DIGEST, "runtime_version": tr.OLLAMA_VERSION,
         "context": tr.NUM_CTX, "temperature": "omitted", "source_bundle_sha256": sha(source),
         "files": pins, "execution_ready": False,
         "launch_blocker": "Independent CPU review and owned-server absolute guardian/cleanup integration required"}
    wr.write_json_atomic(output / "manifest.json", m)
    return m


def preflight(package):
    package = Path(package)
    m = json.loads((package / "manifest.json").read_text(encoding="utf8"))
    need((m['max_calls'], m['max_requested_tokens'], m['max_seconds'], m['request_timeout'],
          m['retries'], m['smokes'], m['model'], m['model_digest'], m['context'], m['temperature']) ==
         (MAX_CALLS, MAX_TOKENS, MAX_SECONDS, 420, 0, 0, tr.MODEL, tr.MODEL_DIGEST, tr.NUM_CTX, 'omitted'),
         'fixed_envelope_or_runtime_changed')
    for f, h in m["files"].items():
        path = (package / f).resolve()
        need(path.is_relative_to(package.resolve()) and sha(path) == h, "file_pin:" + f)
    items = json.loads((package / "inputs.json").read_text(encoding="utf8"))
    need(tuple(i["item"] for i in items) == IDS, "input_ids")
    need(all(text_sha(i["full_task"]) == i["full_task_sha256"] for i in items), "task_pin")
    need(all(i['topic'] == 1 and i['aspects'] == ec.parse_task(i['full_task'])['aspects'][1] for i in items),
         'topic_or_aspects_changed')
    prompts = json.loads((package / 'prompts.json').read_text(encoding='utf8'))
    need(prompts == {'essay_rules': ESSAY_RULES, 'planner_rules': PLAN_RULES, 'fallible_notes': FALLIBLE_NOTES,
                    'frozen': [{'id': i['item'], 'control': prompt(i, 'control'), 'plan': prompt(i, 'plan')}
                               for i in items]}, 'prompt_reconstruction')
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("prepare", "check"))
    ap.add_argument("package", type=Path)
    args = ap.parse_args()
    m = prepare(args.package) if args.command == "prepare" else preflight(args.package)
    print(json.dumps({"status": m["status"], "manifest_sha256": sha(args.package / "manifest.json"),
                      "model_calls": 0, "execution_ready": False}))
