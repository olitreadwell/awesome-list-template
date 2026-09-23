"""Rewriting the Contents section must be surgical and idempotent."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.toc.sync_contents import sync_contents


def test_clean_readme_is_unchanged(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("clean.md")
    updated, changed = sync_contents(text, parse_readme(text))

    assert changed is False
    assert updated == text


def test_stale_readme_is_repaired(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    updated, changed = sync_contents(text, parse_readme(text))

    assert changed is True
    assert "- [Data](#data)" in updated
    assert "- [Gone](#gone)" not in updated
    assert "- [Tools](#tools)" in updated


def test_repair_touches_only_the_toc(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    updated, _ = sync_contents(text, parse_readme(text))
    before = [line for line in text.splitlines() if not line.startswith("- [")]
    after = [line for line in updated.splitlines() if not line.startswith("- [")]

    assert before == after


def test_repair_is_idempotent(fixture_readme: Callable[[str], str]) -> None:
    text = fixture_readme("dirty-toc.md")
    once, _ = sync_contents(text, parse_readme(text))
    twice, changed = sync_contents(once, parse_readme(once))

    assert changed is False
    assert twice == once
