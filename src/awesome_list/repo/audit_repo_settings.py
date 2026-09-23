"""Compare the hosting platform's settings with what the list needs."""

from __future__ import annotations

from dataclasses import dataclass, field

WANTED_TOPICS = ("awesome", "awesome-list", "curated-list")
# GitHub reports these when it cannot match the file to a known licence.
UNRECOGNISED_LICENSES = frozenset({"NOASSERTION", "Other"})
WANTED_BRANCH = "main"


@dataclass(frozen=True, slots=True)
class RepoSettings:
    """The settings gh reports for a repository."""

    slug: str
    description: str = ""
    topics: tuple[str, ...] = ()
    default_branch: str = ""
    archived: bool = False
    has_issues: bool = True
    license_name: str | None = None


@dataclass(frozen=True, slots=True)
class SettingsFinding:
    """One setting, and whether it matches."""

    name: str
    ok: bool
    detail: str
    fix: str = ""


@dataclass(frozen=True, slots=True)
class AuditResult:
    """Every finding for one repository."""

    findings: tuple[SettingsFinding, ...] = field(default_factory=tuple)

    @property
    def drift(self) -> tuple[SettingsFinding, ...]:
        return tuple(finding for finding in self.findings if not finding.ok)


def audit_repo_settings(settings: RepoSettings) -> AuditResult:
    """Return every setting that drifted from what a submission needs."""
    return AuditResult(
        findings=(
            _topics(settings),
            _description(settings),
            _branch(settings),
            _archived(settings),
            _license(settings),
        )
    )


def _topics(settings: RepoSettings) -> SettingsFinding:
    missing = [topic for topic in WANTED_TOPICS if topic not in settings.topics]
    return SettingsFinding(
        "topics",
        not missing,
        "all submission topics are set"
        if not missing
        else f"missing topics: {', '.join(missing)}",
        fix="run make repo-setup --apply",
    )


def _description(settings: RepoSettings) -> SettingsFinding:
    ok = bool(settings.description.strip())
    return SettingsFinding(
        "description",
        ok,
        settings.description or "the repository has no description",
        fix="run make repo-setup --apply",
    )


def _branch(settings: RepoSettings) -> SettingsFinding:
    ok = settings.default_branch == WANTED_BRANCH
    return SettingsFinding(
        "default branch",
        ok,
        settings.default_branch or "unknown",
        fix=f"rename the default branch to {WANTED_BRANCH}",
    )


def _archived(settings: RepoSettings) -> SettingsFinding:
    return SettingsFinding(
        "archived",
        not settings.archived,
        "archived" if settings.archived else "not archived",
        fix="unarchive, or the list cannot take a pull request",
    )


def _license(settings: RepoSettings) -> SettingsFinding:
    name = settings.license_name or ""
    ok = bool(name) and name not in UNRECOGNISED_LICENSES
    return SettingsFinding(
        "license",
        ok,
        name or "no license file detected",
        fix="use a standard licence text, such as the full CC0 legal code;"
        " GitHub cannot tell what a stub is",
    )
