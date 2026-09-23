"""A bullet that is only a URL is not an entry."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_bare_urls import check_bare_urls


def test_clean_list_has_no_bare_urls(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    assert check_bare_urls(document) == ()


def test_flags_a_url_only_bullet(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-bare-urls.md"))
    violations = check_bare_urls(document)

    assert [violation.rule for violation in violations] == ["bare-url"]
    assert "https://bare.example.com/" in violations[0].message
    assert "write the entry as" in violations[0].fix


def test_prose_pointers_are_not_flagged(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("dirty-bare-urls.md"))

    assert len(check_bare_urls(document)) == 1
