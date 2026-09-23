"""make export: write data.json, data.ndjson, and data.csv from the readme."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import cast

from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.export.build_exports import (
    build_export,
    to_csv,
    to_json,
    to_ndjson,
)
from awesome_list.parse.parse_readme import parse_readme

FILES = ("data.json", "data.ndjson", "data.csv")


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Write the list as JSON, NDJSON, and CSV."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument("--out", default="exports", help="directory to write into")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the files on disk are out of date, without writing",
    )
    parser.add_argument("--today", default=None, help="override the date, for tests")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        config = load_list_config(Path(args.config))
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error

    root = config.source_path.parent
    readme_path = Path(args.readme) if args.readme else root / config.readme
    document = parse_readme(readme_path.read_text(encoding="utf-8"))
    generated_at = args.today or date.today().isoformat()
    data = build_export(document, config, generated_at=generated_at)
    rendered = {
        "data.json": to_json(data),
        "data.ndjson": to_ndjson(data),
        "data.csv": to_csv(data),
    }

    out_dir = Path(args.out)

    stale = [
        name
        for name, text in rendered.items()
        if not _is_current(out_dir / name, name, text)
    ]

    if args.check:
        if stale:
            print(f"export-check: {', '.join(stale)} out of date; run make export")
            return 1
        print(f"export-check: {len(FILES)} files are up to date")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in rendered.items():
        (out_dir / name).write_text(text, encoding="utf-8")
    print(f"{out_dir}: {len(FILES)} files, {len(document.entries)} entries")
    return 0


def _is_current(path: Path, name: str, wanted: str) -> bool:
    """Whether the file on disk already holds this content.

    data.json carries the date it was generated, which changes every day, so
    the check compares everything except that field. Otherwise the gate would
    go red every morning for no reason.
    """
    if not path.exists():
        return False
    current = path.read_text(encoding="utf-8")
    if name.endswith(".json"):
        return _without_timestamp(current) == _without_timestamp(wanted)
    return current == wanted


def _without_timestamp(text: str) -> dict[str, object]:
    data = cast("dict[str, object]", json.loads(text))
    data.pop("generated_at", None)
    return data


if __name__ == "__main__":
    sys.exit(main())
