"""make stats and make stats-check: stars and activity on every GitHub link."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

from awesome_list.config.list_config import ListConfig
from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.github.fetch_repo_stats import fetch_repo_stats
from awesome_list.github.github_stats import (
    RepoStats,
    StatsSnapshot,
    apply_github_stats,
    github_repo_slug,
)
from awesome_list.github.stats_snapshot import (
    SnapshotError,
    load_stats_snapshot,
    write_stats_snapshot,
)
from awesome_list.parse.parse_readme import parse_readme

Fetcher = Callable[..., tuple[dict[str, RepoStats], tuple[str, ...]]]


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Fetch stars and last push dates for every GitHub link."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the snapshot or the readme is out of date, without"
        " touching the network",
    )
    parser.add_argument("--today", default=None, help="override the date, for tests")
    return parser


def main(argv: list[str] | None = None, *, fetch: Fetcher = fetch_repo_stats) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    try:
        config = load_list_config(config_path)
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error

    today = date.fromisoformat(args.today) if args.today else date.today()
    readme_path = (
        Path(args.readme) if args.readme else config.source_path.parent / config.readme
    )
    snapshot_path = config.source_path.parent / config.github.snapshot
    text = readme_path.read_text(encoding="utf-8")
    slugs = _linked_slugs(text)
    snapshot = _load_snapshot(snapshot_path)

    if args.check:
        return _check(config, text, slugs, snapshot, snapshot_path, today)

    if not config.github.stats:
        print("stats: github.stats is off in awesome.toml, nothing to do")
        return 0

    if not slugs:
        print(f"{readme_path}: no GitHub entries to look up")
        return 0

    stats, unfetched = fetch(slugs, previous=snapshot.repos if snapshot else None)
    if not stats:
        print(
            "stats: could not reach the GitHub API; the snapshot and the readme"
            " were left alone",
            file=sys.stderr,
        )
        return 0

    for slug in unfetched:
        if slug in stats:
            print(f"stats: kept the previous numbers for {slug}", file=sys.stderr)
        else:
            print(f"stats: no numbers yet for {slug}", file=sys.stderr)

    write_stats_snapshot(
        snapshot_path, StatsSnapshot(generated_at=today.isoformat(), repos=stats)
    )
    updated, changed = apply_github_stats(text, stats)
    if changed:
        readme_path.write_text(updated, encoding="utf-8")

    print(
        f"{readme_path}: {len(stats)} GitHub entries, {changed} stats segments"
        f" updated; wrote {snapshot_path}"
    )
    return 0


def _check(
    config: ListConfig,
    text: str,
    slugs: tuple[str, ...],
    snapshot: StatsSnapshot | None,
    snapshot_path: Path,
    today: date,
) -> int:
    if not config.github.stats:
        print("stats-check: github.stats is off in awesome.toml, nothing to check")
        return 0
    if not slugs:
        print("stats-check: no GitHub entries to check")
        return 0
    if snapshot is None:
        print(f"stats-check: {snapshot_path} does not exist; run make stats")
        return 1

    age = snapshot.age_days(today)
    if age > config.github.max_age_days:
        print(
            f"stats-check: {snapshot_path} is {age} days old, over the"
            f" {config.github.max_age_days} day limit; run make stats"
        )
        return 1

    _updated, changed = apply_github_stats(text, snapshot.repos)
    if changed:
        print(
            f"stats-check: {changed} entries do not show the stats in"
            f" {snapshot_path}; run make stats"
        )
        return 1

    print(f"{snapshot_path}: {len(slugs)} GitHub entries are up to date")
    return 0


def _linked_slugs(text: str) -> tuple[str, ...]:
    """Return the repo slugs this readme links to, in document order."""
    slugs: list[str] = []
    for entry in parse_readme(text).entries:
        slug = github_repo_slug(entry.url)
        if slug and slug not in slugs:
            slugs.append(slug)
    return tuple(slugs)


def _load_snapshot(path: Path) -> StatsSnapshot | None:
    try:
        return load_stats_snapshot(path)
    except SnapshotError as error:
        raise SystemExit(f"github stats: {error}") from error


if __name__ == "__main__":
    sys.exit(main())
