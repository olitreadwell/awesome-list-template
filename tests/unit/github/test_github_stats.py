"""GitHub repos in a list carry stars and a last-push date."""

from __future__ import annotations

from awesome_list.github.github_stats import (
    RepoStats,
    apply_github_stats,
    format_stats,
    github_repo_slug,
)

CIVIC = "https://github.com/codeforamerica/civic-tech-patterns"

STATS = {
    "codeforamerica/civic-tech-patterns": RepoStats(
        slug="codeforamerica/civic-tech-patterns",
        stars=1234,
        pushed_at="2026-09-20",
        archived=False,
    ),
    "datamade/councilmatic": RepoStats(
        slug="datamade/councilmatic",
        stars=87,
        pushed_at="2024-05-01",
        archived=True,
    ),
}


def test_repo_slug_from_common_url_shapes() -> None:
    assert github_repo_slug(
        "https://github.com/codeforamerica/civic-tech-patterns"
    ) == ("codeforamerica/civic-tech-patterns")
    assert github_repo_slug("https://github.com/owner/repo.git") == "owner/repo"
    assert github_repo_slug("https://github.com/owner/repo/#readme") == "owner/repo"
    assert (
        github_repo_slug("https://github.com/owner/repo/tree/main/docs") == "owner/repo"
    )
    assert github_repo_slug("http://www.github.com/owner/repo") == "owner/repo"


def test_non_repo_github_urls_have_no_slug() -> None:
    assert github_repo_slug("https://github.com/owner") is None
    assert github_repo_slug("https://github.com/owner/repo/issues") is None
    assert github_repo_slug("https://github.com/owner/repo/pulls") is None
    assert github_repo_slug("https://gist.github.com/owner/abc") is None
    assert github_repo_slug("https://example.com/owner/repo") is None


def test_format_stats_reads_like_a_sentence() -> None:
    assert format_stats(STATS["codeforamerica/civic-tech-patterns"]) == (
        "★ 1,234 stars, last push 2026-09-20."
    )
    assert format_stats(STATS["datamade/councilmatic"]) == (
        "★ 87 stars, archived 2024-05-01."
    )


def test_single_star_is_not_pluralised() -> None:
    stats = RepoStats(slug="a/b", stars=1, pushed_at="2026-01-01", archived=False)

    assert format_stats(stats) == "★ 1 star, last push 2026-01-01."


def test_apply_adds_a_stats_segment_to_github_entries() -> None:
    text = (
        f"- [civic-tech-patterns]({CIVIC}) - common patterns for civic tech.\n"
        "- [Other](https://example.com/) - not a GitHub repo.\n"
    )
    updated, changed = apply_github_stats(text, STATS)

    assert changed == 1
    assert updated.splitlines()[0].endswith(" - ★ 1,234 stars, last push 2026-09-20.")
    assert (
        updated.splitlines()[1]
        == "- [Other](https://example.com/) - not a GitHub repo."
    )


def test_apply_replaces_a_stale_segment_instead_of_stacking() -> None:
    text = (
        f"- [civic-tech-patterns]({CIVIC}) - common patterns for civic tech."
        " - ★ 9 stars, last push 2019-01-01.\n"
    )
    updated, changed = apply_github_stats(text, STATS)

    assert changed == 1
    assert updated.count("★") == 1
    assert updated.strip().endswith("- ★ 1,234 stars, last push 2026-09-20.")


def test_apply_is_idempotent() -> None:
    text = f"- [civic-tech-patterns]({CIVIC}) - patterns.\n"
    once, _ = apply_github_stats(text, STATS)
    twice, changed = apply_github_stats(once, STATS)

    assert changed == 0
    assert twice == once


def test_apply_leaves_repos_without_stats_alone() -> None:
    text = (
        "- [Unknown](https://github.com/nobody/unknown) - a repo with no stats yet.\n"
    )
    updated, changed = apply_github_stats(text, STATS)

    assert changed == 0
    assert updated == text


def test_apply_preserves_the_rest_of_the_line_byte_for_byte() -> None:
    line = (
        f"    - [civic-tech-patterns]({CIVIC})"
        " - ▦ Data - ○ Open - patterns. - ★ 9 stars, last push 2019-01-01.\n"
    )
    updated, _ = apply_github_stats(line, STATS)

    assert updated.startswith(
        f"    - [civic-tech-patterns]({CIVIC})"
        " - ▦ Data - ○ Open - patterns. - ★ 1,234 stars"
    )
