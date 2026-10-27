"""Question generation: multiple choice, fill-in-the-blank, matching, writing."""

from __future__ import annotations

import html
import random
import re
from typing import Optional, Sequence

from .models import Entry, Question

TYPE_ORDER_EASY = ["multiple_choice", "fill_blank", "match", "writing"]
TYPE_ORDER_HARD = ["writing", "match", "fill_blank", "multiple_choice"]
LETTERS = "ABCDEFGH"


class GeneratorConfig:
    """Knobs that shape question difficulty and volume."""

    def __init__(
        self,
        mc_questions: int = 6,
        fill_questions: int = 5,
        match_sets: int = 1,
        match_pairs: int = 6,
        writing_prompts: int = 3,
        difficulty: str = "easy",
        seed: Optional[int] = 21616,
    ) -> None:
        self.mc_questions = mc_questions
        self.fill_questions = fill_questions
        self.match_sets = match_sets
        self.match_pairs = match_pairs
        self.writing_prompts = writing_prompts
        self.difficulty = difficulty
        self.seed = seed


def _rng(seed: Optional[int], salt: int = 0) -> random.Random:
    return random.Random(None if seed is None else seed + salt)


def _distractors(
    entries: Sequence[Entry], target: Entry, count: int, seed: Optional[int]
) -> list[Entry]:
    pool = [e for e in entries if e.word.lower() != target.word.lower()]
    rng = _rng(seed, abs(hash_for(target)))
    rng.shuffle(pool)
    picked, seen = [], set()
    for e in pool:
        if e.word.lower() in seen:
            continue
        seen.add(e.word.lower())
        picked.append(e)
        if len(picked) == count:
            break
    return picked


def hash_for(entry: Entry) -> int:
    return sum(ord(c) for c in entry.word)


def _stable_shuffle(items: Sequence[str], seed: Optional[int], salt: int = 0) -> list[str]:
    rng = _rng(seed, salt)
    out = list(items)
    rng.shuffle(out)
    return out


def build_multiple_choice(entries: Sequence[Entry], config: GeneratorConfig) -> list[Question]:
    """easy: definition -> word (3 options). hard: word -> definition (5 options)."""
    questions: list[Question] = []
    used: set[str] = set()
    hard = config.difficulty == "hard"
    n_options = 5 if hard else 3
    for entry in entries:
        if len(questions) >= max(config.mc_questions, 0):
            break
        if entry.word.lower() in used:
            continue
        n_needed = n_options - 1
        if hard:
            good = [e for e in entries if e.definition.strip() and e is not entry]
            if len(good) < n_needed:
                continue
            distractors = _distractors(good, entry, n_needed, config.seed)
            choices = [e.definition for e in distractors]
            answer = entry.definition or "(no definition provided)"
            prompt = f"What is the closest meaning of “{entry.word}”?"
        else:
            distractors = _distractors(entries, entry, n_needed, config.seed)
            if len(distractors) < n_needed:
                continue
            choices = [e.word for e in distractors]
            answer = entry.word
            prompt = f"Which word best matches this meaning: “{entry.definition}”?"
        choices.append(answer)
        used.add(entry.word.lower())
        questions.append(
            Question(
                qtype="multiple_choice",
                prompt=prompt,
                answer=answer,
                choices=_stable_shuffle(choices, config.seed, hash_for(entry)),
                entry=entry,
                difficulty="easy" if not hard else "hard",
            )
        )
    return questions


