# STATUS.md — vocab-quiz-builder

Built: 2026-10-27 · v0.1.0 · MIT License · by Asdale Dynamics, LLC

## What was built

A dependency-free Python CLI (`vocab-quiz`) that turns word lists or plain
text files into printable HTML study quizzes, fully offline.

- **Input loaders** (`vocabQuizBuilder/loader.py`): `word,meaning` lists (also
  `word | meaning`, tabs, or bare words; `#` comments) and prose text mining
  (common non-stopword words + a source sentence for each). Detects word list
  vs. prose automatically and merges multiple files, de-duplicated.
- **Question generators** (`generators.py`): multiple choice (easy:
  definition→word, 3 options with hints; hard: word→definition, 5 options,
  no hints), fill-in-the-blank (sentence blanks in context, definition clues
  as fallback), matching grids (scrambled meanings, lettered answers), and an
  optional writing section. Difficulty ordering, deterministic seeds.
- **HTML export** (`export_html.py`): print-ready quiz with all four sections,
  a study-words list, and a collapsible answer key on its own page
  (`page-break-before`). All user text is HTML-escaped.
- **Spaced-review schedule** (`schedule.py`): clean CSV per word with
  review dates on day 0, +3, +7, +16, +35 and a `done` checkbox column.
- **Optional local LLM sentences** (`llm.py`): OpenAI-compatible chat client
  using only the standard library. Default endpoint Ollama
  `http://localhost:11434/v1`, model `llama3.2`; configurable via
  `--llm-endpoint`/`--llm-model` or `VQB_ENDPOINT`/`VQB_MODEL`. **Never sends
  an API key or auth header.** Quietly falls back to offline prompts when the
  endpoint is unreachable.
- **CLI** (`cli.py`): flags for question count/types, difficulty, ordering,
  match pairs, seed, schedule output, `--probe-llm`, `--dump-words`.
- **Docs**: README (credited to Asdale Dynamics, LLC), MIT LICENSE with the
  copyright line `Copyright (c) 2026 Asdale Dynamics, LLC`.
- **Tests**: 26 passing pytest tests with fixture word lists
  (`tests/fixtures/word_list.txt`, `story.txt`).

## How to run it

```bash
pip install -e .          # installs the `vocab-quiz` command
vocab-quiz examples/dog_words.txt -o quiz.html --schedule review.csv
# or without installing:
python3 -m vocabQuizBuilder.cli examples/dog_words.txt -o quiz.html

pytest                    # run the test suite
python3 -m vocabQuizBuilder.cli --help
```

Open `quiz.html` in a browser and print; open `review.csv` in a spreadsheet.
Optional local-AI sentences: `vocab-quiz my_words.txt --llm-writing` (needs
Ollama or another key-free OpenAI-compatible server on localhost).

## Verification results

- `python3 -m pytest -q` → **26 passed, 0 failed** (Python 3.13.5).
- `pip install -e .` succeeded; `vocab-quiz --version` → `vocab-quiz 0.1.0`.
- Demo runs verified end to end:
  - word list → quiz with MC (4) + fill-blank (4) + matching (1 set) +
    writing (4) + answer key + spaced-review CSV;
  - `tests/fixtures/story.txt` (prose) → mined vocabulary, contextual
    sentence blanks rendered with `________`;
  - hard mode → no hints, 5-option MC confirmed by inspection;
  - `--probe-llm` against a dead endpoint → exit code 2, `reachable=no`
    (verifies offline fallback path);
  - seeded runs (`--seed 42`) produce identical quizzes across runs.
- Content safety: HTML export escaping verified by test against
  `<script>` payloads; the LLM client cannot be pointed at inline keys
  (no auth header code path exists).

## Known gaps

- Prose mining is frequency-based; it can pick proper nouns and light
  adverbs (stopword list is handwritten). Quality improves with curated word
  lists.
- No true/false, cloze-with-word-bank, or audio sections (planned if useful).
- Writing questions are open-ended; the tool does not grade sentences
  (local-LLM judging is an idea, but adds a dependency on a running model).
- HTML is print-first; there is no interactive take-the-quiz-in-browser mode.
- The spaced-review schedule ignores past sessions (no state file); it is a
  static date ladder by design.
- Packaging tested only on Linux/Python 3.13 in this environment; Windows
  paths and Ollama portability are expected but not separately verified.

No secrets, keys, or personal data are stored in any file in this repository.
