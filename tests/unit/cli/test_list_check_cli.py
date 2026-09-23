"""Exit codes for make list-check."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from awesome_list.cli import run_list_check

CONFIG = """\
name = "Awesome Dirty"
repo_slug = "awesome-dirty"
sections = ["Tools"]
"""


def setup(tmp_path: Path, fixture_readme: Callable[[str], str], name: str) -> Path:
    (tmp_path / "awesome.toml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "readme.md").write_text(fixture_readme(name), encoding="utf-8")
    return tmp_path


def test_clean_readme_exits_zero(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = setup(tmp_path, fixture_readme, "clean.md")

    assert run_list_check.main(["--config", str(root / "awesome.toml")]) == 0
    assert "no violations" in capsys.readouterr().out


def test_dirty_readme_exits_nonzero(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = setup(tmp_path, fixture_readme, "dirty-duplicates.md")

    assert run_list_check.main(["--config", str(root / "awesome.toml")]) == 1
    assert "duplicate-urls" in capsys.readouterr().out


def test_report_only_exits_zero(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = setup(tmp_path, fixture_readme, "dirty-duplicates.md")

    code = run_list_check.main(
        ["--config", str(root / "awesome.toml"), "--report-only"]
    )

    assert code == 0
    assert "duplicate-urls" in capsys.readouterr().out


def test_warnings_do_not_block_unless_strict(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = setup(tmp_path, fixture_readme, "dirty-grammar.md")
    config = str(root / "awesome.toml")

    capsys.readouterr()
    assert run_list_check.main(["--config", config]) == 1
    capsys.readouterr()
    assert run_list_check.main(["--config", config, "--report-only"]) == 0
    capsys.readouterr()
    assert run_list_check.main(["--config", config, "--report-only", "--strict"]) == 0


def test_markdown_format(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = setup(tmp_path, fixture_readme, "dirty-duplicates.md")

    run_list_check.main(
        [
            "--config",
            str(root / "awesome.toml"),
            "--report-only",
            "--format",
            "markdown",
        ]
    )

    assert "- `" in capsys.readouterr().out


def test_missing_config_falls_back_to_readme(
    tmp_path: Path, fixture_readme: Callable[[str], str]
) -> None:
    (tmp_path / "readme.md").write_text(fixture_readme("clean.md"), encoding="utf-8")

    assert (
        run_list_check.main(
            [
                "--config",
                str(tmp_path / "absent.toml"),
                "--readme",
                str(tmp_path / "readme.md"),
            ]
        )
        == 0
    )


GITHUB_CONFIG = """\
name = "Awesome Github"
repo_slug = "awesome-github"
sections = ["Tools"]

[github]
stats = true
max_age_days = 36500
snapshot = "github-stats.json"
"""


def github_list(tmp_path: Path, fixture_readme: Callable[[str], str]) -> Path:
    """Write a list whose GitHub entry is missing its stats segment."""
    (tmp_path / "awesome.toml").write_text(GITHUB_CONFIG, encoding="utf-8")
    (tmp_path / "github-stats.json").write_text(
        fixture_readme("github-stats.json"), encoding="utf-8"
    )
    text = fixture_readme("github.md").replace(
        " - ★ 4,210 stars, last push 2024-05-06.", ""
    )
    (tmp_path / "readme.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_missing_github_stats_fails_the_gate(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = github_list(tmp_path, fixture_readme)

    code = run_list_check.main(["--config", str(root / "awesome.toml")])

    assert code == 1
    out = capsys.readouterr().out
    assert "github-stats" in out
    assert "make stats" in out


def test_github_stats_pass_when_the_segment_matches(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = github_list(tmp_path, fixture_readme)
    (root / "readme.md").write_text(fixture_readme("github.md"), encoding="utf-8")

    code = run_list_check.main(["--config", str(root / "awesome.toml")])

    assert code == 0
    assert "no violations" in capsys.readouterr().out


def test_github_stats_off_is_not_checked(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = github_list(tmp_path, fixture_readme)
    (root / "awesome.toml").write_text(
        GITHUB_CONFIG.replace("stats = true", "stats = false"), encoding="utf-8"
    )
    (root / "github-stats.json").unlink()

    assert run_list_check.main(["--config", str(root / "awesome.toml")]) == 0
    assert "no violations" in capsys.readouterr().out


def test_a_missing_snapshot_tells_you_to_run_make_stats(
    tmp_path: Path,
    fixture_readme: Callable[[str], str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = github_list(tmp_path, fixture_readme)
    (root / "github-stats.json").unlink()

    assert run_list_check.main(["--config", str(root / "awesome.toml")]) == 1
    assert "make stats" in capsys.readouterr().out
