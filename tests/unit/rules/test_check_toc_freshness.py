"""The Contents section must match the headings exactly."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_toc_freshness import check_toc_freshness


def test_clean_toc_passes(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("clean.md")

    assert check_toc_freshness(parse_readme(text), text) == ()


def test_flags_missing_and_stale_entries(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    messages = [
        violation.message for violation in check_toc_freshness(parse_readme(text), text)
    ]

    assert any(
        "Data is missing from the Contents section" in message for message in messages
    )
    assert any(
        "Gone is in the Contents section but not in the readme" in message
        for message in messages
    )


def test_flags_missing_contents_section(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("clean.md").replace("## Contents", "## Index")
    rendered = [
        violation.render()
        for violation in check_toc_freshness(parse_readme(text), text)
    ]

    assert any(
        "Contents section" in line and "add a Contents section" in line
        for line in rendered
    )


def test_flags_denied_sections_in_toc(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("clean.md").replace(
        "- [Tools](#tools)", "- [Tools](#tools)\n- [Footnotes](#footnotes)"
    )
    messages = [
        violation.message for violation in check_toc_freshness(parse_readme(text), text)
    ]

    assert any("Footnotes must not appear" in message for message in messages)


NESTED = """\
# Awesome Nested [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> Nested headings.

## Contents

- [Tools](#tools)
  - [Sub Tools](#sub-tools)

## Tools

- [A](https://a.example.com/) - ▦ Data - ○ Open - a tool.

### Sub Tools

- [B](https://b.example.com/) - ▦ Data - ○ Open - a sub tool.
"""


def test_a_nested_heading_in_the_contents_is_not_an_extra_line() -> None:
    violations = check_toc_freshness(parse_readme(NESTED), NESTED)

    assert violations == ()


def test_four_space_indentation_is_not_a_depth_problem() -> None:
    """Two spaces and four both render, so neither is wrong on its own."""
    text = NESTED.replace(
        "  - [Sub Tools](#sub-tools)", "        - [Sub Tools](#sub-tools)"
    )

    assert check_toc_freshness(parse_readme(text), text) == ()


def test_a_level_four_heading_in_the_contents_is_reported() -> None:
    text = NESTED.replace("### Sub Tools", "#### Sub Tools")

    messages = [
        violation.message for violation in check_toc_freshness(parse_readme(text), text)
    ]

    assert messages == ["Sub Tools is nested deeper than the Contents section allows"]


def test_a_nested_heading_missing_from_the_contents_is_reported() -> None:
    text = NESTED.replace("  - [Sub Tools](#sub-tools)\n", "")

    violations = check_toc_freshness(parse_readme(text), text)

    assert [violation.message for violation in violations] == [
        "Sub Tools is missing from the Contents section"
    ]
