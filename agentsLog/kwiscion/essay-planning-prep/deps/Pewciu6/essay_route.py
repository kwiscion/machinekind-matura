"""Essay route for the infer.py contract (issue #80): detect essays, build long-form prompts.

Stdlib only. It never calls a model: it writes infer.py input JSONL ({id, prompt, images})
plus a launch manifest, and `infer.py` executes each stage under the lead's launch record.

  build            essay items -> single-pass input and/or plan-stage input + manifest
  write-from-plan  plan-stage infer.py output -> write-stage input (same topic, no retry)

Essays are detected from question structure (essay keyword plus enumerated topics or a
word-count requirement), never from item ids. Non-essay items are skipped, or copied
unchanged with --passthrough. The original item text is kept verbatim; only an explicitly
recognized leading solver header (an imperative "Rozwiąż … zadanie" addressed to the solver
that also says "Odpowiadaj … zwięźle/krótko") is removed, and its hash is recorded. Any
other leading paragraph, including a source that happens to say "krótko", is preserved.

Plan-bearing files (write.input.jsonl) and raw provider output may only be written under a
git-ignored `private/` run directory; `build` refuses any other --out-dir unless --dry-run.
The bounded launcher is scripts/Pewciu6/essay_pilot_run.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from normalize_outputs import final_text  # noqa: E402  (shared adapter helper)

PROMPT_REVISION = "essay-route-v1"
PLAN_CAP = 512
FINAL_CAP = 1536
# Initial pilot envelope from issue #80; the lead's launch record may lower, never raise it.
ENVELOPE_MAX_CALLS = 6
ENVELOPE_MAX_TOKENS = 7168
ENVELOPE_MAX_MINUTES = 30
ENVELOPE_RETRIES = 0
PLAN_SUFFIX = "__plan"

ESSAY_WORD = re.compile(r"wypracowani|WYPRACOWANIE", re.I)
LENGTH_REQ = re.compile(r"(minimum|co najmniej|nie mniej niż)\s+\d{3}\s+(słów|wyrazów)", re.I)
TOPIC_LINE = re.compile(r"(?m)^\s*(?:Temat\s+(?:nr\s+)?)?(\d{1,2})\.\s+\S")
NAMED_TOPIC = re.compile(r"(?m)^\s*Temat\s+(?:nr\s+)?\d{1,2}\.")
CONCISION = re.compile(r"zwięźle|krótko|zwięzł", re.I)
# A solver header is recognized only when it opens with an imperative to solve the task and
# instructs the answerer how to answer; a source paragraph never has this shape.
SOLVER_OPENING = re.compile(r"^\s*Rozwiąż\b[^.\n]*\bzadani", re.I)
SOLVER_INSTRUCTION = re.compile(r"\bOdpowiadaj\b", re.I)
PRIVATE_PART = "private"

COMMON_RULES = """\
To zadanie wymaga rozbudowanego wypracowania, a nie krótkiej odpowiedzi. Spełnij wszystkie wymagania z polecenia poniżej, w tym zakres chronologiczny i wszystkie wskazane w temacie aspekty.

