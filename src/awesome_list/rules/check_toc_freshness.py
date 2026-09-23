"""The Contents section must match the headings, in order, and stay clean."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation
from awesome_list.toc.render_contents import DENIED_TOC_SECTIONS
from awesome_list.toc.sync_contents import _find_contents_heading, _toc_block

RULE = "toc-freshness"
ENTRY_PATTERN = "- ["


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
    listed = [_entry_name(line) for line in lines[start:end]]
    listed = [name for name in listed if name]

    expected = [
        section.name
        for section in document.sections
        if section.name.strip().lower() not in DENIED_TOC_SECTIONS
    ]
    violations: list[RuleViolation] = []

    for line_number, name in zip(range(start + 1, end + 1), listed, strict=False):
        if name.lower() in DENIED_TOC_SECTIONS:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=line_number,
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

    for line_number, name in zip(range(start + 1, end + 1), listed, strict=False):
        if name not in expected and name.lower() not in DENIED_TOC_SECTIONS:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=line_number,
                    message=f"{name} is in the Contents section but not in the readme",
                    fix="run make toc to regenerate the Contents section",
                )
            )

    return tuple(violations)


def _entry_name(line: str) -> str:
    stripped = line.strip()
    if not stripped.startswith(ENTRY_PATTERN):
        return ""
    closing = stripped.find("](")
    if closing == -1:
        return ""
    return stripped[3:closing].strip()
