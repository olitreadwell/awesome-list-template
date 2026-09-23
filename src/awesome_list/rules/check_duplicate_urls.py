"""Two entries, one resource."""

from __future__ import annotations

from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.normalize_url import normalize_url
from awesome_list.rules.rule_violation import RuleViolation

RULE = "duplicate-urls"


def check_duplicate_urls(
    document: ListDocument, allowed_urls: frozenset[str] = frozenset()
) -> tuple[RuleViolation, ...]:
    """Flag every entry that repeats a URL an earlier entry already uses.

    An allowlisted URL is skipped, because a repeated URL is deliberate
    sometimes and the allowlist is where a list says so.
    """
    first_seen: dict[str, str] = {}
    violations: list[RuleViolation] = []

    for entry in document.entries:
        if entry.url.strip() in allowed_urls:
            continue
        key = normalize_url(entry.url)
        if not key:
            continue
        earlier = first_seen.get(key)
        if earlier is None:
            first_seen[key] = entry.name
            continue
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} duplicates the URL used by {earlier}",
                fix="remove one of the two entries, or point this one at a"
                " different page",
            )
        )

    return tuple(violations)
