"""Turn the parsed readme into the files other tools read.

JSON for programs, NDJSON for notebooks and log pipelines, CSV for
spreadsheets. All three come from one document so they cannot disagree.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Iterable
from typing import Any, cast

from awesome_list.config.list_config import ListConfig
from awesome_list.github.github_stats import EXISTING_STATS_TAIL
from awesome_list.parse.readme_model import ListDocument, ListEntry

COLUMNS = (
    "section",
    "group",
    "name",
    "url",
    "description",
    "tags",
    "stars",
    "last_push",
    "line",
)

STARS = re.compile(r"★\s*([\d,]+)\s+stars")
LAST_PUSH = re.compile(r"last push\s+(\d{4}-\d{2}-\d{2})")


def build_export(
    document: ListDocument, config: ListConfig, *, generated_at: str
) -> dict[str, object]:
    """Return the whole list as one JSON-shaped dict."""
    return {
        "name": config.name,
        "repo_slug": config.repo_slug,
        "generated_at": generated_at,
        "entry_count": len(document.entries),
        "sections": [
            {
                "name": section.name,
                "entries": [_entry(entry, group=None) for entry in section.entries]
                + [
                    _entry(entry, group=group.name)
                    for group in section.groups
                    for entry in group.entries
                ],
            }
            for section in document.sections
        ],
    }


def to_json(data: dict[str, object]) -> str:
    """Return pretty JSON, so a diff shows what actually changed."""
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def to_ndjson(data: dict[str, object]) -> str:
    """Return one entry per line."""
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in _rows(data))


def to_csv(data: dict[str, object]) -> str:
    """Return the entries as CSV with a header row."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(COLUMNS), lineterminator="\n")
    writer.writeheader()
    for row in _rows(data):
        writer.writerow({column: row[column] for column in COLUMNS})
    return buffer.getvalue()


def _entry(entry: ListEntry, *, group: str | None) -> dict[str, object]:
    """Return one entry, with the stats segment split out of the description.

    The readme glues stars and the last-push date onto the end of a
    description. A spreadsheet wants those as their own columns, and wants the
    description without them.
    """
    stats = EXISTING_STATS_TAIL.search(entry.description)
    trailer = stats.group(0) if stats else ""
    stars = STARS.search(trailer)
    pushed = LAST_PUSH.search(trailer)
    return {
        "name": entry.name,
        "url": entry.url,
        "description": EXISTING_STATS_TAIL.sub("", entry.description).strip(),
        "tags": [tag.label for tag in entry.tags],
        "group": group,
        "stars": int(stars.group(1).replace(",", "")) if stars else None,
        "last_push": pushed.group(1) if pushed else None,
        "line": entry.line,
    }


def _rows(data: dict[str, object]) -> Iterable[dict[str, object]]:
    sections = cast("list[dict[str, Any]]", data["sections"])
    for section in sections:
        for entry in cast("list[dict[str, Any]]", section["entries"]):
            tags = cast("list[str]", entry["tags"])
            yield {
                "section": section["name"],
                "group": entry["group"] or "",
                "name": entry["name"],
                "url": entry["url"],
                "description": entry["description"],
                "tags": " ".join(tags),
                "stars": entry["stars"] if entry["stars"] is not None else "",
                "last_push": entry["last_push"] or "",
                "line": entry["line"],
            }
