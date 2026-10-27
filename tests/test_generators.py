"""Generator tests: question shapes, difficulty, determinism."""

import re

from vocabQuizBuilder.generators import (
    GeneratorConfig,
    build_all,
    build_fill_blank,
    build_multiple_choice,
)


def test_multiple_choice_easy_uses_three_word_options(generated):
    mc = [q for q in generated if q.qtype == "multiple_choice"]
    assert mc
    for q in mc:
        assert len(q.choices) == 3
        assert q.answer in q.choices


def test_fill_blank_has_answer_and_hint(entries):
    config = GeneratorConfig(fill_questions=4, difficulty="easy", seed=3)
    qs = build_fill_blank(entries, config)
    assert qs
    for q in qs:
        assert q.answer.isalpha() or "-" in q.answer
        assert q.hint.startswith("Hint: starts with")


def test_hard_mode_is_hint_free(entries):
    config = GeneratorConfig(fill_questions=5, mc_questions=3, difficulty="hard", seed=3)
    qs = build_fill_blank(entries, config)
    assert all(q.hint == "" for q in qs)
    mc = build_multiple_choice(entries, config)
    assert all(len(q.choices) == 5 for q in mc if q.choices)


def test_matching_answer_letters_valid(entries):
    config = GeneratorConfig(match_sets=2, match_pairs=4, seed=11)
    qs = build_all(entries, config)
    matches = [q for q in qs if q.qtype == "match"]
    assert len(matches) == 2
    for q in matches:
        assert q.answer.count("→") == len(q.choices) // 2
        for pair in q.answer.split(" ; "):
            num, letter = pair.split("→")
            assert re.fullmatch(r"\d", num.strip())
            assert letter.strip() in "ABCDEFGH"


def test_easy_ordering_groups_sections(generated):
    types_seen = []
    for q in generated:
        if not types_seen or types_seen[-1] != q.qtype:
            types_seen.append(q.qtype)
    assert types_seen == [t for t in ["multiple_choice", "fill_blank", "match", "writing"] if t in types_seen]


def test_hard_ordering_puts_writing_first(word_list_file):
    entries = __import__(
        "vocabQuizBuilder.loader", fromlist=["load_word_list"]
    ).load_word_list(word_list_file)
    config = GeneratorConfig(mc_questions=2, fill_questions=2, writing_prompts=1, difficulty="hard")
    types = [q.qtype for q in build_all(entries, config)]
    assert types[0] == "writing"


def test_same_seed_same_questions(word_list_file):
    loader = __import__("vocabQuizBuilder.loader", fromlist=["load_word_list"])
    entries = loader.load_word_list(word_list_file)
    cfg_a = GeneratorConfig(mc_questions=3, fill_questions=3, seed=42)
    cfg_b = GeneratorConfig(mc_questions=3, fill_questions=3, seed=42)
    a = [(q.qtype, q.prompt) for q in build_all(entries, cfg_a)]
    b = [(q.qtype, q.prompt) for q in build_all(entries, cfg_b)]
    assert a == b
