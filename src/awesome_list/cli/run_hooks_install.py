"""Point git at the versioned hooks in .githooks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Set core.hooksPath and report what happened."""
    del argv
    root = Path(__file__).resolve().parents[3]
    hooks = root / ".githooks"
    if not hooks.is_dir():
        raise SystemExit(f"hooks-install: {hooks} does not exist")
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"], cwd=root, check=True
    )
    print("hooks-install: core.hooksPath = .githooks")
    for name in sorted(path.name for path in hooks.iterdir()):
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
