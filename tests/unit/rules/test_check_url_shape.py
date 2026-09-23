"""URL shape: relative, fragment, script, tracking parameters, plain http."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_url_shape import check_url_shape
from awesome_list.rules.rule_violation import RuleViolation


def shaped(
    fixture_readme: Callable[[str], str],
) -> dict[str, tuple[RuleViolation, ...]]:
    document = parse_readme(fixture_readme("dirty-urls.md"))
    return {entry.name: check_url_shape(entry) for entry in document.entries}


def messages(fixture_readme: Callable[[str], str]) -> dict[str, list[str]]:
    return {
        name: [violation.message for violation in violations]
        for name, violations in shaped(fixture_readme).items()
    }


def test_clean_entries_pass(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    for entry in document.entries:
        assert check_url_shape(entry) == ()


def test_flags_relative_url(fixture_readme: Callable[[str], str]) -> None:
    assert "relative" in messages(fixture_readme)["Relative"][0]


def test_flags_relative_file_url(fixture_readme: Callable[[str], str]) -> None:
    assert "relative URL" in messages(fixture_readme)["Fragment"][0]


def test_flags_fragment_only_url(fixture_readme: Callable[[str], str]) -> None:
    assert "in-page fragment" in messages(fixture_readme)["In Page"][0]


def test_flags_non_http_scheme(fixture_readme: Callable[[str], str]) -> None:
    assert "javascript" in messages(fixture_readme)["Script"][0]


def test_flags_tracking_parameter(fixture_readme: Callable[[str], str]) -> None:
    assert "utm_source" in messages(fixture_readme)["Tracked"][0]


def test_flags_plain_http(fixture_readme: Callable[[str], str]) -> None:
    violation = shaped(fixture_readme)["Plain HTTP"][0]

    assert "plain http" in violation.message
    assert "https" in violation.fix


def test_ordinary_entry_passes(fixture_readme: Callable[[str], str]) -> None:
    assert shaped(fixture_readme)["Fine"] == ()
