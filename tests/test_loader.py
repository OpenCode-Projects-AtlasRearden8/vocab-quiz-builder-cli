"""Loader tests: word lists, prose mining, merging."""

from vocabQuizBuilder.loader import (
    load_from_text,
    load_word_list,
    merge_sources,
    try_word_list,
)


def test_word_list_parses_definitions(word_list_file):
    entries = load_word_list(word_list_file)
    words = {e.word.lower() for e in entries}
    assert "banana" in words
    assert "glacier" in words
    banana = next(e for e in entries if e.word.lower() == "banana")
    assert "fruit" in banana.definition


def test_word_list_skips_comments_and_blank_lines(word_list_file):
    entries = load_word_list(word_list_file)
    assert all(e.word and not e.word.startswith("#") for e in entries)


def test_word_list_dedupes_and_no_stopwords():
    (tmp := __import__("pathlib").Path("/tmp/opencode")).mkdir(exist_ok=True)
    f = tmp / "dup.txt"
    f.write_text("big, large size\nBIG, large size\nbIg, large size\nthe, article\nbanana, fruit\n", encoding="utf-8")
    entries = load_word_list(f)
    words = [e.word.lower() for e in entries]
    assert words == ["big", "banana"]


def test_text_mining_finds_content_words(story_file):
    entries = load_from_text(story_file, limit=10)
    words = {e.word.lower() for e in entries}
    assert "marigold" in words
    assert "the" not in words


def test_text_mining_attaches_sentence(story_file):
    entries = load_from_text(story_file, limit=10)
    target = next(e for e in entries if e.word == "marigold")
    assert "marigold" in target.sentence.lower()


def test_merge_sources_mixes_types(word_list_file, story_file):
    merged = merge_sources([word_list_file, story_file])
    lower = [e.word.lower() for e in merged]
    assert "banana" in lower
    assert "meander" in lower
    assert lower == sorted(lower, key=str.lower)


def test_try_word_list_classifies_prose_story(story_file):
    entries = try_word_list(story_file)
    assert any(e.sentence for e in entries)
