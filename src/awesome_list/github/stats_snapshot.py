"""Read and write github-stats.json, the cache every stats check reads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from awesome_list.github.github_stats import RepoStats, StatsSnapshot


class SnapshotError(ValueError):
    """Raised when the snapshot file is unreadable or says something odd."""


def load_stats_snapshot(path: Path) -> StatsSnapshot | None:
    """Return the snapshot at this path, or None when there is no file yet."""
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SnapshotError(f"cannot read {path}: {error}") from error
    return snapshot_from_dict(raw, source=path)


def snapshot_from_dict(raw: Any, *, source: Path) -> StatsSnapshot:
    """Build a snapshot from parsed JSON, rejecting a shape the rules cannot use."""
    if not isinstance(raw, dict):
        raise SnapshotError(f"cannot read {source}: expected an object")
    generated_at = raw.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        raise SnapshotError(f"cannot read {source}: missing generated_at")
    repos_raw = raw.get("repos", {})
    if not isinstance(repos_raw, dict):
        raise SnapshotError(f"cannot read {source}: repos must be an object")

    repos: dict[str, RepoStats] = {}
    for slug, entry in repos_raw.items():
        if not isinstance(entry, dict):
            raise SnapshotError(f"cannot read {source}: {slug} must be an object")
        repos[str(slug)] = RepoStats(
            slug=str(slug),
            stars=int(entry.get("stars", 0)),
            pushed_at=str(entry.get("pushed_at", "")),
            archived=bool(entry.get("archived", False)),
        )
    return StatsSnapshot(generated_at=generated_at, repos=repos)


def snapshot_to_dict(snapshot: StatsSnapshot) -> dict[str, Any]:
    """Return the JSON-ready form, sorted by slug so diffs stay small."""
    return {
        "generated_at": snapshot.generated_at,
        "repos": {
            slug: {
                "stars": stats.stars,
                "pushed_at": stats.pushed_at,
                "archived": stats.archived,
            }
            for slug, stats in sorted(snapshot.repos.items())
        },
    }


def write_stats_snapshot(path: Path, snapshot: StatsSnapshot) -> None:
    """Write the snapshot with a trailing newline, ready for git."""
    body = json.dumps(snapshot_to_dict(snapshot), indent=2) + "\n"
    path.write_text(body, encoding="utf-8")
