"""The awesome.re submission requirements that a script can decide.

Every check here reads files on disk and nothing else, so it runs offline and
in a hook. The manual reminders the guidelines list are printed, not judged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from awesome_list.config.list_config import ListConfig
from awesome_list.parse.readme_model import ListDocument

CONTRIBUTING_NAMES = (
    "contributing.md",
    "CONTRIBUTING.md",
    ".github/CONTRIBUTING.md",
)
LICENSE_NAMES = ("license", "LICENSE", "LICENSE.md", "license.md")
CONDUCT_NAMES = (
    "code-of-conduct.md",
    "CODE_OF_CONDUCT.md",
    "code_of_conduct.md",
    ".github/CODE_OF_CONDUCT.md",
)
MANUAL_REMINDERS = (
    "The pull request only adds to the list, it does not restructure it.",
    "Every new entry came from a human who checked it.",
    "The list is the only change: no unrelated files in the pull request.",
)


@dataclass(frozen=True, slots=True)
class SubmissionFinding:
    """One requirement, and whether the repo meets it."""

    name: str
    ok: bool
    detail: str


def check_submission(
    document: ListDocument, text: str, root: Path, config: ListConfig
) -> tuple[SubmissionFinding, ...]:
    """Return every checkable submission requirement."""
    return (
        _badge(text),
        _no_ci_badge(text),
        _single_heading(document),
        _contents(text),
        _file(root, "CONTRIBUTING", CONTRIBUTING_NAMES),
        _file(root, "LICENSE", LICENSE_NAMES),
        _file(root, "CODE_OF_CONDUCT", CONDUCT_NAMES),
        _sections(document, config),
        _entries(document),
    )


def _badge(text: str) -> SubmissionFinding:
    ok = "awesome.re/badge" in text
    return SubmissionFinding(
        "awesome badge",
        ok,
        "readme links the awesome badge" if ok else "the readme has no awesome badge",
    )


def _no_ci_badge(text: str) -> SubmissionFinding:
    needles = ("actions/workflow", "travis-ci", "circleci")
    hits = [name for name in needles if name in text]
    return SubmissionFinding(
        "no CI badge",
        not hits,
        "no CI badge in the readme"
        if not hits
        else f"CI badge found: {', '.join(hits)}",
    )


def _single_heading(document: ListDocument) -> SubmissionFinding:
    titles = [heading for heading in document.headings if heading.level == 1]
    return SubmissionFinding(
        "one h1",
        len(titles) == 1,
        f"{len(titles)} top level heading(s)",
    )


def _contents(text: str) -> SubmissionFinding:
    ok = any(
        line.strip().lower() in {"## contents", "## table of contents"}
        for line in text.splitlines()
    )
    return SubmissionFinding(
        "contents section",
        ok,
        "the readme has a Contents section" if ok else "no Contents section",
    )


def _file(root: Path, label: str, names: tuple[str, ...]) -> SubmissionFinding:
    found = next((name for name in names if (root / name).exists()), None)
    return SubmissionFinding(
        label.lower().replace("_", " "),
        found is not None,
        found or f"no {label} file",
    )


def _sections(document: ListDocument, config: ListConfig) -> SubmissionFinding:
    present = {section.name for section in document.sections}
    missing = [name for name in config.sections if name not in present]
    return SubmissionFinding(
        "config sections",
        not missing,
        "every configured section is in the readme"
        if not missing
        else f"missing: {', '.join(missing)}",
    )


def _entries(document: ListDocument) -> SubmissionFinding:
    described = [entry for entry in document.entries if entry.description]
    return SubmissionFinding(
        "entries have descriptions",
        len(described) == len(document.entries),
        f"{len(described)}/{len(document.entries)} entries carry a description",
    )