Zasady formy:
- Pierwsza linia to dokładnie „Temat nr {topic_label}”. Zaraz potem zacznij wypracowanie; nie pisz żadnego wstępu od siebie, komentarza ani zapowiedzi („Oto…”, „Poniżej…”).
- Długość: co najmniej 300 słów tekstu ciągłego (bez nagłówków); celuj w 350–450 słów.
- Wstęp: jedno lub dwa zdania wprowadzenia i wyraźna teza, zapisana jako zdanie zaczynające się od „Teza:”.
- Rozwinięcie: trzy oznaczone części, każda zaczyna się od nagłówka w osobnej linii „Aspekt 1 – …:”, „Aspekt 2 – …:”, „Aspekt 3 – …:”. Jeśli temat wymienia aspekty, użyj dokładnie tych aspektów (gdy wymienia dwa, trzeci poświęć ich wzajemnym powiązaniom lub skutkom); w przeciwnym razie wybierz trzy różne aspekty.
- W każdym aspekcie podaj co najmniej dwa konkretne fakty z datą (rok) oraz nazwą własną (osoba, miejsce, akt prawny, wydarzenie) i przy każdym fakcie wyjaśnij, jak potwierdza tezę.
- Zakończenie: osobny akapit zaczynający się od „Zakończenie:”, który podsumowuje argumenty i wraca do tezy.
- Podawaj tylko fakty, których jesteś pewien; nie wymyślaj nazw, terminów ani dat. Pisz po polsku, jednym spójnym tekstem, bez punktorów w rozwinięciu.
"""

FIXED_TOPIC = "Pisz na temat nr {topic}. Nie wybieraj innego tematu.\n"
CHOOSE_TOPIC = "Wybierz ten temat, o którym znasz najwięcej pewnych faktów z datami, i podaj jego numer w pierwszej linii.\n"

PLAN_RULES = """\
Etap 1 z 2: przygotuj wyłącznie PLAN wypracowania (nie pisz jeszcze wypracowania). Maksymalnie 200 słów, w punktach:
- Temat nr {topic_label}
- Teza: jedno zdanie ze stanowiskiem.
- Aspekt 1, Aspekt 2, Aspekt 3: nazwa aspektu (z tematu, jeśli je wymienia) i po 2–3 fakty, każdy z rokiem, nazwą własną i krótkim związkiem z tezą.
- Zakończenie: jedno zdanie wniosku.
Podawaj tylko fakty, których jesteś pewien. Spełnij wszystkie wymagania z polecenia poniżej.
"""

WRITE_FROM_PLAN = """\
Etap 2 z 2: napisz pełne wypracowanie według poniższego planu. Popraw plan, jeśli zawiera błąd rzeczowy; nie dodawaj faktów, których nie jesteś pewien. Zachowaj temat nr {topic_label} i tezę z planu.

PLAN:
{plan}
"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def template_sha256() -> str:
    parts = [PROMPT_REVISION, COMMON_RULES, FIXED_TOPIC, CHOOSE_TOPIC, PLAN_RULES, WRITE_FROM_PLAN]
    return sha256_text("\x00".join(parts))


def is_solver_header(paragraph: str) -> bool:
    return bool(SOLVER_OPENING.search(paragraph) and SOLVER_INSTRUCTION.search(paragraph)
                and CONCISION.search(paragraph) and not ESSAY_WORD.search(paragraph))


def split_header(prompt: str) -> tuple[str, str]:
    """Split off an explicitly recognized leading solver header; keep everything else."""
    head, sep, body = prompt.partition("\n\n")
    if sep and body.strip() and is_solver_header(head):
        return head, body
    return "", prompt


def extract_topics(body: str) -> list[int]:
    """Topic numbers enumerated in the item, in order ("Temat 1." or "1." lines)."""
    numbers = []
    for match in TOPIC_LINE.finditer(body):
        n = int(match.group(1))
        if n == len(numbers) + 1:
            numbers.append(n)
    return numbers


def detect_essay(prompt: str) -> dict:
    header, body = split_header(prompt)
    topics = extract_topics(body)
    features = {
        "essay_word": bool(ESSAY_WORD.search(body)),
        "length_requirement": bool(LENGTH_REQ.search(body)),
        "named_topics": len(NAMED_TOPIC.findall(body)),
        "enumerated_topics": len(topics),
    }
    is_essay = features["essay_word"] and (
        features["length_requirement"] or features["named_topics"] >= 2 or (len(topics) >= 2 and "temat" in body.lower())
    )
    return {"is_essay": is_essay, "features": features, "topics": topics, "header": header, "body": body}


def topic_label(topics: list[int], topic: int | None) -> str:
    if topic is None:
        return "…" if len(topics) > 1 else "1"
    return str(topic)


def resolve_topic(info: dict, topic: int, select_topic: bool, item_id: str) -> int | None:
    if select_topic:
        return None
    if info["topics"] and topic not in info["topics"]:
        raise ValueError(f"{item_id}: topic {topic} not among enumerated topics {info['topics']}")
    return topic


def topic_directive(topic: int | None) -> str:
    return CHOOSE_TOPIC if topic is None else FIXED_TOPIC.format(topic=topic)


def single_prompt(info: dict, topic: int | None) -> str:
    label = topic_label(info["topics"], topic)
    return (COMMON_RULES.format(topic_label=label) + topic_directive(topic)
            + "\nPOLECENIE:\n" + info["body"])


