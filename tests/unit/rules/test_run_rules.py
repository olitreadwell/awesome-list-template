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


def test_duplicates_and_toc_are_reported(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    rules = {
        violation.rule
        for violation in run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)
    }

    assert "toc-freshness" in rules
