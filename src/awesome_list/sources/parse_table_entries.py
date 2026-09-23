"""Read entries out of an awesome list that lists them in a table.

`public-apis/public-apis` is the reason this exists: it is a curated list whose
entries live in Markdown tables under headings, so the bullet parser reads
nothing from it. Mining it for candidates is the whole point of `make sources`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")
HEADER_WORDS = frozenset({"api", "name", "title", "description"})


@dataclass(frozen=True, slots=True)
class SourceEntry:
    """One upstream entry, with the heading it sat under."""

    name: str
    url: str
    description: str
    section: str
    line: int


def parse_table_entries(text: str) -> tuple[SourceEntry, ...]:
    """Return every linked table row, in document order, duplicates removed."""
    entries: list[SourceEntry] = []
    seen: set[str] = set()
    section = ""

    for number, line in enumerate(text.splitlines(), start=1):
        heading = HEADING.match(line)
        if heading:
            section = _plain(heading.group(2))
            continue

        row = TABLE_ROW.match(line)
        if row is None:
            continue
        cells = _cells(row.group(1))
        if _is_header_or_separator(cells):
            continue

        link = LINK.search(cells[0])
        if link is None:
            continue
        url = link.group(2)
        if url in seen:
            continue
        seen.add(url)
        entries.append(
            SourceEntry(
                name=_plain(link.group(1)),
                url=url,
                description=_plain(cells[1]) if len(cells) > 1 else "",
                section=section,
                line=number,
            )
        )

    return tuple(entries)


def _cells(body: str) -> list[str]:
    return [cell.strip() for cell in body.split("|")]


def _is_header_or_separator(cells: list[str]) -> bool:
    if not cells:
        return True
    if any(SEPARATOR_CELL.match(cell) for cell in cells):
        return True
    return cells[0].strip().lower() in HEADER_WORDS


def _plain(text: str) -> str:
    """Drop the markdown that gets in the way of a keyword search."""
    without_links = LINK.sub(lambda match: match.group(1), text)
    cleaned = without_links.replace("**", "").replace("`", "").replace("_", " ")
    return " ".join(cleaned.split())
