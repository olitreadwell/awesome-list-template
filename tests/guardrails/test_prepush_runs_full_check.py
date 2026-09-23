"""Guardrail: the pre-push hook is the real gate, not the fast subset."""

from __future__ import annotations

from pathlib import Path


def test_prepush_runs_the_full_check(repo_root: Path) -> None:
    hook = (repo_root / ".githooks" / "pre-push").read_text(encoding="utf-8")

    assert "make check" in hook
    assert "check-fast" not in hook


def test_precommit_runs_the_fast_subset(repo_root: Path) -> None:
    hook = (repo_root / ".githooks" / "pre-commit").read_text(encoding="utf-8")

    assert "make check-fast" in hook


def test_commit_msg_hook_checks_conventional_commits(repo_root: Path) -> None:
    hook = (repo_root / ".githooks" / "commit-msg").read_text(encoding="utf-8")

    assert "feat|fix" in hook


def test_hooks_are_executable(repo_root: Path) -> None:
    for name in ("pre-commit", "pre-push", "commit-msg"):
        assert (repo_root / ".githooks" / name).stat().st_mode & 0o111