def plan_prompt(info: dict, topic: int | None) -> str:
    label = topic_label(info["topics"], topic)
    return PLAN_RULES.format(topic_label=label) + topic_directive(topic) + "\nPOLECENIE:\n" + info["body"]


def write_prompt(info: dict, topic: int | None, plan: str) -> str:
    label = topic_label(info["topics"], topic)
    return (COMMON_RULES.format(topic_label=label) + topic_directive(topic)
            + WRITE_FROM_PLAN.format(topic_label=label, plan=plan.strip())
            + "\nPOLECENIE:\n" + info["body"])


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("prompt"), str):
                raise ValueError(f"{path}:{number} requires string id and prompt")
            rows.append(row)
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate ids")
    return rows


def rebase_images(images: list, source: Path, target_dir: Path) -> list[str]:
    """Keep image paths valid relative to the new JSONL location (infer.py resolves them so)."""
    out = []
    for item in images or []:
        path = Path(item)
        if not path.is_absolute():
            path = (source.parent / path).resolve()
        out.append(os.path.relpath(path, target_dir.resolve()))
    return out


def require_private_dir(path: Path) -> None:
    """Refuse to write plan-bearing or raw-output files outside a git-ignored private/ dir.

    Inside a git checkout the dir must have a private/ component below the repo root and be
    git-ignored. Outside one (e.g. a temp dir in tests) a private/ component is required;
    the macOS system prefix /private (/var -> /private/var) does not count.
    """
    absolute = Path(os.path.abspath(path))
    probe = absolute
    while not probe.exists():
        probe = probe.parent
    try:
        top = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=False)
        in_git = top.returncode == 0
    except OSError:
        in_git = False
    if in_git:
        root = Path(top.stdout.strip()).resolve()
        resolved = probe.resolve() / absolute.relative_to(probe)
        try:
            parts = resolved.relative_to(root).parts
        except ValueError:
            parts = ()
        if PRIVATE_PART not in parts:
            raise ValueError(f"{path}: plan-bearing/raw outputs must live under a '{PRIVATE_PART}/' dir in the repo")
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(resolved / "probe.jsonl")],
                                 capture_output=True, check=False)
        if ignored.returncode != 0:
            raise ValueError(f"{path}: directory is not git-ignored; refusing to write private outputs there")
        return
    parts = absolute.parts
    if parts[:2] == ("/", PRIVATE_PART):
        parts = parts[2:]
    if PRIVATE_PART not in parts:
        raise ValueError(f"{path}: plan-bearing/raw outputs must live under a '{PRIVATE_PART}/' directory")


def envelope(stages: dict[str, dict]) -> dict:
    calls = sum(stage["calls"] for stage in stages.values())
    tokens = sum(stage["calls"] * stage["max_output_tokens"] for stage in stages.values())
    return {
        "calls": calls,
        "requested_output_tokens": tokens,
        "max_calls": ENVELOPE_MAX_CALLS,
        "max_requested_output_tokens": ENVELOPE_MAX_TOKENS,
        "retries": ENVELOPE_RETRIES,
        "max_wall_minutes": ENVELOPE_MAX_MINUTES,
        "within_envelope": calls <= ENVELOPE_MAX_CALLS and tokens <= ENVELOPE_MAX_TOKENS,
    }


def write_jsonl(path: Path, rows: list[dict]) -> str:
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
    return sha256_text(text)


