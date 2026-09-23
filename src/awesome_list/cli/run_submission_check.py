"""make submission-check: the awesome.re requirements a script can decide."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from awesome_list.config.load_list_config import ListConfigError, load_list_config
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.submission.check_submission import (
    MANUAL_REMINDERS,
    SubmissionFinding,
    check_submission,
)


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(
        description="Check the list against the awesome.re submission rules."
    )
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument(
        "--reminders",
        action="store_true",
        help="also print the requirements no script can check",
    )
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
    text = readme_path.read_text(encoding="utf-8")
    findings = check_submission(parse_readme(text), text, root, config)

    for finding in findings:
        print(_line(finding))

    if args.reminders:
        print("\nAlso true, and not checkable here:")
        for reminder in MANUAL_REMINDERS:
            print(f"  - {reminder}")

    failed = [finding for finding in findings if not finding.ok]
    if failed:
        print(f"\nsubmission-check: {len(failed)} of {len(findings)} checks failed")
        return 1
    print(f"\nsubmission-check: {len(findings)} checks passed")
    return 0


def _line(finding: SubmissionFinding) -> str:
    mark = "ok  " if finding.ok else "fail"
    return f"{mark} {finding.name}: {finding.detail}"


if __name__ == "__main__":
    sys.exit(main())
