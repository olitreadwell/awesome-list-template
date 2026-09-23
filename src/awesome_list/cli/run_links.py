"""make links and make links-diff: lychee over the list, or over a branch's URLs."""

from __future__ import annotations

import argparse
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.links.added_urls import added_urls
from awesome_list.links.lychee_config import render_lychee_config
from awesome_list.links.run_lychee import git_show as default_git_show
from awesome_list.links.run_lychee import lychee_binary, run_lychee

Runner = Callable[[Sequence[str]], int]


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Check every link in the list with lychee."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="check only the URLs this branch adds, not the whole list",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="the ref a --diff run compares against; by default the first of"
        " origin/HEAD, origin/main, origin/master, and HEAD that resolves",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="print the lychee config and exit, without running lychee",
    )
    parser.add_argument("--lychee", default=None, help="path to the lychee binary")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    run: Runner | None = None,
    git_show: Callable[[str], str] | None = None,
) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    try:
        config = load_list_config(config_path)
    except ListConfigError as error:
        raise SystemExit(f"awesome.toml: {error}") from error

    lychee_config = render_lychee_config(config)
    if args.print_config:
        print(lychee_config, end="")
        return 0

    root = config.source_path.parent
    readme_path = Path(args.readme) if args.readme else root / config.readme

    if args.diff:
        show = git_show or default_git_show
        relative = _repo_relative(readme_path, root)
        base_text = _base_text(show, args.base_ref, relative)
        targets = list(added_urls(readme_path.read_text(encoding="utf-8"), base_text))
        if not targets:
            print("links-diff: no new URLs in this branch")
            return 0
        print(f"links-diff: {len(targets)} new URLs")
    else:
        targets = [str(readme_path)]

    with tempfile.TemporaryDirectory() as directory:
        config_file = Path(directory) / "lychee.toml"
        config_file.write_text(lychee_config, encoding="utf-8")
        command = [
            args.lychee or lychee_binary(),
            "--config",
            str(config_file),
            *targets,
        ]
        runner = run or run_lychee
        return runner(command)


def _repo_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


BASE_REF_CANDIDATES = ("origin/HEAD", "origin/main", "origin/master", "HEAD")


def _base_text(show: Callable[[str], str], explicit: str | None, relative: str) -> str:
    """Return the base version of the readme.

    An explicit --base-ref is used as given, so a typo is reported rather than
    quietly swapped for another ref. Otherwise the first candidate git can read
    wins, because a fresh clone often has no origin/HEAD.
    """
    if explicit is not None:
        return show(f"{explicit}:{relative}")
    errors: list[str] = []
    for candidate in BASE_REF_CANDIDATES:
        try:
            return show(f"{candidate}:{relative}")
        except SystemExit as error:
            errors.append(str(error))
    raise SystemExit(
        "links-diff: cannot read the readme out of git; pass --base-ref.\n"
        + "\n".join(errors)
    )


if __name__ == "__main__":
    sys.exit(main())
