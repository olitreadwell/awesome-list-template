"""Guardrail: no check may exist only inside a hosted workflow."""

from __future__ import annotations

from pathlib import Path

REQUIRED_TARGETS = (
    "check",
    "check-fast",
    "list-check",
    "toc-check",
    "stats",
    "stats-check",
    "sources",
    "export",
    "submission-check",
    "compliance-audit",
)


def test_no_installed_workflows(repo_root: Path) -> None:
    workflows = repo_root / ".github" / "workflows"
    installed = sorted(workflows.glob("*.y*ml")) if workflows.exists() else []

    assert installed == []


def test_ci_script_runs_make_check(repo_root: Path) -> None:
    script = (repo_root / "ci" / "check.sh").read_text(encoding="utf-8")

    assert "make check" in script


def test_every_check_has_a_make_target(repo_root: Path) -> None:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    missing = [target for target in REQUIRED_TARGETS if f"\n{target}:" not in makefile]

    assert missing == []
