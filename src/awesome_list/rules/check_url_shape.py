"""URL shape: absolute, https, no tracking parameters, no scripts."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit

from awesome_list.parse.readme_model import ListEntry
from awesome_list.rules.normalize_url import TRACKING_PARAMETERS
from awesome_list.rules.rule_violation import RuleViolation

RULE = "url-shape"
ALLOWED_SCHEMES = frozenset({"http", "https", "mailto"})


def check_url_shape(entry: ListEntry) -> tuple[RuleViolation, ...]:
    """Return every URL problem in one entry."""
    url = entry.url.strip()
    violations: list[RuleViolation] = []

    if not url:
        return (
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} has no URL",
                fix="add an absolute https URL",
            ),
        )

    if url.startswith("#"):
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} links to an in-page fragment: {url}",
                fix="use an absolute URL that points at the resource",
            )
        )
        return tuple(violations)

    parts = urlsplit(url)
    if not parts.scheme:
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} uses a relative URL: {url}",
                fix="use an absolute URL, for example https://example.com/page",
            )
        )
        return tuple(violations)

    if parts.scheme.lower() == "http":
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} uses plain http: {url}",
                fix="use https when the site supports it",
            )
        )
    elif parts.scheme.lower() not in ALLOWED_SCHEMES:
        scheme = parts.scheme.split(":", 1)[0]
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} uses the {scheme} scheme: {url}",
                fix="use an https URL instead of a script or data URL",
            )
        )

    tracking = sorted(
        key
        for key, _value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() in TRACKING_PARAMETERS
    )
    if tracking:
        violations.append(
            RuleViolation(
                rule=RULE,
                line=entry.line,
                message=f"{entry.name} has a tracking parameter {tracking[0]}: {url}",
                fix=f"remove {tracking[0]} from the URL",
            )
        )

    return tuple(violations)
