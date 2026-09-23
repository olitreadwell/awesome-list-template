"""The only place that shells out to gh for repository settings."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from typing import Any, cast


def run_gh(command: Sequence[str], body: str | None = None) -> str:
    """Run one gh command and return its stdout.

    ``body`` is sent on stdin, which is how gh takes a JSON request body
    (``--input -``). Repeating -f flags cannot express a JSON array.
    """
    result = subprocess.run(
        list(command), input=body, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"{command[0]} failed")
    return result.stdout.strip()


def origin_remote() -> str:
    """Return owner/name for the origin remote."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    url = result.stdout.strip()
    if not url:
        raise SystemExit("repo-setup: no origin remote; pass --slug")
    return url.removesuffix(".git").split("github.com", 1)[-1].lstrip("/: ")


def fetch_repo_settings(slug: str) -> dict[str, object]:
    """Return the settings gh reports for one repository. Read only."""
    raw = run_gh(
        [
            "gh",
            "api",
            f"repos/{slug}",
            "--jq",
            "{description: .description, topics: .topics, default_branch:"
            " .default_branch, archived: .archived, has_issues: .has_issues,"
            " license: .license.spdx_id}",
        ]
    )
    return cast("dict[str, Any]", json.loads(raw))
