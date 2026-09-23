"""Every GitHub link must carry stars and activity, from a fresh snapshot."""

from __future__ import annotations

from datetime import date

from awesome_list.github.github_stats import (
    RepoStats,
    StatsSnapshot,
    format_stats,
    github_repo_slug,
)
from awesome_list.parse.readme_model import ListDocument
from awesome_list.rules.rule_violation import RuleViolation

RULE = "github-stats"


def check_github_stats(
    document: ListDocument,
    snapshot: StatsSnapshot | None,
    max_age_days: int,
    *,
    enabled: bool = True,
    today: date | None = None,
) -> tuple[RuleViolation, ...]:
    """Return every missing or stale stats segment.

    A missing segment is an error because the fix is mechanical: run `make
    stats`. A stale snapshot is a warning because it needs a network round trip
    and a maintainer's judgement about rate limits.
    """
    if not enabled:
        return ()

    linked = [
        (entry.line, entry.name, slug)
        for entry in document.entries
        if (slug := github_repo_slug(entry.url)) is not None
    ]
    if not linked:
        return ()

    if snapshot is None:
        return (
            RuleViolation(
                rule=RULE,
                line=linked[0][0],
                message=(
                    f"{len(linked)} GitHub entries have no stats snapshot"
                    " to check against"
                ),
                fix="run make stats to fetch stars and last push dates",
            ),
        )

    violations: list[RuleViolation] = []
    for line, name, slug in linked:
        stats = snapshot.repos.get(slug)
        if stats is None:
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=line,
                    message=f"{name} has no stars and activity recorded for {slug}",
                    fix="run make stats to fetch them",
                )
            )
            continue
        if not _line_shows(document, line, stats):
            violations.append(
                RuleViolation(
                    rule=RULE,
                    line=line,
                    message=f"{name} does not show stars and activity for {slug}",
                    fix=(
                        f"end the entry with {format_stats(stats)}"
                        " by running make stats"
                    ),
                )
            )

    age = snapshot.age_days(today or date.today())
    if age > max_age_days:
        violations.append(
            RuleViolation(
                rule=RULE,
                line=1,
                message=f"the GitHub stats snapshot is {age} days old",
                fix="run make stats to refresh stars and last push dates",
                severity="warn",
            )
        )

    return tuple(violations)


def _line_shows(document: ListDocument, line: int, stats: RepoStats) -> bool:
    """Return True when the raw line for this entry already ends with these stats."""
    expected = format_stats(stats)
    return any(
        entry.raw.rstrip().endswith(expected)
        for entry in document.entries
        if entry.line == line
    )
