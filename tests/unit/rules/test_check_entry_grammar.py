"""Entry grammar: the dash, the capital, the trailing period."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.parse.readme_model import ListEntry
from awesome_list.rules.check_entry_grammar import check_entry_grammar
from awesome_list.rules.rule_violation import RuleViolation


def violations_by_name(
    fixture_readme: Callable[[str], str],
) -> dict[str, tuple[RuleViolation, ...]]:
    document = parse_readme(fixture_readme("dirty-grammar.md"))
    return {entry.name: check_entry_grammar(entry) for entry in document.entries}


def messages_by_name(fixture_readme: Callable[[str], str]) -> dict[str, list[str]]:
    return {
        name: [violation.message for violation in violations]
        for name, violations in violations_by_name(fixture_readme).items()
    }


def test_clean_entries_pass(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    for entry in document.entries:
        assert check_entry_grammar(entry) == ()


def test_flags_missing_separator(fixture_readme: Callable[[str], str]) -> None:
    violation = violations_by_name(fixture_readme)["No Separator"][0]

    assert violation.rule == "entry-grammar"
    assert "separate the link and the description" in violation.message


def test_flags_lowercase_description(fixture_readme: Callable[[str], str]) -> None:
    violation = violations_by_name(fixture_readme)["Lowercase Start"][0]

    assert "lowercase letter" in violation.message
    assert "capital letter" in violation.fix


def test_flags_missing_period(fixture_readme: Callable[[str], str]) -> None:
    found = messages_by_name(fixture_readme)

    assert any(
        "end the description with a period" in message for message in found["No Period"]
    )


def test_flags_trailing_whitespace(fixture_readme: Callable[[str], str]) -> None:
    found = messages_by_name(fixture_readme)

    assert any("trailing whitespace" in message for message in found["Trailing Space"])


def test_tags_with_no_description_is_an_error(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("dirty-grammar.md"))
    entry = next(item for item in document.entries if item.name == "No Description")
    violations = check_entry_grammar(entry)

    assert [violation.severity for violation in violations] == ["error"]
    assert "has tags but no description" in violations[0].message


def test_bare_link_with_no_description_only_warns() -> None:
    entry = ListEntry(
        name="Bare",
        url="https://bare.example.com/",
        description="",
        tags=(),
        line=3,
        raw="- [Bare](https://bare.example.com/)",
    )
    violations = check_entry_grammar(entry)

    assert [violation.severity for violation in violations] == ["warn"]
    assert "has no description" in violations[0].message


def test_violation_carries_line_and_fix(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-grammar.md"))
    entry = next(item for item in document.entries if item.name == "No Period")
    violation = check_entry_grammar(entry)[0]

    assert violation.line == entry.line
    assert violation.fix


def test_a_camel_case_first_word_is_not_a_lowercase_start() -> None:
    """jQuery, macOS and iOS are spelled that way on purpose."""
    document = parse_readme(
        "# Awesome X\n\n## Tools\n\n"
        "- [Mapael](https://mapael.example.com/) - jQuery plugin for vector maps.\n"
        "- [Dock](https://dock.example.com/) - macOS launcher.\n"
        "- [Cafe](https://cafe.example.com/) - lowercase start here.\n"
    )
    messages = {
        entry.name: [v.message for v in check_entry_grammar(entry)]
        for entry in document.entries
    }

    assert messages["Mapael"] == []
    assert messages["Dock"] == []
    assert any("lowercase" in m for m in messages["Cafe"])
