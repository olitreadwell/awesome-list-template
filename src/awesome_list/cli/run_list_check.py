"""make list-check: every rule, one report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from awesome_list.config.list_config import ListConfig
from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.github.github_stats import StatsSnapshot
from awesome_list.github.stats_snapshot import SnapshotError, load_stats_snapshot
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.render_violations import render_violations, summarise_violations
from awesome_list.rules.run_rules import run_rules
from awesome_list.tags import DEFAULT_TAG_VOCABULARY


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Check a list readme against every rule."
    )
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="print violations and exit zero, for adopting the engine on an"
        " existing list",
    )
    parser.add_argument("--format", choices=("text", "markdown"), default="text")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    readme_path, config = _resolve(args.readme, args.config)
    vocabulary = config.tags if config else DEFAULT_TAG_VOCABULARY
    sections = config.sections if config else ()
    github_enabled = config.github.stats if config else False
    text = readme_path.read_text(encoding="utf-8")
    document = parse_readme(text, vocabulary=vocabulary)
    violations = run_rules(
        document,
        text,
        vocabulary,
        file=str(readme_path),
        entry_sections=sections,
        github_snapshot=_stats_snapshot(config) if github_enabled else None,
        github_stats_enabled=github_enabled,
        github_stats_max_age_days=config.github.max_age_days if config else 14,
    )

    errors = tuple(v for v in violations if v.severity == "error")
    warnings = tuple(v for v in violations if v.severity == "warn")

    if violations:
        print(render_violations(violations, style=args.format))
        print(summarise_violations(violations), file=sys.stderr)
    else:
        print(f"{readme_path}: {len(document.entries)} entries, no violations")

    blocking = errors or (warnings if args.strict else ())
    if blocking and not args.report_only:
        return 1
    return 0


def _resolve(explicit: str | None, config_path: str) -> tuple[Path, ListConfig | None]:
    config_file = Path(config_path)
    if config_file.exists():
        try:
            config = load_list_config(config_file)
        except ListConfigError as error:
            raise SystemExit(f"awesome.toml: {error}") from error
        if explicit:
            return Path(explicit), config
        return config.source_path.parent / config.readme, config
    return Path(explicit or "readme.md"), None


def _stats_snapshot(config: ListConfig | None) -> StatsSnapshot | None:
    if config is None:
        return None
    path = config.source_path.parent / config.github.snapshot
    try:
        return load_stats_snapshot(path)
    except SnapshotError as error:
        raise SystemExit(f"github stats: {error}") from error


if __name__ == "__main__":
    sys.exit(main())
