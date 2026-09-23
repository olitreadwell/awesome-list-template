"""Slug behaviour must match GitHub anchors, which github-slugger defines."""

from __future__ import annotations

import pytest

from awesome_list.slug.github_slug import github_slug


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Hello World", "hello-world"),
        ("Hello, World!", "hello-world"),
        ("Node.js", "nodejs"),
        ("1.0 Release", "10-release"),
        ("Café Data", "café-data"),
        ("Māori Data", "māori-data"),
        ("100% Open", "100-open"),
        ("C++", "c"),
        ("Foo -- Bar", "foo----bar"),
        ("🌏 Tool", "🌏-tool"),
        ("🌏️ Tool", "🌏-tool"),
        ("(括号) Data", "括号-data"),
        ("snake_case and kebab-case", "snake_case-and-kebab-case"),
        ("", ""),
    ],
)
def test_slug_matches_github(heading: str, expected: str) -> None:
    assert github_slug(heading) == expected


def test_slugger_appends_occurrence_suffixes() -> None:
    from awesome_list.slug.github_slug import GithubSlugger

    slugger = GithubSlugger()

    assert slugger.slug("Foo Bar") == "foo-bar"
    assert slugger.slug("Foo Bar") == "foo-bar-1"
    assert slugger.slug("Foo Bar") == "foo-bar-2"
    assert slugger.slug("Other") == "other"
    assert slugger.slug("Foo Bar") == "foo-bar-3"


def test_slugger_reset_starts_over() -> None:
    from awesome_list.slug.github_slug import GithubSlugger

    slugger = GithubSlugger()
    slugger.slug("Foo")
    slugger.reset()

    assert slugger.slug("Foo") == "foo"
