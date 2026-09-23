"""Ask the GitHub API for stars and last-push dates, through the gh CLI.

Network calls live here and nowhere else, and a runner is injectable so tests
never touch the network. Every failure is soft: a slug that cannot be fetched
keeps the number the previous snapshot held, so being offline or rate limited
never corrupts a list.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterable, Mapping

from awesome_list.github.github_stats import RepoStats

Runner = Callable[[str], str]


class FetchError(RuntimeError):
    """Raised when gh cannot answer for a slug."""


def run_gh_api(slug: str) -> str:
    """Return the raw JSON for one repo, raising FetchError if gh fails."""
    result = subprocess.run(
        ["gh", "api", f"repos/{slug}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        reason = result.stderr.strip().splitlines()
        detail = reason[-1] if reason else f"exit {result.returncode}"
        raise FetchError(f"gh api repos/{slug}: {detail}")
    return result.stdout


def parse_repo_json(slug: str, payload: str) -> RepoStats:
    """Turn a GitHub repo payload into the stats a list shows."""
    data = json.loads(payload)
    pushed_at = str(data.get("pushed_at") or "")[:10]
    return RepoStats(
        slug=slug,
        stars=int(data.get("stargazers_count") or 0),
        pushed_at=pushed_at,
        archived=bool(data.get("archived")),
    )


def fetch_repo_stats(
    slugs: Iterable[str],
    *,
    run: Runner = run_gh_api,
    previous: Mapping[str, RepoStats] | None = None,
) -> tuple[dict[str, RepoStats], tuple[str, ...]]:
    """Return stats per slug, plus the slugs that could not be fetched.

    A slug that fails keeps its previous stats, because stale numbers beat
    deleted numbers when the network is unavailable.
    """
    carried = dict(previous or {})
    stats: dict[str, RepoStats] = {}
    unfetched: list[str] = []
    for slug in slugs:
        try:
            stats[slug] = parse_repo_json(slug, run(slug))
        except (FetchError, OSError, json.JSONDecodeError, ValueError):
            unfetched.append(slug)
            if slug in carried:
                stats[slug] = carried[slug]
    return stats, tuple(unfetched)
