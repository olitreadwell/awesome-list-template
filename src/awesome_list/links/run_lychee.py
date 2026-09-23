"""The only place that shells out to lychee and git."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence

LYCHEE_MISSING = (
    "links: lychee is not installed. Install it from"
    " https://github.com/lycheeverse/lychee#installation, or run the link check"
    " on a machine that has it."
)


def lychee_binary() -> str:
    """Return the path to lychee, or explain how to get one."""
    found = shutil.which("lychee")
    if found:
        return found
    raise SystemExit(LYCHEE_MISSING)


def run_lychee(command: Sequence[str]) -> int:
    """Run lychee and return its exit code."""
    try:
        return subprocess.run(list(command), check=False).returncode
    except FileNotFoundError:
        raise SystemExit(LYCHEE_MISSING) from None


def git_show(revision: str) -> str:
    """Return the contents of one file at one revision."""
    result = subprocess.run(
        ["git", "show", revision], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(f"links-diff: cannot read {revision}: {result.stderr.strip()}")
    return result.stdout
