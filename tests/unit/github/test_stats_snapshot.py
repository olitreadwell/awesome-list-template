"""github-stats.json round trips, and a broken file is named clearly."""

from __future__ import annotations

from pathlib import Path

import pytest

from awesome_list.github.github_stats import RepoStats, StatsSnapshot
from awesome_list.github.stats_snapshot import (
    SnapshotError,
    load_stats_snapshot,
    snapshot_to_dict,
    write_stats_snapshot,
)

SNAPSHOT = StatsSnapshot(
    generated_at="2026-09-23",
    repos={
        "owner/repo": RepoStats(
            slug="owner/repo", stars=12, pushed_at="2026-09-01", archived=True
        )
    },
)


def test_missing_file_is_none_not_an_error(tmp_path: Path) -> None:
    assert load_stats_snapshot(tmp_path / "absent.json") is None


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "github-stats.json"
    write_stats_snapshot(path, SNAPSHOT)

    assert load_stats_snapshot(path) == SNAPSHOT


def test_written_file_is_sorted_and_newline_terminated(tmp_path: Path) -> None:
    path = tmp_path / "github-stats.json"
    write_stats_snapshot(path, SNAPSHOT)
    body = path.read_text(encoding="utf-8")

    assert body.endswith("\n")
    assert list(snapshot_to_dict(SNAPSHOT)["repos"]) == ["owner/repo"]


def test_broken_json_raises_snapshot_error(tmp_path: Path) -> None:
    path = tmp_path / "github-stats.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(SnapshotError, match="cannot read"):
        load_stats_snapshot(path)


def test_missing_generated_at_raises(tmp_path: Path) -> None:
    path = tmp_path / "github-stats.json"
    path.write_text('{"repos": {}}', encoding="utf-8")

    with pytest.raises(SnapshotError, match="generated_at"):
        load_stats_snapshot(path)


def test_repos_must_be_an_object(tmp_path: Path) -> None:
    path = tmp_path / "github-stats.json"
    path.write_text('{"generated_at": "2026-09-23", "repos": []}', encoding="utf-8")

    with pytest.raises(SnapshotError, match="repos must be an object"):
        load_stats_snapshot(path)
