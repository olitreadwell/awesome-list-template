"""make stats writes the snapshot and the readme; make stats-check never calls out."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from awesome_list.cli import run_stats
from awesome_list.github.github_stats import RepoStats

CONFIG = """\
name = "Awesome Stats"
repo_slug = "awesome-stats"
sections = ["Tools"]

[github]
stats = true
max_age_days = 14
"""

SLUG = "codeforamerica/civic-tech-patterns"
URL = "https://github.com/codeforamerica/civic-tech-patterns"
STATS = RepoStats(slug=SLUG, stars=4210, pushed_at="2024-05-06", archived=False)


def fake_fetch(
    slugs: list[str], *, previous: object = None
) -> tuple[dict[str, RepoStats], tuple[str, ...]]:
    del previous
    return (dict.fromkeys(slugs, STATS), ())


def offline_fetch(
    slugs: list[str], *, previous: object = None
) -> tuple[dict[str, RepoStats], tuple[str, ...]]:
    del slugs, previous
    return {}, (SLUG,)


@pytest.fixture
def list_dir(tmp_path: Path, fixture_readme: Callable[[str], str]) -> Path:
    (tmp_path / "awesome.toml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "readme.md").write_text(fixture_readme("github.md"), encoding="utf-8")
    return tmp_path


def stats_without_the_segment(tmp_path: Path) -> None:
    readme = tmp_path / "readme.md"
    text = readme.read_text(encoding="utf-8")
    readme.write_text(
        text.replace(" - ★ 4,210 stars, last push 2024-05-06.", ""), encoding="utf-8"
    )


def test_stats_writes_both_files(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stats_without_the_segment(list_dir)

    code = run_stats.main(
        ["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch
    )

    assert code == 0
    readme = (list_dir / "readme.md").read_text(encoding="utf-8")
    assert " - ★ 4,210 stars, last push 2024-05-06." in readme
    snapshot = json.loads((list_dir / "github-stats.json").read_text(encoding="utf-8"))
    assert snapshot["repos"][SLUG]["stars"] == 4210
    assert "1 GitHub entries" in capsys.readouterr().out


def test_offline_leaves_everything_alone(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = (list_dir / "readme.md").read_text(encoding="utf-8")

    code = run_stats.main(
        ["--config", str(list_dir / "awesome.toml")], fetch=offline_fetch
    )

    assert code == 0
    assert (list_dir / "readme.md").read_text(encoding="utf-8") == before
    assert not (list_dir / "github-stats.json").exists()
    assert "could not reach the GitHub API" in capsys.readouterr().err


def test_check_passes_for_a_matching_snapshot(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_stats.main(["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch)
    capsys.readouterr()

    code = run_stats.main(["--check", "--config", str(list_dir / "awesome.toml")])

    assert code == 0
    assert "up to date" in capsys.readouterr().out


def test_check_fails_when_the_readme_is_behind(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_stats.main(["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch)
    stats_without_the_segment(list_dir)
    capsys.readouterr()

    code = run_stats.main(["--check", "--config", str(list_dir / "awesome.toml")])

    assert code == 1
    assert "make stats" in capsys.readouterr().out


def test_check_fails_when_there_is_no_snapshot(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_stats.main(["--check", "--config", str(list_dir / "awesome.toml")])

    assert code == 1
    assert "does not exist" in capsys.readouterr().out


def test_check_fails_when_the_snapshot_is_stale(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_stats.main(["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch)
    capsys.readouterr()

    code = run_stats.main(
        ["--check", "--config", str(list_dir / "awesome.toml"), "--today", "2026-12-01"]
    )

    assert code == 1
    assert "days old" in capsys.readouterr().out


def test_missing_config_is_a_clear_exit(capsys: pytest.CaptureFixture[str]) -> None:
    del capsys
    with pytest.raises(SystemExit, match=r"awesome\.toml"):
        run_stats.main(["--config", "nope/awesome.toml"])


def test_report_only_lists_keeps_the_same_fixture_pair_green(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_stats.main(["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch)
    capsys.readouterr()

    assert run_stats.main(["--check", "--config", str(list_dir / "awesome.toml")]) == 0
