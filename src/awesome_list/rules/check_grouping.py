"""Grouping: empty groups, empty sections, nesting that is too deep."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation

RULE = "grouping"


def check_grouping(document: ListDocument) -> tuple[RuleViolation, ...]:
    """Return every grouping problem in the document."""
    violations: list[RuleViolation] = []

    for section in document.sections:
        if not section.entries and not section.groups:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=section.line,
                    message=f"{section.name} has no entries",
                    fix="add an entry to this section, or remove the heading",
                )
            )
        for group in section.groups:
            if not group.entries:
                violations.append(
                    RuleViolation(
                        rule=RULE,
                        line=group.line,
                        message=f"{group.name} has no entries",
                        fix="indent its entries under the group name, or remove"
                        " the group bullet",
                    )
                )
        for entry in section.entries:
            if entry.nested_under_entry:
                violations.append(
                    RuleViolation(
                        rule=RULE,
                        line=entry.line,
                        message=f"{entry.name} is nested under an entry",
                        fix="pull it up to the section, or make the parent a group name"
                        " by removing its link",
                    )
                )
            if entry.depth > 2:
                violations.append(
                    RuleViolation(
                        rule=RULE,
                        line=entry.line,
                        message=f"{entry.name} is nested too deep",
                        fix="keep entries at one level under a group name",
                    )
                )

    return tuple(violations)
