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


THIRD_LEVEL_SECTIONS = """# Awesome Deep Things

A curated list of deep things.

## Contents

- [Packages](#packages)
- [Archived](#archived)

### Packages

- [First](https://first.example.com/) - does the first thing.
- [Second](https://second.example.com/) - does the second thing.

### Archived

- [Third](https://third.example.com/) - does the third thing.
"""

NO_CONTENTS_THIRD_LEVEL_SECTIONS = """# Awesome Deep Things

### Packages

- [First](https://first.example.com/) - does the first thing.
"""

LINK_ONLY_HEADING = """# Awesome Git Addons

## Contents

- [git-extras](#git-extras)

## [git-extras](https://github.com/tj/git-extras)

- [squash](https://github.com/tj/git-extras/blob/master/Commands.md) - squashes commits.
"""

SECOND_LEVEL_SECTIONS_WITH_SUBHEADINGS = """# Awesome Things

## Contents

- [Tools](#tools)

## Tools

### Sub group

- [First](https://first.example.com/) - does the first thing.
"""


def test_third_level_sections_are_read_as_sections() -> None:
    document = parse_readme(THIRD_LEVEL_SECTIONS)

    assert [section.name for section in document.sections] == ["Packages", "Archived"]
    assert [entry.name for entry in document.entries] == ["First", "Second", "Third"]


def test_third_level_sections_work_without_a_contents_section() -> None:
    document = parse_readme(NO_CONTENTS_THIRD_LEVEL_SECTIONS)

    assert [section.name for section in document.sections] == ["Packages"]
    assert [entry.name for entry in document.entries] == ["First"]


def test_link_only_heading_keeps_the_link_text_as_its_name() -> None:
    document = parse_readme(LINK_ONLY_HEADING)

    assert [section.name for section in document.sections] == ["git-extras"]
    assert [entry.name for entry in document.entries] == ["squash"]


def test_second_level_sections_survive_third_level_subheadings() -> None:
    document = parse_readme(SECOND_LEVEL_SECTIONS_WITH_SUBHEADINGS)

    assert [section.name for section in document.sections] == ["Tools"]
    assert [entry.name for entry in document.entries] == ["First"]


PREAMBLE_SUBHEADINGS = """# Awesome CTF

### Contributing

Please read the contribution guidelines first.

### Why?

It saves time.

## Contents

- [Create](#create)
- [Solve](#solve)

## Create

- [First](https://first.example.com/) - does the first thing.

## Solve

- [Second](https://second.example.com/) - does the second thing.
"""


def test_deeper_preamble_headings_do_not_set_the_section_level() -> None:
    document = parse_readme(PREAMBLE_SUBHEADINGS)

    assert [section.name for section in document.sections] == ["Create", "Solve"]
    assert [entry.name for entry in document.entries] == ["First", "Second"]


def test_badge_only_heading_is_not_a_section() -> None:
    text = """# Awesome Things

## Contents

- [Tools](#tools)

## Tools

- [First](https://first.example.com/) - does the first thing.

## ![build](https://img.example.com/badge.svg)

- [Second](https://second.example.com/) - does the second thing.
"""

    document = parse_readme(text)

    assert [section.name for section in document.sections] == ["Tools"]
    assert [entry.name for entry in document.entries] == ["First", "Second"]


def test_a_bullet_two_levels_below_an_entry_is_also_nested_under_it() -> None:
    """A detail bullet can carry its own detail bullets."""
    document = parse_readme(
        "# Awesome X\n\n## Tools\n\n"
        "- [Piped](https://piped.example.com/) - An alternative front end.\n"
        "    - [Lecture Videos](https://videos.example.com/)\n"
        "        - [Spring 2015](https://videos.example.com/2015)\n"
    )
    depths = {entry.name: entry.nested_under_entry for entry in document.entries}

    assert depths["Lecture Videos"] is True
    assert depths["Spring 2015"] is True
