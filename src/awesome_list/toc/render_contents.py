"""Render the Contents section from the headings."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.slug.github_slug import GithubSlugger

DENIED_TOC_SECTIONS = frozenset(
    {
        "contents",
        "table of contents",
        "contributing",
        "footnotes",
        "related lists",
        "license",
        "licence",
    }
)

# awesome-lint fails a Contents section nested more than two levels, so level
# four headings stay out of it.
# Two spaces per level, which is what GitHub renders and what every real list
# uses. Four also renders, but it is not what a reader sees elsewhere.
TOC_INDENT = "  "
MAX_TOC_DEPTH = 3


def render_contents(document: ListDocument) -> tuple[str, ...]:
    """Return the Contents lines for this document, in heading order."""
    slugger = GithubSlugger()
    slugs = [slugger.slug(heading.text) for heading in document.headings]

    lines: list[str] = []
    denied = False
    for heading, slug in zip(document.headings, slugs, strict=True):
        name = heading.text.strip()
        if heading.level == 1:
            continue
        if heading.level == 2:
            denied = name.lower() in DENIED_TOC_SECTIONS
            if denied:
                continue
            lines.append(f"- [{name}](#{slug})")
            continue
        if denied or heading.level > MAX_TOC_DEPTH:
            continue
        indent = TOC_INDENT * (heading.level - 2)
        lines.append(f"{indent}- [{name}](#{slug})")

    return tuple(lines)
