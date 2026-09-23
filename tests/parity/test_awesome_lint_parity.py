"""Parity with awesome-lint, run as a subprocess so the linter stays the authority.

The template repo is not an awesome list, so the fixture readme is linted inside a
scratch repository. awesome-lint's GitHub rule reads repository metadata, which
says nothing about list content, so those messages are tolerated; everything else
must agree with our rules.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINTER = REPO_ROOT / "tools" / "node_modules" / ".bin" / "awesome-lint"
SCRATCH = REPO_ROOT / "ci" / "awesome-lint-fixture.sh"
ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

pytestmark = pytest.mark.skipif(
    not (LINTER.exists() and SCRATCH.exists()),
    reason="awesome-lint is not installed; run: cd tools && npm ci",
)


def lint(fixture: str) -> tuple[int, str]:
    result = subprocess.run(
        [str(SCRATCH), "--fixture", str(REPO_ROOT / "tests/fixtures/readme" / fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, ANSI.sub("", result.stdout + result.stderr)


def test_clean_fixture_passes_awesome_lint() -> None:
    code, output = lint("clean.md")

    assert code == 0, output


def test_dirty_fixture_is_caught_by_awesome_lint() -> None:
    code, output = lint("dirty-grammar.md")

    assert code == 1
    assert "separated with a dash" in output
    assert "start with valid casing" in output
    assert "end with proper punctuation" in output


def test_our_rules_cover_every_list_item_the_linter_flags() -> None:
    """Every line awesome-lint flags as a list item must also be an error for us."""
    from awesome_list.parse.parse_readme import parse_readme
    from awesome_list.rules.run_rules import run_rules
    from awesome_list.tags import DEFAULT_TAG_VOCABULARY

    text = (REPO_ROOT / "tests/fixtures/readme" / "dirty-grammar.md").read_text(
        encoding="utf-8"
    )
    our_lines = {
        violation.line
        for violation in run_rules(parse_readme(text), text, DEFAULT_TAG_VOCABULARY)
        if violation.severity == "error"
    }
    _, output = lint("dirty-grammar.md")
    linted_lines = {
        int(match.group(1)) for match in re.finditer(r"(\d+):\d+\s+List item", output)
    }

    assert linted_lines <= our_lines
