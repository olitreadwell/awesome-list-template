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
