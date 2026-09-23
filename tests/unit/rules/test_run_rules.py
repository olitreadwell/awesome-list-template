"""The rule runner wires every rule together."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.run_rules import run_rules
from awesome_list.tags import DEFAULT_TAG_VOCABULARY


def test_clean_readme_has_no_errors(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("clean.md")
    violations = run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)

    assert [
        violation for violation in violations if violation.severity == "error"
    ] == []


def test_violations_are_sorted_by_line_then_rule(
    fixture_readme: Callable[[str], str],
) -> None:
    text = fixture_readme("dirty-grammar.md")
    violations = run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)

    keys = [(violation.line, violation.rule) for violation in violations]
    assert keys == sorted(keys)


def test_file_is_recorded_on_every_violation(
    fixture_readme: Callable[[str], str],
) -> None:
    text = fixture_readme("dirty-duplicates.md")
    violations = run_rules(
        parse_readme(text), text, DEFAULT_TAG_VOCABULARY, file="LIST.md"
    )

    assert violations
    assert {violation.file for violation in violations} == {"LIST.md"}


def test_grouping_is_only_checked_for_declared_entry_sections(
    fixture_readme: Callable[[str], str],
) -> None:
    text = fixture_readme("dirty-grouping.md")
    without = run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)
    with_sections = run_rules(
        parse_readme(text),
        text,
        DEFAULT_TAG_VOCABULARY,
        entry_sections=("Empty Group", "Empty Section", "Tools"),
    )

    assert not [
        v for v in without if v.rule == "grouping" and "has no entries" in v.message
    ]
    assert [v for v in with_sections if v.rule == "grouping"]


def test_duplicates_and_toc_are_reported(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    rules = {
        violation.rule
        for violation in run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)
    }

    assert "toc-freshness" in rules
