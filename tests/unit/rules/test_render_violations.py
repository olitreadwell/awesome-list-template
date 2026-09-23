"""Renderer tests: the terminal and the pull request comment see the same data."""

from __future__ import annotations

from awesome_list.rules.render_violations import render_violations, summarise_violations
from awesome_list.rules.rule_violation import RuleViolation

VIOLATIONS = (
    RuleViolation(
        rule="entry-grammar", line=4, message="A has no description", fix="add one"
    ),
    RuleViolation(
        rule="tag-vocabulary",
        line=9,
        message="B is missing a type tag",
        fix="add a type tag",
        severity="warn",
    ),
)


def test_empty_list_renders_nothing() -> None:
    assert render_violations(()) == ""


def test_text_render_includes_file_line_rule_and_fix() -> None:
    rendered = render_violations(VIOLATIONS)

    assert "readme.md:4: entry-grammar: A has no description Fix: add one" in rendered
    assert rendered.count("\n") == 1


def test_warnings_are_labelled() -> None:
    rendered = render_violations(VIOLATIONS)

    assert "B is missing a type tag (warning)" in rendered


def test_markdown_render_is_a_list() -> None:
    rendered = render_violations(VIOLATIONS, style="markdown")

    assert rendered.startswith("- `readme.md:4:")
    assert rendered.count("- `") == 2


def test_summary_counts_by_rule() -> None:
    assert (
        summarise_violations(VIOLATIONS)
        == "2 violations: entry-grammar 1, tag-vocabulary 1"
    )
    assert summarise_violations(()) == "no violations"
