"""Duplicate detection, including near duplicates."""

from __future__ import annotations

from collections.abc import Callable

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_duplicate_urls import check_duplicate_urls
from awesome_list.rules.normalize_url import normalize_url


def test_clean_list_has_no_duplicates(fixture_readme: Callable[[str], str]) -> None:
    document = parse_readme(fixture_readme("clean.md"))

    assert check_duplicate_urls(document) == ()


def test_flags_www_and_trailing_slash_variants(
    fixture_readme: Callable[[str], str],
) -> None:
    document = parse_readme(fixture_readme("dirty-duplicates.md"))
    violations = check_duplicate_urls(document)

    assert len(violations) == 1
    assert violations[0].rule == "duplicate-urls"
    assert "Second" in violations[0].message
    assert "First" in violations[0].message


def test_normalize_url_collapses_known_variants() -> None:
    assert normalize_url("https://www.Example.com/Path/") == "https://example.com/path"
    assert (
        normalize_url("https://example.com/path#section") == "https://example.com/path"
    )
    assert (
        normalize_url("https://example.com/path?utm_source=x&b=1")
        == "https://example.com/path?b=1"
    )


def test_detail_bullets_can_repeat_a_url_when_the_list_opts_in(
    fixture_readme: Callable[[str], str],
) -> None:
    """The same example link under two entries is not two entries."""
    text = fixture_readme("dirty-nested-details.md").replace(
        "    - Official instance: [piped.video](https://piped.video)\n",
        "    - Official instance: [piped.video](https://piped.video)\n"
        "    - Example: [piped.video](https://piped.video)\n",
    )
    document = parse_readme(text)

    assert check_duplicate_urls(document)
    assert check_duplicate_urls(document, skip_details=True) == ()
