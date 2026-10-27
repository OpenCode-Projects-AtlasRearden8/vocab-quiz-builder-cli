"""End-to-end CLI tests and offline LLM fallback tests (no network touched)."""

import csv
from pathlib import Path

from vocabQuizBuilder import cli

def test_cli_builds_html_and_schedule(tmp_path, word_list_file):
    out = tmp_path / "quiz.html"
    sched = tmp_path / "review.csv"
    code = cli.main(
        [
            str(word_list_file),
            "-o", str(out),
            "--title", "Unit 3 study quiz",
            "-n", "8",
            "--schedule", str(sched),
            "--types", "mc,fill,match",
        ]
    )
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert "Unit 3 study quiz" in html
    assert "Answer key" in html
    rows = list(csv.DictReader(sched.open(encoding="utf-8")))
    assert len(rows) >= 5
    assert tmp_path.joinpath("review.csv").exists()


def test_cli_mines_prose_text(tmp_path, story_file):
    out = tmp_path / "prose_quiz.html"
    code = cli.main([str(story_file), "-o", str(out), "--types", "fill"])
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert "Fill in the blank" in html


def test_cli_llm_fallback_is_offline(tmp_path, word_list_file):
    out = tmp_path / "q.html"
    code = cli.main(
        [
            str(word_list_file),
            "-o", str(out),
            "--types", "write",
            "--llm-writing",
            "--llm-endpoint", "http://127.0.0.1:9/v1",
            "--llm-model", "nope",
        ]
    )
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert "offline mode" in html.lower() or "Open-ended" in html


def test_cli_dump_words(word_list_file, capsys):
    code = cli.main([str(word_list_file), "--dump-words"])
    captured = capsys.readouterr()
    assert code == 0
    assert "banana" in captured.out


def test_cli_rejects_missing_file(tmp_path):
    code = cli.main([str(tmp_path / "nope.txt"), "-o", str(tmp_path / "q.html")])
    assert code == 1


def test_cli_probes_dead_endpoint():
    code = cli.main(
        ["--probe-llm", "--llm-endpoint", "http://127.0.0.1:9/v1"]
    )
    assert code == 2


def test_no_api_key_logic():
    """The LLM trainer never sends auth headers — key-free contract."""
    import inspect

    import vocabQuizBuilder.llm as llm

    endpoint, model = llm.endpoint_from_env()
    assert endpoint == llm.DEFAULT_ENDPOINT
    assert "localhost" in endpoint or "127.0.0.1" in endpoint
    src = inspect.getsource(llm.chat)
    assert "Authorization" not in src
    assert llm.DEFAULT_ENDPOINT.startswith("http://")  # local servers, never keys
