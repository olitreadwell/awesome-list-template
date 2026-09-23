"""Fetching stars and last push dates, with every failure soft."""

from __future__ import annotations

import json

from awesome_list.github.fetch_repo_stats import (
    FetchError,
    fetch_repo_stats,
    parse_repo_json,
)

PAYLOAD = json.dumps(
    {
        "stargazers_count": 4210,
        "pushed_at": "2024-05-06T11:22:33Z",
        "archived": False,
    }
)


def test_parse_reads_stars_date_and_archived() -> None:
    stats = parse_repo_json("codeforamerica/civic-tech-patterns", PAYLOAD)

    assert stats.slug == "codeforamerica/civic-tech-patterns"
    assert stats.stars == 4210
    assert stats.pushed_at == "2024-05-06"
    assert stats.archived is False


def test_parse_copes_with_missing_fields() -> None:
    stats = parse_repo_json("owner/repo", "{}")

    assert stats.stars == 0
    assert stats.pushed_at == ""
    assert stats.archived is False


def test_fetch_returns_stats_per_slug() -> None:
    stats, unfetched = fetch_repo_stats(["owner/repo"], run=lambda slug: PAYLOAD)

    assert unfetched == ()
    assert stats["owner/repo"].stars == 4210


def test_a_failed_fetch_keeps_the_previous_numbers() -> None:
    previous = parse_repo_json("owner/repo", PAYLOAD)

    def explode(slug: str) -> str:
        raise FetchError(f"gh api repos/{slug}: HTTP 403")

    stats, unfetched = fetch_repo_stats(
        ["owner/repo"], run=explode, previous={"owner/repo": previous}
    )

    assert unfetched == ("owner/repo",)
    assert stats["owner/repo"] == previous


def test_a_failed_fetch_with_no_history_is_reported() -> None:
    def explode(slug: str) -> str:
        raise FetchError(slug)

    stats, unfetched = fetch_repo_stats(["owner/repo"], run=explode)

    assert stats == {}
    assert unfetched == ("owner/repo",)


def test_bad_json_is_soft_too() -> None:
    stats, unfetched = fetch_repo_stats(["owner/repo"], run=lambda slug: "not json")

    assert stats == {}
    assert unfetched == ("owner/repo",)
