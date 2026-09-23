"""Tags must come from the configured vocabulary, one per axis."""

from __future__ import annotations

from collections import Counter

from awesome_list.parse.readme_model import ListEntry
from awesome_list.rules.rule_violation import RuleViolation
from awesome_list.tags import TagVocabulary

RULE = "tag-vocabulary"
REQUIRED_AXES = ("type", "access")


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def check_tag_vocabulary(
    entry: ListEntry, vocabulary: TagVocabulary
) -> tuple[RuleViolation, ...]:
    """Return every tag problem in one entry."""
    violations: list[RuleViolation] = []

    for axis, label in entry.unknown_tags:
        known = ", ".join(vocabulary.labels_for(axis))
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} has an unknown {axis} tag: {label}",
                fix=f"use one of the configured {axis} tags: {known}",
            )
        )

    counts = Counter(tag.axis for tag in entry.tags)
    for axis in ("type", "access", "status"):
        if counts[axis] > 1:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=entry.line,
                    message=f"{entry.name} has more than one {axis} tag",
                    fix=f"keep exactly one {axis} tag",
                )
            )
    for axis in REQUIRED_AXES:
        # An axis is only required when the config defines tags for it, so a
        # list that does not use tags is not nagged about them.
        if not vocabulary.labels_for(axis):
            continue
        if counts[axis] == 0 and not any(
            item_axis == axis for item_axis, _ in entry.unknown_tags
        ):
            known = ", ".join(vocabulary.labels_for(axis))
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=entry.line,
                    message=f"{entry.name} is missing {_article(axis)} {axis} tag",
                    fix=f"add {_article(axis)} {axis} tag from: {known}",
                )
            )

    return tuple(violations)
