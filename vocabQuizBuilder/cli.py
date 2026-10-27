"""Command-line interface for vocab-quiz-builder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .export_html import render_quiz
from .generators import GeneratorConfig, build_all, build_writing
from .llm import build_writing_questions, chat, endpoint_from_env, probe
from .loader import load_from_text, load_word_list, merge_sources
from .models import Entry, Question
from .schedule import schedule_blurb, write_schedule

TYPES_HELP = "comma list: mc,fill,match,write (default all)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vocab-quiz",
        description=(
            "Turn any word list or text file into printable study quizzes — "
            "fill-in-the-blank, matching, and multiple choice, fully offline."
        ),
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="word list (word,definition lines) or plain text file(s)",
    )
    parser.add_argument(
        "-o", "--output", default="quiz.html", help="HTML quiz output path"
    )
    parser.add_argument(
        "--title", default=None, help="quiz title (defaults to the input filename)"
    )
    parser.add_argument(
        "-n", "--questions", type=int, default=14, help="approx. total questions"
    )
    parser.add_argument(
        "--questions-per-type",
        type=int,
        default=4,
        help="questions per selected type (granular override of -n)",
    )
    parser.add_argument(
        "--types",
        default="mc,fill,match,write",
        help=TYPES_HELP,
    )
    parser.add_argument(
        "--order",
        choices=["easy", "hard"],
        default="easy",
        help="difficulty direction (easy quiz starts with warm-ups and hints)",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "hard"],
        default="easy",
        help="question style: easy = word-choices with hints, hard = reversed, no hints",
    )
    parser.add_argument(
        "--match-pairs", type=int, default=6, help="word–definition pairs per matching set"
    )
    parser.add_argument(
        "--seed", type=int, default=21616, help="deterministic shuffle seed"
    )
    parser.add_argument(
        "--schedule",
        default=None,
        help="write a spaced-review CSV here (e.g., --schedule review.csv)",
    )
    parser.add_argument(
        "--llm-writing", action="store_true",
        help="use a local OpenAI-compatible endpoint for sentence examples",
    )
    parser.add_argument(
        "--llm-endpoint",
        default=None,
        help="OpenAI-compatible base URL (default: Ollama http://localhost:11434/v1; "
        "no API key is ever sent)",
    )
    parser.add_argument(
        "--llm-model", default=None, help="chat model name (default: llama3.2)"
    )
    parser.add_argument(
        "--probe-llm", action="store_true",
        help="check the local LLM endpoint and exit",
    )
    parser.add_argument(
        "--dump-words", action="store_true",
        help="print the mined word list and exit",
    )
    parser.add_argument("--version", action="version", version=f"vocab-quiz {__version__}")
    return parser


def parse_types(flag: str) -> set[str]:
    aliases = {
        "mc": "mc",
        "multiple": "mc",
        "multiple_choice": "mc",
        "multiple-choice": "mc",
        "fill": "fill",
        "fill_blank": "fill",
        "fill-in-the-blank": "fill",
        "match": "match",
        "matching": "match",
        "write": "write",
        "writing": "write",
        "sentences": "write",
        "sentence": "write",
    }
    selected = set()
    for part in flag.split(","):
        part = part.strip().lower()
        if not part:
            continue
        if part not in aliases:
            raise SystemExit(f"Unknown question type {part!r}. Try: mc,fill,match,write")
        selected.add(aliases[part])
    return selected or {"mc", "fill", "match", "write"}


def split_question_budget(total: int, types: set[str]) -> dict[str, int]:
    per_type = max(1, round(total / max(len(types), 1)))
    budget = {t: per_type for t in sorted(types)}
    return budget


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    endpoint, default_model = endpoint_from_env()
    model = args.llm_model or default_model
    if args.llm_endpoint:
        endpoint = args.llm_endpoint.rstrip("/")

    if args.probe_llm:
        ok = probe(endpoint, model)
        print(f"endpoint={endpoint} model={model} reachable={'yes' if ok else 'no'}")
        return 0 if ok else 2

    if not args.input:
        parser.error("give me at least one input file")

    for src in args.input:
        if not Path(src).exists():
            print(f"error: no such file: {src}", file=sys.stderr)
            return 1

    entries = merge_sources(args.input, limit_per_text=30)
    entries = dedupe(entries)
    if args.dump_words:
        for e in entries:
            print(f"{e.word}\t{e.definition}".rstrip("\t"))
        return 0
    if len(entries) < 3:
        print(
            "error: I found fewer than 3 usable words. "
            "A word list looks like: 'banana, a long yellow fruit' (one per line).",
            file=sys.stderr,
        )
        return 1

    types = parse_types(args.types)
    if args.questions_per_type:
        budget = {t: args.questions_per_type for t in types}
    else:
        budget = split_question_budget(args.questions, types)

    config = GeneratorConfig(
        mc_questions=budget.get("mc", 0),
        fill_questions=budget.get("fill", 0),
        match_sets=1 if "match" in types else 0,
        match_pairs=args.match_pairs,
        writing_prompts=budget.get("write", 0),
        difficulty=args.difficulty,
        seed=args.seed,
    )
    include_writing = "write" not in types
    questions = build_all(entries, config, include_writing)

    if "write" in types:
        writing = budget.get("write", 0)
        if args.llm_writing:
            writing_questions, llm_ok = build_writing_questions(
                entries, endpoint, model, limit=writing
            )
        else:
            writing_questions = build_writing(entries, config)
            llm_ok = True
        questions.extend(writing_questions)
    else:
        llm_ok = True

    title = args.title or f"Vocabulary quiz: {Path(args.input[0]).stem}"
    schedule_path = None
    schedule_html = ""
    if args.schedule:
        schedule_path = write_schedule(args.schedule, entries)
        schedule_html = schedule_blurb(schedule_path)

    html_out = render_quiz(title, questions, entries, schedule_html)
    output = Path(args.output)
    output.write_text(html_out, encoding="utf-8")

    sections = summarize(questions)
    line = ", ".join(f"{k}: {v}" for k, v in sections.items() if v)
    print(f"Wrote {output} ({line})")
    if schedule_path:
        print(f"Wrote review schedule {schedule_path}")
    if args.llm_writing and not llm_ok:
        print("note: LLM endpoint unreachable; fell back to offline prompts.")
    return 0


def questions_qtype_present(questions: list[Question], qtype: str) -> bool:
    return any(q.qtype == qtype for q in questions)


def summarize(questions: list[Question]) -> dict[str, int]:
    counts = {"multiple_choice": 0, "fill_blank": 0, "match": 0, "writing": 0, "writing_llm": 0}
    for q in questions:
        counts[q.qtype] = counts.get(q.qtype, 0) + 1
    return counts


def dedupe(entries: list[Entry]) -> list[Entry]:
    seen: set[str] = set()
    out = []
    for e in entries:
        key = e.word.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(e)
    return out


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
