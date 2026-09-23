"""The gate insists that GitHub links carry live-looking stats."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from awesome_list.github.github_stats import RepoStats, StatsSnapshot
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_github_stats import check_github_stats

TODAY = date(2026, 9, 23)
CIVIC = "https://github.com/codeforamerica/civic-tech-patterns"
NO_STATS_LINE = f"- [Without Stats]({CIVIC}) - patterns.\n"

FRESH = StatsSnapshot(
    generated_at="2026-09-23",
    repos={
        "codeforamerica/civic-tech-patterns": RepoStats(
            slug="codeforamerica/civic-tech-patterns",
            stars=1234,
            pushed_at="2026-09-20",
            archived=False,
        )
    },
)

TEXT = f"""\
# Awesome Test [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A test list.

## Contents

- [Tools](#tools)

## Tools

- [With Stats]({CIVIC}) - patterns. - ★ 1,234 stars, last push 2026-09-20.
- [Without Stats]({CIVIC}) - patterns.
- [Not A Repo](https://example.com/) - nothing to see.
"""


def test_missing_stats_is_a_violation(fixture_readme: Callable[[str], str]) -> None:
    del fixture_readme
    document = parse_readme(TEXT)
    violations = check_github_stats(document, FRESH, 14, today=TODAY)

    assert [violation.rule for violation in violations] == ["github-stats"]
    assert "Without Stats" in violations[0].message
    assert "make stats" in violations[0].fix


def test_entries_that_are_up_to_date_pass(fixture_readme: Callable[[str], str]) -> None:
    del fixture_readme
    text = TEXT.replace(NO_STATS_LINE, "")

    assert check_github_stats(parse_readme(text), FRESH, 14, today=TODAY) == ()


def test_stale_snapshot_warns_instead_of_failing() -> None:
    old = StatsSnapshot(generated_at="2026-01-01", repos=FRESH.repos)
    text = TEXT.replace(NO_STATS_LINE, "")
    violations = check_github_stats(parse_readme(text), old, 14, today=TODAY)

    assert [violation.severity for violation in violations] == ["warn"]
    assert "days old" in violations[0].message


def test_stats_can_be_turned_off() -> None:
    assert (
        check_github_stats(parse_readme(TEXT), FRESH, 14, enabled=False, today=TODAY)
        == ()
    )
