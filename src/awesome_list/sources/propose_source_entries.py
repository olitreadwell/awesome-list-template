"""Propose upstream entries a list might add, without ever writing an entry.

awesome.re rejects lists and pull requests written by automation, so this
module stops at a report a human reads. It says which upstream entries match a
list's keywords and are not already in the readme, and carries the repo stats
the list demands of every GitHub link.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from awesome_list.github.github_stats import RepoStats, format_stats, github_repo_slug
from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.normalize_url import normalize_url
from awesome_list.sources.parse_table_entries import SourceEntry


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """One upstream entry worth a human's attention."""

    entry: SourceEntry
    matched: tuple[str, ...]
    stats: RepoStats | None = None


def propose_source_entries(
    document: ListDocument,
    source_entries: Sequence[SourceEntry],
    keywords: Sequence[str],
    stats: Mapping[str, RepoStats] | None = None,
) -> tuple[SourceCandidate, ...]:
    """Return matching entries the list does not already carry."""
    known = {normalize_url(entry.url) for entry in document.entries}
    wanted = tuple(keyword.strip().lower() for keyword in keywords if keyword.strip())
    candidates: list[SourceCandidate] = []

    for entry in source_entries:
        if normalize_url(entry.url) in known:
            continue
        haystack = f"{entry.name} {entry.description} {entry.section}".lower()
        matched = tuple(keyword for keyword in wanted if _matches(haystack, keyword))
        if wanted and not matched:
            continue
        slug = github_repo_slug(entry.url)
        candidates.append(
            SourceCandidate(
                entry=entry,
                matched=matched,
                stats=(stats or {}).get(slug) if slug else None,
            )
        )

    return tuple(candidates)


def _matches(haystack: str, keyword: str) -> bool:
    """Match a whole word, so "ons" never matches "icons" or "options"."""
    pattern = rf"\b{re.escape(keyword)}\b"
    return re.search(pattern, haystack) is not None


def render_source_report(
    candidates: Sequence[SourceCandidate], sources: Sequence[str] = ()
) -> str:
    """Render the candidates as the Markdown a maintainer reads or an issue holds."""
    lines = [
        "# Source candidates",
        "",
        "Nothing here is an entry yet. A human writes every entry, then "
        "`make list-check` decides.",
        "",
    ]
    if sources:
        lines += ["Read from:", ""]
        lines += [f"- {url}" for url in sources]
        lines += [""]

    if not candidates:
        lines += ["No candidates matched.", ""]
        return "\n".join(lines)

    lines += [
        f"{len(candidates)} candidates.",
        "",
        "| Entry | Where | Why | Stats |",
        "| --- | --- | --- | --- |",
    ]
    for candidate in candidates:
        entry = candidate.entry
        stats = format_stats(candidate.stats) if candidate.stats else "not a repo"
        matched = ", ".join(candidate.matched) or "no keyword needed"
        lines.append(
            f"| [{entry.name}]({entry.url}) | {entry.section} | {matched} | {stats} |"
        )
    lines.append("")
    return "\n".join(lines)
