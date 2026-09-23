"""One violation, rendered the same way everywhere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warn"]


@dataclass(frozen=True, slots=True)
class RuleViolation:
    """A single rule failure, with where it is and how to fix it.

    Errors are mechanical and safe to fix without touching anyone's prose:
    a separator, a period, a capital, a tag, a duplicate, a stale table of
    contents. Warnings need a human to write something, so they never block a
    branch on their own.
    """

    rule: str
    line: int
    message: str
    fix: str = ""
    file: str = "readme.md"
    severity: Severity = "error"

    def render(self) -> str:
        """Return a one-line report for a terminal."""
        label = "" if self.severity == "error" else " (warning)"
        fix = f" Fix: {self.fix}" if self.fix else ""
        return f"{self.file}:{self.line}: {self.rule}: {self.message}{label}{fix}"
