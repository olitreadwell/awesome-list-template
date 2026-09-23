"""Awkward shapes in the readme must parse, not crash."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme


def test_parses_names_with_dots_emoji_code_and_emphasis(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("edges.md"))
    names = [entry.name for entry in document.entries]

    assert names == [
        "Node.js",
        "Emoji 🌏 Tool",
        "Code Named",
        "Multiple Links",
        "Emphasis Tool",
        "Nested Child",
        "Another Child",
    ]


def test_keeps_only_the_first_link_as_the_entry_url(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("edges.md"))
    entry = next(item for item in document.entries if item.name == "Multiple Links")

    assert entry.url == "https://multi.example.com/"
    assert "the docs" in entry.description
    assert entry.description.endswith("for more.")


def test_nested_child_with_two_space_indent_is_grouped(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("edges.md"))
    grouped = next(
        section for section in document.sections if section.name == "Grouped"
    )

    assert [group.name for group in grouped.groups] == ["Group Parent"]
    assert len(grouped.groups[0].entries) == 2


def test_html_comment_in_the_toc_is_ignored(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("edges.md"))

    assert document.tagline == "A list with awkward shapes in it."
