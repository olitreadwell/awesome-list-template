"""links.allowlist records the exceptions a list has decided to live with."""

from __future__ import annotations

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.check_duplicate_urls import check_duplicate_urls
from awesome_list.rules.check_url_shape import check_url_shape
from awesome_list.rules.run_rules import run_rules
from awesome_list.tags import TagVocabulary

PLAIN_HTTP_ONLY = """# Awesome Example

## Contents

- [Tools](#tools)

## Tools

- [Old Blog](http://http-only.example.com/) - the site has no working https.
- [Other](https://other.example.com/) - a normal entry.
"""

DUPLICATED = """# Awesome Example

## Contents

- [Tools](#tools)

## Tools

- [One](https://same.example.com/) - the first one.
- [Two](https://same.example.com/) - the same URL on purpose.
"""


def test_a_plain_http_url_is_flagged_by_default() -> None:
    entry = parse_readme(PLAIN_HTTP_ONLY).entries[0]

    assert [v.rule for v in check_url_shape(entry)] == ["url-shape"]


def test_an_allowlisted_url_is_skipped_entirely() -> None:
    entry = parse_readme(PLAIN_HTTP_ONLY).entries[0]

    assert check_url_shape(entry, frozenset({"http://http-only.example.com/"})) == ()


def test_run_rules_honours_the_allowlist() -> None:
    document = parse_readme(PLAIN_HTTP_ONLY, vocabulary=TagVocabulary())

    without = run_rules(document, PLAIN_HTTP_ONLY, TagVocabulary())
    with_allowlist = run_rules(
        document,
        PLAIN_HTTP_ONLY,
        TagVocabulary(),
        allowed_urls=("http://http-only.example.com/",),
    )

    assert "url-shape" in {v.rule for v in without}
    assert "url-shape" not in {v.rule for v in with_allowlist}


def test_a_duplicate_is_flagged_by_default() -> None:
    document = parse_readme(DUPLICATED)

    assert [v.rule for v in check_duplicate_urls(document)] == ["duplicate-urls"]


def test_an_allowlisted_url_may_repeat() -> None:
    document = parse_readme(DUPLICATED)

    assert (
        check_duplicate_urls(document, frozenset({"https://same.example.com/"})) == ()
    )
