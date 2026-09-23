"""The Contents section must match the headings, in order, and stay clean."""

from __future__ import annotations

from collections.abc import Sequence

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation
from awesome_list.toc.render_contents import (
    DENIED_TOC_SECTIONS,
    render_contents,
)
from awesome_list.toc.sync_contents import _find_contents_heading, _toc_block

RULE = "toc-freshness"
ENTRY_PATTERN = "- ["
DEPTH_FIX = (
    "run make toc to regenerate the Contents section; awesome-lint fails a"
    " nested list deeper than two levels"
)


def check_toc_freshness(document: ListDocument, text: str) -> tuple[RuleViolation, ...]:
    """Return every problem with the Contents section."""
    lines = text.splitlines()
    heading_index = _find_contents_heading(lines)

    if heading_index is None:
        return (
            RuleViolation(
                rule=RULE,
                line=1,
                message="the readme has no Contents section",
                fix="add a Contents section as the first section, then run make toc",
            ),
        )

    start, end = _toc_block(lines, heading_index)
    listed_lines = [line for line in lines[start:end] if _entry_name(line)]
    listed = [_entry_name(line) for line in listed_lines]
    rendered = render_contents(document)
    expected = [_entry_name(line) for line in rendered]
    expected_depth = dict(zip(expected, _depth_ranks(rendered), strict=False))
    known = {heading.text.strip() for heading in document.headings if heading.level > 1}

    violations: list[RuleViolation] = []

    for number, name in zip(range(start + 1, end + 1), listed, strict=False):
        if name.lower() in DENIED_TOC_SECTIONS:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=number,
                    message=f"{name} must not appear in the Contents section",
                    fix="remove this line; awesome.re keeps these out of the"
                    " table of contents",
                )
            )

    for name in expected:
        if name not in listed:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=heading_index + 1,
                    message=f"{name} is missing from the Contents section",
                    fix="run make toc to regenerate the Contents section",
                )
            )

    listed_depth = _depth_ranks(listed_lines)
    for number, name, depth in zip(
        range(start + 1, end + 1), listed, listed_depth, strict=False
    ):
        if name.lower() in DENIED_TOC_SECTIONS:
            continue
        if name in expected:
            # Compare nesting depth, not the number of spaces: two and four both
            # render, and a list is free to use either.
            if depth != expected_depth[name]:
                violations.append(
                    RuleViolation(
                        rule=RULE,
                        line=number,
                        message=(
                            f"{name} sits at the wrong depth in the Contents section"
                        ),
                        fix=DEPTH_FIX,
                    )
                )
            continue
        if name in known:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=number,
                    message=f"{name} is nested deeper than the Contents section allows",
                    fix=DEPTH_FIX,
                )
            )
            continue
        violations.append(
            RuleViolation(
                rule=RULE,
                line=number,
                message=f"{name} is in the Contents section but not in the readme",
                fix="run make toc to regenerate the Contents section",
            )
        )

    return tuple(violations)


def _depth_ranks(lines: Sequence[str]) -> list[int]:
    """Turn indentation widths into levels, so two spaces and four both read as one."""
    widths = sorted({len(line) - len(line.lstrip(" ")) for line in lines})
    rank = {width: index + 1 for index, width in enumerate(widths)}
    return [rank[len(line) - len(line.lstrip(" "))] for line in lines]


def _entry_name(line: str) -> str:
    stripped = line.strip()
    if not stripped.startswith(ENTRY_PATTERN):
        return ""
    closing = stripped.find("](")
    if closing == -1:
        return ""
    return stripped[3:closing].strip()
