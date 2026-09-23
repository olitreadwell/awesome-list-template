"""Every Makefile target has to point at something that exists.

The template ships a menu of automations. A target that names a module or a
script nobody wrote turns `make check-full` into a promise the repo cannot
keep, so each target is expanded with `make -n` and its pieces are checked.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

MAKEFILE_TARGET = re.compile(r"^([a-z][a-z0-9-]*):", re.MULTILINE)
MODULE = re.compile(r"python -m (awesome_list\.[a-z_.]+)")
SCRIPT = re.compile(r"(?:^|\s)((?:jobs|ci|tools)/[\w./-]+\.(?:sh|py))")


def _targets(repo_root: Path) -> list[str]:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    return MAKEFILE_TARGET.findall(makefile)


def _expansion(target: str, repo_root: Path) -> str:
    return subprocess.run(
        ["make", "-n", target],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout


def test_every_python_module_a_target_calls_exists(repo_root: Path) -> None:
    missing = []
    for target in _targets(repo_root):
        for module in MODULE.findall(_expansion(target, repo_root)):
            path = repo_root / "src" / (module.replace(".", "/") + ".py")
            if not path.exists():
                missing.append(f"{target} -> {module}")

    assert missing == []


def test_every_script_a_target_calls_exists(repo_root: Path) -> None:
    missing = []
    for target in _targets(repo_root):
        for line in _expansion(target, repo_root).splitlines():
            for script in SCRIPT.findall(line):
                if not (repo_root / script).exists():
                    missing.append(f"{target} -> {script}")

    assert missing == []
