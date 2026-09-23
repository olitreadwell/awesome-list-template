"""Exit codes and writes for make toc and make toc-check."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from awesome_list.cli import run_toc


def write(tmp_path: Path, fixture_readme: Callable[[str], str], name: str) -> Path:
    path = tmp_path / "readme.md"
    path.write_text(fixture_readme(name), encoding="utf-8")
    return path


def test_current_toc_reports_and_exits_zero(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = write(tmp_path, fixture_readme, "clean.md")

    assert (
        run_toc.main(["--readme", str(path), "--config", str(tmp_path / "none.toml")])
        == 0
    )
    assert "is current" in capsys.readouterr().out


def test_stale_toc_is_written(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = write(tmp_path, fixture_readme, "dirty-toc.md")

    assert (
        run_toc.main(["--readme", str(path), "--config", str(tmp_path / "none.toml")])
        == 0
    )
    assert "updated" in capsys.readouterr().out
    assert "- [Data](#data)" in path.read_text(encoding="utf-8")


def test_check_mode_fails_without_writing(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = write(tmp_path, fixture_readme, "dirty-toc.md")
    before = path.read_text(encoding="utf-8")

    code = run_toc.main(
        ["--readme", str(path), "--check", "--config", str(tmp_path / "none.toml")]
    )

    assert code == 1
    assert "is stale" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == before
