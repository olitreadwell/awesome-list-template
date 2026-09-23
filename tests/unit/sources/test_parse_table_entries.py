"""Reading a table-shaped awesome list, the shape public-apis uses."""

from __future__ import annotations

from pathlib import Path

from awesome_list.sources.parse_table_entries import parse_table_entries

LIST = Path(__file__).resolve().parents[2] / "fixtures" / "sources" / "table-list.md"


def test_reads_linked_rows_with_their_heading() -> None:
    entries = parse_table_entries(LIST.read_text(encoding="utf-8"))

    assert [entry.name for entry in entries] == [
        "Cat Facts",
        "Dogs",
        "Open Government, New Zealand",
        "Data.gov",
        "UK Police",
    ]
    assert entries[0].url == "https://catfact.ninja/"
    assert entries[0].description == "Random cat facts"
    assert entries[0].section == "Animals"
    assert entries[2].section == "Government"


def test_skips_header_and_separator_rows() -> None:
    entries = parse_table_entries("| API | Description |\n|:---|:---|\n")

    assert entries == ()


def test_skips_rows_without_a_link() -> None:
    entries = parse_table_entries("| just text | description |\n")

    assert entries == ()


def test_drops_markdown_noise_from_text() -> None:
    entries = parse_table_entries(
        "| [UK Police](https://x.test/) | **UK** `Police` _data_ |\n"
    )

    assert entries[0].name == "UK Police"
    assert entries[0].description == "UK Police data"


def test_duplicate_urls_are_read_once() -> None:
    text = (
        "| [One](https://x.test/) | first |\n"
        "| [One again](https://x.test/) | second |\n"
    )

    assert len(parse_table_entries(text)) == 1
