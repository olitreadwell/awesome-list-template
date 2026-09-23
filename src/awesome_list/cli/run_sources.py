"""make sources: propose entries from upstream lists, and write none of them."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from awesome_list.config.list_config import ListConfig
from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.github.github_stats import RepoStats
from awesome_list.github.stats_snapshot import SnapshotError, load_stats_snapshot
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.sources.fetch_source_readme import fetch_source_readmes
from awesome_list.sources.parse_table_entries import SourceEntry, parse_table_entries
from awesome_list.sources.propose_source_entries import (
    propose_source_entries,
    render_source_report,
)

Fetcher = Callable[..., tuple[dict[str, str], tuple[str, ...]]]


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Report entries an upstream list has that this one might want."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument(
        "--source",
        action="append",
        default=None,
        help="upstream readme URL, repeatable; defaults to the [sources] config",
    )
    parser.add_argument("--out", default=None, help="where to write the report")
    parser.add_argument(
        "--stdout", action="store_true", help="print the report instead of writing it"
    )
    return parser


def main(
    argv: list[str] | None = None, *, fetch: Fetcher = fetch_source_readmes
) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    config = _load_config(Path(args.config))
    readme_path = (
        Path(args.readme) if args.readme else config.source_path.parent / config.readme
    )
    document = parse_readme(readme_path.read_text(encoding="utf-8"))
    urls = tuple(args.source) if args.source else config.sources.lists

    if not urls:
        print("sources: no upstream lists configured, nothing to do")
        return 0

    readmes, unread = fetch(urls)
    for url in unread:
        print(f"sources: could not read {url}", file=sys.stderr)
    if not readmes:
        print(
            "sources: no upstream list could be read, no report written",
            file=sys.stderr,
        )
        return 0

    entries: list[SourceEntry] = []
    for readme in readmes.values():
        entries.extend(parse_table_entries(readme))

    candidates = propose_source_entries(
        document, entries, config.sources.keywords, stats=_stats(config)
    )
    report = render_source_report(candidates, sources=tuple(readmes))

    if args.stdout:
        print(report)
        return 0

    out_path = (
        Path(args.out)
        if args.out
        else config.source_path.parent / config.sources.report
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"{out_path}: {len(candidates)} candidates from {len(readmes)} lists")
    return 0


def _load_config(path: Path) -> ListConfig:
    try:
        return load_list_config(path)
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error


def _stats(config: ListConfig) -> dict[str, RepoStats]:
    path = config.source_path.parent / config.github.snapshot
    try:
        snapshot = load_stats_snapshot(path)
    except SnapshotError as error:
        raise SystemExit(f"github stats: {error}") from error
    return dict(snapshot.repos) if snapshot else {}


if __name__ == "__main__":
    sys.exit(main())
