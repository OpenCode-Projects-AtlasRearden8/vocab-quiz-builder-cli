"""Printable HTML quiz export with an answer key page."""

from __future__ import annotations

import html
import math
from typing import Sequence

from . import __version__
from .models import Entry, Question

LABELS = "ABCDEF"

CSS = """\
:root { --ink:#1c2733; --accent:#0b6bcb; --soft:#f4f6f9; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; color: var(--ink);
       max-width: 46rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.55; }
header h1 { font-size: 1.6rem; margin-bottom: 0.2rem; }
header .meta { color: #5b6b7c; font-size: 0.85rem; margin-bottom: 1.2rem; }
section { margin: 1.5rem 0; padding: 1rem 1.2rem; background: var(--soft);
          border-radius: 8px; page-break-inside: avoid; }
section h2 { font-size: 1.1rem; margin: 0 0 0.2rem; color: var(--accent); }
ol, ul { padding-left: 1.4rem; margin: 0.3rem 0; }
li { margin-bottom: 0.7rem; }
.choices { list-style: none; padding-left: 0; }
.choices li { margin: 0.25rem 0; }
.hint { color: #7a5b00; font-size: 0.85rem; }
.menote { font-style: italic; font-size: 0.8rem; color: #5b6b7c; }
table { border-collapse: collapse; width: 100%; margin-top: 0.4rem; }
table td, table th { border: 1px solid #c9d3dd; padding: 0.4rem 0.6rem; vertical-align: top; }
.answer-lines { border-bottom: 1px solid #9aa8b5; height: 1.4em; margin-top: 0.5rem; }
.key { page-break-before: always; }
.key h1 { color: var(--accent); }
.key details { background: #fff; border: 1px solid #d7dee6; border-radius: 6px; padding: 0.7rem 1rem; }
.key summary { cursor: pointer; font-weight: bold; }
.footer { font-size: 0.8rem; color: #5b6b7c; margin-top: 2rem; }
@media print { .no-print { display: none; } body { margin: 0 auto; } }
"""


def render_quiz(
    title: str,
    questions: Sequence[Question],
    entries: Sequence[Entry],
    schedule_text: str = "",
) -> str:
    """Build a full printable quiz + answer key HTML document."""
    body = _render_body(questions)
    key = _render_key(questions)
    if entries and all(e.definition.strip() for e in entries):
        words_units = "<br>".join(
            f"<strong>{html.escape(e.word)}</strong> — {html.escape(e.definition)}"
            for e in entries[:60]
        )
    else:
        words_units = html.escape(", ".join(e.word for e in entries[:60]))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>{html.escape(title)}</h1>
<p class="meta">Generated locally with vocab-quiz-builder v{__version__} — runs fully offline, print-ready.
</header>
{body}
<section>
<h2>Study words</h2>
<p>{words_units}</p>
{schedule_text}
</section>
<p class="footer">Generated from your own file on your own machine.</p>
<div class="key">
<h1>Answer key</h1>
<details open>
<summary>Answers — fold this up before printing student copies</summary>
{key}
</details>
</div>
</body>
</html>
"""


def _render_body(questions: Sequence[Question]) -> str:
    parts: list[str] = []
    current = ""
    counter = 0
    for q in questions:
        if q.qtype != current:
            if current:
                parts.append("</ol></section>")
            current = q.qtype
            counter = 0
            parts.append(
                f"<section><h2>{section_name(current)}</h2>"
                f'<p class="menote">{html.escape(section_note(current))}</p><ol>'
            )
        counter += 1
        parts.append(question_item(q, counter))
    if current:
        parts.append("</ol></section>")
    return "".join(parts)


def _render_key(questions: Sequence[Question]) -> str:
    parts: list[str] = []
    current = ""
    counter = 0
    for q in questions:
        if q.qtype != current:
            if current:
                parts.append("</ol></section>")
            current = q.qtype
            counter = 0
            parts.append(f"<section><h2>Key · {section_name(current)}</h2><ol>")
        counter += 1
        parts.append(
            f'<li><strong>{html.escape(q.answer)}</strong></li>'
        )
    if current:
        parts.append("</ol></section>")
    return "".join(parts)


def section_name(qtype: str) -> str:
    return {
        "multiple_choice": "Part 1 · Multiple choice",
        "fill_blank": "Part 2 · Fill in the blank",
        "match": "Part 3 · Matching",
        "writing": "Part 4 · Write a sentence (optional)",
        "writing_llm": "Part 4 · Write a sentence (model-suggested)",
    }.get(qtype, qtype.replace("_", " ").title())


def section_note(qtype: str) -> str:
    return {
        "multiple_choice": "Circle the best answer. No penalty for guessing!",
        "fill_blank": "Write your word on the line. Hints show the first letter.",
        "match": "Write the matching letter beside each number.",
        "writing": "Optional writing practice. Sentences you invent yourself stick best.",
        "writing_llm": "Optional writing practice using model-suggested sentences.",
    }.get(qtype, "")


def question_item(q: Question, number: int) -> str:
    esc = html.escape
    out = [f"<li><p>{esc(q.safe_prompt())}</p>"]
    if q.qtype == "multiple_choice":
        out.append('<ul class="choices">')
        for i, c in enumerate(q.choices):
            label = LABELS[i] if i < len(LABELS) else LABELS[-1]
            out.append(f"<li>◻ {label}. {esc(str(c))}</li>")
        out.append("</ul>")
    elif q.qtype == "fill_blank":
        out.append('<div class="answer-lines">&nbsp;</div>')
        if q.hint:
            out.append(f'<p class="hint">{esc(q.hint)}</p>')
    elif q.qtype == "match":
        half = math.ceil(len(q.choices) / 2)
        left, right = q.choices[:half], q.choices[half:]
        out.append("<table><tr><th>Word</th><th>Meaning</th></tr>")
        for i in range(half):
            lcell = esc(left[i]) if i < len(left) else ""
            rcell = esc(right[i]) if i < len(right) else ""
            out.append(f"<tr><td>{lcell}</td><td>{rcell}</td></tr>")
        out.append("</table>")
    elif q.qtype in ("writing", "writing_llm"):
        out.append('<div class="answer-lines">&nbsp;</div>')
        out.append('<div class="answer-lines">&nbsp;</div>')
        if q.hint:
            out.append(f'<p class="menote">{esc(q.hint)}</p>')
    out.append("</li>")
    return "".join(out)
