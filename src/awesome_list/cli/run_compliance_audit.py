"""make compliance-audit: read the repo settings and report drift."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.repo.audit_repo_settings import RepoSettings, audit_repo_settings
from awesome_list.repo.github_repo_settings import fetch_repo_settings

Fetcher = Callable[[str], dict[str, Any]]


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Report repository settings that drifted from the guidelines."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument(
        "--slug", default=None, help="owner/name, defaults to repo_slug"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="print the drift and exit zero, for a list not ready to enforce yet",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    fetch: Fetcher | None = None,
) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        config = load_list_config(Path(args.config))
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error

    slug = args.slug or config.repo_slug
    raw = (fetch or fetch_repo_settings)(slug)
    settings = RepoSettings(
        slug=slug,
        description=str(raw.get("description") or ""),
        topics=_string_tuple(raw.get("topics")),
        default_branch=str(raw.get("default_branch") or ""),
        archived=bool(raw.get("archived")),
        has_issues=bool(raw.get("has_issues", True)),
        license_name=_optional_str(raw.get("license")),
    )
    result = audit_repo_settings(settings)

    for finding in result.findings:
        mark = "ok  " if finding.ok else "drift"
        print(f"{mark} {finding.name}: {finding.detail}")
        if not finding.ok and finding.fix:
            print(f"     fix: {finding.fix}")

    if not result.drift:
        print(f"compliance-audit: {slug} matches the guidelines")
        return 0
    print(f"compliance-audit: {len(result.drift)} setting(s) drifted")
    return 0 if args.report_only else 1


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, str))


if __name__ == "__main__":
    sys.exit(main())
