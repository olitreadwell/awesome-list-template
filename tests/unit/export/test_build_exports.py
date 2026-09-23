"""The three export shapes all come from one document."""

from __future__ import annotations

import json
from pathlib import Path

from awesome_list.config.load_list_config import load_list_config
from awesome_list.export.build_exports import build_export, to_csv, to_json, to_ndjson
from awesome_list.parse.parse_readme import parse_readme

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "readme"


def _data() -> dict[str, object]:
    config = load_list_config(FIXTURES / "awesome.toml")
    document = parse_readme((FIXTURES / "clean.md").read_text(encoding="utf-8"))
    return build_export(document, config, generated_at="2026-09-23")


def test_export_counts_every_entry() -> None:
    data = _data()

    assert data["name"] == "Awesome Example"
    assert data["generated_at"] == "2026-09-23"
    assert data["entry_count"] == 5


def test_json_round_trips() -> None:
    data = _data()

    assert json.loads(to_json(data)) == data


def test_ndjson_has_one_line_per_entry() -> None:
    lines = to_ndjson(_data()).splitlines()

    assert len(lines) == 5
    assert json.loads(lines[0])["url"] == "https://example.govt.nz/"


def test_csv_has_a_header_and_one_row_per_entry() -> None:
    rows = to_csv(_data()).splitlines()

    assert rows[0] == ("section,group,name,url,description,tags,stars,last_push,line")
    assert len(rows) == 6
    assert "Example Portal" in rows[1]
    assert rows[1].startswith("Start here,,")
    assert rows[4].startswith("Tools,Example Group,First Tool,")


def test_tags_are_readable_labels_not_slugs() -> None:
    rows = to_csv(_data()).splitlines()

    assert "Data Open" in rows[1]


def test_the_stats_segment_is_split_out_of_the_description() -> None:
    config = load_list_config(FIXTURES / "awesome.toml")
    line = (
        "- [Tool](https://github.com/example/tool) - does a thing."
        " - \u2605 4,210 stars, last push 2024-05-06."
    )
    readme = (
        "# Awesome Example\n\n## Contents\n\n- [Tools](#tools)\n\n## Tools\n\n"
        + line
        + "\n"
    )
    data = build_export(parse_readme(readme), config, generated_at="2026-09-23")
    entry = data["sections"][0]["entries"][0]  # type: ignore[index]

    assert entry["description"] == "does a thing."
    assert entry["stars"] == 4210
    assert entry["last_push"] == "2024-05-06"


def test_an_entry_without_stats_gets_empty_columns() -> None:
    config = load_list_config(FIXTURES / "awesome.toml")
    readme = """# Awesome Example

## Contents

- [Tools](#tools)

## Tools

- [Tool](https://tool.example.com/) - does a thing.
"""
    data = build_export(parse_readme(readme), config, generated_at="2026-09-23")
    entry = data["sections"][0]["entries"][0]  # type: ignore[index]

    assert entry["stars"] is None
    assert entry["last_push"] is None
