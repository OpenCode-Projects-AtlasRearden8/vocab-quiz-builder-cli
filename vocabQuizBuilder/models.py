"""Core data types used across the quiz builder."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Entry:
    """A vocabulary word, its meaning, and (optionally) a source sentence."""

    word: str
    definition: str = ""
    sentence: str = ""
    source: str = "word-list"

    def clean_sentence(self) -> str:
        return self.sentence.strip()


@dataclass
class Question:
    """One generated quiz question of any type."""

    qtype: str  # "multiple_choice" | "fill_blank" | "match" | "writing"
    prompt: str
    answer: str
    choices: list[str] = field(default_factory=list)
    hint: str = ""
    entry: Optional[Entry] = None
    difficulty: str = "medium"

    def safe_prompt(self) -> str:
        return html.escape(self.prompt, quote=False)
