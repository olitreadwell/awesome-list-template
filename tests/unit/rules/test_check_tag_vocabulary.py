"""Tags must come from the configured vocabulary."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_tag_vocabulary import check_tag_vocabulary
from awesome_list.tags import DEFAULT_TAG_VOCABULARY


def tagged(fixture_readme: Callable[[str], str]) -> dict[str, list[str]]:
    document = parse_readme(fixture_readme("dirty-tags.md"))
    return {
        entry.name: [
            violation.message
            for violation in check_tag_vocabulary(entry, DEFAULT_TAG_VOCABULARY)
        ]
        for entry in document.entries
    }


def test_clean_entries_pass(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    for entry in document.entries:
        assert check_tag_vocabulary(entry, DEFAULT_TAG_VOCABULARY) == ()


def test_flags_missing_type_and_access(fixture_readme: Callable[[str], str]) -> None:
    found = tagged(fixture_readme)

    assert any("missing a type tag" in message for message in found["No Tags"])
    assert any("missing an access tag" in message for message in found["No Tags"])


def test_flags_unknown_label(fixture_readme: Callable[[str], str]) -> None:
    found = tagged(fixture_readme)

    assert any(
        "unknown type tag: Database" in message for message in found["Unknown Tag"]
    )


def test_flags_repeated_axis(fixture_readme: Callable[[str], str]) -> None:
    found = tagged(fixture_readme)

    assert any(
        "more than one type tag" in message for message in found["Duplicate Axis"]
    )
