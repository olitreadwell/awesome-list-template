"""The submission checks decide from files on disk, and never the network."""

from __future__ import annotations

from pathlib import Path

from awesome_list.config.load_list_config import load_list_config
from awesome_list.parse.parse_readme import parse_readme
from awesome_list.submission.check_submission import (
    SubmissionFinding,
    check_submission,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "readme"


def _findings(root: Path, text: str) -> dict[str, SubmissionFinding]:
    config = load_list_config(FIXTURES / "awesome.toml")
    return {
        finding.name: finding
        for finding in check_submission(parse_readme(text), text, root, config)
    }


def test_the_fixture_fails_only_the_checks_it_should(tmp_path: Path) -> None:
    text = (FIXTURES / "clean.md").read_text(encoding="utf-8")

    findings = _findings(tmp_path, text)

    assert findings["awesome badge"].ok is True
    assert findings["no CI badge"].ok is True
    assert findings["one h1"].ok is True
    assert findings["contents section"].ok is True
    assert findings["contributing"].ok is False
    assert findings["license"].ok is False


def test_missing_contributing_and_license_are_named(tmp_path: Path) -> None:
    (tmp_path / "contributing.md").write_text("hi", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("mit", encoding="utf-8")
    text = (FIXTURES / "clean.md").read_text(encoding="utf-8")

    findings = _findings(tmp_path, text)

    assert findings["contributing"].ok is True
    assert findings["license"].ok is True


def test_a_ci_badge_and_a_second_h1_are_both_caught(tmp_path: Path) -> None:
    text = (
        "# Awesome Example\n\n"
        "![build](https://github.com/x/y/actions/workflow/status.svg)\n\n"
        "## Contents\n\n## One\n\n## Two\n"
    )

    findings = _findings(tmp_path, text)

    assert findings["no CI badge"].ok is False
    assert findings["one h1"].ok is True
    assert findings["one h1"].detail == "1 top level heading(s)"


def test_a_missing_configured_section_is_reported(tmp_path: Path) -> None:
    text = "# Awesome Example\n\n## Contents\n\n## Start here\n"

    findings = _findings(tmp_path, text)

    assert findings["config sections"].ok is False
    assert "Tools" in findings["config sections"].detail
