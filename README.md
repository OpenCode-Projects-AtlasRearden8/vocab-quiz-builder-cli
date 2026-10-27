# vocab-quiz-builder

Turn any word list or text file into a printable study quiz — **right on your
own computer, fully offline**. It reads your file, mines the vocabulary, and
writes out a clean HTML quiz with multiple-choice, fill-in-the-blank, and
matching sections, plus a full answer key and a lightweight spaced-review
schedule file so the words come back to visit at friendly intervals.

Built the Asdale Dynamics way: plain English, step by step, no accounts, no
cloud, no data leaving your machine.

## Why you might like it

- **Local-first, always.** Every quiz is generated with plain Python on your
  machine. Nothing is uploaded, and there is no API key to lose.
- **Works on any word list.** A simple `word, meaning` text file, or any
  essay/story/article — it mines the interesting words for you.
- **Printable with a real answer key.** Open the HTML, hit Ctrl+P, fold the
  key, and quiz yourself (or a classroom).
- **Spaced review for free.** A companion CSV schedules each word for review
  on day 0, +3, +7, +16, and +35.
- **Optional AI sentences.** If you run a local model (Ollama by default), it
  can suggest example sentences. Never connected to the internet; never sends
  an API key — it targets key-free local OpenAI-compatible endpoints only.

## Quick start

```bash
# from this folder (Python 3.10+)
python3 -m vocabQuizBuilder.cli examples/dog_words.txt -o quiz.html --schedule review.csv
```

Or install it and use the short command:

```bash
pip install -e .
vocab-quiz examples/dog_words.txt -o quiz.html --schedule review.csv
```

Then open `quiz.html` in a browser and print. That's it.

### Input formats

**Word list** (`word,meaning`, one per line — also accepts ` | `, tabs, or a
bare word on its own; lines starting with `#` are comments):

```
loyal, always standing by your friends and family
meander, to wander slowly without a firm direction
```

**Any text file** — a story, article, or essay. The builder mines common,
non-stopword words and finds a sentence for each so the fill-in-the-blank
section can blank them out in context.

## Useful flags

| Flag | What it does |
| --- | --- |
| `-n 14` | about 14 questions total, split across the chosen types |
| `--questions-per-type 4` | exact count per question type |
| `--types mc,fill,match,write` | pick which sections to include |
| `--difficulty easy\|hard` | easy = word-choice questions with hints; hard = reversed, no hints, 5 options |
| `--order easy\|hard` | section order (same idea, flip the warm-up to the end) |
| `--match-pairs 6` | word–definition pairs per matching set |
| `--seed 42` | same seed, same quiz — great for reprints |
| `--schedule review.csv` | write the spaced-review CSV |
| `--dump-words` | show the mined word list and exit |

## Optional: local AI example sentences

By default there is **no AI at all** — the tool is fully offline. If you want
a local model to suggest an example sentence for the writing section:

```bash
ollama serve                       # already running? skip this
vocab-quiz my_words.txt --llm-writing --llm-model llama3.2
```

- Default endpoint: `http://localhost:11434/v1` (Ollama — no key needed).
- Works with LM Studio, llama.cpp server, or anything OpenAI-compatible on
  `localhost`. Override with `--llm-endpoint` or the `VQB_ENDPOINT` /
  `VQB_MODEL` environment variables.
- If the endpoint is asleep, the tool quietly falls back to offline prompts.
- **No API keys, ever.** The client never sends an auth header; it only talks
  to key-free local servers. Your words never leave your machine.

Check connectivity without building a quiz:

```bash
vocab-quiz --probe-llm
```

## Spaced review file

With `--schedule review.csv`, you get a plain CSV your calendar-friendly brain
can love:

```
word,definition,review_1,review_2,review_3,review_4,review_5,done
bark,the loud sound a dog makes,2026-10-27,2026-10-30,2026-11-03,2026-11-12,2026-12-01, ☐
```

Review each word on the listed dates, tick the `done` box, move on. Open it
with any spreadsheet app. No notifications, no accounts — just dates.

## Run the tests

```bash
pip install -e ".[dev]"
pytest
```

26 tests cover loading (word lists and prose mining), question generation
(difficulty modes, determinism, matching grids), HTML export (escaping,
answer key), the review schedule, and the CLI end to end — including the
offline LLM fallback. Test fixtures live in `tests/fixtures/`.

## Project layout

```
vocabQuizBuilder/        the Python package
  loader.py              word-list + prose miners
  generators.py          quiz question builders (mc, fill, match, writing)
  export_html.py         printable HTML + answer key
  schedule.py            spaced-review CSV
  llm.py                 optional local OpenAI-compatible client (no keys)
  cli.py                 the vocab-quiz command
examples/                sample word list
tests/                   pytest suite + fixture files
```

## Status

This is a small, focused tool — see `STATUS.md` for what was verified and the
known gaps.

## About

Made by **Asdale Dynamics, LLC** — beginner-friendly AI education, books, and
practical local-first tools. Learn AI "like a friend would" at
[dylanasdale.github.io](https://dylanasdale.github.io), in *The Massive AI
Manual*, and in other Asdale Dynamics titles.

Different from a flashcard agent: this builds **printable quizzes** and a
review schedule from your own files — no agent runtime required.

Licensed under the MIT License (see `LICENSE`).
Copyright (c) 2026 Asdale Dynamics, LLC.
