"""A readme with no Contents section gets one, in the right place."""

from __future__ import annotations

from awesome_list.parse.parse_readme import parse_readme
from awesome_list.toc.sync_contents import sync_contents

WITHOUT_TOC = """\
# Awesome Missing [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A list that forgot its table of contents.

## Tools

- [A](https://a.example.com/) - ▦ Data - ○ Open - a tool.
"""


def test_inserts_contents_after_the_tagline() -> None:
    updated, changed = sync_contents(WITHOUT_TOC, parse_readme(WITHOUT_TOC))

    assert changed is True
    assert updated.startswith(
        "# Awesome Missing [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)\n"
        "\n"
        "> A list that forgot its table of contents.\n"
        "\n"
        "## Contents\n"
        "\n"
        "- [Tools](#tools)\n"
    )


def test_inserted_toc_is_then_stable() -> None:
    once, _ = sync_contents(WITHOUT_TOC, parse_readme(WITHOUT_TOC))
    twice, changed = sync_contents(once, parse_readme(once))

    assert changed is False
    assert twice == once
