"""make toc and make toc-check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from awesome_list.config.load_list_config import load_list_config
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.rules.render_violations import render_violations
from awesome_list.rules.run_rules import run_rules
from awesome_list.tags import DEFAULT_TAG_VOCABULARY, TagVocabulary
from awesome_list.toc.sync_contents import sync_contents


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser."""
    parser = argparse.ArgumentParser(description="Regenerate the Contents section.")
    parser.add_argument("--readme", default=None, help="path to the readme")
    parser.add_argument("--config", default="awesome.toml", help="path to awesome.toml")
    parser.add_argument("--check", action="store_true", help="fail instead of writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and return a process exit code."""
    args = build_parser().parse_args(argv)
    readme_path = _readme_path(args.readme, args.config)
    text = readme_path.read_text(encoding="utf-8")
    document = parse_readme(text)
    updated, changed = sync_contents(text, document)

    if not changed:
        print(f"{readme_path}: Contents section is current")
        return 0

    if args.check:
        violations = run_rules(
            document, text, _vocabulary(args.config), file=str(readme_path)
        )
        toc = tuple(v for v in violations if v.rule == "toc-freshness")
        report = (
            render_violations(toc) or "run make toc to regenerate the Contents section"
        )
        print(f"{readme_path}: Contents section is stale")
        print(report)
        return 1

    readme_path.write_text(updated, encoding="utf-8")
    print(f"{readme_path}: Contents section updated")
    return 0


def _readme_path(explicit: str | None, config_path: str) -> Path:
    if explicit:
        return Path(explicit)
    config_file = Path(config_path)
    if config_file.exists():
        config = load_list_config(config_file)
        return config.source_path.parent / config.readme
    return Path("readme.md")


def _vocabulary(config_path: str) -> TagVocabulary:
    config_file = Path(config_path)
    if config_file.exists():
        return load_list_config(config_file).tags
    return DEFAULT_TAG_VOCABULARY


if __name__ == "__main__":
    sys.exit(main())
