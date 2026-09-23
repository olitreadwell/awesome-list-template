"""links-diff only checks what the branch adds."""

from __future__ import annotations

from awesome_list.links.added_urls import added_urls

BASE = """# Awesome Example

## Contents

- [Tools](#tools)

## Tools

- [Old](https://old.example.com/) - already in the list.
"""


def test_a_new_url_is_reported() -> None:
    new = BASE + "- [New](https://new.example.com/) - added by this branch.\n"

    assert added_urls(new, BASE) == ("https://new.example.com/",)


def test_an_unchanged_list_adds_nothing() -> None:
    assert added_urls(BASE, BASE) == ()


def test_a_removed_url_is_not_reported() -> None:
    new = BASE.replace("- [Old](https://old.example.com/) - already in the list.\n", "")

    assert added_urls(new, BASE) == ()


def test_a_trailing_slash_change_is_not_a_new_url() -> None:
    new = BASE.replace("https://old.example.com/", "https://old.example.com")

    assert added_urls(new, BASE) == ()


def test_http_to_https_is_not_a_new_url() -> None:
    new = BASE.replace("https://old.example.com/", "http://old.example.com")

    assert added_urls(new, BASE) == ()


def test_each_new_url_is_reported_once() -> None:
    new = BASE + (
        "- [New](https://new.example.com/) - added.\n"
        "- [New again](https://new.example.com) - the same link.\n"
    )

    assert added_urls(new, BASE) == ("https://new.example.com/",)