def build_fill_blank(entries: Sequence[Entry], config: GeneratorConfig) -> list[Question]:
    """Blank the word in a source sentence, or fall back to a definition clue."""
    questions: list[Question] = []
    seen: set[str] = set()
    for entry in entries:
        if len(questions) >= max(config.fill_questions, 0):
            break
        if entry.word.lower() in seen:
            continue
        sentence = entry.clean_sentence()
        blanked = _blank_word(sentence, entry.word) if sentence else ""
        if blanked:
            hint = (
                ""
                if config.difficulty == "hard"
                else f"Hint: starts with “{entry.word[:1]}” ({len(entry.word)} letters)"
            )
            prompt = html.unescape(html.escape(blanked, quote=False))
            seen.add(entry.word.lower())
            questions.append(
                Question(
                    qtype="fill_blank",
                    prompt=prompt,
                    answer=entry.word,
                    hint=hint,
                    entry=entry,
                    difficulty="medium",
                )
            )
            continue
        if entry.definition.strip():
            prompt = f"What word means: {entry.definition}"
            hint = (
                ""
                if config.difficulty == "hard"
                else f"Hint: starts with “{entry.word[:1]}” ({len(entry.word)} letters)"
            )
            seen.add(entry.word.lower())
            questions.append(
                Question(
                    qtype="fill_blank",
                    prompt=prompt,
                    answer=entry.word,
                    hint=hint,
                    entry=entry,
                    difficulty="medium",
                )
            )
    return questions


def _blank_word(sentence: str, word: str) -> str:
    pattern = rf"\b{re.escape(word)}\b"
    if not re.search(pattern, sentence, flags=re.IGNORECASE):
        return ""
    return re.sub(pattern, "________", sentence, count=1, flags=re.IGNORECASE)


def build_match_sets(entries: Sequence[Entry], config: GeneratorConfig) -> list[Question]:
    """Word -> definition matching grids with a scrambled right-hand side."""
    has_defs = [e for e in entries if e.definition.strip()]
    questions: list[Question] = []
    pairs_needed = max(3, config.match_pairs)
    for set_no in range(max(config.match_sets, 0)):
        start = set_no * pairs_needed
        chunk = has_defs[start : start + pairs_needed]
        if len(chunk) < 3:
            break
        left = [(i + 1, e.word) for i, e in enumerate(chunk)]
        right = _stable_shuffle(
            [e.definition for e in chunk], config.seed, salt=100 + set_no
        )
        answer_letter = {}
        for _num, _word in left:
            definition = chunk[_num - 1].definition
            answer_letter[_num] = LETTERS[right.index(definition)]
        questions.append(
            Question(
                qtype="match",
                prompt=f"Match each word (left) to its meaning (right) — Set {set_no + 1}.",
                answer=" ; ".join(f"{num} → {letter}" for num, letter in answer_letter.items()),
                choices=[f"{num}. {word}" for num, word in left]
                + [f"{LETTERS[i]}. {d}" for i, d in enumerate(right)],
                entry=chunk[0],
                hint=f"Words {chunk[0].word}…{chunk[-1].word}",
                difficulty="hard",
            )
        )
    return questions


def build_writing(entries: Sequence[Entry], config: GeneratorConfig) -> list[Question]:
    questions: list[Question] = []
    skip: set[str] = set()
    for entry in entries:
        if len(questions) >= max(config.writing_prompts, 0):
            break
        if entry.word.lower() in skip:
            continue
        skip.add(entry.word.lower())
        questions.append(
            Question(
                qtype="writing",
                prompt=f"Write one original sentence using “{entry.word}”.",
                answer="(Open-ended; check yourself against the example sentence.)",
                entry=entry,
                difficulty="hard",
            )
        )
    return questions


def build_all(
    entries: Sequence[Entry], config: GeneratorConfig, include_writing: bool = True
) -> list[Question]:
    ordered_type = TYPE_ORDER_EASY if config.difficulty != "hard" else TYPE_ORDER_HARD
    qs = build_multiple_choice(entries, config) + build_fill_blank(entries, config)
    vqs = build_match_sets(entries, config) + build_writing(entries, config)
    qs += vqs
    if not include_writing:
        qs = [q for q in qs if q.qtype != "writing"]
    qs.sort(key=lambda q: ordered_type.index(q.qtype))
    return qs
