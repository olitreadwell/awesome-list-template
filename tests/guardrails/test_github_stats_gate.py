"""Guardrail: the stats gate is local, offline, and writes only where it may."""

from __future__ import annotations

from pathlib import Path

WRITE_CALL = "readme_path.write_text"


def test_only_toc_and_stats_commands_write_the_readme(repo_root: Path) -> None:
    cli_dir = repo_root / "src" / "awesome_list" / "cli"
    writers = {
        path.name
        for path in sorted(cli_dir.glob("*.py"))
        if WRITE_CALL in path.read_text(encoding="utf-8")
    }

    assert writers == {"run_toc.py", "run_stats.py"}


def test_stats_check_runs_in_the_gate(repo_root: Path) -> None:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    check_line = next(
        line for line in makefile.splitlines() if line.startswith("check:")
    )

    assert "stats-check" in check_line


def test_stats_check_never_calls_the_network(repo_root: Path) -> None:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    target = makefile.split("stats-check:", 1)[1].split("\n\n", 1)[0]

    assert "--check" in target
    assert "gh " not in target


def test_network_calls_live_in_one_module(repo_root: Path) -> None:
    src = repo_root / "src" / "awesome_list"
    callers = {
        path.relative_to(src).as_posix()
        for path in sorted(src.rglob("*.py"))
        if "subprocess" in path.read_text(encoding="utf-8")
    }

    assert callers == {"cli/run_hooks_install.py", "github/fetch_repo_stats.py"}
