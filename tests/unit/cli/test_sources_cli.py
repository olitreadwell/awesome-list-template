"""make sources writes a report, and never touches the readme."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from awesome_list.cli import run_sources

CONFIG = """\
name = "Awesome Data"
repo_slug = "awesome-data"
sections = ["Tools"]

[sources]
lists = ["https://upstream.test/table-list.md"]
keywords = ["new zealand", "government"]
"""

TARGET = """\
# Awesome Data [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> Data sources.

## Contents

- [Tools](#tools)

## Tools

- [Cat Facts](https://catfact.ninja/) - already here.
"""


@pytest.fixture
def list_dir(tmp_path: Path, fixture_readme: Callable[[str], str]) -> Path:
    (tmp_path / "awesome.toml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "readme.md").write_text(TARGET, encoding="utf-8")
    return tmp_path


def fake_fetch(urls: object, **_: object) -> tuple[dict[str, str], tuple[str, ...]]:
    del urls
    return ({"https://upstream.test/table-list.md": TABLE}, ())


TABLE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "sources" / "table-list.md"
).read_text(encoding="utf-8")


def test_writes_a_report_and_leaves_the_readme_alone(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = (list_dir / "readme.md").read_text(encoding="utf-8")

    code = run_sources.main(
        ["--config", str(list_dir / "awesome.toml")], fetch=fake_fetch
    )

    assert code == 0
    report = (list_dir / "reports" / "source-candidates.md").read_text(encoding="utf-8")
    assert "Open Government, New Zealand" in report
    assert "Cat Facts" not in report
    assert (list_dir / "readme.md").read_text(encoding="utf-8") == before
    assert "3 candidates from 1 lists" in capsys.readouterr().out


def test_stdout_prints_instead_of_writing(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_sources.main(
        ["--config", str(list_dir / "awesome.toml"), "--stdout"], fetch=fake_fetch
    )

    assert code == 0
    assert "Source candidates" in capsys.readouterr().out
    assert not (list_dir / "reports").exists()


def test_no_sources_configured_is_a_no_op(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (list_dir / "awesome.toml").write_text(
        CONFIG.split("[sources]")[0], encoding="utf-8"
    )

    assert run_sources.main(["--config", str(list_dir / "awesome.toml")]) == 0
    assert "nothing to do" in capsys.readouterr().out


def test_every_source_down_writes_nothing(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def dead(urls: object, **_: object) -> tuple[dict[str, str], tuple[str, ...]]:
        del urls
        return {}, ("https://upstream.test/table-list.md",)

    assert (
        run_sources.main(["--config", str(list_dir / "awesome.toml")], fetch=dead) == 0
    )
    assert "no report written" in capsys.readouterr().err
    assert not (list_dir / "reports").exists()


def test_a_source_argument_overrides_the_config(
    list_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_sources.main(
        [
            "--config",
            str(list_dir / "awesome.toml"),
            "--source",
            "https://other.test/list.md",
            "--stdout",
        ],
        fetch=fake_fetch,
    )

    assert code == 0
    assert capsys.readouterr().out


def test_github_stats_from_the_snapshot_ride_along(tmp_path: Path) -> None:
    (tmp_path / "awesome.toml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "readme.md").write_text(TARGET, encoding="utf-8")
    (tmp_path / "github-stats.json").write_text(
        '{"generated_at": "2026-09-23", "repos": {"owner/repo": '
        '{"stars": 9, "pushed_at": "2026-01-01", "archived": false}}}',
        encoding="utf-8",
    )
    table = "| [Repo](https://github.com/owner/repo) | a government thing |\n"

    def one(urls: object, **_: object) -> tuple[dict[str, str], tuple[str, ...]]:
        del urls
        return ({"https://upstream.test/table-list.md": table}, ())

    assert (
        run_sources.main(["--config", str(tmp_path / "awesome.toml")], fetch=one) == 0
    )
    report = (tmp_path / "reports" / "source-candidates.md").read_text(encoding="utf-8")
    assert "★ 9 stars, last push 2026-01-01." in report
