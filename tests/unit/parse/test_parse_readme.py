"""The parser turns readme.md into the entry model."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme


def test_reads_title_tagline_and_sections(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    assert document.title == "Awesome Example"
    assert document.tagline == "A curated list of example things, with tags."
    assert [section.name for section in document.sections] == ["Start here", "Tools"]


def test_parses_entries_with_tags(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))
    entry = document.entries[0]

    assert entry.name == "Example Portal"
    assert entry.url == "https://example.govt.nz/"
    assert entry.description == "the catalogue of example datasets."
    assert [(tag.axis, tag.label) for tag in entry.tags] == [
        ("type", "Data"),
        ("access", "Open"),
    ]
    assert entry.line == 12


def test_parses_groups(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))
    tools = document.sections[1]

    assert tools.entries == ()
    assert [group.name for group in tools.groups] == ["Example Group"]
    assert [entry.name for entry in tools.groups[0].entries] == [
        "First Tool",
        "Second Tool",
    ]


def test_skips_contents_and_footnotes(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    assert [section.name for section in document.sections] == ["Start here", "Tools"]
    assert all(entry.url.startswith("https://") for entry in document.entries)


def test_entry_lines_are_one_based(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))
    lines = [entry.line for entry in document.entries]

    assert lines == sorted(lines)
    assert all(line > 0 for line in lines)
