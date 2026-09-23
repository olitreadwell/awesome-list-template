"""Entry grammar: the dash, the period, the capital, the whitespace.

These rules follow awesome-lint's list-item rule where it has an opinion, so a
clean list is clean for both. The casing check only applies to entries with no
tags, because that is what the linter sees: with tags in place the first word it
inspects is the tag label, which is already capitalised.
"""

from __future__ import annotations

from awesome_list.parse.readme_model import ListEntry
from awesome_list.rules.rule_violation import RuleViolation

RULE = "entry-grammar"


def check_entry_grammar(entry: ListEntry) -> tuple[RuleViolation, ...]:
    """Return every grammar problem in one entry."""
    violations: list[RuleViolation] = []

    if entry.raw != entry.raw.rstrip():
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} has trailing whitespace",
                fix="remove the whitespace at the end of the line",
            )
        )

    if entry.description and not entry.has_separator:
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} does not separate the link and the description",
                fix="separate the link and the description with ' - ', for example:"
                " - [Name](https://example.com/) - what it is.",
            )
        )
        return tuple(violations)

    if not entry.description:
        # awesome-lint flags a tagged entry with nothing after the tags as bad
        # punctuation, so that case is an error. A bare link with no tags and no
        # description is accepted upstream, so that one only warns: fixing it
        # needs a human to write the words.
        if entry.tags:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=entry.line,
                    message=f"{entry.name} has tags but no description",
                    fix="add a description after the tags, or remove the tags",
                )
            )
        else:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=entry.line,
                    message=f"{entry.name} has no description",
                    fix="add a description if the title does not say enough on its own",
                    severity="warn",
                )
            )
        return tuple(violations)

    first = entry.description[0]
    if not entry.tags and first.isalpha() and not first.isupper():
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} starts the description with a lowercase letter",
                fix="start the description with a capital letter",
            )
        )

    if not entry.description.endswith((".", "!", "?")):
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} does not end the description with a period",
                fix="end the description with a period",
            )
        )

    return tuple(violations)
