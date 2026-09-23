"""Grouping: empty groups, empty sections, nesting that is too deep."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation

RULE = "grouping"

# A group of entries is level two, and this list style allows one level of
# sub-entries under an entry, which is level three.
MAX_ENTRY_DEPTH = 3


def check_grouping(
    document: ListDocument, entry_sections: tuple[str, ...] = ()
) -> tuple[RuleViolation, ...]:
    """Return every grouping problem in the document.

    A section is only expected to hold entries when the config lists it, so
    prose sections such as Contributing or Legend are left alone.
    """
    violations: list[RuleViolation] = []

    for section in document.sections:
        if section.name not in entry_sections:
            continue
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
            if entry.depth > MAX_ENTRY_DEPTH:
                violations.append(
                    RuleViolation(
                        rule=RULE,
                        line=entry.line,
                        message=f"{entry.name} is nested too deep",
                        fix="keep entries at most two levels under a group name",
                    )
                )

    return tuple(violations)
