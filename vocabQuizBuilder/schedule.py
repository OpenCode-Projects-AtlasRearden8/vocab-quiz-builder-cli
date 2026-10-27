"""Lightweight spaced-review schedule exporter (no database, just a file).

Schedule intervals: today, +3 days, +7, +16, +35 — a friendly expanding ladder.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Sequence

from .models import Entry

DEFAULT_INTERVALS = (0, 3, 7, 16, 35)

INTERVAL_HEADER = ["word", "definition", "review_1", "review_2", "review_3", "review_4", "review_5", "done"]


def build_schedule(entries: Sequence[Entry], start: dt.date | None = None) -> list[list[str]]:
    start = start or dt.date.today()
    rows: list[list[str]] = []
    for entry in sorted(entries, key=lambda e: e.word.lower()):
        dates = []
        for interval in DEFAULT_INTERVALS:
            dates.append((start + dt.timedelta(days=interval)).isoformat())
        row = [entry.word, entry.definition] + dates
        row.append(" ☐")
        rows.append(row)
    return rows


def write_schedule(
    path: str | Path, entries: Sequence[Entry], start: dt.date | None = None
) -> Path:
    """Write a clean CSV spaced-review file; returns the path written.

    Intervals are day 0 (today), +3, +7, +16, +35. Mark rows ☑ as you review.
    """
    path = Path(path)
    rows = build_schedule(entries, start)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(INTERVAL_HEADER)
        writer.writerows(rows)
    return path


def schedule_blurb(path: str | Path) -> str:
    return (
        "<h2>Spaced review</h2>"
        f"<p>Re-glance these words on the schedule saved to "
        f"<code>{Path(path).name}</code> (same folder as this quiz): "
        "day 0, +3, +7, +16, +35.</p>"
    )
