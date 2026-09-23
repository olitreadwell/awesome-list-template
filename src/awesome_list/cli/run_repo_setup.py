"""make repo-setup: put the topics, description, and default branch right."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.repo.github_repo_settings import origin_remote, run_gh

DEFAULT_TOPICS = ("awesome", "awesome-list", "curated-list")
DEFAULT_BRANCH = "main"

Runner = Callable[[Sequence[str]], str]


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Set the GitHub topics, description, and default branch."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument(
        "--slug", default=None, help="owner/name, defaults to the origin remote"
    )
    parser.add_argument(
        "--description", default=None, help="defaults to the readme tagline"
    )
    parser.add_argument(
        "--topic",
        action="append",
        default=None,
        help=(
            "a topic to set; repeat it. Defaults to awesome, awesome-list, curated-list"
        ),
    )
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="the default branch")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="run the commands; without it the command only prints them",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner | None = None,
    remote: Callable[[], str] | None = None,
) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        config = load_list_config(Path(args.config))
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error

    root = config.source_path.parent
    slug = args.slug or (remote or origin_remote)()
    description = args.description or _tagline(root / config.readme)
    topics = tuple(args.topic) if args.topic else DEFAULT_TOPICS
    commands = _commands(slug, description, topics, args.branch)

    if not args.apply:
        print("repo-setup: dry run, pass --apply to run these")
        for command in commands:
            print("  " + " ".join(command))
        return 0

    run = runner or run_gh
    for command in commands:
        print(run(command))
    return 0


def _commands(
    slug: str, description: str, topics: tuple[str, ...], branch: str
) -> tuple[tuple[str, ...], ...]:
    repository = f"repos/{slug}"
    return (
        (
            "gh",
            "api",
            "-X",
            "PATCH",
            repository,
            "-f",
            f"description={description}",
        ),
        (
            "gh",
            "api",
            "-X",
            "PUT",
            f"{repository}/topics",
            "-H",
            "Accept: application/vnd.github+json",
            *(f"-f names[]={topic}" for topic in topics),
        ),
        (
            "gh",
            "api",
            "-X",
            "PATCH",
            repository,
            "-f",
            f"default_branch={branch}",
        ),
    )


def _tagline(readme_path: Path) -> str:
    return parse_readme(readme_path.read_text(encoding="utf-8")).tagline


if __name__ == "__main__":
    sys.exit(main())
