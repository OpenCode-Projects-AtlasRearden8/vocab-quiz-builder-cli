"""HTML export and spaced-review schedule tests."""

import csv
import datetime as dt
from pathlib import Path

from vocabQuizBuilder.export_html import render_quiz
from vocabQuizBuilder.generators import GeneratorConfig, build_all
from vocabQuizBuilder.schedule import DEFAULT_INTERVALS, write_schedule


def _quiz(entries, tmp_path, config=None):
    config = config or GeneratorConfig(mc_questions=3, fill_questions=3, match_sets=1, writing_prompts=1, seed=5)
    questions = build_all(entries, config)
    html = render_quiz("Test quiz", questions, entries)
    return questions, html


def test_html_contains_answers_and_key(entries):
    _q, html = _quiz(entries, None)
    assert "Answer key" in html
    assert "<!DOCTYPE html>" in html
    assert "Part 3 · Matching" in html


def test_html_escapes_user_text(tmp_path):
    entry_file = tmp_path / "evil.txt"
    entry_file.write_text(
        "banana, fruit with tags like <b> and <script>alert(1)</script>\n"
        "meander, to wander slowly\n",
        encoding="utf-8",
    )
    from vocabQuizBuilder.loader import load_word_list

    entries = load_word_list(entry_file)
    _q, html = _quiz(entries, tmp_path)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_schedule_intervals_are_expanding(tmp_path, entries):
    path = write_schedule(tmp_path / "review.csv", entries)
    assert isinstance(path, Path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows, "schedule should have one row per word"
    start = dt.date.fromisoformat(rows[0]["review_1"])
    deltas = [
        (dt.date.fromisoformat(rows[0][f"review_{i}"]) - start).days
        for i in range(1, 6)
    ]
    assert deltas == list(DEFAULT_INTERVALS)


def test_schedule_word_column(tmp_path, entries):
    write_schedule(tmp_path / "review.csv", entries)
    rows = list(csv.DictReader((tmp_path / "review.csv").open(encoding="utf-8")))
    words = [r["word"] for r in rows]
    assert "banana" in words
    assert words == sorted(words, key=str.lower)


def test_quiz_mentions_answer_letters(entries):
    questions, html = _quiz(entries, None)
    mc = [q for q in questions if q.qtype == "multiple_choice"]
    assert mc
    first_answer = mc[0].answer
    assert first_answer in html
