"""Shared pytest fixtures: sample word lists and generated questions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vocabQuizBuilder.generators import GeneratorConfig, build_all  # noqa: E402
from vocabQuizBuilder.loader import load_from_text, load_word_list  # noqa: E402
from vocabQuizBuilder.models import Question  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def word_list_file() -> Path:
    return FIXTURES / "word_list.txt"


@pytest.fixture(scope="session")
def story_file() -> Path:
    return FIXTURES / "story.txt"


@pytest.fixture(scope="session")
def entries(word_list_file: Path):
    return load_word_list(word_list_file)


@pytest.fixture(scope="session")
def story_entries(story_file: Path):
    return load_from_text(story_file, limit=10)


@pytest.fixture()
def config() -> GeneratorConfig:
    return GeneratorConfig(
        mc_questions=4,
        fill_questions=4,
        match_sets=1,
        match_pairs=5,
        writing_prompts=2,
        difficulty="easy",
        seed=7,
    )


@pytest.fixture()
def generated(entries, config) -> list[Question]:
    return build_all(entries, config)
