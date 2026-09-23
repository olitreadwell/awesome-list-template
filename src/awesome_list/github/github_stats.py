"""Stars and last-push dates for the GitHub repos a list links to.

Pure logic only: this module never touches the network and never reads a file,
so a rule can run it on a fixture. Fetching lives in
`awesome_list.github.fetch_repo_stats`, and the two commands that write live in
`awesome_list.cli.run_stats`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})

# Paths after owner/repo that mean the link is a tab or a query inside a repo
# rather than the repo itself, so stars for the repo would answer the wrong
# question. `tree` and `blob` stay because they point at the repo's content.
RESERVED_REPO_TABS = frozenset(
    {
        "actions",
        "blame",
        "branches",
        "commits",
        "compare",
        "discussions",
        "forks",
        "graphs",
        "issues",
        "labels",
        "milestones",
        "network",
        "projects",
        "pulls",
        "releases",
        "security",
        "settings",
        "stargazers",
        "tags",
        "watchers",
        "wiki",
    }
)

LINK_URL = re.compile(r"\]\(([^)\s]+)\)")
EXISTING_STATS_TAIL = re.compile(r"\s+-\s+★[^★]*?\.\s*$")
STAR_GLYPH = "★"


@dataclass(frozen=True, slots=True)
class RepoStats:
    """What a reader wants to know before clicking: stars and last activity."""

    slug: str
    stars: int
    pushed_at: str
    archived: bool = False


@dataclass(frozen=True, slots=True)
class StatsSnapshot:
    """Every repo stat the last `make stats` run saw, and when it ran."""

    generated_at: str
    repos: Mapping[str, RepoStats]

    def age_days(self, today: date) -> int:
        """Return how many days ago this snapshot was generated."""
        return (today - date.fromisoformat(self.generated_at)).days


def github_repo_slug(url: str) -> str | None:
    """Return `owner/repo` for a repo URL, and None for anything else."""
    parts = urlsplit(url.strip())
    if parts.netloc.lower() not in GITHUB_HOSTS:
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) < 2:
        return None
    owner, repo = segments[0], segments[1]
    if len(segments) > 2 and segments[2].lower() in RESERVED_REPO_TABS:
        return None
    if repo.lower().endswith(".git"):
        repo = repo[: -len(".git")]
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def format_stats(stats: RepoStats) -> str:
    """Return the stats segment as one sentence, with a singular star."""
    noun = "star" if stats.stars == 1 else "stars"
    count = f"{stats.stars:,} {noun}"
    if stats.archived:
        return f"{STAR_GLYPH} {count}, archived {stats.pushed_at}."
    return f"{STAR_GLYPH} {count}, last push {stats.pushed_at}."


def apply_github_stats(
    text: str, stats_map: Mapping[str, RepoStats]
) -> tuple[str, int]:
    """Add a stats segment to every GitHub entry, and count the lines changed.

    Existing segments are replaced rather than stacked, so running this twice
    changes nothing the second time. Lines whose repo has no stats are left
    byte for byte alone.
    """
    lines: list[str] = []
    changed = 0
    for line in text.splitlines(keepends=True):
        slug = _entry_slug(line)
        stats = stats_map.get(slug) if slug else None
        if stats is None:
            lines.append(line)
            continue
        rewritten = _with_stats(line, stats)
        changed += rewritten != line
        lines.append(rewritten)
    return "".join(lines), changed


def _entry_slug(line: str) -> str | None:
    """Return the repo slug of the first markdown link on this line, if any."""
    match = LINK_URL.search(line)
    if match is None:
        return None
    return github_repo_slug(match.group(1))


def _with_stats(line: str, stats: RepoStats) -> str:
    """Replace or append the stats segment, leaving the rest of the line alone."""
    newline = ""
    body = line
    if body.endswith("\n"):
        body, newline = body[:-1], "\n"
    stripped = EXISTING_STATS_TAIL.sub("", body).rstrip()
    return f"{stripped} - {format_stats(stats)}{newline}"
