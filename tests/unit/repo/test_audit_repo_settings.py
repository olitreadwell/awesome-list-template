"""Repo settings drift is reported, never silently fixed."""

from __future__ import annotations

from awesome_list.repo.audit_repo_settings import RepoSettings, audit_repo_settings


def _settings(**overrides: object) -> RepoSettings:
    base: dict[str, object] = {
        "slug": "olitreadwell/awesome-example",
        "description": "A curated list of example things.",
        "topics": ("awesome", "awesome-list", "curated-list"),
        "default_branch": "main",
        "archived": False,
        "has_issues": True,
        "license_name": "MIT",
    }
    base.update(overrides)
    return RepoSettings(**base)  # type: ignore[arg-type]


def test_a_healthy_repo_has_no_drift() -> None:
    assert audit_repo_settings(_settings()).drift == ()


def test_a_missing_topic_is_drift_with_a_fix() -> None:
    drift = audit_repo_settings(_settings(topics=("awesome",))).drift

    assert [finding.name for finding in drift] == ["topics"]
    assert "awesome-list" in drift[0].detail
    assert drift[0].fix == "run make repo-setup --apply"


def test_an_empty_description_is_drift() -> None:
    drift = audit_repo_settings(_settings(description="   ")).drift

    assert [finding.name for finding in drift] == ["description"]


def test_a_master_default_branch_is_drift() -> None:
    drift = audit_repo_settings(_settings(default_branch="master")).drift

    assert [finding.name for finding in drift] == ["default branch"]
    assert drift[0].fix == "rename the default branch to main"


def test_an_archived_repo_is_drift() -> None:
    drift = audit_repo_settings(_settings(archived=True)).drift

    assert [finding.name for finding in drift] == ["archived"]
    assert drift[0].ok is False


def test_a_repo_without_a_license_is_drift() -> None:
    drift = audit_repo_settings(_settings(license_name=None)).drift

    assert [finding.name for finding in drift] == ["license"]
