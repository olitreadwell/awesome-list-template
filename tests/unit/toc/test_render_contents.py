"""Rendering the Contents section, including nested headings."""

from __future__ import annotations

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.toc.render_contents import render_contents

WITH_SUBHEADINGS = """\
# Awesome Nested [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> Nested headings.

## Contents

- [Tools](#tools)
- [Data](#data)

## Tools

- [A](https://a.example.com/) - ▦ Data - ○ Open - a tool.

### Sub Tools

- [B](https://b.example.com/) - ▦ Data - ○ Open - a sub tool.

## Data

- [C](https://c.example.com/) - ▦ Data - ○ Open - data.

## Footnotes

- Notes that stay out of the table of contents.
"""


def test_nested_headings_are_indented_one_level() -> None:
    lines = render_contents(parse_readme(WITH_SUBHEADINGS))

    assert lines == (
        "- [Tools](#tools)",
        "  - [Sub Tools](#sub-tools)",
        "- [Data](#data)",
    )


def test_denied_sections_and_their_children_are_skipped() -> None:
    lines = render_contents(parse_readme(WITH_SUBHEADINGS))

    assert all("Footnotes" not in line for line in lines)
    assert all("Contents" not in line for line in lines)


def test_repeated_headings_get_suffixes() -> None:
    text = WITH_SUBHEADINGS.replace("## Data", "## Tools")
    lines = render_contents(parse_readme(text))

    assert "- [Tools](#tools)" in lines
    assert "- [Tools](#tools-1)" in lines


def test_headings_below_level_three_are_skipped() -> None:
    text = WITH_SUBHEADINGS.replace("### Sub Tools", "#### Sub Sub Tools")
    lines = render_contents(parse_readme(text))

    assert all("Sub Sub Tools" not in line for line in lines)
