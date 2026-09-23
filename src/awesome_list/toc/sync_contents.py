"""Rewrite the Contents section in place, and only that."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.toc.render_contents import render_contents

CONTENTS_HEADING = "## contents"


def sync_contents(text: str, document: ListDocument) -> tuple[str, bool]:
    """Return the text with a correct Contents section, and whether it changed."""
    wanted = list(render_contents(document))
    lines = text.splitlines()
    heading_index = _find_contents_heading(lines)

    if heading_index is None:
        updated = _insert_contents(lines, wanted)
        return updated, updated != text

    start, end = _toc_block(lines, heading_index)
    current = lines[start:end]
    if current == wanted:
        return text, False

    updated_lines = lines[:start] + wanted + lines[end:]
    return "\n".join(updated_lines) + ("\n" if text.endswith("\n") else ""), True


def _find_contents_heading(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.strip().lower() == CONTENTS_HEADING:
            return index
    return None


def _toc_block(lines: list[str], heading_index: int) -> tuple[int, int]:
    index = heading_index + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    start = index
    while index < len(lines):
        stripped = lines[index].lstrip()
        if stripped.startswith("- ") and lines[index].startswith(("- ", " ", "\t")):
            index += 1
            continue
        break
    return start, index


def _insert_contents(lines: list[str], wanted: list[str]) -> str:
    title_index = next(
        (index for index, line in enumerate(lines) if line.startswith("# ")), 0
    )
    index = title_index + 1
    while index < len(lines):
        stripped = lines[index].lstrip()
        if not stripped or stripped.startswith((">", "<!--")):
            index += 1
            continue
        break
    block = ["## Contents", "", *wanted, ""]
    updated = lines[:index] + block + lines[index:]
    return "\n".join(updated) + "\n"
