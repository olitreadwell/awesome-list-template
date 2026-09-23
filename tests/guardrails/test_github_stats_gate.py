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


def test_the_sources_report_is_never_a_readme_write(repo_root: Path) -> None:
    cli = (repo_root / "src" / "awesome_list" / "cli" / "run_sources.py").read_text(
        encoding="utf-8"
    )

    assert "readme" in cli
    assert "out_path.write_text" in cli
    assert "readme_path.write_text" not in cli


# Every module allowed to shell out, and why. Adding one here is a deliberate
# act: it is the list a reader checks to find every place the engine leaves the
# process.
SHELL_OUT_ALLOWED = {
    "cli/run_hooks_install.py",  # git config core.hooksPath
    "github/fetch_repo_stats.py",  # gh api repos/{slug}
    "links/run_lychee.py",  # lychee over the readme, and git show for --diff
    "repo/github_repo_settings.py",  # gh api for topics and description
}


def test_subprocess_use_is_confined_to_the_modules_that_say_so(
    repo_root: Path,
) -> None:
    src = repo_root / "src" / "awesome_list"
    callers = {
        path.relative_to(src).as_posix()
        for path in sorted(src.rglob("*.py"))
        if "subprocess" in path.read_text(encoding="utf-8")
    }

    assert callers == SHELL_OUT_ALLOWED
