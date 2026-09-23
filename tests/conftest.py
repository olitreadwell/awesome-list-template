"""Shared helpers for the test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_readme() -> object:
    """Return a loader for readme fixtures by file name."""

    def load(name: str) -> str:
        return (FIXTURE_DIR / "readme" / name).read_text(encoding="utf-8")

    return load


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root."""
    return Path(__file__).resolve().parents[1]
