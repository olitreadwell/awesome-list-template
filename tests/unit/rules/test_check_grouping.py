"""Grouping: empty groups, empty sections, nesting that is too deep."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_grouping import check_grouping


def test_clean_list_has_no_grouping_problems(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    assert check_grouping(document) == ()


def test_flags_empty_group(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-grouping.md"))
    messages = [violation.message for violation in check_grouping(document)]

    assert any("Empty Group Name has no entries" in message for message in messages)


def test_flags_empty_section(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-grouping.md"))
    messages = [violation.message for violation in check_grouping(document)]

    assert any("Empty Section has no entries" in message for message in messages)


def test_flags_entry_nested_under_an_entry(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("dirty-grouping.md"))
    messages = [violation.message for violation in check_grouping(document)]

    assert any("nested under an entry" in message for message in messages)


def test_flags_entry_nested_too_deep(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-grouping.md"))
    messages = [violation.message for violation in check_grouping(document)]

    assert any("nested too deep" in message for message in messages)