def build(args: argparse.Namespace) -> int:
    rows = read_jsonl(args.input)
    modes = ["single", "plan"] if args.mode == "both" else [args.mode]
    out_dir: Path = args.out_dir
    records = {mode: [] for mode in modes}
    passthrough, items = [], []
    for row in rows:
        info = detect_essay(row["prompt"])
        if not info["is_essay"]:
            if args.passthrough:
                passthrough.append({"id": row["id"], "prompt": row["prompt"], "images": rebase_images(row.get("images"), args.input, out_dir)})
            continue
        if args.limit is not None and len(items) >= args.limit:
            continue
        topic = resolve_topic(info, args.topic, args.select_topic, row["id"])
        images = rebase_images(row.get("images"), args.input, out_dir)
        items.append({
            "id": row["id"],
            "features": info["features"],
            "topics": info["topics"],
            "topic": topic,
            "header_stripped_sha256": sha256_text(info["header"]) if info["header"] else None,
            "body_sha256": sha256_text(info["body"]),
        })
        if "single" in records:
            records["single"].append({"id": row["id"], "prompt": single_prompt(info, topic), "images": images})
        if "plan" in records:
            records["plan"].append({"id": row["id"] + PLAN_SUFFIX, "prompt": plan_prompt(info, topic), "images": images})
    if not items:
        raise ValueError("No essay items detected; nothing to build")
    stages = {}
    if "single" in records:
        stages["single"] = {"file": "single.input.jsonl", "calls": len(items), "max_output_tokens": FINAL_CAP}
    if "plan" in records:
        stages["plan"] = {"file": "plan.input.jsonl", "calls": len(items), "max_output_tokens": PLAN_CAP}
        stages["write"] = {"file": "write.input.jsonl", "calls": len(items), "max_output_tokens": FINAL_CAP,
                           "built_by": "essay_route.py write-from-plan after the plan stage"}
    budget = envelope(stages)
    manifest = {
        "prompt_revision": PROMPT_REVISION,
        "prompt_template_sha256": template_sha256(),
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "mode": args.mode,
        "topic_selection": bool(args.select_topic),
        "fixed_topic": None if args.select_topic else args.topic,
        "caps": {"plan": PLAN_CAP, "final": FINAL_CAP},
        "stages": stages,
        "envelope": budget,
        "items": items,
        "non_essay_passthrough": len(passthrough) if args.passthrough else 0,
        "commands": launch_commands(out_dir, stages, args.input),
        "notes": "No model calls were made by this script. Inference requires the lead's host assignment and launch record.",
    }
    if not budget["within_envelope"]:
        print(json.dumps(manifest["envelope"], ensure_ascii=False), file=sys.stderr)
        raise ValueError(f"Envelope exceeded: {budget['calls']} calls / {budget['requested_output_tokens']} tokens")
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    require_private_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    for mode, stage_rows in records.items():
        stages[mode]["sha256"] = write_jsonl(out_dir / stages[mode]["file"], stage_rows)
    if passthrough:
        manifest["passthrough_file"] = "passthrough.input.jsonl"
        manifest["passthrough_sha256"] = write_jsonl(out_dir / "passthrough.input.jsonl", passthrough)
    if args.base_config:
        manifest["configs"] = write_configs(args.base_config, out_dir, stages)
    with (out_dir / "manifest.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(items)} essay item(s), {budget['calls']} planned calls, "
          f"{budget['requested_output_tokens']} requested output tokens to {out_dir}")
    return 0


def write_configs(base_config: Path, out_dir: Path, stages: dict) -> dict:
    """Derive per-stage infer.py configs that differ from the base only in max_output_tokens."""
    base = json.loads(base_config.read_text(encoding="utf-8"))
    if not isinstance(base, dict):
        raise ValueError("Base config must be a JSON object")
    written = {}
    for cap_name, cap in (("final", FINAL_CAP), ("plan", PLAN_CAP)):
        if cap_name == "plan" and "plan" not in stages:
            continue
        config = dict(base, max_output_tokens=cap)
        text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        name = f"config.{cap_name}.json"
        with (out_dir / name).open("x", encoding="utf-8") as handle:
            handle.write(text)
        written[name] = sha256_text(text)
    return written


def launch_commands(out_dir: Path, stages: dict, source: Path) -> list[str]:
    """The only sanctioned launch path: the bounded orchestrator (one global deadline, no retries)."""
    d = out_dir.as_posix()
    return [f"python scripts/Pewciu6/essay_pilot_run.py --manifest {d}/manifest.json --source {source.as_posix()}"]


def validate_plan_rows(rows: list, expected: set[str]) -> dict[str, dict]:
    """Strictly validate plan-stage infer.py rows; ambiguity is an error, never a silent choice."""
    plans = {}
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError(f"plan output row {number}: not an object with a string id")
        if row["id"] in plans:
            raise ValueError(f"plan output row {number}: duplicate plan id {row['id']}")
        if row["id"] not in expected:
            raise ValueError(f"plan output row {number}: unexpected plan id {row['id']}")
        if "raw_response" not in row or "error" not in row:
            raise ValueError(f"plan output row {number}: completion record lacks raw_response/error")
        error = row["error"]
        if error is not None and not (isinstance(error, dict) and error):
            raise ValueError(f"plan output row {number}: error must be null or a nonempty object")
        if error is None:
            if not isinstance(row["raw_response"], dict):
                raise ValueError(f"plan output row {number}: completed record has no provider response object")
            if not final_text(row["raw_response"]).strip():
                raise ValueError(f"plan output row {number}: completed record (error=null) has empty text")
        plans[row["id"]] = row
    return plans


