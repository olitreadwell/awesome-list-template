"""A bullet that is only a URL is not an entry."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation

RULE = "bare-url"
URL_PREFIXES = ("http://", "https://", "www.")


def check_bare_urls(document: ListDocument) -> tuple[RuleViolation, ...]:
    """Flag bullets that are a bare URL rather than a link and a name."""
    violations: list[RuleViolation] = []
    for section in document.sections:
        for bullet in section.plain_bullets:
            text = bullet.text.strip()
            if not text.lower().startswith(URL_PREFIXES):
                continue
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=bullet.line,
                    message=f"{text} is a bare URL",
                    fix="write the entry as - [Name](url) - what it is, so the "
                    "list reads the same everywhere",
                )
            )
    return tuple(violations)
