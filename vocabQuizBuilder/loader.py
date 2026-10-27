"""Load vocabulary entries from word lists, CSV-ish files, or plain text."""

from __future__ import annotations

import random
import re
import string
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from .models import Entry

STOPWORDS = frozenset(
    """a about above after again all also am an and any are aren't as at be
    because been before being below between both but by can can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm i've
    if in into is isn't it it's its itself let's me more most mustn't my
    myself no nor not of off on once only or other ought our ours ourselves
    out over own same shan't she she'd she'll she's should shouldn't so some
    such than that that's the their theirs them themselves then there there's
    these they they'd they'll they're they've this those through to too under
    until up very was wasn't we we'd we'll we're we've were weren't what
    what's when when's where where's which while who who's whom why why's
    with won't would wouldn't you you'd you'll you're you've your yours
    yourself yourselves will just
    along among around because beside beyond both during ever every
    finally first however instead kept liked mine mostly moving moved
    near nearly next opened outside ourselves perhaps rather soon still
    therefore toward towards under upon whose
""".split()
)

MIN_WORD_LEN = 3
MAX_WORD_LEN = 18


def _split_definition(line: str) -> tuple[str, str]:
    """Split a line like 'word, definition' or 'word | definition' or 'word<TAB>def'."""
    for sep in ("\t", " | ", "\\|", ","):
        if sep in line:
            parts = [p.strip() for p in line.split(sep, 1)]
            if parts[0] and parts[1]:
                return parts[0], parts[1]
    return line.strip(), ""


def _looks_like_word(token: str) -> bool:
    if not (MIN_WORD_LEN <= len(token) <= MAX_WORD_LEN):
        return False
    if token.lower() in STOPWORDS:
        return False
    return all(ch.isalpha() or ch in "'-" for ch in token)


def load_word_list(path: str | Path) -> list[Entry]:
    """Load 'word,definition' (or word-only) lines from a text file."""
    entries: list[Entry] = []
    seen: set[str] = set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        word, definition = _split_definition(line)
        key = word.lower()
        if not key or key in seen or not _looks_like_word(word):
            continue
        seen.add(key)
        entries.append(Entry(word=word, definition=definition, source=str(path)))
    return entries


def load_from_text(path: str | Path, limit: int = 30) -> list[Entry]:
    """Extract common, non-stopword words and one source sentence each."""
    text = Path(path).read_text(encoding="utf-8")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    counts = Counter()
    for word in _tokens(text):
        counts[word.lower()] += 1
    ranked = [w for w, _ in counts.most_common() if _looks_like_word(w)][:limit]

    entries: list[Entry] = []
    for target in ranked:
        sentence = next((s for s in sentences if _word_in_sentence(target, s)), "")
        entries.append(Entry(word=target, definition="", sentence=sentence, source=str(path)))
    return entries


def _tokens(text: str) -> Iterable[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def _word_in_sentence(word: str, sentence: str) -> bool:
    pattern = rf"\b{re.escape(word)}\b"
    return re.search(pattern, sentence, flags=re.IGNORECASE) is not None


def merge_sources(paths: Sequence[str | Path], limit_per_text: int = 30) -> list[Entry]:
    """Load any mix of word lists and text files, de-duplicated, ordered by name."""
    merged: dict[str, Entry] = {}
    for p in paths:
        path = Path(p)
        if path.suffix.lower() == ".csv":
            entries = load_word_list(path)
        else:
            entries = try_word_list(path, fallback_text_limit=limit_per_text)
        for entry in entries:
            merged.setdefault(entry.word.lower(), entry)
    return sorted(merged.values(), key=lambda e: e.word.lower())


def try_word_list(path: Path, fallback_text_limit: int = 30) -> list[Entry]:
    text = path.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    candidate = load_word_list(path)
    # Treat as a word list only when lines are short (no prose paragraphs).
    avg_len = sum(len(ln) for ln in lines[:50]) / max(len(lines[:50]), 1)
    if avg_len <= 80 and len(candidate) >= max(2, len(lines) // 2):
        return candidate
    return load_from_text(path, limit=fallback_text_limit)


def shuffle_deterministic(items: list, seed: int | None = 21616) -> list:
    """Deterministic shuffling so tests and regeneration stay stable."""
    if seed is None:
        random.shuffle(items)
        return items
    rng = random.Random(seed)
    rng.shuffle(items)
    return items


def filter_alpha(entries: list[Entry]) -> list[Entry]:
    out = []
    for e in entries:
        w = e.word.strip(string.punctuation)
        if _looks_like_word(w):
            e.word = w
            out.append(e)
    return out
