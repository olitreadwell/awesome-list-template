"""Candidates: matched, not already carried, and never written as entries."""

from __future__ import annotations

from awesome_list.github.github_stats import RepoStats
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.sources.parse_table_entries import SourceEntry
from awesome_list.sources.propose_source_entries import (
    propose_source_entries,
    render_source_report,
)

TARGET = """\
# Awesome Test [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A test list.

## Contents

- [Tools](#tools)

## Tools

- [Already Here](https://catfact.ninja/) - the list already carries this one.
"""

ENTRIES = (
    SourceEntry(
        name="Cat Facts",
        url="https://catfact.ninja/",
        description="Random cat facts",
        section="Animals",
        line=6,
    ),
    SourceEntry(
        name="Open Government, New Zealand",
        url="https://www.data.govt.nz/",
        description="New Zealand Government Open Data",
        section="Government",
        line=14,
    ),
    SourceEntry(
        name="Data.gov",
        url="https://api.data.gov/",
        description="US Government Data",
        section="Government",
        line=15,
    ),
)


def test_only_new_entries_that_match_a_keyword_are_proposed() -> None:
    candidates = propose_source_entries(
        parse_readme(TARGET), ENTRIES, ["new zealand", "government"]
    )

    assert [candidate.entry.name for candidate in candidates] == [
        "Open Government, New Zealand",
        "Data.gov",
    ]
    assert candidates[0].matched == ("new zealand", "government")


def test_an_entry_already_in_the_list_is_never_proposed() -> None:
    candidates = propose_source_entries(parse_readme(TARGET), ENTRIES, ["cat"])

    assert candidates == ()


def test_no_keywords_proposes_everything_new() -> None:
    candidates = propose_source_entries(parse_readme(TARGET), ENTRIES, [])

    assert len(candidates) == 2


def test_repo_stats_ride_along() -> None:
    stats = {"owner/repo": RepoStats("owner/repo", 87, "2024-05-01", archived=True)}
    entries = (
        *ENTRIES,
        SourceEntry(
            name="Repo",
            url="https://github.com/owner/repo",
            description="",
            section="Tools",
            line=20,
        ),
    )

    candidates = propose_source_entries(parse_readme(TARGET), entries, [], stats=stats)
    repo = next(c for c in candidates if c.entry.name == "Repo")

    assert repo.stats == stats["owner/repo"]


def test_report_says_nothing_was_written() -> None:
    candidates = propose_source_entries(parse_readme(TARGET), ENTRIES, ["new zealand"])
    report = render_source_report(
        candidates, sources=("https://upstream.test/list.md",)
    )

    assert "Nothing here is an entry yet" in report
    assert "| Entry | Where | Why | Stats |" in report
    assert "[Open Government, New Zealand](https://www.data.govt.nz/)" in report
    assert "not a repo" in report
    assert "https://upstream.test/list.md" in report


def test_empty_report_says_so() -> None:
    assert "No candidates matched." in render_source_report(())