def build_write_rows(manifest: dict, source: Path, plan_rows: list, out_dir: Path) -> tuple[list[dict], dict]:
    """Return write-stage rows and {item id: fallback reason} for plans that failed or are missing."""
    if manifest.get("prompt_revision") != PROMPT_REVISION or manifest.get("prompt_template_sha256") != template_sha256():
        raise ValueError("Manifest was built by a different prompt revision")
    if "write" not in manifest["stages"]:
        raise ValueError("Manifest has no plan/write stage")
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest["input_sha256"]:
        raise ValueError("Source input does not match manifest input_sha256")
    sources = {row["id"]: row for row in read_jsonl(source)}
    plans = validate_plan_rows(plan_rows, {item["id"] + PLAN_SUFFIX for item in manifest["items"]})
    rows, fallbacks = [], {}
    for item in manifest["items"]:
        row = sources[item["id"]]
        info = detect_essay(row["prompt"])
        if sha256_text(info["body"]) != item["body_sha256"]:
            raise ValueError(f"{item['id']}: item text changed since build")
        plan_row = plans.get(item["id"] + PLAN_SUFFIX)
        if plan_row is None:
            reason = "missing_plan"
        elif plan_row["error"] is not None:
            reason = "failed_plan:" + str(plan_row["error"].get("type", "unknown"))
        else:
            reason = None
        if reason is None:
            prompt = write_prompt(info, item["topic"], final_text(plan_row["raw_response"]))
        else:
            # No retry: a failed or missing plan falls back to the single-pass prompt in the same call slot.
            prompt = single_prompt(info, item["topic"])
            fallbacks[item["id"]] = reason
        rows.append({"id": item["id"], "prompt": prompt, "images": rebase_images(row.get("images"), source, out_dir)})
    return rows, fallbacks


def write_from_plan(args: argparse.Namespace) -> int:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    out_dir = args.manifest.parent
    require_private_dir(out_dir)
    rows, fallbacks = build_write_rows(manifest, args.source, read_jsonl_any(args.plan_output), out_dir)
    digest = write_jsonl(out_dir / manifest["stages"]["write"]["file"], rows)
    record = {"write_sha256": digest, "plan_output_sha256": hashlib.sha256(args.plan_output.read_bytes()).hexdigest(),
              "plan_fallback_to_single": list(fallbacks), "plan_fallback_reasons": fallbacks}
    with (out_dir / "write.record.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(rows)} write-stage record(s); {len(fallbacks)} plan fallback(s)")
    return 0


def read_jsonl_any(path: Path) -> list:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: malformed JSON ({exc.msg})") from exc
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="build stage inputs and a launch manifest")
    b.add_argument("--input", required=True, type=Path, help="model-input JSONL {id, prompt, images}")
    b.add_argument("--out-dir", required=True, type=Path,
                   help="new git-ignored run dir, e.g. agentsLog/Pewciu6/essay/private/<run_id>")
    b.add_argument("--mode", choices=["single", "plan", "both"], default="both")
    b.add_argument("--topic", type=int, default=1, help="fixed topic number used by every arm (default 1)")
    b.add_argument("--select-topic", action="store_true", help="ablation: let the model choose the topic (OFF by default)")
    b.add_argument("--limit", type=int, help="use only the first N detected essay items")
    b.add_argument("--passthrough", action="store_true", help="also copy non-essay items unchanged")
    b.add_argument("--base-config", type=Path, help="infer.py config to derive per-stage caps from")
    b.add_argument("--dry-run", action="store_true", help="print the manifest/envelope only; write nothing")
    w = sub.add_parser("write-from-plan", help="build write-stage input from plan-stage infer.py output")
    w.add_argument("--manifest", required=True, type=Path)
    w.add_argument("--source", required=True, type=Path, help="the original input JSONL given to build")
    w.add_argument("--plan-output", required=True, type=Path, help="infer.py output of plan.input.jsonl")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            return build(args)
        return write_from_plan(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
